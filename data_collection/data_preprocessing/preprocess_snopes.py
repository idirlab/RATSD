import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd


def get_reviewclaimpairs():
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
    snopes_df = pd.read_csv(
        "./data_collection/raw_data/factcheckrepo/snopes.csv", names=headers
    )
    print(snopes_df["verdict"].unique(), len(snopes_df["verdict"].unique()))

    verdict_types = [
        "False"
        "True"
        "Mixture"
        "Unproven"
        "true"
        "pants-fire"
        "half-flip"
        "full-flop"
        "no-flip"
    ]

    # true_df = snopes_df.loc[snopes_df['verdict']=='true'] # 2457 support
    # mostlytrue_df = snopes_df.loc[snopes_df['verdict']=='mostly-true'] # 3228 support/query/comment
    # halftrue_df = snopes_df.loc[snopes_df['verdict']=='half-true'] # 3481 comment/query
    # baretrue_df = snopes_df.loc[snopes_df['verdict']=='barely-true'] # 3316 deny
    # false_df = snopes_df.loc[snopes_df['verdict']=='false'] # 5077 deny
    # pantsfire_df = snopes_df.loc[snopes_df['verdict']=='pants-fire'] # 2529 deny

    # noflip_df = snopes_df.loc[snopes_df['verdict']=='no-flip'] # 28
    # halfflip_df = snopes_df.loc[snopes_df['verdict']=='half-flip'] # 75
    # fullflop_df = snopes_df.loc[snopes_df['verdict']=='full-flop'] # 175

    # # print(len(true_df), len(mostlytrue_df), len(halftrue_df), len(baretrue_df), len(false_df),
    # #       len(pantsfire_df), len(noflip_df), len(halfflip_df), len(fullflop_df))

    # cnt_0, cnt_1, cnt_2 = 0, 0, 0
    texts, labels = [], []
    # for idx, df in enumerate([true_df, mostlytrue_df, halftrue_df, baretrue_df, false_df, pantsfire_df]):
    #     for row in df.iterrows():
    #         row = row[1]
    #         texts.append([row['fact'], row['claimReviewed']])
    #         # if ? in review, that is a question rather than factual claim
    #         if '?' in row['fact']:  continue
    #         # True, Mostly True are considered as Positive
    #         if idx==0 or idx==1:
    #             labels.append(0)
    #             cnt_0 += 1
    #         # Half True is considered as Neutral
    #         elif idx==2:
    #             labels.append(1)
    #             cnt_1 += 1
    #         # Bare True, False, Pansfire are considered as Negative
    #         elif idx==3 or idx==4 or idx==5:
    #             labels.append(2)
    #             cnt_2 += 1

    # print(cnt_0, cnt_1, cnt_2)
    return texts, labels


if __name__ == "__main__":
    texts, labels = get_tweetclaimpairs()
