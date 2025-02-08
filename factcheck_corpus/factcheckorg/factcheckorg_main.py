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
from utils.factcheckorg_xpath import factcheckorg_xpath

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Factcheck.org timestamp:", current_time)

def main():
    """ Glitches url
    """
    base_url = "https://factcheck.org"
    # total page: 350
    new_data, page_num, cont, publisher = [], 0, True, 'factcheckorg'
    latest_claim_url, add_header = get_latest_claim_url(src='factcheckorg')

    while cont:
        page_url = base_url + "/page/"+str(page_num)+"/"
        page_source = make_request(page_url, verify='./consolidate.pem')
        selector = etree.HTML(page_source)
        cont = False
        
        article_urls = factcheckorg_xpath(selector, item='articles')
        if not article_urls: print('Cannot find any articles in page: {}'.format(page_url))
        
        pubdates = factcheckorg_xpath(selector, item='pubdates')
        if not pubdates: 
            print('Cannot find any article publish date in page: {}'.format(page_url))
            pubdates = [''] * 10
        else: pubdates = [p.lstrip().rstrip() for p in pubdates]
        
        imageurls = factcheckorg_xpath(selector, item='imageurl')
        if not imageurls: 
            print('Cannot find any thumbnail image in page: {}'.format(page_url))
            imageurls = [''] * 10
        else: imageurls = [p.lstrip().rstrip() for p in imageurls]
        
        for article_url, pubdate, imageurl in zip(article_urls, pubdates, imageurls):
            article_source = make_request(article_url, verify='./consolidate.pem')
            article_selector = etree.HTML(article_source)
            
            fact = factcheckorg_xpath(article_selector, item='fact')
            if not fact: print('Cannot find any fact in page: {}'.format(article_url))
            else: fact = fact[0]
            
            # note that there is no space between paragraphs
            review = factcheckorg_xpath(article_selector, item='review')
            if not review: print('Cannot find any review in page: {}'.format(article_url))
            else: review = ' '.join(review).replace('  ', ' ').replace('\n', ' ')
            
            author = factcheckorg_xpath(article_selector, item='author')
            if not author: print('Cannot find any author in page: {}'.format(article_url))
            else: author = ', '.join(author)

            tags = factcheckorg_xpath(article_selector, item='tags')
            if not tags: print('Cannot find any tags in page: {}'.format(article_url))
            else: tags = ", ".join(tags)

            pubdate = format_date('factcheckorg', pubdate)
            
            data = (publisher, "", fact, review, "", author, "", pubdate, imageurl, article_url, tags)
            if article_url in latest_claim_url:
                cont = False
                break
            elif all([fact, review, pubdate, author]):
                new_data.append(data)
                cont = True

        page_num += 1
        
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/factcheckorg.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/factcheckorg.csv', mode='a', header=None, index=False)
    return new_df
            
if __name__ == '__main__':
    conn = create_connection('postgresql')
    new_data = main()
    
    if not new_data.empty: insert_factcheck(conn, new_data, 'factcheckorg')
    else: print("factcheckorg scrapper didn't find new data")
    conn.close()