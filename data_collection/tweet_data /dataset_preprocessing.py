""" 
data preprocessing for tweet-claim paris
"""

import json
from datetime import datetime
from tqdm import tqdm
from twarc import Twarc2
from credentials import BEARER_TOKEN
from constants import satire_websites, invalid_websites, headers
import requests
import re
from bs4 import BeautifulSoup
from lxml import etree
import time


def filter_before(json_path):
    """
    filter out any tweets that were published 31 or more days before the claim was posted.

    max_before = 31
    before_cnt = 2933
    """
    before_cnt = 0
    max_before = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for x in dataset:
            # format tweet timestamp
            twt_date = x["tweet_timestamp"][:10].split("-")
            clm_date = x["claim_timestamp"].split("-")
            twt_date = datetime(int(twt_date[0]), int(twt_date[1]), int(twt_date[2]))
            clm_date = datetime(int(clm_date[0]), int(clm_date[1]), int(clm_date[2]))
            if twt_date < clm_date:
                delta_str = int(str(clm_date - twt_date).split(" ")[0])
                max_before = max(max_before, delta_str)
                before_cnt += 1
    print("max before: ", max_before)
    print("before cnt: ", before_cnt)


def filter_within(json_path):
    """
    filter out any tweets that were published 365 or more days after the claim was posted.

    max_after = 336
    after_cnt = 21316
    """
    after_cnt = 0
    max_after = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for x in dataset:
            twt_date = x["tweet_timestamp"][:10].split("-")
            clm_date = x["claim_timestamp"].split("-")
            twt_date = datetime(int(twt_date[0]), int(twt_date[1]), int(twt_date[2]))
            clm_date = datetime(int(clm_date[0]), int(clm_date[1]), int(clm_date[2]))
            if twt_date >= clm_date:
                delta_str = str(twt_date - clm_date).split(" ")[0]
                if delta_str == "0:00:00":
                    delta_str = 0
                else:
                    delta_str = int(delta_str)
                if delta_str >= max_after:
                    print(twt_date, clm_date)
                max_after = max(max_after, delta_str)
                after_cnt += 1
    print("max after: ", max_after)
    print("after cnt: ", after_cnt)


def filter_factchecker(json_path):
    """
    filter out tweets from fact checker
    """
    # "@PolitiFact", "@PolitiFactTexas", "@snopes", "@washingtonpost", "@factcheckdotorg", "PolitiFact Live", "PolitiFact Florida", "PolitiFactWiscs"
    fact_checkers = (
        "8953122",
        "91377501",
        "14294848",
        "2467791",
        "21344507",
        "749640119766966272",
        "116099364",
        "2399104862",
    )

    fc_cnt = 0
    ans = []
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for x in dataset:
            if x["tweet_userhandle"] in fact_checkers:
                fc_cnt += 1
            else:
                ans.append(x)

    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(ans, f, indent=4, ensure_ascii=False)

    print("{} after applied filter becomes {}".format(len(dataset), len(ans)))
    print("fact checker cnt: ", fc_cnt)


