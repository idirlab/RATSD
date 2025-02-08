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
from utils.healthfeedback_xpath import healthfeedback_xpath

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Healthfeedback timestamp:", current_time)

def main():
    """
    """
    base_url = "https://healthfeedback.org/claim-reviews/"
    new_data, page_num, cont, publisher = [], 1, True, 'healthfeedback'
    
    latest_claim_url, add_header = get_latest_claim_url(src='fullfact')
    
    while cont:
        page_url = base_url + "/latest/?page="+str(page_num)
        page_source = make_request(page_url)
        selector = etree.HTML(page_source)
        cont = False
        
        urls = fullfact_xpath(selector, item='articles')
        if not urls: print('Cannot find any articles in page: {}'.format(page_url))

        imageurls = fullfact_xpath(selector, item='imageurl')
        if not imageurls: 
            print('Cannot find any thumbnail image in page: {}'.format(page_url))
            imageurls = [''] * len(urls)
                      
        for url, imageurl in zip(urls, imageurls):
            claim, review, factcheckdate, fact_checker, summary = '', '', '', '', ''

            url_source = make_request(base_url+url)
            url_selector = etree.HTML(url_source)

            claim = fullfact_xpath(url_selector, item='claim')
            if not claim: print('Cannot find any factual claim in page: {}'.format(base_url+url))
            else: claim = claim[0]
            
            summary = fullfact_xpath(url_selector, item='summary')
            if not summary: print('Cannot find any summary in page: {}'.format(base_url+url))
            else: summary = summary[0]
            
            factcheckdate = fullfact_xpath(url_selector, item='factcheckdate')
            if not factcheckdate: print('Cannot find any factcheckdate in page: {}'.format(base_url+url))
            else: factcheckdate = format_date('fullfact', factcheckdate[0])
            
            review = fullfact_xpath(url_selector, item='review')
            if not review: print('Cannot find any review in page: {}'.format(base_url+url))
            else: review = ' '.join(review).replace('  ', ' ')

            tags = fullfact_xpath(url_selector, item='tags')
            if not tags: print('Cannot find any tags in page: {}'.format(base_url+url))
            else: tags = ''.join([t.strip() for t in tags])
            
            
            data = (publisher, claim, summary, review, "", "", "", factcheckdate, base_url+imageurl, base_url+url, tags)

            if base_url+url in latest_claim_url:
                cont = False
                break
            else:
                if all([claim, summary, review, factcheckdate, imageurl]): new_data.append(data)
                cont = True

        page_num += 1
    
    # Building a dataframe using pandas. To store the collected data into csv file.  
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/fullfact.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/fullfact.csv', mode='a', header=None, index=False)
    return new_df
            
if __name__ == '__main__':
    # Building the connection between database and current script.
    # The credectials of the database connection is in factcheckrepo\utils\db_util.py
    # For local testing, one need to setup postgreSQL on their local machine and use credentials mentioned above. 
    conn = create_connection()
    new_data = main()
    
    if not new_data.empty: insert_factcheck(conn, new_data, 'fullfact')
    else: print("fullfact scrapper didn't find new data")
    conn.close()
