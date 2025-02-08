"""
Helper functions for tweet claim pair collection
"""
import json
import difflib
from datetime import datetime
import requests
import pandas as pd
from twarc import Twarc2
from credentials import BEARER_TOKEN
import spacy
import csv
import re
from lxml import etree
from string import punctuation
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from googletrans import Translator
from tqdm import tqdm
from credentials import CLAIMBUSTER_HEADER
from random import shuffle, seed
import codecs
import translitcodec
from collections import defaultdict
from constants import state_names, title_prefixes, stop_words
from html import unescape

pd.options.mode.chained_assignment = None
seed(42)
nlp = spacy.load("en_core_web_sm")
translator = Translator()
model = SentenceTransformer("all-MiniLM-L6-v2")
punctuation += "’"

# apply claimbuster to identify check worthy tweets
requests.adapters.DEFAULT_RETRIES = 5
claimbuster_api = requests.session()
claimbuster_api.keep_alive = True


def apply_claimbuster(input_claim, mode):
    """
    apply claimbuster to identify check worthy tweets
    """
    if mode == "server":
        api_endpoint = (
            f"http://192.168.1.13/claimbuster-prod/api/v2/score/text/{input_claim}"
        )
    elif mode == "local":
        api_endpoint = (
            f"https://idir.uta.edu/claimbuster/api/v2/score/text/{input_claim}"
        )
    try:
        response = claimbuster_api.get(url=api_endpoint, headers=CLAIMBUSTER_HEADER)
    except Exception as e:
        print("Cannot apply claimbuster to {}, error: {}".format(input_claim, e))
        return None
    if response:
        response = response.json()
    return response["results"][0]["score"] if response and response["results"] else None


def get_factchecks(first_rows=None, last_rows=None, from_to=None, sample_size=0):
    """
    return dataframe in specified range
    """
    politifact_df = pd.read_csv(
        "./data_collection/raw_data/factcheckrepo/politifact_with_uuid.csv"
    )
    politifact_df = politifact_df.iloc[::-1]
    if sample_size:
        return politifact_df.sample(n=sample_size, random_state=42)
    elif first_rows:
        return politifact_df.head(first_rows)
    elif last_rows:
        return politifact_df.tail(last_rows)
    elif from_to:
        return politifact_df.iloc[from_to[0] : from_to[1]]
    else:
        return politifact_df


def remove_url_and_mention_hashtag(text):
    """
    remove urls, mentions and hashtag from tweet
    """
    text = re.sub(
        r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
        "",
        text.strip(),
    )
    text = re.sub(r"(@[A-Za-z0-9]+)", "", text.strip())
    text = re.sub(r"(#[A-Za-z0-9]+)", "", text.strip())
    return text


def is_English_text(text):
    """
    check if tweet
    """
    try:
        dec_lan = translator.detect(text)
        if dec_lan.lang == "en":
            return True
        else:
            return False
    except:
        return False


def string_similarity(s_1, s_2):
    """
    Compute string similarity of two tweets by difflib
    """
    s_1, s_2 = (
        remove_url_and_mention_hashtag(s_1).lower(),
        remove_url_and_mention_hashtag(s_2).lower(),
    )
    return difflib.SequenceMatcher(None, s_1, s_2).quick_ratio()


def semantic_similarity(s_1, s_2):
    """
    Compute semantic similarity of two tweets by Sentence Transformer
    """
    embeddings = model.encode([s_1, s_2])
    return cosine_similarity(embeddings[:1], embeddings[1:]).flatten()[0]


def is_token_legal(token, mode="nva"):
    """
    check if token is legal
    mode: noun, verb, adjective
    """
    legal_words = ("covid-19", "covid19")
    banned_words = ("quote", "say", "tests", "said", "quoted")
    if any(w == token.text.lower() for w in legal_words):
        return True
    if token.is_space or token.is_punct:
        return False
    if any(w == token.text.lower() for w in banned_words):
        return False
    if any(c in punctuation for c in token.text):
        return False
    if token.text.lower() in stop_words:
        return False
    if mode == "nva":
        if (
            token.pos_ != "PROPN"
            and token.pos_ != "NOUN"
            and token.pos_ != "ADJ"
            and token.pos_ != "VERB"
            and token.pos_ != "NUM"
        ):
            return False
        else:
            return True
    if mode == "nv":
        if (
            token.pos_ != "PROPN"
            and token.pos_ != "NOUN"
            and token.pos_ != "VERB"
            and token.pos_ != "NUM"
        ):
            return False
        else:
            return True
    if mode == "na":
        if (
            token.pos_ != "PROPN"
            and token.pos_ != "NOUN"
            and token.pos_ != "ADJ"
            and token.pos_ != "NUM"
        ):
            return False
        else:
            return True
    if mode == "n":
        if token.pos_ != "PROPN" and token.pos_ != "NOUN" and token.pos_ != "NUM":
            return False
        else:
            return True
    else:
        raise ValueError("Invalid mode provided in is_token_legal function")