def filter_invalid(json_path):
    from helpers import remove_url_and_mention_hashtag

    """
    filter out tweets that
    1. from suspended account
    2. contain any image or video
    3. the factual claim's verdict belongs to ('half-flip', 'full-flop', 'no-flip')
    4. the tweet is only a sharing of a new article link without any other information
    5. the tweet contains any satire websites, note that the website list is from wikipedia
    """
    ans = []
    has_attachment = 0
    is_flip = 0
    is_sharing = 0
    is_satire = 0
    is_invalid_url = 0
    is_user_invalid = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
    }
    seen_url = {}
    timeout_urls = set()

    with open(json_path, "r", encoding="utf-8") as f:
        jsonf = json.load(f)
        for item in tqdm(jsonf):
            if item["claim_verdict"] in ("half-flip", "full-flop", "no-flip"):
                is_flip += 1
            elif any(1 for w in satire_websites if w in item["tweet"]):
                is_satire += 1
            elif "attachments" in item["raw_api_response"]:
                has_attachment += 1
            elif (
                "account is temporarily unavailable" in item["raw_api_response"]["text"]
            ):
                is_user_invalid += 1
            elif (
                "entities" in item["raw_api_response"]
                and "urls" in item["raw_api_response"]["entities"]
            ):
                url_title = []
                for url in item["raw_api_response"]["entities"]["urls"]:
                    url = url["expanded_url"]
                    if url in timeout_urls or any(
                        1 for w in invalid_websites if w in url
                    ):
                        is_invalid_url += 1
                        break
                    if url in seen_url:
                        url_title.append(seen_url[url])
                        continue
                    else:
                        try:
                            resp = requests.get(url, headers=headers, timeout=5)
                        except:
                            print(url)
                            timeout_urls.add(url)
                            is_invalid_url += 1
                            break
                        if resp.status_code != 200:
                            is_invalid_url += 1
                            break
                        soup = BeautifulSoup(resp.content, "html.parser")
                        if soup.title != None:
                            tweet_text = remove_url_and_mention_hashtag(item["tweet"])
                            title = soup.title.text
                            if title == tweet_text:
                                is_sharing += 1
                                break
                            url_title.append("!@#$".join([url, title]))
                            seen_url[url] = "!@#$".join([url, title])
                else:
                    item["tweet_url_title"] = "$#@!".join(url_title)
                    ans.append(item)
            else:
                item["tweet_url_title"] = ""
                ans.append(item)

    # print(f"{len(valid_tweet_ids)} tweets are valid out of 1500 ground truth set.")
    print(f"{is_flip} tweets' related factual claim belongs to flip.")
    print(f"{is_satire} tweets contains satire website link.")
    print(f"{has_attachment} tweets contain attachments.")
    print(f"{is_user_invalid} tweets contains invalid user account.")
    print(f"{is_sharing} tweets are only sharing a new article link.")
    print(f"{is_invalid_url} tweets contains invalid website link.")
    print(f"{len(ans)} pairs are valid after applied filters")

    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker_noflip_nosatire_noattachment_nosharing_noinvalidurl.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(ans, f, indent=4, ensure_ascii=False)


def find_rulings(json_path):
    """
    find the number of tweets that have a ruling

    {'half-flip', 'barely-true', 'mostly-true', 'true', 'half-true', 'false', 'full-flop', 'no-flip', 'pants-fire'}
    """
    rulings = set()
    with open(json_path, "r", encoding="utf-8") as f:
        jsonf = json.load(f)
        for item in tqdm(jsonf):
            rulings.add(item["claim_verdict"])
    print(rulings)


def count_tweet_with_valid_link(json_path):
    """
    adhoc function to count tweet with valid link
    """
    T = Twarc2(bearer_token=BEARER_TOKEN)
    tweet_ids = []
    valid_tweet_ids = set()
    with open(json_path, "r", encoding="utf-8") as f:
        jsonf = json.load(f)
        for item in tqdm(jsonf):
            tweet_ids.append(item["tweet_id"])
    tweet_ids = tweet_ids[:300]
    twitter_resp = T.tweet_lookup(tweet_ids)
    invalid_cnt = 0
    for page in twitter_resp:
        for tweet in page["data"]:
            if "entities" not in tweet:
                continue
            elif "urls" not in tweet["entities"]:
                continue
            try:
                print("---------------")
                for url in tweet["entities"]["urls"]:
                    if url["expanded_url"]:
                        resp = requests.get(url["expanded_url"], headers=headers)
                        print(resp)
                        """
                        200: OK
                        301: Moved Permanently (Not working)
                        302: Found (Not working)
                        """
                        for k, v in vars(resp).items():
                            if k not in (
                                "_content",
                                "_next",
                                "raw",
                                "headers",
                                "request",
                                "_content_consumed",
                                "encoding",
                                "elapsed",
                            ):
                                print(f"{k}: {v}")
                            if k == "_content":
                                print(f"{k}: {v[:40]}")
                        # if resp.url=='https://www.facebook.com/': # 200; 301=>302
                        if resp.url.count("/") <= 3:
                            invalid_cnt += 1
                            break
                        elif resp.status_code == 404:
                            invalid_cnt += 1
                            break
                        elif resp.content == b"":
                            invalid_cnt += 1
                            break
            except Exception as e:
                print("Exception: ", e)
                invalid_cnt += 1

    print(f"{invalid_cnt} tweets are valid out of 1500 ground truth set.")


