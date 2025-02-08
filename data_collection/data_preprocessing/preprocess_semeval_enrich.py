import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd
import numpy as np
import re
import json
from config import tweety_config

tweety_app = tweety_config()


def label_to_int(label):
    if label == "support":
        return 1
    elif label == "deny":
        return -1
    elif label == "query":
        return 2
    elif label == "comment":
        return 0
    else:
        raise ValueError


def processText(text):
    text = re.sub(
        r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
        "$URL$",
        text.strip(),
    )
    text = re.sub(r"(@[A-Za-z0-9]+)", "$MENTION$", text.strip())
    return text


def read_labels(file_path, mode="train"):
    label_distribution = {}
    with open(file_path) as f:
        data = json.load(f)["subtaskaenglish"]
        for _, v in data.items():
            label_distribution[v] = label_distribution.get(v, 0) + 1
    print(f"There are {len(data)} labels in {mode} set.")
    print(f"Label distribution: {label_distribution}")
    print("-------------------")
    return data


def read_twitter_metadata(directory):
    folders = os.listdir(directory)
    # print(folders)
    dataset = {}
    for folder in folders:
        for thread in os.listdir(os.path.join(directory, folder)):
            # read json under /source-tweet
            src_tweet_path = os.listdir(
                os.path.join(directory, folder, thread, "source-tweet")
            )[0]
            # print(src_tweet_path)
            with open(
                os.path.join(directory, folder, thread, "source-tweet", src_tweet_path)
            ) as f:
                src_tweet_json = json.load(f)
                src_tweet_text = src_tweet_json["text"]
                src_tweet_id = src_tweet_json["id"]
                src_tweet_user = src_tweet_json["user"]["name"]
                src_tweet_user_profile = src_tweet_json["user"]["description"]
                dataset[src_tweet_id] = {
                    # "tweet_text": src_tweet_text,
                    "tweet_user": src_tweet_user,
                    "tweet_user_profile": src_tweet_user_profile,
                }

            # print(f"source tweet: {src_tweet_text}, {src_tweet_id}, {src_tweet_user_profile}")

            # read json under /replies
            try:
                replies = os.listdir(os.path.join(directory, folder, thread, "replies"))
                replies = [
                    os.path.join(directory, folder, thread, "replies", reply)
                    for reply in replies
                ]
            except:
                replies = [
                    os.path.join(
                        directory, folder, thread, "source-tweet", src_tweet_path
                    )
                ]
            for reply in replies:
                with open(reply) as f:
                    reply_json = json.load(f)
                    reply_text = reply_json["text"]
                    reply_id = reply_json["id"]
                    reply_tweet_user = reply_json["user"]["name"]
                    reply_user_profile = reply_json["user"]["description"]
                    dataset[reply_id] = {
                        # "tweet_text": reply_text,
                        "tweet_user": reply_tweet_user,
                        "tweet_user_profile": reply_user_profile,
                    }

    print(f"There are {len(dataset)} pairs in the twitter dataset.")
    print("-------------------")
    return dataset


def read_reddit_metadata(directory):
    folders = os.listdir(directory)
    dataset = {}
    for subreddit in folders:
        # read json under /source-tweet
        src_tweet_path = os.listdir(os.path.join(directory, subreddit, "source-tweet"))[
            0
        ]
        with open(
            os.path.join(directory, subreddit, "source-tweet", src_tweet_path)
        ) as f:
            src_tweet_json = json.load(f)["data"]["children"][0]["data"]
            if "body" in src_tweet_json:
                src_tweet_text = src_tweet_json["body"]
            else:
                src_tweet_text = "None"

            src_tweet_author = src_tweet_json["author"]
            src_tweet_id = src_tweet_json["id"]
            if "selftext" in src_tweet_json:
                src_tweet_context = src_tweet_json["selftext"]
            else:
                src_tweet_context = "None"
            dataset[src_tweet_id] = {
                "src_tweet_text": src_tweet_text,
                "src_tweet_user": src_tweet_author,
                "src_tweet_context": src_tweet_context,
                "src_tweet_id": src_tweet_id,
            }

    print(f"There are {len(dataset)} pairs in the reddit dataset.")
    print("-------------------")
    return dataset


def enrich_twitter_dataset(source_csv_path, twitter_metadata):
    source_df = pd.read_csv(source_csv_path)
    for i, row in source_df.iterrows():
        tweet_id = row["id"]
        if tweet_id in twitter_metadata:
            print(f"enriching {tweet_id}...")
            print(f'tweet_user: {twitter_metadata[tweet_id]["tweet_user"]}')
            print(
                f'tweet_user_profile: {twitter_metadata[tweet_id]["tweet_user_profile"]}'
            )
            source_df.at[i, "tweet_user"] = twitter_metadata[tweet_id]["tweet_user"]
            source_df.at[i, "tweet_user_profile"] = twitter_metadata[tweet_id][
                "tweet_user_profile"
            ]
        else:
            source_df.at[i, "tweet_user"] = "None"
            source_df.at[i, "tweet_user_profile"] = "None"
        break


if __name__ == "__main__":
    train_label_path = "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-training-data/train-key.json"
    # dev_label_path = './data_collection/benchmarks/rumoureval2019/rumoureval-2019-training-data/dev-key.json'
    # test_label_path = './data_collection/benchmarks/rumoureval2019/final-eval-key.json'
    # train_labels = read_labels(train_label_path, mode='train')
    # dev_labels = read_labels(dev_label_path, mode='dev')
    # test_labels = read_labels(test_label_path, mode='test')

    twitter_train_dataset = read_twitter_metadata(
        "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-training-data/twitter-english",
    )
    twitter_test_dataset = read_twitter_metadata(
        "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-test-data/twitter-en-test-data",
    )

    reddit_train_dataset = read_reddit_metadata(
        "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-training-data/reddit-training-data",
    )
    reddit_dev_dataset = read_reddit_metadata(
        "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-training-data/reddit-dev-data",
    )
    reddit_test_dataset = read_reddit_metadata(
        "./data_collection/benchmarks/rumoureval2019/rumoureval-2019-test-data/reddit-test-data",
    )

    source_train_csv_path = (
        "./data_collection/benchmarks/SemEval2019/TwitterTrainDataSrc.csv"
    )
    source_dev_csv_path = (
        "./data_collection/benchmarks/SemEval2019/TwitterDevDataSrc.csv"
    )
    source_test_csv_path = (
        "./data_collection/benchmarks/SemEval2019/TwitterTestDataSrc.csv"
    )
    enrich_twitter_dataset(source_train_csv_path, twitter_train_dataset)
    # enrich_twitter_dataset(source_dev_csv_path, twitter_train_dataset)
    # enrich_twitter_dataset(source_test_csv_path, twitter_test_dataset)