def remove_short_keywords(keywords):
    """
    remove short keywords that less than 4 words
    """
    keywords = set(keywords)
    if len(keywords) < 5:
        return ""
    else:
        return " ".join(list(keywords))


def keywords_extractor(claim, mode="nva"):
    """
    Use only nouns, adjectives, verbs and numbers in the claim
    Remove Auxiliary(is, has, will, do, should) and Adposition(in, to, during), stop words.
    """
    claim = nlp(claim)
    kws = []
    # print('Claim: ', claim)
    for token in claim:
        # print(token.text, token.pos_)
        if is_token_legal(token, mode=mode):
            kws.append(token.text.lower())
    # kws = remove_short_keywords(kws)
    return kws


def format_time(timestamp):
    """
    format time as 'YYYY-MM-DD'
    """
    try:  # Mar 1, 2020
        timestamp = datetime.strptime(timestamp, "%b %d, %Y").strftime("%Y-%m-%d")
    except Exception as e:
        print(e)
        if len(timestamp) > 3:  # Oct 26
            curr_year = str(datetime.now().year)
            timestamp = curr_year + datetime.strptime(
                curr_year + " " + timestamp, "%Y %b %d"
            ).strftime("-%m-%d")
        else:  # 9h 21h
            now = datetime.now()
            timestamp = "-".join([str(now.year), str(now.month), str(now.day)])
    return timestamp


def json_to_csv(json_path, csv_path):
    """
    save json file to csv file
    """
    with open(json_path, "r") as f:
        dataset = json.load(f)
        dataset = pd.DataFrame(dataset)
        dataset["screening"] = -3
        dataset["answered"] = 0

        dataset = dataset[
            [
                "id",
                "claim_author",
                "claim_text",
                "tweet_text",
                "screening",
                "answered",
                "tweet_url_title",
                "claim_timestamp",
                "tweet_timestamp",
                "tweet_id",
                "tweet_userhandle",
                "retweet_count",
                "reply_count",
                "quote_count",
                "claim_source",
                "claim_verdict",
                "factcheck_timestamp",
                "claim_review_summary",
                "claim_review",
                "factcheck_url",
                "claim_tags",
                "claimbuster_score",
                "pair_id",
            ]
        ]
        dataset.to_csv(csv_path, index=False, encoding="uft-8")
        print("Successfully created the CSV file from JSON")



def postprocess_csv(csv_path):
    """ csv file header
    idx,pair_id,factcheck_id,claim_author,raw_claim,raw_tweet,tweet_stance,claim_timestamp,tweet_timestamp,twitter_user,factcheck_timestamp,factcheck_source,claim_verdict
    """
    df = pd.read_csv(csv_path)  # 19023
    df["twitter_user"] = df["twitter_user"].fillna("Anonymity")
    print("The shape of raw csv file: {}".format(df.shape))
    df = df[df["raw_claim"].str.contains("\?") == False]  # 18095
    print("The shape of dataframe after remove question claims: {}".format(df.shape))
    df = df[df["raw_tweet"].str.len() > 30]  # 18051
    print("The shape of dataframe after remove short tweets: {}".format(df.shape))
    df = df.drop_duplicates(subset=["raw_tweet"])  # 16997
    print("The shape of dataframe after remove duplicate tweets: {}".format(df.shape))

    final_rows = []
    nonverb_cnt = 0
    for idx, row in df.iterrows():
        # remove non-claim pairs: Fake News about the Florida School Shooting; Proposition 205 "blocks market entry" for new marijuana dispensaries; "No Collusion, No Obstruction, Complete and Total EXONERATION."
        claim = nlp(row["raw_claim"])
        pos = [token.pos_ for token in claim]
        if "VERB" not in pos and "AUX" not in pos:
            nonverb_cnt += 1
            continue
        # remove Says, Said, Claimed, State and that at the beginning of the claim
        while row["raw_claim"][:12] == "Claimed that":
            row["raw_claim"] = row["raw_claim"][12:].strip()
        while row["raw_claim"][:11] == "Claims that":
            row["raw_claim"] = row["raw_claim"][11:].strip()
        while row["raw_claim"][:10] == "Claim that":
            row["raw_claim"] = row["raw_claim"][10:].strip()
        while row["raw_claim"][:11] == "Stated that":
            row["raw_claim"] = row["raw_claim"][11:].strip()
        while row["raw_claim"][:11] == "States that":
            row["raw_claim"] = row["raw_claim"][11:].strip()
        while row["raw_claim"][:10] == "State that":
            row["raw_claim"] = row["raw_claim"][10:].strip()
        while row["raw_claim"][:8] == "Say that":
            row["raw_claim"] = row["raw_claim"][8:].strip()
        while row["raw_claim"][:9] == "Says that":
            row["raw_claim"] = row["raw_claim"][9:].strip()
        while row["raw_claim"][:9] == "Said that":
            row["raw_claim"] = row["raw_claim"][9:].strip()

        while row["raw_claim"][:7] == "Claimed":
            row["raw_claim"] = row["raw_claim"][7:].strip()
        while row["raw_claim"][:6] == "Claims":
            row["raw_claim"] = row["raw_claim"][6:].strip()
        while row["raw_claim"][:5] == "Claim":
            row["raw_claim"] = row["raw_claim"][5:].strip()
        while row["raw_claim"][:6] == "Stated":
            row["raw_claim"] = row["raw_claim"][6:].strip()
        while row["raw_claim"][:6] == "States":
            row["raw_claim"] = row["raw_claim"][6:].strip()
        while row["raw_claim"][:5] == "State":
            row["raw_claim"] = row["raw_claim"][5:].strip()
        while row["raw_claim"][:4] in ["Says", "Said"]:
            row["raw_claim"] = row["raw_claim"][4:].strip()
        while row["raw_claim"][:3] == "Say":
            row["raw_claim"] = row["raw_claim"][3:].strip()
        while row["raw_claim"][:4] in ["That", "that"]:
            row["raw_claim"] = row["raw_claim"][4:].strip()

        # clean claim text: remove quotation mark, replace \n with space, replace | to .
        row["raw_claim"] = (
            row["raw_claim"]
            .replace("|", ".")
            .replace("\n", " ")
            .replace('"', "")
            .replace("“", "")
            .replace("”", "")
        )
        # clean tweet text: replace \n with space, replace | to . and remove unwanted dot
        row["raw_tweet"] = (
            row["raw_tweet"].replace("|", ".").replace("\n", " ").replace(".@", "@")
        )

        if row["raw_tweet"][0] == ".":
            row["raw_tweet"] = row["raw_tweet"][1:]
        row["claim_author"] = row["claim_author"].replace("|", ".").replace("\n", " ")
        row["twitter_user"] = row["twitter_user"].replace("|", ".").replace("\n", " ")
        final_rows.append(row)
    df = pd.DataFrame(final_rows)  # 16507 => 15470 => 14937
    print(df.shape)
    df["idx"] = [i + 1 for i in range(df.shape[0])]
    df.to_csv(
        "./datasets/tweet-claim_v8_postprocessed.csv",
        index=False,
        sep="|",
        quoting=csv.QUOTE_NONE,
    )


