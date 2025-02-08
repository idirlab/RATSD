"""
Based on factual claims, collect tweet pairs that are related to the claim.
"""
import argparse
import json
from datetime import datetime
from tqdm import tqdm
from twarc import Twarc2
from credentials import BEARER_TOKEN
from dateutil import relativedelta
from helpers import get_factchecks, keywords_extractor, format_url, string_similarity


def search_tweet(keywords, start_time, end_time):
    """
    search tweets based on the keywords and time range
    """
    return T.search_all(keywords, start_time=start_time, end_time=end_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        help="the script is running on the local or server environment",
        default="local",
    )
    args = parser.parse_args()

    factchecks = get_factchecks(from_to=[2112, -1], sample_size=None)
    T = Twarc2(bearer_token=BEARER_TOKEN)
    now = datetime.now()
    # 1-166 are training/screening sample
    PAIRS_CNT = 12217
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v3.json",
        "w",
        encoding="utf-8",
    ) as dataset:
        # go to the end of file
        dataset.seek(0, 2)
        # if file is empty then add { to json
        if dataset.tell() == 0:
            dataset.write("[")
        for _, factcheck in tqdm(factchecks.iterrows(), total=len(factchecks)):
            claim = factcheck["Claim"]
            claim_date = factcheck["Claim Published Date"]
            claim_author = factcheck["Author"] if factcheck["Author"] else "None"
            # remove retweet, reply and quote
            KEYWORDS = keywords_extractor(claim)
            if not KEYWORDS:
                continue
            SUFFIX = " -is:retweet -is:reply -is:quote lang:en"
            KEYWORDS += SUFFIX
            print("Claim:", claim)
            print("Keywords:", KEYWORDS)
            seen_tweets = set()
            DEALTA_TIME = relativedelta.relativedelta(months=1)
            START_TIME = datetime.strptime(claim_date, "%Y-%m-%d") - DEALTA_TIME
            END_TIME = min(START_TIME + relativedelta.relativedelta(months=3), now)
            try:
                tweets = search_tweet(KEYWORDS, START_TIME, END_TIME)
                for paginate in tweets:
                    for tweet in paginate["data"]:
                        # if the tweet content is similar to factual claim, then skip it
                        if string_similarity(claim, tweet["text"]) > 0.9:
                            continue
                        # if the tweet content is similar to any of the collected tweets, then skip it
                        SEEN = False
                        for seen_tweet in seen_tweets:
                            if string_similarity(seen_tweet, tweet["text"]) > 0.8:
                                SEEN = True
                                break
                        if SEEN:
                            continue
                        # add new tweet to seen set and jsondump
                        seen_tweets.add(tweet["text"])
                        pair = {}
                        pair["id"] = PAIRS_CNT
                        pair["claim_author"] = claim_author
                        pair["claim"] = claim
                        # replace short url with expanded url while remove media urls
                        # also find article url titles
                        tweet_text, tweet_url_title = tweet["text"], ""
                        if "entities" in tweet and "urls" in tweet["entities"]:
                            format_res = format_url(
                                tweet["text"], tweet["entities"]["urls"]
                            )
                            tweet_text, tweet_url_title = format_res[0], format_res[1]

                        pair["tweet"] = tweet_text
                        pair["screening"] = -3
                        pair["answered"] = None
                        pair["tweet_url_title"] = tweet_url_title
                        pair["claim_timestamp"] = claim_date
                        pair["tweet_timestamp"] = tweet["created_at"]
                        pair["tweet_id"] = tweet["id"]
                        pair["tweet_userhandle"] = tweet["author_id"]
                        pair["tweet_timestamp"] = tweet["created_at"]
                        pair["retweet_count"] = tweet["public_metrics"]["retweet_count"]
                        pair["reply_count"] = tweet["public_metrics"]["reply_count"]
                        pair["like_count"] = tweet["public_metrics"]["like_count"]
                        pair["quote_count"] = tweet["public_metrics"]["quote_count"]
                        pair["claim_source"] = factcheck["Publisher"]
                        pair["claim_verdict"] = factcheck["Verdict"]
                        pair["factcheck_timestamp"] = factcheck[
                            "Factcheck Published Date"
                        ]
                        pair["claim_review_summary"] = factcheck["Review Summary"]
                        pair["claim_review"] = factcheck["Review"]
                        pair["factcheck_url"] = factcheck["Factcheck Url"]
                        pair["claim_tags"] = factcheck["Tags"]
                        pair["claimbuster_score"] = None
                        pair["pair_id"] = str(PAIRS_CNT) + "-" + factcheck["ID"]

                        PAIRS_CNT += 1
                        dataset.write(json.dumps(pair))
                        dataset.write(",\n")
            except Exception as e:
                print(e)
                continue
            print(f"Collected {PAIRS_CNT} pairs in total")
            print("----" * 10)
        dataset.write("]")
