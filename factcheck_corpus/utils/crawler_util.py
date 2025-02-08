# -*- coding: utf-8 -*-
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

from retry import retry
import requests
import os
import pandas as pd
from datetime import datetime
import html2text
from math import isnan
from lxml import etree
from utils.apnew_xpath import apnews_xpath
import uuid

CSV_HEADER = ['Publisher', 'Claim', 'Review Summary', 'Review', 'Verdict', 'Author', \
              'Claim Published Date', 'Factcheck Published Date', 'Image Url', \
              'Factcheck Url', 'Tags']

def format_date(src, predate):
    """ format any form of date to year-month-day
    """
    # E.g.: November 11, 2021
    if src in ['politifact', 'factcheckorg']:
        return datetime.strptime(predate, "%B %d, %Y").strftime("%Y-%m-%d") 
    if src in ['fullfact', 'snopes']:
        return datetime.strptime(predate, "%d %B %Y").strftime("%Y-%m-%d") 
    if src=='factcheckafp':
        return datetime.strptime(predate, "%d/%m/%Y").strftime("%Y-%m-%d") 
    if src=='apnews':
        try: return datetime.strptime(predate, "%B %d, %Y").strftime("%Y-%m-%d") 
        except: return datetime.now().strftime("%Y-%m-%d") # yesterday, 2hours ago etc.
        
        
    
def get_latest_claim_url(src="politifact"):
    if src=="politifact": csv_file = './dataset/politifact.csv'
    elif src=="snopes": csv_file = './dataset/snopes.csv'
    elif src=="metafact": csv_file = './dataset/metafact.csv'
    elif src=="fullfact": csv_file = './dataset/fullfact.csv'
    elif src=="factcheckafp": csv_file = './dataset/factcheckafp.csv'
    elif src=="factcheckorg": csv_file = './dataset/factcheckorg.csv'
    elif src=="apnews": csv_file = './dataset/apnews.csv'
    
    if os.path.isfile(csv_file):
        add_header = False
        latest_df = pd.read_csv(csv_file, on_bad_lines='skip')
        latest_series = latest_df.iloc[-10:]
        latest_series = latest_series.values[:]
        latest_claim_url = [s[-2] for s in latest_series]
        return latest_claim_url, add_header
    else:
        add_header = True
        print('The last version of {} doesn\'t exist'.format(csv_file))
        return "None", add_header

@retry(tries=5, delay=10)
def make_request(url, verify=None):
    if not verify: req = requests.get(url)
    else: req = requests.get(url, verify=verify)
    return req.text
    
def reverse_csv():
    if source=="politifact": csv_file = './dataset/politifact.csv'
    elif source=="snopes": csv_file = './dataset/snopes.csv'
    elif source=="metafact": csv_file = './dataset/metafact.csv'
    elif source=="fullfact": csv_file = './dataset/fullfact.csv'
    elif source=="factcheckafp": csv_file = './dataset/factcheckafp.csv'
    if os.path.isfile(csv_file):
        df = pd.read_csv(csv_file, header=None)
        df = df.iloc[::-1]
        df.to_csv(csv_file, mode='w', header=False, index=False)
        
def infer_url(fid, question):
    question = "".join([c for c in question if c.isalnum() or c==' ']).lower()
    return "-".join([str(fid)]+question.split())

def interrogative2declarative(question):
    # TODO: implement this function
    return question

def factcheck_statistic():
    csv_file1 = './dataset_bak/politifact.csv'
    csv_file2 = './dataset_bak/snopes.csv'
    csv_file3 = './dataset_bak/metafact.csv'
    csv_file4 = './dataset_bak/fullfact.csv'
    csv_file5 = './dataset_bak/factcheckafp.csv'
    csv_file6 = './dataset_bak/apnews.csv'
    csv_file7 = './dataset_bak/factcheckorg.csv'
    sm = 0
    for f in [csv_file1,csv_file2,csv_file3,csv_file4,csv_file5,csv_file6,csv_file7]:
        df = pd.read_csv(f)
        sm += df.shape[0]
    return sm
    

def choice2verdict(n):
    if n==1: return 'Near certain'
    elif n==2: return 'Likely'
    elif n==3: return 'Uncertain'
    elif n==4: return 'Unlikely'
    elif n==5: return 'Extremly unlikely'
    else: return ''
    
def format_review(text):
    return html2text.html2text(text)


