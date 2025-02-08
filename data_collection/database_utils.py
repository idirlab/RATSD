import json
import mysql.connector
from credentials import DB_PASSWORD
from tqdm import tqdm
from collections import Counter

db = mysql.connector.connect(
    host="localhost", user="root", passwd=DB_PASSWORD, database="wildfire", port=3308
)
db.autocommit = True
my_cursor = db.cursor()

"""
Sentence table: 
    ('id', 'claim_author', 'claim', 'tweet', 'screening', 'answered', 'tweet_url_title', 'claim_timestamp', 
     'tweet_timestamp', 'tweet_id', 'tweet_userhandle', 'retweet_count', 'reply_count', 'like_count', 'quote_count', 
     'claim_source', 'claim_verdict', 'factcheck_timestamp', 'claim_review_summary', 'claim_review', 'factcheck_url', 
     'claim_tags', 'claimbuster_score', 'pair_id', 'factcheck_author_url', 'factcheck_post_time', 'factcheck_author_info')
"""


def get_top_annotators():
    get_top_quality_annotators_query = f"""
        SELECT su.username as USERNAME
        FROM		Sentence_User su,
                    Sentence s
        WHERE		s.id = su.sentence_id and
                    su.response != -2 and
                    s.id not in (select sentence_id from Training)
        GROUP BY 	su.username
        HAVING		-0.20*	(	sum(if(screening = 0 and response = 0, 1, 0))+ sum(if(screening = 1 and response = 1, 1, 0))+ sum(if(screening = 2 and response = 2, 1, 0))+ sum(if(screening = 3 and response = 3, 1, 0))+ sum(if(screening = -1 and response = -1, 1, 0)) ) / ( sum(screening != -3 and response != -2))
                    +0.50 *	(	sum(if(screening = 0 and response = 3, 1, 0))+ sum(if(screening = 1 and response = 0, 1, 0))+ sum(if(screening = 1 and response = 2, 1, 0))+ sum(if(screening = 2 and response = 1, 1, 0))+ sum(if(screening = 2 and response = 3, 1, 0))+ sum(if(screening = 3 and response = 2, 1, 0))+ sum(if(screening = 3 and response = -1, 1, 0))+ sum(if(screening = -1 and response = 3, 1, 0)) ) / ( sum(screening != -3 and response != -2))
                    +0.50*	(	sum(if(screening = 0 and response = 2, 1, 0))+ sum(if(screening = 1 and response = 3, 1, 0))+ sum(if(screening = 2 and response = 0, 1, 0))+ sum(if(screening = 2 and response = -1, 1, 0))+ sum(if(screening = 3 and response = 1, 1, 0))+ sum(if(screening = -1 and response = 2, 1, 0))+ sum(if(screening = 3 and response = 0, 1, 0))+ sum(if(screening = -1 and response = 0, 1, 0)) ) / (sum(screening != -3 and response != -2))
                    +1.00*	(	sum(if(screening = 0 and response = 1, 1, 0))+ sum(if(screening = 0 and response = -1, 1, 0)) ) / (sum(screening != -3 and response != -2))
                    +2.00*	(	sum(if(screening = 1 and response = -1, 1, 0))+ sum(if(screening = -1 and response = 1, 1, 0)) ) / (sum(screening != -3 and response != -2)) <= 0.0
        and count(*) >= 10;
    """
    my_cursor.execute(get_top_quality_annotators_query)
    resp = my_cursor.fetchall()
    print(f"There are {len(resp)} top annotators.")
    res = ",".join(["'" + r[0] + "'" for r in resp])
    print(f"Top annotators are: {res}.")
    return res


def get_finished_pairs(top_annotators):
    # get agreed pairs from annotators
    get_finished_pairs_query = f"""
        SELECT A.sentence_id, A.Label_0, A.Label_1, A.Label_2, A.Label_3, A.Label_4 -- , "TOP_QUALITY_SENTENCES01"*/
        FROM (
            select 	su.sentence_id, s.screening,
                    sum(if(su.response = -1, 1, 0)) as Label_0,
                    sum(if(su.response = 0, 1, 0)) as Label_1,
                    sum(if(su.response = 1, 1, 0)) as Label_2,
                    sum(if(su.response = 2, 1, 0)) as Label_3,
                    sum(if(su.response = 3, 1, 0)) as Label_4
            from		Sentence_User as su, Sentence s
            where		s.id = su.sentence_id and
                        s.screening = -3 and
                        su.sentence_id not in (select sentence_id from Training) and
                        su.username in ({top_annotators})
            group by	sentence_id
            having		(Label_0 >= 3 and	Label_0 >= 2+Label_1	and	Label_0 >= 2+Label_2	and	Label_0 >= 2+Label_3	and	Label_0 >= 2+Label_4 	and	Label_0 >= round((Label_1 + Label_2 + Label_3 + Label_4) / 2, 1) ) or
								(Label_1 >= 3 and	Label_1 >= 2+Label_0	and	Label_1 >= 2+Label_2	and	Label_1 >= 2+Label_3	and	Label_1 >= 2+Label_4 	and	Label_1 >= round((Label_0 + Label_2 + Label_3 + Label_4) / 2, 1) ) or
								(Label_2 >= 3 and	Label_2 >= 2+Label_0	and	Label_2 >= 2+Label_1	and	Label_2 >= 2+Label_3	and	Label_2 >= 2+Label_4 	and	Label_2 >= round((Label_0 + Label_1 + Label_3 + Label_4) / 2, 1) ) or
								(Label_3 >= 3 and	Label_3 >= 2+Label_0	and	Label_3 >= 2+Label_1	and	Label_3 >= 2+Label_2	and	Label_3 >= 2+Label_4 	and	Label_3 >= round((Label_0 + Label_1 + Label_2 + Label_4) / 2, 1) ) or
								(Label_4>0) 
        ) A;
    """
    my_cursor.execute(get_finished_pairs_query)
    resp = my_cursor.fetchall()
    print(f"There are {len(resp)} finished pairs.")
    return resp