def verify_csv(csv_path):
    df = pd.read_csv(csv_path, sep="|")  # 19023
    cnt = 0
    for idx, row in df.iterrows():
        print(row["raw_claim"])
        print(row["raw_tweet"])
        print("------" * 4)
        cnt += 1
        if cnt > 20:
            break
    return True


def tweet_filter(json_path, filtered_json_path):
    """
    1. filter tweets that too short, semantic similarity is too low, not in English
    2. save tweets into `filtered_json_path`
    """
    with open(json_path, "r") as f:
        with open(filtered_json_path, "w") as output:
            dataset = json.load(f)
            # dataset = dataset[:10]
            output.write("[")
            fails = 0
            for _, item in enumerate(tqdm(dataset)):
                claim_text = item["claim_text"]
                tweet_text = remove_url_and_mention_hashtag(item["tweet_text"])
                if tweet_text.strip():
                    is_English = is_English_text(tweet_text)
                else:
                    is_English = False
                semantic_sim = semantic_similarity(claim_text, tweet_text)
                if (
                    len(tweet_text) < len(claim_text) // 4
                    or not is_English
                    or semantic_sim < 0.36
                ):
                    fails += 1
                    continue
                output.write(json.dumps(item))
                output.write(",\n")
            output.write("]")
    print(f"# tweets removed: {fails}; removed percentage: {fails/len(dataset)}")


def format_url(tweet_text, urls):
    """
    Extract titles from tweet json's urls
    """
    titles = []
    for url_info in urls:
        tweet_text = tweet_text.replace(url_info["url"], url_info["expanded_url"])
        if "title" in url_info:
            titles.append(url_info["title"])
    return tweet_text, ", ".join(titles)


def extract_tweet_from_json(json_path):
    """
    extract non-health-related tweet texts from json file
    """
    ans = []
    tags = set()
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in dataset:
            tags.add(item["claim_tags"])
            if (
                "health" not in item["claim_tags"].lower()
                and "medicare" not in item["claim_tags"].lower()
                and "disability" not in item["claim_tags"].lower()
                and "health" not in item["tweet"].lower()
                and "medicare" not in item["tweet"].lower()
                and "disability" not in item["tweet"].lower()
            ):
                ans.append(item)
    return ans


def find_full_url(tweet_text):
    """
    replace short url with full url
    """
    for url in re.findall(r"http\S+", tweet_text):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=5)
            print(response.json)
            tweet_text = tweet_text.replace(url, response.url)
        except:
            continue
    return tweet_text