def dataset_user_enrichment(json_path):
    twarc2_client = Twarc2(bearer_token=BEARER_TOKEN)

    # Function to batch user IDs into chunks of 100 (API limit per request)
    def chunk_user_ids(user_ids, batch_size=100):
        for i in range(0, len(user_ids), batch_size):
            yield user_ids[i : i + batch_size]

    def get_user_profiles(user_ids):
        user_profiles = []
        failed_ids = []

        for chunk in chunk_user_ids(user_ids):
            print(f"Fetching batch of {len(chunk)} user profiles...")
            attempts = 0
            success = False
            while attempts < 3 and not success:
                try:
                    users = list(twarc2_client.user_lookup(chunk))
                    user_profiles.extend(users)
                    success = True
                except Exception as e:
                    print(f"Error fetching batch: {e}. Retrying...")
                    attempts += 1
                    time.sleep(15)  # Short sleep before retrying the batch
                    if "Rate limit" in str(e):
                        time.sleep(15 * 60)  # If rate-limited, wait for 15 minutes

            if not success:
                failed_ids.extend(chunk)  # Log IDs that failed after 3 attempts
            print(f"Successfully fetched {len(user_profiles)} user profiles.")
        return user_profiles, failed_ids

    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        user_ids = []
        for item in tqdm(dataset):
            twitter_user_id = item["tweet_userhandle"]
            if twitter_user_id == None:
                continue
            user_ids.append(twitter_user_id)
        user_ids = list(set(user_ids))
        print(len(user_ids))
        user_profiles, failed_user_ids = get_user_profiles(user_ids)
        # Optionally save the results to a JSON file
        with open("user_profiles.json", "w") as f:
            json.dump(user_profiles, f, indent=2)

        # Optionally save the failed IDs to another file for further investigation
        if failed_user_ids:
            with open("failed_user_ids.txt", "w") as f:
                for user_id in failed_user_ids:
                    f.write(f"{user_id}\n")

        print(f"Retrieved {len(user_profiles)} user profiles.")
        print(f"Failed to retrieve {len(failed_user_ids)} user profiles.")


def dataset_link_enrichment(json_path):
    # Function to fetch raw HTML
    def fetch_html_and_text(url, timeout=10):
        try:
            # Fetch the HTML content of the URL with a timeout
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an HTTPError if the response is not 200 OK

            # Get the raw HTML
            raw_html = response.text

            # Parse the HTML and extract text
            soup = BeautifulSoup(raw_html, "html.parser")
            text_content = soup.get_text(separator="\n")  # Extract text with newlines

            return raw_html, text_content

        except requests.exceptions.Timeout:
            print(f"Timeout error for URL: {url}")
            return None, None
        except requests.exceptions.RequestException as e:
            # Catch all other exceptions (e.g., 404, connection errors)
            print(f"Error fetching URL {url}: {e}")
            return None, None

    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        urls = set()
        for item in tqdm(dataset):
            tweet_url_title = item["tweet_url_title"]
            if tweet_url_title == None:
                continue
            for url_title in tweet_url_title.split("!@#$"):
                if url_title.startswith("https"):
                    urls.add(url_title)

        url2article = {}
        # Loop through URLs, fetch HTML, and extract text
        for url in tqdm(urls):
            print(f"Fetching content from: {url}")

            # Fetch raw HTML
            raw_html, text_content = fetch_html_and_text(url, timeout=10)

            if raw_html and text_content:
                # Print the first 500 characters of raw HTML and text content
                print(f"Raw HTML (first 5 chars):\n{raw_html[:5]}")
                print(f"Text content (first 5 chars):\n{text_content[:5]}")
                print("\n---\n")
                url2article[url] = [text_content, raw_html]
            else:
                print(f"Failed to retrieve content for {url}\n")
        print(len(urls))
        print(len(url2article))
        with open("./data_collection/tweet_data/test/url2article.json", "w") as f:
            json.dump(url2article, f, indent=2)


