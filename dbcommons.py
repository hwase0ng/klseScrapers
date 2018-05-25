'''
Created on May 25, 2018

@author: hwase0ng
'''
import settings as S
from pymongo.mongo_client import MongoClient
from common import isOpen, getMt4StartDate, loadCfg, loadMap, getDataDir
from utils.fileutils import cd
import subprocess
import os


def exportQuotes(dt=getMt4StartDate()):
    startMongoD()
    cmd = "mongoexport -d %s -c %s --type=csv -q \"{'1':{'$gt':'%s'}}\" "
    cmd += "--fields \"0,1,2,3,4,5,6\" --noHeaderLine --out quotes.csv"
    cmd = cmd % (S.MONGODB, S.MONGOEOD, dt)
    print cmd
    os.system(cmd)


def exportCounters(dt=getMt4StartDate()):
    startMongoD()
    i3map = loadMap("scrapers/i3investor/klse.txt", ",")
    for key in sorted(i3map.iterkeys()):
        filenm = key + '.' + i3map[key] + '.csv'
        cmd = "mongoexport -d %s -c %s --type=csv -q \"{'0':'%s', '1':{'$gt':'%s'}}\" "
        cmd += "--fields \"0,1,2,3,4,5,6\" --noHeaderLine --out %s"
        cmd = cmd % (S.MONGODB, S.MONGOEOD, key, dt, filenm)
        print cmd
        os.system(cmd)


def startMongoD():
    global mongod
    if not isOpen('127.0.0.1', 27017):
        print 'Startind MongoDB ...'
        with cd(S.DATA_DIR):
            mongod = subprocess.Popen(['mongod', '--dbpath',os.path.expanduser(S.DATA_DIR)])


def initKlseDB():
    startMongoD()
    mongo_client = MongoClient()
    db = mongo_client.klsedb
    return db


if __name__ == '__main__':
    loadCfg(S.DATA_DIR)
    with cd(getDataDir(S.DATA_DIR)):
        exportCounters()
        exportQuotes()
    if mongod is not None:
        mongod.terminate()
    pass