def remove_factcheck_tweet_from_json(json_path):
    """
    remove fact check tweet from the collect dataset json
    """
    ans = []
    factcheck_websites = (
        "politifact",
        "factstream",
        "washingtonpost",
        "factcheck",
        "snopes",
        "flip-flop",
        "pants on fire",
        "fact-check",
        "fact check",
        "factcheck",
        "rating",
        "rated",
    )
    cnt = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            for fw in factcheck_websites:
                if fw in item["tweet"].lower():
                    break
            else:
                cnt += 1
                item["idx"] = cnt
                ans.append(item)
    # print(len(ans)) # 30498
    print("Pairs count after remove fact check special case: ", cnt)
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v1.2.json", "w"
    ) as f:
        json.dump(ans, f, indent=4)
    return True


def remove_factcheck_tweet(json_path):
    """
    remove fact check tweet from the collect dataset json
    """

    def check_factcheck_url(tweet_text):
        factcheck_websites = (
            "politifact",
            "factstream",
            "factcheck",
            "snopes",
            "fact-check",
            "factchecking",
        )
        has_factcheck_url = False
        for url in re.findall(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
            tweet_text,
        ):
            if any(fw in "/".join(url) for fw in factcheck_websites):
                has_factcheck_url = True
                break
        tweet_text = re.sub(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
            "THEURL",
            tweet_text,
        )
        return has_factcheck_url, tweet_text

    def check_claimant(tweet_text, claimant):
        tweet_text = tweet_text.lower()
        claimant = claimant.lower()
        has_claimant = False
        if claimant in tweet_text:
            tweet_text = tweet_text.replace(claimant, "THECLAIMANT")
            has_claimant = True
        else:
            for claimant in claimant.split():
                if claimant in tweet_text:
                    tweet_text = tweet_text.replace(claimant, "THECLAIMANT")
                    has_claimant = True
                    break
        return has_claimant, tweet_text

    def check_websitename(tweet_text):
        factcheck_websites = (
            "politifact",
            "factstream",
            "washingtonpost",
            "factcheck",
            "snopes",
            "fact check",
            "poynter",
        )
        tweet_text = tweet_text.lower()
        has_verdict = False
        for website in factcheck_websites:
            if website in tweet_text:
                tweet_text = tweet_text.replace(website, "THEWEBSITE")
                has_verdict = True
        return has_verdict, tweet_text

    def check_verdict(tweet_text):
        verdicts = (
            "mostlytrue",
            "mostly true",
            "halftrue",
            "half true",
            "mostlyfalse",
            "mostly false",
            "true",
            "falsely",
            "false",
            "pantsonfire",
            "pants on fire",
            "pant on fire",
            "pantonfire",
            "misleading",
        )
        tweet_text = tweet_text.lower()
        for verdict in verdicts:
            if verdict in tweet_text:
                tweet_text = tweet_text.replace(verdict, "THEVERDICT")
        return tweet_text.lower()

    def check_prefix(tweet_text):
        user_title_prefixes = [x.lower() for x in state_names + title_prefixes]
        prefixes = (
            "via",
            "flipometer",
            "truthometer",
            "icymi",
            "factcheck",
            "rated",
            "rating",
            "rt",
            "mt",
            "says",
            "said",
            "claimed",
            "claims",
            "claim",
            "say",
            "state",
            "states",
            "stated",
        )
        _tweet_text = []
        # remove prefixes from tweet_text
        for w in tweet_text.split():
            for prefix in prefixes:
                if w.lower() == prefix:
                    _tweet_text.append("THEPREFIX")
                    break
            else:
                _tweet_text.append(w)

        # remove user title prefixes from tweet_text
        if "theclaimant" in _tweet_text:
            idx = _tweet_text.index("theclaimant")
            for i in range(max(idx - 4, 0), idx):
                if _tweet_text[i] in user_title_prefixes:
                    _tweet_text[i] = "THEPREFIX"
        return " ".join(_tweet_text)

    def check_factual_claim(tweet_text, claim):
        # compute A jaccard similarity between A claim and A tweet
        claim = claim.lower()
        tweet_text = tweet_text.lower()
        tweet_text_list = [
            word
            for word in tweet_text.split()
            if word
            not in ("theclaimant", "theverdict", "thewebsite", "theurl", "theprefix")
        ]
        claim_words = set(claim.split())
        tweet_words = set(tweet_text_list)
        # remove stop words from claim_words and tweet_words
        jaccard_similarity = len(claim_words.intersection(tweet_words)) / (
            (len(tweet_words)) + 1e-6
        )
        # jaccard_similarity = len(claim_words.intersection(tweet_words)) / len(claim_words)
        if jaccard_similarity > 0.8:
            return (
                True,
                jaccard_similarity,
                claim_words.intersection(tweet_words),
                tweet_words,
            )
        else:
            return (
                False,
                jaccard_similarity,
                claim_words.intersection(tweet_words),
                tweet_words,
            )

    # ans = defaultdict(list)
    ans = []
    cnt = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            tweet_text = item["tweet"].lower()
            # check if the tweet has fact check url and it with URL
            has_factcheck_url, tweet_text = check_factcheck_url(tweet_text)
            # remove mentions and hashtags
            tweet_text = re.sub(r"@\w+", "", tweet_text)
            tweet_text = re.sub(r"#\w+", "", tweet_text)
            # unescape special html characters like '&gt;'
            tweet_text = unescape(tweet_text)
            # remove all special characters in tweet text
            tweet_text = re.sub(r"[^\w\s]", "", tweet_text)
            # remove date in Month day year format from tweet_text
            tweet_text = re.sub(r"\w+ \d+ \d+", "", tweet_text)
            claim_author = re.sub(r"[^\w\s]", "", item["claim_author"])

            claim = re.sub(r"[^\w\s]", "", item["claim"])
            # check if the tweet has claimant and replace it with CLAIMANT
            has_claimant, tweet_text = check_claimant(tweet_text, claim_author)
            # check if the tweet has fact check website name and replace it with WEBSITE
            has_websitename, tweet_text = check_websitename(tweet_text)
            # check if the tweet has verdict and replace it with VERDICT
            tweet_text = check_verdict(tweet_text)
            # check if the tweet has user title and other prefix and replace it with PREFIX
            tweet_text = check_prefix(tweet_text)
            # check if the tweet has factual claim and replace it with FACTUALCLAIM
            (
                has_factualclaim,
                jaccard_sim,
                claimwords,
                tweet_words,
            ) = check_factual_claim(tweet_text, claim)
            flag = False
            if has_factualclaim:
                if (
                    has_factcheck_url
                    or has_websitename
                    or (has_websitename and has_factcheck_url)
                    or (has_claimant and has_factcheck_url)
                    or (has_claimant and has_websitename)
                    or (has_claimant and has_websitename and has_factcheck_url)
                ):
                    flag = True
            if not flag:
                ans.append(item)
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v4.json", "w"
    ) as f:
        json.dump(ans, f, indent=4)

    #         is_cnt = False
    #         if has_factualclaim:
    #             if has_factcheck_url:
    #                 ans['has factual claim and factcheck url'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #             if has_websitename:
    #                 ans['has factual claim and website name'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #             if has_websitename and has_factcheck_url:
    #                 ans['has factual claim and website name and factcheck url'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #             if has_claimant and has_factcheck_url:
    #                 ans['has claimant and factual claim and factcheck url'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #             if has_claimant and has_websitename:
    #                 ans['has claimant and factual claim and website name'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #             if has_claimant and has_websitename and has_factcheck_url:
    #                 ans['has claimant and factual claim and factcheck url and websitename'].append([item['claim_author'], item['claim'], item['tweet'], tweet_text, jaccard_sim, claimwords, tweet_words])
    #                 is_cnt = True
    #         if is_cnt: cnt += 1

    # seen = set()
    # for k, v in ans.items():
    #     for x in v:
    #         if x[0]+x[1]+x[2] not in seen:
    #             if x[4]<0.65:
    #                 print('##########'*6)
    #                 # print(k)
    #                 # print('-----------'*3)
    #                 print('\tClaimant: ', x[0])
    #                 print('-----------'*3)
    #                 print('\tClaim: ', x[1])
    #                 print('-----------'*3)
    #                 print('\tTweet: ', x[2])
    #                 print('-----------'*3)
    #                 print('\tProcessed Tweet: ', x[3])
    #                 print('-----------'*3)
    #                 print('\tWords: ', x[6]-(x[6].intersection(x[5])))
    #                 print('\tJaccard: ', x[4])
    #         seen.add(x[0]+x[1]+x[2])
    # print(cnt)

    # rule 1: factual claim + fact check link
    # rule 2: factual claim + website name
    # rule 3: factual claim + website name+ link
    # rule 4: claimant + factual claim + link
    # rule 5: claimant + factual claim + website name
    # rule 6: claimant + factual claim + link + website name

    # print(len(ans)) # 30498
    # print("Pairs count after remove fact check special case: ", cnt)
    # with open('./data_collection/tweet_data/test/claim_related_tweets_v3.2.0.json', 'w') as f:
    #     json.dump(ans, f, indent=4)
    # return True


