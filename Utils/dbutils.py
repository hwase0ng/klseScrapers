'''
Created on May 14, 2018

@author: hwase0ng
'''

from pymongo import MongoClient
from Utils.fileutils import cd
from pandas._libs.parsers import EmptyDataError
import pandas as pd
import settings as S
import os
import glob
import json
import pprint

header = ["0-Code", "1-Date", "2-Open", "3-High", "4-Low", "5-Close", "6-Volume"]


def importCsv(filenm, db):
    if db is None:
        print "ERR: Missing DB"
        return

    print filenm
    try:
        data = pd.read_csv(filenm, header=None)
        '''
        data.columns = header
        '''
        data_json = json.loads(data.to_json(orient='records'))
        if data_json is not None and len(data_json) > 0:
            if S.DBG_ALL:
                print data_json[:3]
            # db.klsedb.remove()
            db.klsedb.insert(data_json)
    except EmptyDataError:
        pass


def processCsv():
    with cd(S.DATA_DIR):
        print os.getcwd()
        csvfiles = glob.glob("*.csv")
        for csvf in csvfiles:
            importCsv(csvf, db)


if __name__ == '__main__':
    mongo_client = MongoClient()
    db = mongo_client.klsedb
    csvfile = '3A.0012.csv'
    if len(csvfile) > 0:
        pprint.pprint(db.klsedb.find_one({'0': 'FTFBMKLCI', '1': '2018-05-07'}))
        pprint.pprint(db.klsedb.find_one({'0': 'ZHULIAN', '1': '2018-05-02'}))
        pprint.pprint(db.klsedb.find_one({'0': 'USDMYR'}))
        pprint.pprint(db.klsedb.find_one())
        with cd(S.DATA_DIR):
            importCsv(csvfile)
        pprint.pprint(db.klsedb.find_one())
        pprint.pprint(db.klsedb.find_one({'0': '3A', '1-Date': '2018-05-08'}))
    else:
        db.klsedb.drop()
        processCsv()
        pprint.pprint(db.klsedb.find_one())
        pprint.pprint(db.klsedb.find_one({'0': '3A', '1': '2018-01-08'}))
    pass