def use_profile_cleanup(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        user_profiles = {}
        dataset = json.load(f)
        for item in tqdm(dataset):
            data = item["data"]
            for user in data:
                user_profiles[user["id"]] = user
        print(len(user_profiles))
        with open(json_path[:-5] + "_cleaned.json", "w", encoding="utf-8") as f:
            json.dump(user_profiles, f, indent=4)


def sort_pairs_by_jaccard(json_path):
    """
    adhoc function to sort pairs by jaccard similarity
    """
    with open(json_path, "r", encoding="utf-8") as f:
        jsonf = json.load(f)
        cnt_claim_jaccard = 0
        cnt_jaccard = 0
        cntfb = 0
        for item in tqdm(jsonf):
            if "fb.me" in item["tweet"] or "facebook.com" in item["tweet"]:
                cntfb += 1
                continue
            # remove special characters
            tweet = re.sub(r"[^\w\s]", " ", item["tweet"])
            claim = re.sub(r"[^\w\s]", " ", item["claim"])

            # raw_tweet_tokens = set(re.split(",|-|/|//|:|\"|\ ", item['tweet'].lower()))
            tweet_tokens = set(tweet.lower().split())
            for token in ("https", "www", "twitter", "com", "status", "org", "http"):
                try:
                    tweet_tokens.remove(token)
                except:
                    pass
            claim_tokens = set(claim.lower().split())
            jaccard = len(tweet_tokens.intersection(claim_tokens)) / len(
                tweet_tokens.union(claim_tokens)
            )
            claim_jaccard = len(claim_tokens.intersection(tweet_tokens)) / len(
                claim_tokens
            )
            if claim_jaccard < 0.9:
                cnt_claim_jaccard += 1

            if jaccard < 0.5:
                cnt_jaccard += 1
                print(
                    "--------------------------------------------------------------------"
                )
                print(item["claim"])
                print("-------")
                print(
                    item["tweet"],
                    "https://twitter.com/anyuser/status/" + item["tweet_id"],
                )
                print("-------")
                print(tweet_tokens)
                print(claim_tokens)
                print(jaccard)
                print(claim_jaccard)

        # print(f"jaccard>0.95: {cnt95}")
        # print(f"jaccard>0.9: {cnt9}")
        # print(f"jaccard>0.7: {cnt7}")
        print(len(jsonf))
        print(f"jaccard<0.2: {cnt_jaccard}")
        print(f"fb.me: {cntfb}")
        print(f"claim_jaccard<0.6: {1235-cnt_claim_jaccard}")


def remove_duplicates(json_path):
    ans = []
    seen = set()
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            if item["tweet_id"] in seen:
                continue
            ans.append(item)
            seen.add(item["tweet_id"])

    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v5.json",
        "w",
        encoding="utf-8",
    ) as output:
        output.write(json.dumps(ans, indent=4))


def get_claimant_info(json_path):
    seen_claimant = {}
    invalid_claimant = set()
    seen_factcheck_url = {}
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            url = item["factcheck_url"]
            claimant = item["claim_author"]
            if url in seen_factcheck_url:
                continue
            # if claimant in seen_claimant or claimant in invalid_claimant: continue
            try:
                selector = etree.HTML(requests.get(url, headers=headers).text)
                author_url = (
                    "https://www.politifact.com"
                    + selector.xpath(
                        '//*[@id="top"]/main/section[3]/div/article/div[1]/div[2]/a'
                    )[0].attrib["href"]
                )
                post_time_info = selector.xpath(
                    '//*[@id="top"]/main/section[3]/div/article/div[1]/div[2]/div/text()'
                )[0]
                post_time_info = post_time_info[1:-1]
                if claimant not in seen_claimant:
                    claimant_selector = etree.HTML(
                        requests.get(author_url, headers=headers).text
                    )
                    author_info = claimant_selector.xpath(
                        '//*[@id="top"]/main/section[3]/div/article/div[2]/p//text()'
                    )[0]
                    seen_claimant[claimant] = author_info
                    seen_factcheck_url[url] = (author_url, post_time_info, author_info)
                else:
                    seen_factcheck_url[url] = (
                        author_url,
                        post_time_info,
                        seen_claimant[claimant],
                    )
                # print(url, author_text, author_url, post_time_info, author_info)
            except Exception as e:
                invalid_claimant.add(claimant)
                print(url, e)

    # save url2claimant to json
    with open(
        "./data_collection/tweet_data/test/url2claimant.json", "w", encoding="utf-8"
    ) as output:
        output.write(json.dumps(seen_factcheck_url, indent=4))