def random_sample(json_path, sample_path, sample_size, existing_sample_path=None):
    """
    random sample from json file
    """
    with open(existing_sample_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        existing_sample_id = set([item["id"] for item in dataset])

    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        shuffle(dataset)
        with open(sample_path, "w", encoding="utf-8") as output:
            output.write("[")
            i = 0
            while sample_size:
                if dataset[i]["id"] not in existing_sample_id:
                    print("----------")
                    print(dataset[i]["tweet"])
                    full_url_tweet = find_full_url(dataset[i]["tweet"])
                    print(full_url_tweet)
                    output.write(json.dumps(dataset[i]))
                    output.write(",\n")
                    sample_size -= 1
                i += 1
                print(i)
            output.write("]")


def clean_sample(json_path):
    ans = []
    factcheck_tweets = []
    factcheck_websites = (
        "politifact",
        "factstream",
        "washingtonpost",
        "factcheck",
        "snopes",
        "flip-flop",
        "pants on fire",
        "fact-check",
        "fact check",
        "factcheck",
        "PunditFact",
    )
    cnt = 0
    factcheck_cnt = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            # item['tweet'] = find_full_url(item['tweet'])
            for fw in factcheck_websites:
                if fw in item["tweet"].lower():
                    item = {
                        "claim_author": item["claim_author"],
                        "claim": item["claim"],
                        "tweet": item["tweet"],
                    }
                    factcheck_tweets.append(item)
                    factcheck_cnt += 1
                    break
            else:
                cnt += 1
                item["idx"] = cnt
                item["tweet"] = item["tweet"].encode("ascii", "ignore").decode("ascii")
                item["claim"] = item["claim"].encode("ascii", "ignore").decode("ascii")
                ans.append(item)

    # print(len(ans)) # 30498
    # print("Pairs count after remove fact check special case: ", cnt)
    # with open('./data_collection/tweet_data/test/claim_related_tweets_v1.2.4_sample.json', 'w', encoding="utf-8") as f:
    #     json.dump(ans, f, indent=4, ensure_ascii=False)

    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v3_factcheck_sample.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(factcheck_tweets, f, indent=4, ensure_ascii=False)
    print("factcheck_cnt: ", factcheck_cnt)
    return True


def reindex_training_samples(csv_path):
    """
    reindex training samples to json file
    """
    df = pd.read_csv(csv_path, sep="|")
    df["idx"] = [i + 1 for i in range(df.shape[0])]
    for idx, row in df.iterrows():
        print(row)
        break


def build_full_url_dataset(json_path):
    ans = []
    cnt = 0
    satire_websites = [
        "http://www.adequacy.org/",
        "https://alhudood.net/",
        "https://babylonbee.com",
        "https://www.thebeaverton.com/",
        "http://betootaadvocate.com",
        "http://www.burrardstreetjournal.com",
        "http://www.chaser.com.au",
        "http://elchiguirebipolar.net",
        "http://www.thecivilian.co.nz/",
        "http://www.clickhole.com",
        "https://www.cracked.com/",
        "http://dailybonnet.com/",
        "http://www.thedailymash.co.uk/",
        "http://www.dailysquib.co.uk",
        "https://thedailywtf.com",
        "http://www.speld.nl",
        "http://exiledonline.com/",
        "http://www.der-postillon.com/",
        "http://www.duffelblog.com/",
        "http://www.elmundotoday.com/",
        "http://framleyexaminer.com",
        "http://www.freewoodpost.net/",
        "https://hard-drive.net",
        "http://thehardtimes.net",
        "https://www.humortimes.com/",
        "https://www.huzlers.com/",
        "http://khabaristantimes.com",
        "http://www.landoverbaptist.org",
        "http://www.legorafi.fr",
        "https://www.york.ac.uk/",
        "http://www.lercio.it",
        "http://www.nationalreport.net/",
        "http://www.newsbiscuit.com/",
        "https://newsthump.com/",
        "https://www.theonion.com/",
        "http://www.theoxymoron.co.uk/",
        "http://www.thepoke.co.uk/",
        "https://panorama.pub",
        "http://reductress.com/",
        "https://rochdaleherald.co.uk",
        "http://www.ScrappleFace.com",
        "http://thefauxy.com/",
        "http://www.truenorthtimes.ca/",
        "https://www.corporate.truenorthtimes.ca/",
        "http://www.theunrealtimes.com/",
        "https://waterfordwhispersnews.com/",
        "http://worldnewsdailyreport.com",
        "http://www.zaytung.com",
    ]
    with open(json_path, "r") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            for website in satire_websites:
                # remove http prefix
                domain_name = (
                    website.split("//")[1]
                    .replace(".com/", "")
                    .replace(".com", "")
                    .replace("www.", "")
                    .replace(".net/", "")
                    .replace(".net", "")
                )
                if domain_name in item["tweet"]:
                    cnt += 1
    print(cnt)
    # for k, v in item.items():
    #     if isinstance(v, str):
    #         item[k] = codecs.encode(v, 'translit/long').encode('ascii', 'ignore').decode('ascii')
    # ans.append(item)

    # print(len(ans)) # 30498
    # print("Pairs count after remove fact check special case: ", cnt)
    # with open('./data_collection/tweet_data/test/claim_related_tweets_v1.2.4_sample.json', 'w', encoding="utf-8") as f:
    #     json.dump(ans, f, indent=4, ensure_ascii=False)
    # with open('./data_collection/tweet_data/test/claim_related_tweets_v4.json', 'w') as f:
    #     json.dump(ans, f, indent=4)


def find_claimant_prefix(json_path):
    ans = []
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            tweet_text = remove_url_and_mention_hashtag(item["tweet"].lower())
            w = item["claim_author"].lower()
            if w in tweet_text and 0 < len(tweet_text[: tweet_text.index(w)]) < 20:
                print("-----------")
                print("Info: ", w, "|", tweet_text)
                print("Prefix: ", tweet_text[: tweet_text.index(w)])


def collect_satire_websites():
    """
    adhoc function to collect satire websites
    """
    wiki_list_url = "https://en.wikipedia.org/wiki/List_of_satirical_news_websites"
    resp = requests.get(wiki_list_url).content
    selector = etree.HTML(resp)
    satire_urls = selector.xpath(
        "/html/body/div[3]/div[3]/div[5]/div[1]/table/tbody/tr/td[1]//a/@href"
    )
    ans = []
    for url in satire_urls:
        print(url)
        url = "https://en.wikipedia.org/" + url
        resp = requests.get(url).content
        selector = etree.HTML(resp)
        website_name = selector.xpath(
            "/html/body/div[3]/div[3]/div[5]/div[1]/table[@class='infobox vcard']//a[@rel='nofollow']/@href"
        )
        for name in website_name:
            ans.append(name)
    print(ans)
    """
    ['http://www.adequacy.org/', 'https://alhudood.net/', 'https://babylonbee.com', 'https://www.thebeaverton.com/', 'http://betootaadvocate.com', 'http://www.burrardstreetjournal.com', 'http://www.chaser.com.au', 'http://elchiguirebipolar.net', 'http://www.thecivilian.co.nz/', 'http://www.clickhole.com', 'https://www.cracked.com/', 'http://dailybonnet.com/', 'http://www.thedailymash.co.uk/', 'http://www.dailysquib.co.uk', 'https://thedailywtf.com', 'http://www.speld.nl', 'http://exiledonline.com/', 'http://www.der-postillon.com/', 'http://www.duffelblog.com/', 'http://www.elmundotoday.com/', 'http://framleyexaminer.com', 'http://www.freewoodpost.net/', 'https://hard-drive.net', 'http://thehardtimes.net',
        'https://www.humortimes.com/', 'https://www.huzlers.com/', 'http://khabaristantimes.com', 'http://www.landoverbaptist.org', 'http://www.legorafi.fr', 'https://www.york.ac.uk/', 'http://www.lercio.it', 'http://www.nationalreport.net/', 'http://www.newsbiscuit.com/', 'https://newsthump.com/', 'https://www.theonion.com/', 'http://www.theoxymoron.co.uk/', 'http://www.thepoke.co.uk/', 'https://panorama.pub', 'http://reductress.com/', 'https://rochdaleherald.co.uk', 'http://www.ScrappleFace.com', 'http://thefauxy.com/', 'http://www.truenorthtimes.ca/', 'https://www.corporate.truenorthtimes.ca/', 'http://www.theunrealtimes.com/', 'https://waterfordwhispersnews.com/', 'http://worldnewsdailyreport.com', 'http://www.zaytung.com']
    """


def count_invalid_tweet(json_path):
    T = Twarc2(bearer_token=BEARER_TOKEN)
    cnt = 0
    tweet_ids = []
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            tweet_ids.append(item["tweet_id"])
    # tweet_ids = tweet_ids[:10]
    valid_tweet_ids = {}
    for page in T.tweet_lookup(tweet_ids):
        for tweet in page["data"]:
            valid_tweet_ids[tweet["id"]] = tweet
            cnt += 1
    print(cnt)
    ans = []
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            if item["tweet_id"] in valid_tweet_ids:
                item["raw_api_response"] = valid_tweet_ids[item["tweet_id"]]
                ans.append(item)

    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v4_valid.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(ans, f, indent=4, ensure_ascii=False)


def find_difference_by_id(json_path1, json_path2):
    """
    adhoc function to find difference between two json files by id
    """
    with open(json_path1, "r", encoding="utf-8") as f:
        dataset1 = json.load(f)
    with open(json_path2, "r", encoding="utf-8") as f:
        dataset2 = json.load(f)
    dataset1 = {item["id"]: item for item in dataset1}
    dataset2 = {item["id"]: item for item in dataset2}
    ans = []
    for k, v in dataset1.items():
        if k not in dataset2:
            ans.append(k)
    print(len(ans))
    print(ans)


def get_html_from_url(json_path):
    """
    adhoc function to get html from url
    """
    json_path = "./data_collection/tweet_data/test/claim_related_tweets_v6.json"
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    cnt = 0
    for item in tqdm(dataset):
        if (
            "raw_api_response" in item
            and "entities" in item["raw_api_response"]
            and "urls" in item["raw_api_response"]["entities"]
            and len(item["raw_api_response"]["entities"]["urls"]) > 0
        ):
            url = item["raw_api_response"]["entities"]["urls"][0]["expanded_url"]
            try:
                resp = requests.get(url).content
                item["html"] = resp.decode("utf-8")
                cnt += 1
            except:
                print(url)
                continue
    print(cnt)
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v6_html.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)


