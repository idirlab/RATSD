import re
import pandas as pd
import sys
import os
from collections import Counter

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)


class TruthfulnessStanceDetection:
    def __init__(self):
        self.file_path = "./data_collection/processed_datasets/TruthSD_20240131.json"
        self.rag_file_path = (
            "./data_collection/processed_datasets/all_corpus_TruthSD_RAG.json"
        )
        # id, claim_author, claim, tweet, screening, answered, tweet_url_title, claim_timestamp, tweet_timestamp, tweet_id, tweet_userhandle, retweet_count, reply_count, like_count, quote_count, claim_source, claim_verdict, factcheck_timestamp, claim_review_summary, claim_review, factcheck_url, claim_tags, claimbuster_score, pair_id, factcheck_author_url, factcheck_post_time, factcheck_author_info, subset
        self.columns = [
            "id",
            "claim_author",
            "claim",
            "tweet",
            "screening",
            "answered",
            "tweet_url_title",
            "claim_timestamp",
            "tweet_timestamp",
            "tweet_id",
            "tweet_userhandle",
            "retweet_count",
            "reply_count",
            "like_count",
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
            "factcheck_author_url",
            "factcheck_post_time",
            "factcheck_author_info",
            "subset",
            "label",
        ]
        self.rag_columns = [
            "corpus",
            "claim_context",
            "tweet_context",
            "paraphrase",
        ]

    def read_raw_dataframe(self, is_rag=False):
        if is_rag:
            df = pd.read_json(self.rag_file_path)
            # print c
            df.columns = self.columns + self.rag_columns
            return df
        else:
            df = pd.read_json(self.file_path)
            df.columns = self.columns
            return df

    def read_annotations(self, mode="4cls", is_rag=False):
        """
        -1: Negative; 0: Neutral; 1: Positive; 2: Unrelated
        ==> 0, 1, 2, 3
        """
        if mode not in ["4cls", "3cls"]:
            raise ValueError("mode should be one of '4cls', '3cls'")
        label_map = {
            1: 0,
            0: 1,
            -1: 2,
            2: 3,
        }
        if is_rag:
            df = self.read_raw_dataframe(is_rag=True)
            unique_claims = set()
            unique_tweets = set()
            texts, labels = [], []
            print(f"There are {len(df)} annotations in the dataset.")

            for _, row in df.iterrows():
                if row["label"] != 3 and row["tweet"]:
                    if mode == "3cls":
                        if row["label"] == 2:
                            continue
                    texts.append([row["text"]])
                    unique_claims.add(row["claim"])
                    unique_tweets.add(row["tweet"])
                    labels.append(label_map[row["label"]])
            print(
                f"There are {len(unique_claims)} unique claims and {len(unique_tweets)} unique tweets in the RAG dataset."
            )
            print(f"There are {len(texts)} non-problematic annotations in the dataset.")
            print(set(labels))
            return texts, labels
        else:
            df = self.read_raw_dataframe()
            unique_claims = set()
            unique_tweets = set()
            texts, labels = [], []
            print(f"There are {len(df)} annotations in the dataset.")
            verdicts = Counter()
            seen = set()
            print(verdicts)

            for _, row in df.iterrows():
                if row["claim"] not in seen:
                    seen.add(row["claim"])
                    verdicts[row["claim_verdict"]] += 1
                if row["label"] != 3 and row["tweet"]:
                    if mode == "3cls":
                        if row["label"] == 2:
                            continue
                    texts.append([row["text"]])
                    unique_claims.add(row["claim"])
                    unique_tweets.add(row["tweet"])
                    labels.append(label_map[row["label"]])
            print(
                f"There are {len(unique_claims)} unique claims and {len(unique_tweets)} unique tweets in the dataset."
            )
            print(f"There are {len(texts)} non-problematic annotations in the dataset.")
            print(set(labels))
            print(verdicts)
            return texts, labels

    @staticmethod
    def processText(text):
        text = re.sub(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
            "$URL$",
            text.strip(),
        )
        text = re.sub(r"(@[A-Za-z0-9]+)", "$MENTION$", text.strip())
        return text

    def RAG_enrichment(self):
        raw_df = self.read_raw_dataframe()
        seen_claim = {}
        print(raw_df.columns)
        for _, row in raw_df.iterrows():
            if row["claim"] not in seen_claim:
                pass


if __name__ == "__main__":
    TruthSD = TruthfulnessStanceDetection()
    texts, labels = TruthSD.read_annotations(mode="3cls")
    print(len(texts))
