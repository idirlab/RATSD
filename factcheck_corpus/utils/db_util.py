# -*- coding: utf-8 -*-
# psycopy2 is PostgreSQL database adapter for the Python
# -*- coding: utf-8 -*-
import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

import psycopg2
import psycopg2.extras as extras
import mysql.connector
import pandas as pd
from argparse import ArgumentParser
from utils.crawler_util import CSV_HEADER


def create_connection(database='postgresql'):
    # connect to postgres on server 11
    if database=='postgresql': 
        connection = psycopg2.connect(user = "yours",
                                      password = "yours",
                                      host="127.0.0.1",
                                      database = "fact_checks")
        cursor = connection.cursor()
    # connect to mysql on server 4
    elif database=='mysql': 
        connection = mysql.connector.connect(user = "yours",
                                             password = "yours",
                                             host="localhost",
                                             database = "fact_checks")
        cursor = connection.cursor()
    return connection

def insert_factcheck(conn, df, src=''):
    table = 'factchecks'
    tuples = [tuple(x) for x in df.to_numpy()]
    df.columns = ['publisher', 'claimReviewed', 'fact', 'review', 'verdict', \
                  'author', 'claimPublishedDate', 'factcheckPublishedDate', 'thumbnailUrl', 'url', 'tags']
    cols = ','.join(list(df.columns))
    query  = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_values(cursor, query, tuples)
        conn.commit()
        print("{} successfully insert {} pieces of factchecks".format(src, len(tuples)))
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    cursor.close()
    
        
def create_table(conn, database="postgresql"):
    command = """
                CREATE TABLE factchecks (
                    publisher TEXT,   
                    claimReviewed TEXT, 
                    fact TEXT, 
                    review TEXT, 
                    verdict TEXT, 
                    author TEXT, 
                    claimPublishedDate TEXT, 
                    factcheckPublisheddate TEXT, 
                    thumbnailUrl TEXT, 
                    url TEXT,
                    tags TEXT)
              """
    if database=='postgresql':
        try:
            cur = conn.cursor()
            cur.execute(command)
            cur.close()
            conn.commit()
            print('Successfully create table named factchecks')
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
    else: 
        # TODO: change the syntax for mysql
        try:
            cur = conn.cursor()
            cur.execute(command)
            cur.close()
            conn.commit()
            print('Successfully create table named factchecks')
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            
            
def delete_table(conn):
    command = """
                DROP TABLE factchecks CASCADE;
              """
    try:
        cur = conn.cursor()
        cur.execute(command)
        cur.close()
        conn.commit()
        print('Successfully delete table')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
def insert_hisotorical_data(conn, src):
    df = pd.read_csv('./dataset/{}.csv'.format(src), on_bad_lines='warn')
    insert_factcheck(conn, df)
    print('Successfully insert {} pieces of {} historicial data'.format(len(df), src))
    

if __name__ == "__main__":
    conn = create_connection()
    parser = ArgumentParser()
    parser.add_argument("-c", "--is_create_table", type=int,
                        help="create the default table")
    parser.add_argument("-d", "--is_delete_table", type=int,
                        help="create the default table")
    parser.add_argument("-i", "--is_insert_data", type=int,
                        help="insert data into tables")
    args = parser.parse_args()
    # # Test: insert table
    # # sample_df = pd.read_csv('./dataset/politifact.csv', header=CSV_HEADER).head(5)
    # # print(sample_df.head())
    # # sample_df.columns = ['author', 'claim', 'fact_date', 'factcheck_date', 'verdict']
    # # print(sample_df.head())
    # # insert_factcheck(conn, sample_df, 'test')

    # Test: create table
    if args.is_create_table:
        create_table(conn)
    
    # Test: delete table
    if args.is_delete_table:
        delete_table(conn)
    
    # Test: insert historical data
    if args.is_insert_data:
        insert_hisotorical_data(conn, 'apnews')
        insert_hisotorical_data(conn, 'factcheckafp')
        insert_hisotorical_data(conn, 'factcheckorg')
        insert_hisotorical_data(conn, 'fullfact')
        insert_hisotorical_data(conn, 'metafact')
        insert_hisotorical_data(conn, 'politifact')
        insert_hisotorical_data(conn, 'snopes')
    
    conn.close()