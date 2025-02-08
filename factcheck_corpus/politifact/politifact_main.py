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
from utils.politifact_xpath import politifact_xpath

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Politifact timestamp:", current_time)

def main():
    """
    Available data: publisher, claim, verdict, claimer, claimdate, factcheckPublishedData, url
    example for which doesn't have thumbnail url(https://www.politifact.com/factchecks/2021/jun/03/facebook-posts/no-stanley-meyer-was-not-assassinated-pentagon/)
    """
    # Setting base url and the link where the factcheck list is present
    url_prefix = "https://www.politifact.com/" 
    base_url = "https://www.politifact.com/factchecks/list/"
    
    # interesting glitch:  page 635-636 are missing
    page_num, cont, end_cnt, new_data, publisher = 1, True, 0, [], 'politifact'
    latest_claim_url, add_header = get_latest_claim_url(src="politifact")
    
    while cont:
        page_url = base_url + "?page="+str(page_num)+'&'
        page_source = make_request(page_url)
        selector = etree.HTML(page_source)
        cont = False
        
        data = politifact_xpath(selector, 'data')
        if not data:
            print('Cannot find any data in page: {}'.format(page_url))
            page_num, end_cnt, cont = page_num+1, end_cnt+1, True
            if end_cnt>3: break
            else: continue
        
        for j, obj in enumerate(zip(*data)):
            # Breaking the obj into multiple objects which we want to strip according to our needs in this case. 
            # For example: Striping the dates to make them uniform for scrappers in our database.   
            claimer, claim, claimdate, factcheckdate, verdict, url_postfix = obj
            
            claimer = claimer.lstrip().rstrip()
            claim = claim.lstrip().rstrip()
            
            claimdate = claimdate.split('on')[1].split(', ')
            claimdate = ", ".join([claimdate[0][1:], claimdate[1][:4]]).lstrip().rstrip()
            claimdate = format_date('politifact', claimdate)
            factcheckdate = factcheckdate.split('•')[1].lstrip().rstrip()
            factcheckdate = format_date('politifact', factcheckdate)
            url = url_prefix[:-1]+url_postfix
            
            subpage_source = make_request(url)
            subpage_selector = etree.HTML(subpage_source)
            
            # the section about "IF YOUR TIME IS SHORT ..."
            summary = politifact_xpath(subpage_selector, item='summary')
            if not summary: print("Cannot find summary of politifact in {}".format(url))
            
            # the main article
            review = politifact_xpath(subpage_selector, item='review')
            if not review: print("Cannot find review of politifact in {}".format(url))
            else: review = ' '.join(review).replace('\n', '')
            
            imageurl = politifact_xpath(subpage_selector, item='imageurl')
            if not imageurl: print("Cannot find imageurl of politifact in {}".format(url))
            else: imageurl = imageurl[0]
            
            tags = politifact_xpath(subpage_selector, item='tags')
            if not tags: print("Cannot find tags of politifact in {}".format(url))
            else: tags = ', '.join(tags)

            data = (publisher, claim, summary, review, verdict, claimer, claimdate, factcheckdate, imageurl, url, tags)

            if not url in latest_claim_url:
                new_data.append(data)
                cont = True
            else:
                cont = False 
                break
        page_num += 1

    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/politifact.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/politifact.csv', mode='a', header=None, index=False)
    return new_df
        
    
if __name__ == '__main__':
    # The credectials of the database connection is in factcheckrepo\utils\db_util.py
    # For local testing, one need to setup postgreSQL on their local machine and use credentials mentioned above. 

    conn = create_connection()
    new_data = main()
    
    if not new_data.empty: insert_factcheck(conn, new_data, src='politifact')
    else: print("politifact scrapper didn't find new data")
    
    conn.close()