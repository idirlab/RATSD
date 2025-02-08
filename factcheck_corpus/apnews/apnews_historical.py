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
from utils.crawler_util import get_latest_claim_url, make_request, reverse_csv, format_date, CSV_HEADER
from utils.db_util import create_connection, insert_factcheck
import psycopg2
import mysql.connector
from utils.apnew_xpath import apnews_xpath
from apnews.twitter_credential import *
from twarc import Twarc2

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Apnews timestamp:", current_time)

def main():
    T = Twarc2(bearer_token=bear_token)
    historical_articles = []
    # each page has 100 tweets
    for page in T.search_all(query='from:APFactCheck -is:retweet'):
        for tweet in page['data']:
            if 'entities' in tweet and 'urls' in tweet['entities']:
                for url in tweet['entities']['urls']:
                    if "http://apne.ws/"==url['expanded_url'][:15]:
                        historical_articles.append(url['expanded_url'])
    
    new_data, publisher = [], 'apnews'
    
    for article_url in historical_articles:
        article_source = make_request(article_url)
        article_selector = etree.HTML(article_source)
        
        pubdate = apnews_xpath(article_selector, item='historical_pubdate')
        if not pubdate:
            print('Cannot find any article publish date in page: {}'.format(article_url))
            continue
        else: pubdate = format_date('apnews', pubdate[0][:-4])
        
        author = apnews_xpath(article_selector, item='historical_author')
        if not author: 
            print('Cannot find any author in page: {}'.format(article_url))
            continue
        else: 
            try: author = ''.join(author[0].split('By ')[1])
            except: author = author[0]
        
        body = apnews_xpath(article_selector, item='body')
        if not body: 
            print('Cannot find any body content in page: {}'.format(article_url))
            continue
        
        # convert body to list and check data completeness
        body = ''.join(body).replace(u'\xa0', u' ').replace('\n', ' ')
        if body[:7]!="CLAIM: ":
            print('Cannot find any claim in page: {}'.format(article_url))
            continue
        elif "AP’S ASSESSMENT:" not in body:
            print('Cannot find any summary in page: {}'.format(article_url))
            continue
        elif "THE FACTS:" not in body:
            print('Cannot find any review in page: {}'.format(article_url))
            continue

        try:
            claim, body = body.split("AP’S ASSESSMENT: ")
            # remove "CLAIM: " prefix in claim
            claim = claim[7:]
            verdict_summary, review = body.split("THE FACTS: ")
            verdict, summary = verdict_summary.split('. ')[0], ". ".join(verdict_summary.split('. ')[1:])
        except: 
            print("The data format is invalid")
            continue
        
        # extract tags at the bottom of the article page
        tags = apnews_xpath(article_selector, 'tags')
        if not tags:
            print('Cannot find any tags in page: {}'.format(article_url))
            continue
        else: tags = ", ".join(tags)
        
        data = (publisher, claim, summary, review, verdict, author, "", pubdate, "", article_url, tags)
        new_data.append(data)

            
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    new_df.to_csv('./dataset/apnews_historical.csv', mode='a', header=CSV_HEADER, index=False)
    return new_df
            
if __name__ == '__main__':
    new_data = main()
