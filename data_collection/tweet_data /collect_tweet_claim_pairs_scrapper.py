import requests
from selenium import webdriver
from lxml import etree
import time

from helpers import string_similarity, get_xpaths, keywords_extractor, format_time
import json
from tqdm import tqdm

with open("../raw_data/DataCommons/fact_checks_v1.1.txt") as datacommons:
    datacommon_factchecks = json.load(datacommons)

with open("../raw_data/FactCheckMarkupToolDataFeed/fact_checks.txt") as datafeed:
    datafeed_factchecks = json.load(datafeed)

datacommon_factchecks = datacommon_factchecks[896:]
with open("./test_results/tweet-claim_test.json", "a") as dataset:
    # go to the end of file
    dataset.seek(0, 2)
    # if file is empty then add { to json
    if dataset.tell() == 0:
        dataset.write("{")
    for factcheck in tqdm(datacommon_factchecks, total=len(datacommon_factchecks)):
        driver = webdriver.Chrome()
        claim = factcheck["raw_claim"]
        # avoid too long claim crash the program
        if len(claim) > 400:
            continue

        claim_author = (
            factcheck["claim_author"] if factcheck["claim_author"] else "None"
        )
        keyword = keywords_extractor(claim, claim_author)
        print(claim, keyword)
        curr_idx = 0
        twt_claim_meta = {}
        duplicate_twt = []
        error_catcher = False
        tweet_url = "https://twitter.com/search?q={}&src=typed_query".format(keyword)
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script(
            "return document.body.scrollHeight"
        )  # get scroll height

        driver.get(tweet_url)
        time.sleep(6)

        # deal with twitter's something wrong has happened
        if error_catcher:
            break
        print(keyword)
        while not error_catcher:
            twt_src = driver.page_source
            twt_selector = etree.HTML(twt_src)
            # twitter api will frequently change their xpath
            tweet_elements = twt_selector.xpath(
                '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/section/div/div/div/div/div'
            )
            print("Len", len(tweet_elements))
            if not tweet_elements:
                error_catcher = True
                break
            for element in tweet_elements:
                tweetID = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a/@href"
                )
                if not tweetID:
                    continue  # remove promotions betweetn tweets
                tweetID = tweetID[0].split("/")[-1]

                username = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[1]/div[1]/span/span"
                )
                if username:
                    username = username[0].text
                else:
                    username = ""

                twitter_handle = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/a/div/div[2]/div/span"
                )
                if twitter_handle:
                    twitter_handle = twitter_handle[0].text
                else:
                    twitter_handle = ""

                timestamp = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a/time"
                )[0].text
                timestamp = format_time(timestamp)

                comment_cnt = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[2]/div[3]/div/div[1]/div/div/div[2]/span/span/span"
                )
                if not comment_cnt:
                    comment_cnt = element.xpath(
                        "./article/div/div/div/div[2]/div[2]/div[2]/div[4]/div/div[1]/div/div/div[2]/span/span/span"
                    )
                comment_cnt = comment_cnt[0].text if comment_cnt else "0"

                retweet_cnt = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[2]/div[3]/div/div[2]/div/div/div[2]/span/span/span"
                )
                if not retweet_cnt:
                    retweet_cnt = element.xpath(
                        "./article/div/div/div/div[2]/div[2]/div[2]/div[4]/div/div[2]/div/div/div[2]/span/span/span"
                    )
                retweet_cnt = retweet_cnt[0].text if retweet_cnt else "0"

                like_cnt = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[2]/div[4]/div/div[3]/div/div/div[2]/span/span/span"
                )
                if not like_cnt:
                    like_cnt = element.xpath(
                        "./article/div/div/div/div[2]/div[2]/div[2]/div[3]/div/div[3]/div/div/div[2]/span/span/span"
                    )
                like_cnt = like_cnt[0].text if like_cnt else "0"

                bodytext_1 = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[2]/div[1]/div//text()"
                )
                bodytext_2 = element.xpath(
                    "./article/div/div/div/div[2]/div[2]/div[2]/div[2]/div//text()"
                )
                if not bodytext_1:
                    continue
                elif bodytext_1[0] == "Replying to ":
                    reply_to = "".join(bodytext_1)
                    tweet_text = "".join(bodytext_2)
                else:
                    reply_to = ""
                    tweet_text = "".join(bodytext_1)

                print("tweetID", tweetID)
                print("username", username)
                print("twitter_handle", twitter_handle)
                print("timestamp", timestamp)
                print("comment_cnt", comment_cnt, type(comment_cnt))
                print("retweet_cnt", retweet_cnt, type(retweet_cnt))
                print("like", like_cnt, type(like_cnt))
                print("reply_to", reply_to)
                print("tweet_text", tweet_text)
                print("-------" * 4)

                try:
                    if twitter_handle + "+" + timestamp not in twt_claim_meta:
                        sim_score = string_similarity(tweet_text.lower(), claim.lower())
                        # Filter out the tweet-claim pairs which are too similar
                        # also filter out the claims that already in the twt_claim_meta
                        if (
                            sim_score < 0.8
                            and tweet_text.replace(" ", "") not in duplicate_twt
                        ):
                            duplicate_twt.append(tweet_text.replace(" ", ""))
                            twt_claim_meta[twitter_handle + "+" + timestamp] = {
                                "tweet_id": tweetID,
                                "tweet_timestamp": timestamp,
                                "twitter_user": username,
                                "twitter_userhandle": twitter_handle,
                                "reply_to": reply_to,
                                "raw_tweet": tweet_text,
                                "comment_count": comment_cnt,
                                "retweet_count": retweet_cnt,
                                "like_count": like_cnt,
                                "tweet_stance": None,
                            }
                except Exception as e:
                    print(e)
                    continue

            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        # insert
        for k, v in twt_claim_meta.items():
            factcheck_copy = factcheck.copy()
            factcheck_copy.update(v)
            data_idx = str(factcheck["factcheck_id"]) + "-" + str(curr_idx)
            dataset.write(json.dumps({data_idx: factcheck_copy})[1:-1])
            dataset.write(",\n")
            curr_idx += 1
        driver.quit()
    dataset.write("}")
