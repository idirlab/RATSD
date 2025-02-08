# -*- coding: utf-8 -*-
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

import json
from lxml import etree
import requests
from datetime import datetime
import pandas as pd
import csv
import time
from retry import retry
import psycopg2
import mysql.connector

from utils.crawler_util import get_latest_claim_url, make_request, reverse_csv, format_date, CSV_HEADER
from utils.db_util import create_connection, insert_factcheck
from utils.snopes_xpath import snopes_xpath

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Snopes timestamp:", current_time)

def main():
    base = "https://www.snopes.com"
    base_url = f"{base}/fact-check/"
    
    new_data, page_num, cont, publisher = [], 1, True, "snopes"
    latest_claim_url, add_header = get_latest_claim_url(src="snopes")

    while cont:
        page_url = base_url + "page/"+str(page_num)+'/'
        page_source = make_request(page_url)
        selector = etree.HTML(page_source)
        cont = False
        
        article_urls = snopes_xpath(selector, item="articles")
        if not article_urls: print("Cannot find article urls of Snopes in {}".format(page_url))
        for url in article_urls:
            claim, review, factcheckPublishedDate, author, verdict = [''], [''], '', '', ['']
            url_source = make_request(url)
            url_selector = etree.HTML(url_source)

            claim = snopes_xpath(url_selector, item='claim')
            if not claim: print("Cannot find claim of Snopes in {}".format(url))
            else: claim = claim[0].replace('\n', '').replace('\t', '')
            
            summary = snopes_xpath(url_selector, item='summary')
            if not summary: print("Cannot find summary of Snopes in {}".format(url))
            
            review = snopes_xpath(url_selector, item='review')
            if not review: print("Cannot find review of Snopes in {}".format(url))
            else: review = ' '.join(review)
            
            verdict = snopes_xpath(url_selector, item='verdict')
            if not verdict: print("Cannot find verdict of Snopes in {}".format(url))
            else: verdict = verdict[0]
            
            author = snopes_xpath(url_selector, item='author')
            if not author: print("Cannot find author of Snopes in {}".format(url))
            else: author = author[0].replace('\n', '').replace('\t', '')

            publishdate = snopes_xpath(url_selector, item='date')
            if not publishdate: print("Cannot find publish date of Snopes in {}".format(url))
            else: publishdate = format_date('snopes', publishdate[0])
            
            imageurl = snopes_xpath(url_selector, item='imageurl')
            if not imageurl: print("Cannot find imageurl of Snopes in {}".format(url))
            else: imageurl = imageurl[0]

            tags = snopes_xpath(url_selector, item='tags')
            if not tags: print("Cannot find tags of Snopes in {}".format(url))
            else: tags = tags[0].lstrip().rstrip()
            
            data = (publisher, claim, summary, review, verdict, author, "", publishdate, imageurl, url, tags)
            if url not in latest_claim_url:
                new_data.append(data)
                cont = True
            else:
                cont = False 
                break
        page_num += 1

    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/snopes.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/snopes.csv', mode='a', header=None, index=False)
    return new_df
        

if __name__ == '__main__':
    # The credectials of the database connection is in factcheckrepo\utils\db_util.py
    # For local testing, one need to setup postgreSQL on their local machine and use credentials mentioned above. 
    conn = create_connection()
    new_data = main()
    
    if not new_data.empty: insert_factcheck(conn, new_data, 'snopes')
    else: print("snopes scrapper didn't find new data")
    conn.close()