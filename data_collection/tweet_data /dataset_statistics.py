import json
from tqdm import tqdm
from collections import Counter
import glob


def count_unique_factual_claims(json_data):
    claim_set = set()
    for data in json_data:
        claim = data["claim"]
        claim_set.add(claim)
    return len(claim_set)


def count_unique_users(json_data):
    usr_set = set()
    for data in json_data:
        usr = data["tweet_userhandle"]
        usr_set.add(usr)
    return len(usr_set)


def get_time_range(json_data):
    time_range = []
    for data in json_data:
        time = data["claim_timestamp"]
        time_range.append(time)
    return min(time_range), max(time_range)


def get_all_tags(json_path):
    """
    collect all the tags from tweet-claim pair
    Possible health related tags are:
        Abortion, Medical professionals and vaccines, Ebola, Addiction, Drugs
        Disability, Drug Administration and Control,
    """
    tags = set()
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            for t in item["claim_tags"].split(","):
                tags.add(t.strip())
    return tags


def get_pairs_with_health_tag(json_path, health_tags):
    health_pairs = []
    cnt = Counter()
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        for item in tqdm(dataset):
            if any(t in item["claim_tags"] for t in health_tags):
                if cnt[item["claim"]] < 10:
                    health_pairs.append(item)
                    cnt[item["claim"]] += 1

    print("total health related tweet-claim pairs: ", sum(cnt.values()))
    # save the health related pairs
    with open(json_path.replace(".json", "_health.json"), "w", encoding="utf-8") as f:
        json.dump(health_pairs, f, ensure_ascii=False, indent=4)