def insert_sentence(json_path):
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
    with open(json_path, "r") as dataset:
        data = json.load(dataset)
        print(len(data))
        # insert data into Sentence table
        for idx in tqdm(range(len(data))):
            v = data[idx]
            sql = f"""INSERT INTO wildfire.Sentence (id, claim_author, claim, tweet, screening, answered, tweet_url_title, claim_timestamp, tweet_timestamp, tweet_id, tweet_userhandle, retweet_count, reply_count, like_count, quote_count, claim_source, claim_verdict, factcheck_timestamp, claim_review_summary, claim_review, factcheck_url, claim_tags, claimbuster_score, pair_id, factcheck_author_url, factcheck_post_time, factcheck_author_info, subset) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   """
            if v["tweet_url_title"] == [] or v["tweet_url_title"] == None:
                v["tweet_url_title"] = ""
            else:
                # resolve the emoji in the tweet_url_title
                v["tweet_url_title"] = (
                    v["tweet_url_title"].encode("ascii", "ignore").decode("ascii")
                )

            if v["id"] in screening:
                print("screening ", v["id"])
                v["screening"] = screening[v["id"]]
            vals = (
                v["id"],
                v["claim_author"],
                v["claim"],
                v["tweet"],
                v["screening"],
                0,
                v["tweet_url_title"],
                v["claim_timestamp"],
                v["tweet_timestamp"],
                v["tweet_id"],
                v["tweet_userhandle"],
                v["retweet_count"],
                v["reply_count"],
                v["like_count"],
                v["quote_count"],
                v["claim_source"],
                v["claim_verdict"],
                v["factcheck_timestamp"],
                v["claim_review_summary"],
                v["claim_review"],
                v["factcheck_url"],
                v["claim_tags"],
                v["claimbuster_score"],
                v["pair_id"],
                v["factcheck_author_url"],
                v["factcheck_post_time"],
                v["factcheck_author_info"],
                v["id"] % 10,
            )
            try:
                my_cursor.execute(sql, vals)
            except Exception as e:
                print(e)
                print(v)
                break


def export_annotated_dataset():
    """
    Export finished pairs from Sentence table
    """
    top_annotators = get_top_annotators()
    resp = get_finished_pairs(top_annotators)
    annotator_agreements = {}
    for r in resp:
        if r[5] != 0:
            annotator_agreements[r[0]] = 3
        else:
            idx = r.index(max(r[1:]))
            if idx == 1:
                annotator_agreements[r[0]] = -1
            elif idx == 2:
                annotator_agreements[r[0]] = 0
            elif idx == 3:
                annotator_agreements[r[0]] = 1
            elif idx == 4:
                annotator_agreements[r[0]] = 2

    # get the screening and training pairs
    screening_pairs = {}
    sql = f"""SELECT id, screening FROM Sentence WHERE screening!=-3"""
    my_cursor.execute(sql)
    resp = my_cursor.fetchall()
    for r in resp:
        if r[1] != 3:
            screening_pairs[r[0]] = r[1]
    annotator_agreements.update(screening_pairs)
    print("There are", len(annotator_agreements), "annotated pairs.")
    # get detail information based on the annotator_agreements's sentence_id
    sql = f"""SELECT id, claim_author, claim, tweet, screening, answered, tweet_url_title, claim_timestamp, tweet_timestamp, tweet_id, tweet_userhandle, retweet_count, reply_count, like_count, quote_count, claim_source, claim_verdict, factcheck_timestamp, claim_review_summary, claim_review, factcheck_url, claim_tags, claimbuster_score, pair_id, factcheck_author_url, factcheck_post_time, factcheck_author_info, subset FROM Sentence WHERE id in ({','.join([str(k) for k, v in annotator_agreements.items()])});"""
    my_cursor.execute(sql)
    resp = my_cursor.fetchall()
    verdicts_distribution = Counter()
    label_distribution = Counter()
    seen_claims = set()

    # # export the agreements into a json
    with open("./data_collection/processed_datasets/TruthSD_20241014.json", "w") as f:
        ans = []
        for r in resp:
            r = list(r)
            if r[2] not in seen_claims:
                seen_claims.add(r[2])
                verdicts_distribution[r[16]] += 1

            r.append(annotator_agreements[r[0]])
            label_distribution[annotator_agreements[r[0]]] += 1
            ans.append(r)
        json.dump(ans, f, indent=4)
    print(verdicts_distribution)
    print(f'Unique claim count: {sum(verdicts_distribution.values())}')
    print(label_distribution)
    print(sum(label_distribution.values()))
    return annotator_agreements


def test_conn():
    """
    Test the connection to the database
    """
    sql = f"SELECT * FROM wildfire.Sentence limit 1"
    my_cursor.execute(sql)
    resp = my_cursor.fetchall()
    if resp:
        print("Successfully connected to the database!")
    else:
        print("Failed to connect to the database!")


if __name__ == "__main__":
    """
    test functionality
    """
    # test_conn()
    # top_annotators = get_top_annotators()
    # get_finished_pairs(top_annotators)

    """
    insert data into Sentence table
    """
    # insert_sentence('./data_collection/tweet_data/test/claim_related_tweets_v5_nofactchecker_withclaimant_mysql.json')
    # insert_sentence('./data_collection/tweet_data/test/claim_related_tweets_v6_rawurlvalid.json')
    # insert_sentence('/Users/zzy/Downloads/groundtruth_sentence_2023_04_07.json')

    """
    export finished pairs
    """
    export_annotated_dataset()