def combine_claimant_to_dataset(json_path, claimant_info_path):
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    with open(claimant_info_path, "r", encoding="utf-8") as f:
        claimant_info = json.load(f)
    for item in tqdm(dataset):
        url = item["factcheck_url"]
        if url in claimant_info:
            item["factcheck_author_url"] = claimant_info[url][0]
            item["factcheck_post_time"] = claimant_info[url][1]
            item["factcheck_author_info"] = claimant_info[url][2]
        else:
            item["factcheck_author_url"] = ""
            item["factcheck_post_time"] = ""
            item["factcheck_author_info"] = ""

    with open(
        json_path[:-5] + "_withclaimant_v6.json", "w", encoding="utf-8"
    ) as output:
        output.write(json.dumps(dataset, indent=4))


def remove_invalid_tweet(json_path):
    """
    77 invalid tweets in total in v6_rawurlvalid
    from 5793 to 5716
    {'1457023401130971139', '1425860247445381123', '1446888019999531009', '113415111464591360', '1381755273040265223', '1482746673772343304', '1509585605558218756', '1391150046205329409', '1536867325399298050', '1464664659290570758', '1508240783564054529', '1268593626860453889', '1500846303743467522', '1536319250243133444', '664921693132103681', '1473791941653454848', '1478564841078022148', '1535649429302218752', '1429980528560676885', '1484485924465504264', '1252215417369755648', '1422925684985540613', '1197340267315154944', '1266893930060185601', '1167786393680171008', '1494455378553286657', '1521806466369392640', '1454901917755363330', '1435624927336480773', '1429839866569793542', '1475872373094158336', '1012180705609175043', '493124136424595456', '1492643401728237572', '1513369944414687233', '1427042220805394435', '1544763983311372290', '1511433555779502086', '809500142478958594', '1345916317094785025', '134735338261327872', '1346917028188147713', '1531261137903398913', '1215300124332711947', '1324745363236990976', '1348418681366261762', '253671850910027776', '982848187042951169', '1142083607709847555', '1419898552415756288', '1009640591955779586', '1448259222576173061', '1481363782492647425', '1493126539600281600', '2408038995', '1379250458431213571', '1487179427305992193', '157894097598816256', '1514048671133810699', '1541952088304807936', '1528490016661454849', '258393043370123265', '1133470839465230336', '1309546779931742210', '1528388975169249281', '1549902179061809152', '279697292292939776', '1403483942783754244', '615309652276965378', '20339017555', '1230191534999515136', '1220623414139871233', '1314006661216993281', '18642819416', '1141851473954975744', '1322573365215961088', '1540864308002840579'}
    """
    tweet_ids = []
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            tweet_ids.append(item["tweet_id"])
    # query twitter api and find invalid tweets
    tweet_ids = set(tweet_ids)

    T = Twarc2(bearer_token=BEARER_TOKEN)
    valid_tweet_ids = set()
    for x in T.tweet_lookup(tweet_ids):
        for tweet in x["data"]:
            valid_tweet_ids.add(tweet["id"])
    print(tweet_ids - valid_tweet_ids)
    print(len(tweet_ids - valid_tweet_ids))


