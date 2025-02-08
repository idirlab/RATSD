import pandas as pd
import sys
import os
from collections import Counter

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)


class COVIDLies:
    def __init__(self):
        self.json_file_path = (
            "./data_collection/benchmarks/covidlies/covid_lies_stuffed.json"
        )
        self.label_map = {
            "pos": 0,
            "na": 1,
            "neg": 2,
        }

    def read_annotations(self):
        df = pd.read_json(self.json_file_path, encoding="utf-8")
        print(df.columns)
        texts = []
        labels = []
        for i, row in df.iterrows():
            if row["text"] is None:
                continue
            texts.append([row["text"]])
            labels.append(self.label_map[row["label"]])

        return texts, labels


if __name__ == "__main__":
    covidlies = COVIDLies()
    texts, labels = covidlies.read_annotations()
    print(len(texts))
