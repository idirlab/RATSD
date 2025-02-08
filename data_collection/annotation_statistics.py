import json
from collections import defaultdict, Counter



def count_each_class(json_path):
    class_cnt = defaultdict(int)
    with open(json_path, "r") as dataset:
        data = json.load(dataset)
        for d in data:
            class_cnt[d[-1]] += 1

    for k, v in class_cnt.items():
        if k == -1:
            k = "Negative"
        elif k == 0:
            k = "Neutral"
        elif k == 1:
            k = "Positive"
        elif k == 2:
            k = "Unrelated"
        print(f"For the class {k}, the labels are {v}")


def create_groundtruth():
    annotation_cnt = defaultdict(lambda: defaultdict(list))
    with open(
        "./data_collection/processed_datasets/health_annotation.json", "r"
    ) as dataset:
        data = json.load(dataset)
        for d in data:
            if d["response"] not in (-2, 2, 3):
                annotation_cnt[d["sentence_id"]][(d["response"])].append(d["username"])
        # disagreement = []
        # for k, v in annotation_cnt.items():
        #     if len(v)>1:
        #         disagreement.append([k, v])
        # disagreement.sort()
        # print(len(disagreement))
        # for x in disagreement:
        #     print(x)
        # # print(len(annotation_cnt))
        # print([d[0] for d in disagreement])

        agreement = {}
        agreement_cnt = 0
        for k, v in annotation_cnt.items():
            if len(v) == 1 and any(len(x) == 3 for x in v.values()):
                agreement_cnt += 1
        print(agreement_cnt)

        # if len(v)==3:
        #     agreement_cnt += 1
        # print(agreement_cnt)
        # if len(v)==1:
        #     for kk, vv in v.items():
        #         agreement[k] = kk
        # elif len(v)==2:
        #     for kk, vv in v.items():
        #         if 'zzy' in vv:
        #             agreement[k] = kk
    # print(agreement)
    # print(len(agreement))

    # with open('./data_collection/tweet_data/test/claim_related_tweets_v5_health_urlvalid_mysql.json') as dataset:
    #     data = json.load(dataset)
    #     final_data = []
    #     for d in data:
    #         # print(d['id'])
    #         if d['id'] in agreement:
    #             d['label'] = agreement[d['id']]
    #             final_data.append(d)

    # with open('./data_collection/tweet_data/test/claim_related_tweets_v5_health_urlvalid_mysql_label.json', 'w') as dataset:
    #     json.dump(final_data, dataset, indent=4)


def get_claims():
    claims = set()
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v5_health_urlvalid_mysql_label.json",
        "r",
    ) as dataset:
        data = json.load(dataset)
        for d in data:
            if d["claim"][0] == '"' and d["claim"][-1] == '"':
                d["claim"] = d["claim"][1:-1]
            else:
                claims.add(d["claim"])
    print(list(claims))


def get_sample_pairs():
    pairs = defaultdict(set)
    with open(
        "./data_collection/tweet_data/test/claim_related_tweets_v5_health_urlvalid_mysql_label.json",
        "r",
    ) as dataset:
        data = json.load(dataset)
        for d in data:
            if len(pairs[d["label"]]) < 2:
                if d["claim"][0] == '"' and d["claim"][-1] == '"':
                    claim = d["claim"][1:-1]
                else:
                    claim = d["claim"]
                pairs[d["label"]].add((claim, d["tweet"], "BERT"))

    for k, v in pairs.items():
        for x in v:
            print(list(x))


def process_raw_twitter_api():
    # read the raw twitter api response
    with open("./data_collection/tweet_data/test/test_api.jsonl", "r") as dataset:
        data = json.load(dataset)["data"]
        tweet_texts = set()
        for tweet in data:
            tweet_texts.add(tweet["text"])
        print(len(tweet_texts))
        for x in tweet_texts:
            print("-----------------")
            print(x)


def count_label_by_all():
    cnt = Counter()
    with open(
        "./data_collection/processed_datasets/health_annotation.json", "r"
    ) as dataset:
        data = json.load(dataset)
        for d in data:
            # if d['response'] not in (-2, 2, 3):
            cnt[d["sentence_id"]] += 1
    print(
        "There are {} paris labeled by 2".format(
            sum([1 for k, v in cnt.items() if v == 2])
        )
    )  # 151
    print(
        "There are {} paris labeled by 3".format(
            sum([1 for k, v in cnt.items() if v == 3])
        )
    )  # 13


if __name__ == "__main__":
    # get_all_labeled()
    # create_groundtruth()
    # get_claims()
    # get_sample_pairs()
    # process_raw_twitter_api()
    # count_label_by_all()
    # count_agreement('/Users/zzy/Downloads/groundtruth_annotation_2023_04_06.json')

    # Count the number of pairs for each class
    count_each_class("./data_collection/processed_datasets/TruthSD_20240131.json")
