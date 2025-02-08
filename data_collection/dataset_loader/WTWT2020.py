import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd
import re
from credentials import BEARER_TOKEN
import json


class WTWT2020:
    """
    Read and process WTWT2020 dataset
    """

    def __init__(self):
        self.source_file_path = "./data_collection/benchmarks/WTWT2020/wtwt_ids.json"
        self.raw_file_path = "./data_collection/benchmarks/WTWT2020/wtwt_short.json"
        self.clean_file_path = "./data_collection/benchmarks/WTWT2020/cleaned_wtwt.csv"

    def read_wtwt(self, mode="4cls"):
        """Dataset static
        Positive: 5999
        Neutral: 18320
        Negative: 3864
        Unrelated: 16504
        """
        wtwt_df = pd.read_csv(self.clean_file_path)

        texts, labels = [], []
        for row in wtwt_df.iterrows():
            row = row[1]

            if row["stance"] == 0:
                labels.append(0)
            elif row["stance"] == 1:
                labels.append(1)
            elif row["stance"] == 2:
                labels.append(2)
            elif row["stance"] == 3:
                if mode == "4cls":
                    labels.append(3)
                else:
                    labels.append(1)
            else:
                continue
            texts.append([row["text"]])

        return texts, labels

    def clean_wtwt(self):
        wtwt_df = pd.read_json(self.raw_file_path)

        # remove unnecessary "unrelated" pairs
        # wtwt_df = wtwt_df[wtwt_df.stance!="unrelated"]

        # apply data preprocessing functions
        wtwt_df["stance"] = wtwt_df.stance.apply(self.label_to_int)
        wtwt_df["merger"] = wtwt_df.merger.apply(self.merger_to_claim)

        wtwt_df.columns = ["tweet", "date", "claim", "stance"]
        print(wtwt_df["stance"].value_counts())
        wtwt_df.to_csv(self.clean_file_path, index=False)

    def hydrate_tweets(self):
        """
        deprecated
        """
        processed_datasets = []
        with open("./data_collection/raw_data/wtwt_ids.json") as dataset:
            dataset = json.load(dataset)

            tweet_ids = [tweet_json["tweet_id"] for tweet_json in dataset]
            idx = 0
            for response in self.twarc2.tweet_lookup(tweet_ids):
                for tweet in response["data"]:
                    dataset[idx]["text"] = tweet["text"]
                    idx += 1
            print(idx)  # 44238

        with open("./data_collection/processed_datasets/wtwt_2020.json", "w") as f:
            json.dump(dataset, f)

        return True

    @staticmethod
    def label_to_int(label):
        if label == "support":
            return 0
        elif label == "comment":
            return 1
        elif label == "refute":
            return 2
        elif label == "unrelated":
            return 3
        else:
            raise ValueError("Invalid label")

    @staticmethod
    def merger_to_claim(merger):
        if merger == "CI_ESRX":
            return "Cigna is acquiring Express Scripts."
        elif merger == "CVS_AET":
            return "CVS Health is acquiring Aetna."
        elif merger == "ANTM_CI":
            return "Anthem is acquiring Cigna."
        elif merger == "FOXA_DIS":
            return "Disney is acquiring 21st Century Fox."
        elif merger == "AET_HUM":
            return "Aetna is acquiring Humana."

    @staticmethod
    def remove_url_and_mention(text):
        # remove links in tweet
        text = re.sub(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
            "$URL$",
            text.strip(),
        )
        # replace @twitter_handle with special token
        text = re.sub(r"(@[A-Za-z0-9]+)", "$MENTION$", text.strip())
        return text


if __name__ == "__main__":
    wtwt = WTWT2020()

    """
    One time use only
    """
    wtwt.clean_wtwt()

    # """
    # Test read WTWT2020 dataset
    # """
    # txt, l = wtwt.read_wtwt()
    # print("Total number of samples in WTWT2020 benchmark dataset:", len(txt))
