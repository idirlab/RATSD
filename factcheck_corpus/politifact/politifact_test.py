""" Test single page
"""
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

def main(url):
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

    print(review)
        
    
if __name__ == '__main__':
    test_url = "https://www.politifact.com/factchecks/2022/feb/18/shelia-stubbs/stubbs-48-hour-gun-waiting-period-statement-backed/"
    main(test_url)