def filter_nonhealth(src):
    """ filter out non-health-related fact-checks from sample file
    """
    if src=="politifact": csv_file = './dataset/politifact.csv'
    elif src=="snopes": csv_file = './dataset/snopes.csv'
    elif src=="metafact": csv_file = './dataset/metafact.csv'
    elif src=="fullfact": csv_file = './dataset/fullfact.csv'
    elif src=="factcheckafp": csv_file = './dataset/factcheckafp.csv'
    elif src=="factcheckorg": csv_file = './dataset/factcheckorg.csv'
    elif src=="apnews": csv_file = './dataset/apnews.csv'
    
    if os.path.isfile(csv_file):
        df = pd.read_csv(csv_file, header=None, on_bad_lines='warn')
        df.columns = HEADER
        df = df.dropna(subset='Tags')
        print("CSV file size: ", len(df))
        
        tags_col = df.iloc[:, -1].tolist()
        tags_set = set()
        for s in tags_col:
            for tag in s.split(', '):
                tags_set.add(tag)
        print("Number of tags: ", len(tags_set))
        # print(tags_set)
        
        health_tag = set()
        politifact_cand = [
            'health', 'disease', 'nhs', 'coronavirus', 'covid', 'drug'
            ]
        metafact_cand = [
            'asthma', 'fasting', 'migraine', 'cancer', 'pathology', 'paediatric', \
            'cholesterol', 'acne', 'stroke', 'cardiology', 'immunology', 
            'hematology', 'headaches', 'gynaecology', 'nephrology', 'pulmonology', \
            'traumatology', 'pediatrics', 'oncology', 'physiotherapy', 'therapy', \
            'clinic', 'pharmaceutical', 'immunopathology', 'etiology', 'immunotherapy', \
            'nutrition', 'osteology', 'hepatology', 'embryology', 'virology', \
            'dentistry', 'metabolomics', 'vaccinology', 'vaccine', \
            'addiction', 'obesity', 'psychopathology', 'immunogenetics', \
            'musculoskeletal', 'vitamin', 'Disorders', 'eating', 'endocrinology', \
            'epidemiology', 'psychiatry', 'food', 'psychology', 'autism', \
            'medical', 'medicine', 'gerontology', 'caffeine', 'obstetrics', \
            'infectious', 'audiology', 'parkinson', 'dermatology', 'mental', \
            'gastroenterology', 'pharmacology', 'fertility', \
            'aetiology', 'alzheimer', 'diabetes', 'urology', 'rheumatology', \
            'toxicology', 'allergology', 'ADHD', 'alcohol use', 'hematology', \
            'immunology', 'dietetic', 'ophthalmology', 'otolaryngology', \
            'anaesthesiology'
            ]
        cand = politifact_cand + metafact_cand
        
        for tag in tags_set:
            if any([c in tag.lower() for c in cand]):
                health_tag.add(tag)
        print("Number of health tags: ", len(health_tag))
        # print(health_tag)
        
        factcheck_with_label = []
        health_factcheck = []
        for _, row in df.iterrows():
            if any([t in health_tag for t in row['Tags'].split(', ')]):
                row['Label'] = True
                health_factcheck.append(row)
            else: row['Label'] = False
            factcheck_with_label.append(row)
        print("Number of health factcheck: ", len(health_factcheck))
        
        # save all fact checks with label
        output = pd.DataFrame(factcheck_with_label, columns=HEADER+['Label'])
        output.to_csv('./dataset/{}_with_label.csv'.format(src), index=False)
        # save health related fact checks
        output = pd.DataFrame(health_factcheck, columns=HEADER)
        output.to_csv('./dataset/{}_health.csv'.format(src), index=False)
    else:
        print('The csv file of {} doesn\'t exist'.format(csv_file))
        return False
    

def test_xpath():
    source = make_request('http://apne.ws/7oz8k7s')
    selector = etree.HTML(source)
    tags = apnews_xpath(selector, 'tags')
    print(tags)
    

def add_uuid(src):
    df = pd.read_csv('./dataset/{}.csv'.format(src), on_bad_lines='warn')
    df['uuid'] = [uuid.uuid4() for _ in range(len(df.index))]
    df.to_csv('./dataset/{}_with_uuid.csv'.format(src), mode='w', header=CSV_HEADER+["ID"], index=False)
    

if __name__ == "__main__":
    # tmp = get_latest_claim_url()
    # print(tmp, type(tmp))
    # infer_url(273, "Does lutein & zeaxanthin decrease the risk of macular degeneration?")
    # ans = format_review("<p>I agree with Robert Barber. I'd add two further points:</p><p><br></p><ol><li>The distinction between genes ('nature') and environment ('nurture') is now known not to be what is usually assumed: that they are separate influences.  We now know that there are genetic variations that, for example, incline people to take risks: this will affect their experiences. Conversely, there are experiences (eg maternal deprivation) that alter the expression (activity) of certain genes for long periods, maybe a lifetime. So each can alter the other, and what we are really considering is a mixture of influences.  All this applies to disorders such as Alzheimer's. The old distinction (nature vs nurture) no longer applies. </li><li>Alhzeimer's (AD) is not a single disorder, so the factors that  encourage or reduce its incidence will vary accordingly.  In some cases, for example, very early onset AD, there may be rare genetic variants that play a huge part in the risk.  But most cases are 'sporadic', and this applies to what Dr Barber says. </li></ol>")
    # print(ans)
    
    """ Test filter_nonhealth function
    Politifact: there are 4696 tags in 20668 fact checks, 27 tags are health-relate \
                3604 fact checks are health related.
    Metafact: there are 240 tags in 3345 fact checks, 98 tags are health-relate \
                2320 fact checks are health related.
    """
    # filter_nonhealth("politifact")
    # filter_nonhealth("metafact")
    
    """ Test fact check statistic
    """
    # sm = factcheck_statistic()
    # print(sm)
    
    """ Test xpath
    """
    # res = test_xpath()
    # print(res)

    """ Test add_uuid function
    """
    add_uuid('apnews_historical')
    # add_uuid('apnews')
    # add_uuid('factcheckafp')
    # add_uuid('factcheckorg')
    # add_uuid('fullfact')
    # add_uuid('metafact')
    # add_uuid('politifact')
    # add_uuid('snopes')