def collect_nlpclimate_keywords(mode="nva"):
    df1 = pd.read_csv(
        "./data_collection/tweet_data/nlpclimate_workshop/keyword_claims_set.csv"
    )
    df2 = pd.read_csv(
        "./data_collection/tweet_data/nlpclimate_workshop/keyword_review_set.csv"
    )
    df3 = pd.read_csv(
        "./data_collection/tweet_data/nlpclimate_workshop/tag_claims_set.csv"
    )
    # combine three datasets
    df = pd.concat([df1, df2, df3], ignore_index=True)
    print(len(df))
    res = []
    seen = set()
    for idx, row in df.iterrows():
        if row["Claim"] not in seen:
            seen.add(row["Claim"])
            kw = keywords_extractor(row["Claim"], mode=mode)
            if len(kw) < 4:
                kw = keywords_extractor(row["Claim"], mode="nv")
            if len(kw) < 4:
                kw = keywords_extractor(row["Claim"], mode="nva")
            row["ClaimKeywords"] = kw
            res.append(row.to_dict())  # Convert Series to dictionary
    print(len(res))
    # store the result to json
    with open(
        f"./data_collection/tweet_data/nlpclimate_workshop/union_claims_keywords_{mode}.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(res, f, indent=4)


def nlpclimate_statistics():
    df = pd.read_json(
        "./data_collection/tweet_data/nlpclimate_workshop/union_claims_keywords_n.json"
    )
    # print unique publisher
    print(df["Publisher"].unique())


if __name__ == "__main__":
    """ test twitter login function
    """
    # driver = webdriver.Chrome()
    # login_twitter(driver, username, password)
    """ save tweet claim pairs to csv
    """
    # json_path = './data_collection/tweet_data/test/claim_related_tweets_test.json'
    # csv_name = './data_collection/processed_datasets/tweet-claim_v9_test.csv'
    # json_to_csv(json_path, csv_name)
    """ calculate two sentence similarity
    """
    # tweet_filter('./data_collection/processed_datasets/politifact_health_tweets_2021-2022.json', './data_collection/processed_datasets/filtered_politifact_health_tweets_2021-2022.json')
    """ test postprocess_csv
    """
    # postprocess_csv('./datasets/tweet-claim_v8.csv')
    """ verify processed csv file
    """
    # verify_csv('./datasets/tweet-claim_v6.5.csv')
    """
    test check English function
    """
    # is_English_text('我是')

    # extracted_tweet = extract_tweet_from_json(JSON_PATH)
    # print(len(extracted_tweet))
    # save tweet list to json file
    # with open('./data_collection/tweet_data/test/non_health_tweets.json', 'w', encoding='utf-8') as dataset:
    #     json.dump(extracted_tweet, dataset)
    """
    test remove_factcheck_tweet_from_json
    """
    # remove_factcheck_tweet_from_json('./data_collection/tweet_data/test/claim_related_tweets_v1.json')
    """
    test random sample
    """
    # JSON_PATH = './data_collection/tweet_data/test/claim_related_tweets_v4.json'
    # SAMPLE_PATH = './data_collection/tweet_data/test/claim_related_tweets_v4_sample2.json'
    # random_sample(JSON_PATH, SAMPLE_PATH, 500, './data_collection/tweet_data/test/claim_related_tweets_v4_sample.json')
    """
    test clean sample
    """
    # clean_sample('./data_collection/tweet_data/test/claim_related_tweets_v3.json')
    """
    reorder training samples
    """
    # csv_path = './data_collection/tweet_data/test/stance_annotation_training_groundtruth.csv'
    # reindex_training_samples(csv_path)
    """
    test build full url dataset
    """
    # build_full_url_dataset('./data_collection/tweet_data/test/claim_related_tweets_v4.json')
    """
    test find claimant prefix
    """
    # find_claimant_prefix('./data_collection/tweet_data/test/claim_related_tweets_v1.json')
    """
    test remove fact check special case
    """
    # remove_factcheck_tweet('./data_collection/tweet_data/test/claim_related_tweets_v3.1.json')
    """
    test find_full_url
    """
    # text = "http://www.cairoscene.com/ViewArticle.aspx?AId=125080-CNN-ISIS-Lures-Women-Kittens-Nutell"
    # # text = "Now you know why the elites on all sides want this investigation stopped. http://fb.me/57svwzYuM"
    # res = find_full_url(text)
    # print(res)
    """
    test collect_satire_websites
    """
    # collect_satire_websites()
    """
    test count invalid tweet
    """
    # count_invalid_tweet('./data_collection/tweet_data/test/claim_related_tweets_v4.json')
    """
    test find difference by id
    """
    # find_difference_by_id('./data_collection/tweet_data/test/claim_related_tweets_v4_sample_filtered.json', './data_collection/tweet_data/test/claim_related_tweets_v4_sample_filtered_v2.json')

    """
    test get html from url
    """
    # get_html_from_url('./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json')

    """
    test collect nlpclimate keywords
    """
    # collect_nlpclimate_keywords(mode='n')

    """
    test nlpclimate statistics
    """
    nlpclimate_statistics()
