import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd
import numpy as np
import re


def label_to_int(label):
    if label == "support":
        return 0
    elif label == "deny":
        return 1
    elif label == "query":
        return 2
    elif label == "comment":
        return 3
    else:
        return 3


def processText(text):
    text = re.sub(
        r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
        "$URL$",
        text.strip(),
    )
    text = re.sub(r"(@[A-Za-z0-9]+)", "$MENTION$", text.strip())
    return text


def processStanceData(twitterDf, RedditDf, is_process_text=False):
    frames = [twitterDf, RedditDf]

    resultDf = pd.concat(frames)  # Concatenating twitter and reddit data
    result1 = resultDf.replace(np.nan, "", regex=True)  # Getting rid of NaN values

    result1["labelvalue"] = result1.label_x.apply(
        label_to_int
    )  # Converting labels to numbers
    result1["SrcInre"] = result1["inreText"].str.cat(result1["sourceText"], sep=" ")

    data = result1[
        ["text_x", "id", "inre_x", "source_x", "label_x", "SrcInre", "labelvalue"]
    ].copy()

    """ replyText           - the reply post (whose stance towards the target needs to be learnt)
        replyTextId         - the ID of the reply post
        previousText        - the text to which replyText was replied
        sourceText          - the source post of the conversation thread
        label               - the label value assigned to each post
        previousPlusSrctext - the concatenation of the previousText and the sourceText
        labelValue          - the numberic value assigned to each label"""

    data.columns = [
        "replyText",
        "replyTextId",
        "previousText",
        "sourceText",
        "label",
        "previousPlusSrcText",
        "labelValue",
    ]

    if is_process_text:
        data["pReplyText"] = data.replyText.apply(processText)
        data["pPreviousPlusSrcText"] = data.previousPlusSrcText.apply(processText)
    return data


def read_semeval(mode="train"):
    """
    mode: train, test
    """
    if mode == "train":
        twitterTrainDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/TwitterTrainDataSrc.csv"
        )
        redditTrainDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/RedditTrainDataSrc.csv"
        )
        twitterDevDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/TwitterDevDataSrc.csv"
        )
        redditDevDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/RedditDevDataSrc.csv"
        )
        trainDf = processStanceData(twitterTrainDf, redditTrainDf, True)
        devDf = processStanceData(twitterDevDf, redditDevDf, True)

        text_a = trainDf["pReplyText"].values.tolist()
        text_b = trainDf["pPreviousPlusSrcText"].values.tolist()
        X_train = [[a, b] for a, b in zip(text_a, text_b)]
        y_train = trainDf["labelValue"].values.tolist()

        text_a = devDf["pReplyText"].values.tolist()
        text_b = devDf["pPreviousPlusSrcText"].values.tolist()
        X_val = [[a, b] for a, b in zip(text_a, text_b)]
        y_val = devDf["labelValue"].values.tolist()
        return X_train, X_val, y_train, y_val
    elif mode == "test":
        twitterTestDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/TwitterTestDataSrc.csv"
        )
        redditTestDf = pd.read_csv(
            "./data_collection/benchmarks/SemEval2017/RedditTestDataSrc.csv"
        )
        testDf = processStanceData(twitterTestDf, redditTestDf, True)

        text_a = testDf["pReplyText"].values.tolist()
        text_b = testDf["pPreviousPlusSrcText"].values.tolist()
        X_test = [[a, b] for a, b in zip(text_a, text_b)]
        y_test = testDf["labelValue"].values.tolist()
        return X_test, y_test


if __name__ == "__main__":
    a, b, _, _ = read_semeval(mode="train")
    a, b = read_semeval(mode="test")
