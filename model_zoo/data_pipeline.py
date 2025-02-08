from sklearn.model_selection import train_test_split
from data_collection.dataset_loader.TruthfulnessStance import (
    TruthfulnessStanceDetection,
)
from data_collection.dataset_loader.WTWT2020 import WTWT2020
from data_collection.dataset_loader.SemEval import SemEval
from data_collection.dataset_loader.COVIDLies import COVIDLies
import pandas as pd
import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)


def get_dataset(data_source="semeval"):
    if data_source == "semeval":
        semeval = SemEval()
        target_classes = ["Positive", "Neutral", "Negative", "Query"]
        X_train, X_val, y_train, y_val = semeval.read_semeval(mode="train")
        X_test, y_test = semeval.read_semeval(mode="test")
        return X_train + X_val, X_test, y_train + y_val, y_test, target_classes
    elif data_source == "semeval-3":
        semeval = SemEval()
        target_classes = ["Positive", "Neutral", "Negative"]
        X_train, X_val, y_train, y_val = semeval.read_semeval(
            mode="train", mode_3cls=True
        )
        X_test, y_test = semeval.read_semeval(mode="test", mode_3cls=True)
        X_train = X_train + X_val
        y_train = y_train + y_val
        return X_train, X_test, y_train, y_test, target_classes
    elif data_source == "wtwt2020":
        wtwt2020 = WTWT2020()
        target_classes = ["Positive", "Neutral", "Negative", "Unrelated"]
        texts_wt, labels_wt = wtwt2020.read_wtwt()
        X_train, X_test, y_train, y_test = train_test_split(
            texts_wt, labels_wt, test_size=0.2, random_state=42
        )
    elif data_source == "wtwt2020-3":
        wtwt2020 = WTWT2020()
        target_classes = ["Positive", "Neutral", "Negative"]
        texts_wt, labels_wt = wtwt2020.read_wtwt(mode="3cls")
        X_train, X_test, y_train, y_test = train_test_split(
            texts_wt, labels_wt, test_size=0.2, random_state=42
        )
    elif data_source == "truthSD":
        tsd = TruthfulnessStanceDetection()
        target_classes = ["Negative", "Neutral", "Positive", "Unrelated"]
        text, labels = tsd.read_annotations()
        X_train, X_test, y_train, y_test = train_test_split(
            text, labels, test_size=0.2, random_state=42
        )
    elif data_source == "truthSD-3":
        tsd = TruthfulnessStanceDetection()
        target_classes = ["Positive", "Neutral", "Negative"]
        text, labels = tsd.read_annotations(mode="3cls")
        X_train, X_test, y_train, y_test = train_test_split(
            text, labels, test_size=0.2, random_state=42
        )
    elif data_source == "truthSD-3-rag":
        tsd = TruthfulnessStanceDetection()
        target_classes = ["Positive", "Neutral", "Negative"]
        text, labels = tsd.read_annotations(mode="3cls", is_rag=True)
        X_train, X_test, y_train, y_test = train_test_split(
            text, labels, test_size=0.2, random_state=42
        )
    elif data_source == "all":
        semeval = SemEval()
        target_classes = ["Positive", "Neutral", "Negative", "Query"]
        _X_train, _X_val, _y_train, _y_val = semeval.read_semeval(mode="train")
        _X_test, _y_test = semeval.read_semeval(mode="test")
        _X_train = _X_train + _X_val
        _y_train = _y_train + _y_val

        wtwt2020 = WTWT2020()
        texts_wt, labels_wt = wtwt2020.read_wtwt()
        _X_train = _X_train + texts_wt
        _y_train = _y_train + labels_wt

        tsd = TruthfulnessStanceDetection()
        text, labels = tsd.read_annotations()
        _X_train = _X_train + text
        _y_train = _y_train + labels

        X_train, X_test, y_train, y_test = train_test_split(
            _X_train, _y_train, test_size=0.2, random_state=42
        )
    elif data_source == "covidlies":
        covidlies = COVIDLies()
        target_classes = ["Positive", "Neutral", "Negative"]
        texts, labels = covidlies.read_annotations()
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
    else:
        raise ValueError(
            "data_source should be one of 'semeval', 'wtwt2020', 'truthSD', 'all'"
        )

    return X_train, X_test, y_train, y_test, target_classes


if __name__ == "__main__":
    get_dataset("semeval-3")