def filter_out_pairs_with_invalid_url(json_path):
    valid_pairs = []
    training = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
    screening = {
        1466: 1,
        9355: 1,
        6247: 1,
        1611: 1,
        1414: 1,
        6245: 1,
        1233: 1,
        9914: 2,
        8144: 1,
        2008: 1,
        10899: 1,
        7570: 2,
        2861: 1,
        2249: 1,
        3882: 1,
        6866: 1,
        2252: -1,
        2928: 1,
        6637: 1,
        8230: 1,
        7381: 1,
        9358: 1,
        11376: 0,
        7565: 2,
        10247: 1,
        10924: 1,
        1572: -1,
        5295: 1,
        2160: 1,
        3829: 1,
        3527: 2,
        10852: 1,
        5264: 1,
        8139: 1,
        2380: 1,
        3466: 1,
        10179: 1,
        2884: 3,
        9325: -1,
        5261: 1,
        5178: 1,
        9465: 1,
        5504: 1,
        1236: 1,
        2799: 1,
        3256: 1,
        1624: 1,
        4622: -1,
        3531: -1,
        1730: 1,
        6486: -1,
        9735: 0,
        1835: 1,
        10912: 1,
        4924: 2,
        3889: 1,
        9360: 1,
        4794: 1,
        6481: 2,
        2494: -1,
        1491: 1,
        4017: 1,
        2164: 1,
        1232: 1,
        5550: 1,
        9985: 1,
        6913: 1,
        1725: 1,
        5393: -1,
        6835: 1,
        7365: 1,
        1986: 1,
        7382: 1,
        5378: 1,
        7569: 2,
        3861: 1,
        382: 1,
        2457: 1,
        7230: 1,
        2148: 1,
        1018: 1,
        1777: 1,
        11463: 1,
        314: 1,
        2167: 1,
        1724: 1,
        3804: 1,
        5272: 1,
        4672: 1,
        1788: 1,
        3862: 1,
        11449: 1,
        2889: 1,
        3203: 1,
        9969: 1,
        10829: 1,
        5181: 1,
        2147: -1,
        2162: -1,
        9931: 1,
        1441: 1,
        10267: 1,
        11369: 1,
        9824: 1,
        9401: 1,
        5385: 0,
        10444: 2,
        2791: -1,
        3900: 1,
        4664: 1,
        10932: -1,
        1239: 1,
        3258: 1,
        6860: 1,
        11478: 1,
        5713: 1,
        4911: 1,
        11386: 1,
        7772: 1,
        4666: 1,
        5837: 0,
        7035: 1,
        10451: 3,
        2251: 1,
        6448: -1,
        6871: 1,
        9996: 1,
        7574: 2,
        4920: 2,
        4854: 1,
        4488: 1,
        1784: 1,
        10887: -1,
        1786: 1,
        2937: 1,
        1833: 1,
        2401: -1,
        10884: 1,
        2253: 1,
        10414: 1,
        2032: 1,
        3810: 1,
        1234: 1,
        1468: -1,
        9967: 1,
        6135: 1,
        11372: -1,
        1240: 1,
        2933: 1,
        3609: 1,
        7557: 1,
        10250: 1,
        3606: 1,
        9471: 1,
        1727: 1,
        10885: 1,
        2835: 1,
        4992: 1,
        3437: 1,
        6134: -1,
        1566: 1,
        11447: 1,
        790: -1,
        5438: 1,
        1444: 1,
        10201: 0,
        11455: 1,
        5671: 1,
        3530: -1,
        2115: 1,
        8174: -1,
        7363: 0,
        5452: 0,
        11390: 1,
        5274: 1,
        4857: 1,
        9828: 1,
        3693: 1,
        9356: 1,
        1625: 1,
        5396: -1,
        2891: 0,
        9522: 1,
        5330: 1,
        1231: 1,
        2881: 3,
        9385: 1,
        10386: 1,
        2934: 1,
        9518: 1,
        6225: 1,
        3827: -1,
        7143: 1,
        6791: 1,
        2867: 1,
        7568: 2,
        10494: 1,
        4900: 1,
        6906: 1,
        5183: 1,
        322: 1,
        2789: 1,
        6868: 1,
        9288: -1,
        2009: 1,
        4016: 1,
        5442: 1,
        5377: 1,
        6787: 1,
        1095: 1,
        7572: 2,
        10828: 1,
        2525: 1,
        4921: 2,
        4678: 1,
        5443: 0,
        4020: 1,
        4490: 1,
        1235: 1,
        9183: -1,
        9404: 1,
        2890: 1,
        3701: 1,
        10817: 1,
        9812: -1,
        1681: 1,
        5440: 0,
        11448: 1,
        11388: 1,
        4478: 1,
        11384: 1,
        4671: 1,
        5486: 1,
        4658: 1,
        11374: 1,
        9988: 0,
        9399: 1,
        7564: 1,
        2866: 1,
        1834: 1,
        3436: 1,
        3494: 1,
        1783: 1,
        4015: 1,
        11385: 1,
        10941: 1,
        6865: 1,
        2569: 1,
        4898: 1,
        2859: -1,
        4705: 1,
        5882: 1,
        5398: -1,
        9408: 1,
        5376: 1,
        3884: 1,
        3363: 1,
        7048: 1,
        1785: 1,
        10888: -1,
        6485: 2,
        4899: 1,
        1722: 1,
        3846: 0,
        11392: 1,
        10495: -1,
        9555: 1,
        10936: 2,
        4919: 1,
        10925: 1,
        10906: 1,
        2527: 1,
        5184: 1,
        7384: 1,
        1789: 1,
        10919: 1,
        10939: 0,
        5269: 1,
        4014: 1,
        4823: 1,
        1840: 1,
        2010: 1,
        5530: 1,
        1839: 1,
        1565: 1,
        2735: 1,
        6930: 0,
        5170: -1,
        10942: 1,
        9395: 1,
        2468: 1,
        10921: 1,
        2142: 0,
        1438: 1,
        6556: 1,
        10180: 1,
        5441: 1,
        1017: 1,
        5379: 1,
        1446: 1,
        1837: 1,
        10314: -1,
        1836: 1,
        2935: 1,
        11393: 1,
        2459: 1,
        10894: -1,
        4859: 1,
        4923: 2,
        9651: 1,
        1230: 1,
        2011: 1,
        10208: 1,
        1778: 1,
        7037: 1,
        11389: 1,
        5380: 1,
        9362: 1,
        2423: 1,
        1421: 1,
        9684: 1,
        1: 1,
        3: -1,
        9: 2,
        15: 3,
    }
    screening_cnt = 0
    training_cnt = 0
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        print("total tweet-claim pairs before filtering: ", len(dataset))
        for item in tqdm(dataset):
            # the pair is screening question
            if item["id"] in screening:
                valid_pairs.append(item)
                screening_cnt += 1
            elif item["id"] in training:
                valid_pairs.append(item)
                training_cnt += 1

            # the pair doesn't have url
            elif "entities" not in item["raw_api_response"]:
                valid_pairs.append(item)
            elif "urls" not in item["raw_api_response"]["entities"]:
                valid_pairs.append(item)
            else:
                for url in item["raw_api_response"]["entities"]["urls"]:
                    # the pair has url but the url is not valid
                    if "status" not in url or url["status"] != 200:
                        break
                else:
                    valid_pairs.append(item)

    print("total tweet-claim pairs with valid urls: ", len(valid_pairs))
    print("total screening questions: ", screening_cnt)
    print("total training questions: ", training_cnt)
    # save the health related pairs
    with open(
        json_path.replace(".json", "_rawurlvalid.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(valid_pairs, f, ensure_ascii=False, indent=4)


def count_dataset_length(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    return len(dataset)


if __name__ == "__main__":
    # with open(
    #     "./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json"
    # ) as f:
    #     json_data = json.load(f)
    #     """
    #     collected tweet statistics
    #     """
    #     print("total tweets collected: ", len(json_data))
    #     claims_cnt = count_unique_factual_claims(json_data)
    #     print("total claims with related tweet collected: ", claims_cnt)
    #     users_cnt = count_unique_users(json_data)
    #     print("Unique user count: ", users_cnt)
    #     start_time, end_time = get_time_range(json_data)
    #     print("Time range: ", start_time, end_time)

    """
    collected health related tweet statistics
    """
    # json_path = "./data_collection/tweet_data/test/claim_related_tweets_v4_valid.json"
    # tags = get_all_tags(json_path)
    # print(tags)
    """
    get health related tweet-claim pairs
    """
    # json_path = "./data_collection/tweet_data/test/claim_related_tweets_v5.json"
    # # health_tags = ('Abortion', 'Medical professionals and vaccines', 'Ebola', 'Addiction', 'Disability')
    # health_tags = (
    #     "Abortion",
    #     "Medical professionals and vaccines",
    #     "Ebola",
    #     "Addiction",
    #     "Drugs",
    #     "Disability",
    #     "Drug Administration and Control",
    #     "Heartland Institute",
    #     "Planned Parenthood Action Fund",
    #     "National Right to Life Committee",
    #     "Medicare",
    #     "Anthony Fauci",
    #     "Social Security",
    #     "Health Care",
    #     "Coronavirus",
    #     "COVID-19",
    # )
    # get_pairs_with_health_tag(json_path, health_tags)
    """
    get valid tweet-claim pairs
    """
    # json_path = "./data_collection/tweet_data/test/claim_related_tweets_v6.json"
    # filter_out_pairs_with_invalid_url(json_path)

    # read all the files under data_collection/tweet_data/test and get the total number of tweet-claim pairs
    for file in glob.glob("./data_collection/tweet_data/test/*"):
        if file.endswith(".json"):
            try:
                l = count_dataset_length(file)
                print(file, l)
            except Exception as e:
                pass
