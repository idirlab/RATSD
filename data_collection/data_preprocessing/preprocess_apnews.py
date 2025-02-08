import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd


def get_factclaimpairs():
    """ Dataset static
    Positive: 4951
    Neutrual: 2948
    Negative: 10088
    
    For 'half-flip' 'full-flop' 'no-flip', the factual claim column is just a phrase rather than factual claim,
    so we drop them.
    """
    headers = [
        "publisher",
        "claimReviewed",
        "fact",
        "review",
        "verdict",
        "author",
        "claimPublishedDate",
        "factcheckPublishedDate",
        "thumbnailUrl",
        "url",
    ]
    apnews_df = pd.read_csv(
        "./data_collection/raw_data/factcheckrepo/apnews.csv", names=headers
    )

    print(apnews_df["verdict"].unique())

    verdict_types = ["False" "Missing context" "Partly false" "Altered photo" "True"]

    true_df = apnews_df.loc[apnews_df["verdict"] == "True"]  # 2457 support
    missingcontext_df = apnews_df.loc[
        apnews_df["verdict"] == "Missing context"
    ]  # 3228 support/query/comment
    partlyfalse_df = apnews_df.loc[
        apnews_df["verdict"] == "Partly false"
    ]  # 3481 comment/query
    alteredphoto_df = apnews_df.loc[
        apnews_df["verdict"] == "Altered photo"
    ]  # 3316 deny
    false_df = apnews_df.loc[apnews_df["verdict"] == "False"]  # 5077 deny

    print(
        len(true_df),
        len(missingcontext_df),
        len(partlyfalse_df),
        len(alteredphoto_df),
        len(false_df),
    )

    cnt_0, cnt_1, cnt_2 = 0, 0, 0
    texts, labels = [], []
    for idx, df in enumerate(
        [true_df, missingcontext_df, partlyfalse_df, alteredphoto_df, false_df]
    ):
        for row in df.iterrows():
            row = row[1]
            texts.append([row["fact"], row["claimReviewed"]])

            # True, Mostly True are considered as Positive
            if idx == 0 or idx == 1:
                labels.append(0)
                cnt_0 += 1
            # Half True is considered as Neutral
            elif idx == 2:
                labels.append(1)
                cnt_1 += 1
            # Bare True, False, Pansfire are considered as Negative
            elif idx == 3 or idx == 4 or idx == 5:
                labels.append(2)
                cnt_2 += 1

    # print(cnt_0, cnt_1, cnt_2)
    return texts, labels


if __name__ == "__main__":
    get_factclaimpairs()
    # texts, labels = get_factclaimpairs()
