'''
Created on May 14, 2018

@author: hwase0ng
'''
from utils.fileutils import cd
from common import getDataDir, loadCfg
from pandas.errors import EmptyDataError
from dbcommons import initKlseDB
import pandas as pd
import settings as S
import os
import glob
import json
import pprint

header = ["0-fy", "1-anndate", "2-qr", "3-qnum", "4-revenue", "5-pbt", "6-np", "7-dividend",
                "8-npmargin", "9-roe", "10-eps", "11-adjeps", "12-dps"]


def dbUpsertCounters(db, filenm):
    try:
        data = pd.read_csv(S.DATA_DIR + filenm, header=None)
        data_json = json.loads(data.to_json(orient='records'))
        if data_json is not None and len(data_json) > 0:
            if S.DBG_ALL:
                print data_json[:3]
            for jitem in data_json:
                print "Upserting", jitem['0']
                key = {'0': jitem['0'], '1': jitem['1']}
                db.klsefin.update(key, jitem, upsert=True)
                if S.DBG_ALL:
                    pprint.pprint(db.klsefin.find_one(key))
    except EmptyDataError:
        pass


def dbReplaceCounter(db, filenm):
    if db is None:
        return None
    stk = filenm.split('.')
    print stk[0], stk[1]
    try:
        data = pd.read_csv(filenm, header=None)
        data_json = json.loads(data.to_json(orient='records'))
        if data_json is not None and len(data_json) > 0:
            if S.DBG_ALL:
                print data_json[:3]
            db.klsefin.remove({0: stk[0]})
            db.klsefin.insert(data_json)
    except EmptyDataError:
        pass


def dbNewImport(db, filenm):
    if db is None:
        return None

    print filenm
    try:
        data = pd.read_csv(filenm, header=None)
        data.columns = header
        data_json = json.loads(data.to_json(orient='records'))
        if data_json is not None and len(data_json) > 0:
            if S.DBG_ALL:
                print data_json[:3]
            db.klsefin.insert(data_json)
    except EmptyDataError:
        pass


def processCsv(db, csvfile):
    with cd(getDataDir(S.DATA_DIR, 1)):
        print os.getcwd()
        if len(csvfile) > 0:
            dbReplaceCounter(db, csvfile)
            if S.DBG_ALL:
                pprint.pprint(db.klsefin.find_one({0: '3A', 1: '2018-05-08'}))
        else:
            db.klsefin.drop()
            csvfiles = glob.glob("*.fin")
            for csvf in csvfiles:
                dbNewImport(db, csvf)
            if S.DBG_ALL:
                pprint.pprint(db.klsefin.find_one({'0': '3A', '1': '2018-01-08'}))


if __name__ == '__main__':
    '''
    with cd('../data'):
        exportQuotes('2018-05-10')
    '''
    loadCfg(getDataDir(S.DATA_DIR, 1))
    db = initKlseDB()
    if db is None:
        print "No DB connection"
    else:
        '''
        dbUpsertCounters(db, 'latest.eod')
        '''
        csvfile = ''
        processCsv(db, csvfile)
    pass
