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

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Apnews timestamp:", current_time)

def main():
    new_data, publisher, page_url = [], 'apnews', "https://apnews.com/hub/fact-checking"
    latest_claim_url, add_header = get_latest_claim_url(src='apnews')

    page_source = make_request(page_url)
    selector = etree.HTML(page_source)
    
    article_urls = apnews_xpath(selector, item='articles')
    if not article_urls: print('Cannot find any articles in page: {}'.format(page_url))
    
    pubdates = apnews_xpath(selector, item='pubdates')
    if not pubdates: 
        print('Cannot find any article publish date in page: {}'.format(page_url))
        pubdates = [''] * len(article_urls)
    else: pubdates = [format_date('apnews', p[:-4]) for p in pubdates] # [:-4] for removing ` GMT`
    
    authors = apnews_xpath(selector, item='authors')
    if not authors: 
        print('Cannot find any authors in page: {}'.format(page_url))
        authors = [''] * len(article_urls)
    else: authors = [''.join(a.split('By ')[1]) for a in authors]
    
    for article_url, pubdate, author in zip(article_urls, pubdates, authors):
        article_url = 'https://apnews.com'+article_url
        article_source = make_request(article_url)
        article_selector = etree.HTML(article_source)
        
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
        if not tags: print('Cannot find any tags in page: {}'.format(article_url))
        else: tags = ", ".join(tags)
        
        data = (publisher, claim, summary, review, verdict, author, "", pubdate, "", article_url, tags)
        if article_url in latest_claim_url: break
        elif claim and summary and review and verdict and author and pubdate and article_urls and tags: 
            new_data.append(data)

        
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/apnews.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/apnews.csv', mode='a', header=None, index=False)
    return new_df
            
if __name__ == '__main__':
    conn = create_connection('postgresql')
    
    new_data = main()
    if not new_data.empty: insert_factcheck(conn, new_data, 'apnews')
    else: print("apnews scrapper didn't find new data")
    
    conn.close()