def prepare_RAG_corpus(
    raw_dataset_json_file,
    usr_profile_json_file,
    url2article_json_file,
    annotated_dataset_list,
):
    def parse_url_from_tweet(tweet):
        if tweet == None:
            return None

        urls = re.findall(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            tweet,
        )
        if urls:
            return urls[0]
        else:
            return None

    with open(usr_profile_json_file, "r", encoding="utf-8") as f:
        user_profiles = json.load(f)
        user_profiles_dict = {}
        for user_page in user_profiles:
            for user in user_page["data"]:
                user_profiles_dict[user["id"]] = user

    with open(url2article_json_file, "r", encoding="utf-8") as f:
        url2article = json.load(f)

    with open(raw_dataset_json_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        corpus = dict()
        for item in dataset:
            id = item["id"]
            user_id = item["tweet_userhandle"]
            article_url = parse_url_from_tweet(item["tweet"])
            if article_url in url2article:
                article_text = url2article[article_url][0]
            else:
                article_text = None
            if user_id in user_profiles_dict:
                user_profile = user_profiles_dict[user_id]
            else:
                user_profile = None
            item["usr_profile"] = user_profile
            item["article_text"] = article_text
            corpus[id] = item

    with open(annotated_dataset_list, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        all_corpus_dataset = []
        factcheck_corpus_only_dataset = []
        tweet_corpus_only_dataset = []
        for item in dataset:
            id = item[0]
            if id in corpus:
                _item1 = item.copy()
                _item1.append(corpus[id])
                all_corpus_dataset.append(_item1)

                _item2 = item.copy()
                if "raw_api_response" in corpus[id]:
                    _item2.append(corpus[id]["raw_api_response"])
                tweet_corpus_only_dataset.append(_item2)

                _item3 = item.copy()
                if "raw_api_response" in corpus[id]:
                    corpus[id].pop("raw_api_response")
                _item3.append(corpus[id])
                factcheck_corpus_only_dataset.append(_item3)
        # save the three datasets
        with open(
            "./data_collection/processed_datasets/all_corpus_TruthSD.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(all_corpus_dataset, f, indent=4)
        with open(
            "./data_collection/processed_datasets/factcheck_corpus_only_TruthSD.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(factcheck_corpus_only_dataset, f, indent=4)
        with open(
            "./data_collection/processed_datasets/tweet_corpus_only_TruthSD.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(tweet_corpus_only_dataset, f, indent=4)


if __name__ == "__main__":
    """
    test filter_before
    """
    # filter_before('./data_collection/tweet_data/test/claim_related_tweets_v5.json')

    """
    test filter_within
    """
    # filter_within('./data_collection/tweet_data/test/claim_related_tweets_v5.json')

    """
    test filter_factchecker
    """
    # filter_factchecker('./data_collection/tweet_data/test/claim_related_tweets_v5.json')

    """
    test find_rulings
    """
    # find_rulings('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker.json')

    """
    test filter_invalid_data
    """
    # filter_invalid('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker.json')

    """
    test count_tweet_with_valid_link
    """
    # count_tweet_with_valid_link('./data_collection/tweet_data/test/claim_related_tweets_v4_valid.json')

    """
    test sort_pairs_by_jaccard
    """
    # sort_pairs_by_jaccard('./data_collection/tweet_data/test/claim_related_tweets_v4.json')
    # sort_pairs_by_jaccard('./data_collection/tweet_data/test/claim_related_tweets_v4_sample_filtered_v2.json')

    """
    test remove_duplicates
    """
    # remove_duplicates('./data_collection/tweet_data/test/claim_related_tweets_v4_valid.json')

    """
    test generate_json_for_mysql
    """
    # generate_json_for_mysql('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker_withclaimant.json')

    """
    test get_claimant_info
    """
    # get_claimant_info('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker.json')

    """
    test add claimant info to dataset
    """
    # combine_claimant_to_dataset('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker_noflip_nosatire_noattachment_nosharing_noinvalidurl.json', './data_collection/tweet_data/test/url2claimant.json')

    """
    test remove invalid tweet
    """
    # remove_invalid_tweet(
    #     "./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json"
    # )

    """
    test dataset enrichment
    """
    # dataset_user_enrichment(
    #     "./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json"
    # )
    """
    test use profile cleanup
    """
    # use_profile_cleanup("./data_collection/tweet_data/test/user_profile.json")
    """
    test dataset link enrichment
    """
    # dataset_link_enrichment(
    #     "./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json"
    # )
    """
    test RAG corpus preparation
    """
    prepare_RAG_corpus(
        "./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json",
        "./data_collection/tweet_data/test/user_profile.json",
        "./data_collection/tweet_data/test/url2article.json",
        "./data_collection/processed_datasets/TruthSD_20240131.json",
    )
