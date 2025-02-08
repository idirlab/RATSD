# -*- coding: utf-8 -*-
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

import json
import requests
from datetime import datetime
from lxml import etree
import pandas as pd
import csv
import time
from utils.crawler_util import get_latest_claim_url, make_request, reverse_csv, infer_url, interrogative2declarative, choice2verdict, format_review, CSV_HEADER
from utils.db_util import create_connection, insert_factcheck

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("-----" * 10)
print("Metafact timestamp:", current_time)

def main():
    # base url of metafact
    # Setting base url and the link where the factcheck list is present
    url_prefix = "https://metafact.io/factchecks/"
    base_url = "https://metafact.io/factchecks/load_factchecks?filter=popular&include_fields=true&offset="
    page_offset, new_data, cont, publisher,  = 0, [], True, 'metafact'
    latest_claim_url, add_header = get_latest_claim_url(src="metafact")
    while cont:
        page_url = base_url+str(page_offset)
        json_response = make_request(page_url)
        # json_response is a str, "[]" is empty
        if len(json_response)==2: break

        for question_jsn in json.loads(json_response):
            has_answer = True
            if not cont: break
            fid, question = question_jsn['id'], question_jsn['question']
            claim_date = question_jsn['created_at'][:10]
            question_url = url_prefix+infer_url(fid, question)
            question = interrogative2declarative(question)
            tags = ", ".join([mp['name'] for mp in question_jsn['scientific_fields_by_mapping']])
            
            ans_offset = 0
            while has_answer:
                has_answer = False
                ans_urls = url_prefix+'{}/load_answers?filter=Top&offset={}'.format(fid, ans_offset)                
                ans_response = make_request(ans_urls)
                
                for ans_jsn in json.loads(ans_response):
                    if not ans_jsn['description']: continue
                    review = format_review(ans_jsn['description']).replace('\n', ' ')
                    verdict = choice2verdict(ans_jsn['choice'])
                    factcheck_date = ans_jsn['updated_at'][:10]
                    author = ' '.join([ans_jsn['user']['first_name'], ans_jsn['user']['last_name']])
                    
                    data = (publisher, question, "", review, verdict, author, claim_date, factcheck_date, "", question_url, tags)
                    
                    if question_url not in latest_claim_url:
                        new_data.append(data)
                        has_answer, cont = True, True
                    else:
                        has_answer, cont = False, False
                        break
                ans_offset += 20
        page_offset += 20
        
    new_df = pd.DataFrame(new_data)
    new_df = new_df.iloc[::-1]
    if add_header: new_df.to_csv('./dataset/metafact.csv', mode='a', header=CSV_HEADER, index=False)
    else: new_df.to_csv('./dataset/metafact.csv', mode='a', header=None, index=False)
    return new_df
            
            
if __name__ == '__main__':
    # Building the connection between database and current script.
    # The credectials of the database connection is in factcheckrepo\utils\db_util.py
    # For local testing, one need to setup postgreSQL on their local machine and use credentials mentioned above. 
    conn = create_connection()
    new_df = main()
    
    if not new_df.empty: insert_factcheck(conn, new_df, 'metafact')
    else: print("metafact scrapper didn't find new data")
    conn.close()