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
from utils.factcheckafp_xpath import factcheckafp_xpath

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Factcheck.afp timestamp:", current_time)

def main():
    """ Glitches url
    https://factcheck.afp.com/introduction-fact-checking-0
    https://factcheck.afp.com/training-resources
    """
    base_url = "https://factcheck.afp.com"
    # total page: 380
    new_data, page_num, cont, publisher = [], 1, True, 'factcheckafp'
    latest_claim_url, add_header = get_latest_claim_url(src='factcheckafp')
    
    while cont:
        page_url = base_url + "/list/all/all/?page="+str(page_num)
        page_source = make_request(page_url)
        selector = etree.HTML(page_source)
        cont = False   
        
        article_urls = factcheckafp_xpath(selector, item='articles')
        if not article_urls: print('Cannot find any articles in page: {}'.format(page_url))
        
        pub_dates = factcheckafp_xpath(selector, item='pubdates')
        if not pub_dates: 
            print('Cannot find any article publish date in page: {}'.format(page_url))
            pub_dates = [''] * len(article_urls)
        else: pub_dates = [p.lstrip().rstrip() for p in pub_dates]
        
        image_urls = factcheckafp_xpath(selector, item='imageurl')
        if not image_urls: 
            print('Cannot find any thumbnail image in page: {}'.format(page_url))
            image_urls = [''] * len(article_urls)
        else: image_urls = [p.lstrip().rstrip() for p in image_urls]
        
        for article_url, pub_date, image_url in zip(article_urls, pub_dates, image_urls):
            subpage_source = make_request(base_url+article_url)
            sub_selector = etree.HTML(subpage_source)
            
            pub_date = format_date('factcheckafp', pub_date)
            
            # abstract of fact check articles as fact
            summary = factcheckafp_xpath(sub_selector, item='summary')
            if not summary: print('Cannot find any summary in page: {}'.format(base_url+article_url))
            else: summary = ''.join(summary)
            
            review = factcheckafp_xpath(sub_selector, item='review')
            if not review: print('Cannot find any review in page: {}'.format(base_url+article_url))
            else: review = " ".join(review).replace('  ', ' ')
            
            tags = factcheckafp_xpath(sub_selector, item='tags')
            if not tags: print('Cannot find any tags in page: {}'.format(base_url+article_url))
            else: tags = ", ".join(tags)
            
            data = (publisher, "", summary, review, "", "", "", pub_date, base_url+image_url, base_url+article_url, tags)
            if base_url+article_url in latest_claim_url:
                cont = False
                break
            else:
                new_data.append(data)
                cont = True
                
        page_num += 1
        
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/factcheckafp.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/factcheckafp.csv', mode='a', header=None, index=False)
    return new_df
            
if __name__ == '__main__':
    conn = create_connection()
    new_data = main()
    
    if not new_data.empty: insert_factcheck(conn, new_data, 'factcheckafp')
    else: print("factcheckafp scrapper didn't find new data")
    conn.close()