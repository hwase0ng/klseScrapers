'''
Created on Apr 27, 2018

@author: hwase0ng
'''
from Utils.fileutils import getStockCode
import csv
import json
import sys
import settings as S
import os


def loadSetting(c):
    S.BKUP_DIR = c["main"]["BKUP_DIR"]
    S.MT4_DIR = c["main"]["MT4_DIR"]
    # Allows DATA_DIR to be overwritten here
    try:
        datadir = c["main"]["DATA_DIR"]
        if len(datadir) > 0 and datadir.endswith('/'):
            S.DATA_DIR = datadir
    except Exception:
        pass


def loadCfg(datadir):
    try:
        # Refers backup drive instead of DATA_DIR which is in network share
        with open(datadir + 'config.json') as json_data_file:
            cfg = json.load(json_data_file)
            loadSetting(cfg)
            return cfg
    except EnvironmentError:
        print "Missing config.json file:", datadir
        sys.exit(1)


def loadMap(klsemap, sep=","):
    ID_MAPPING = {}
    try:
        with open(klsemap) as idmap:
            for line in idmap:
                name, var = line.partition(sep)[::2]
                if sep in var:
                    # input: "3A,0012,THREE-A RESOURCES BHD,507"
                    # drops ",THREE-A RESOURCES BHD,507"
                    var, dummy = var.partition(sep)[::2]
                ID_MAPPING[name.strip()] = var.strip()
            if S.DBG_ALL:
                print dict(ID_MAPPING.items()[0:3])
    except EnvironmentError:
        print "Invalid map file:", klsemap
    except KeyError:
        print "loadIdMap KeyError:", name
    return ID_MAPPING


def loadKlseCounters(infile):
    stocklist = {}
    with open(infile) as f:
        reader = csv.reader(f)
        slist = list(reader)
        if S.DBG_ALL:
            print slist[:3]
        for counter in slist[:]:
            if S.DBG_ALL:
                print "\t", counter[0]
            stocklist[counter[0]] = counter[1]
    return stocklist


def formStocklist(stocks, infile):
    stocklist = {}
    if "," in stocks:
        stocks = stocks.split(",")
    else:
        stocks = [stocks]

    for shortname in stocks:
        stock_code = getStockCode(shortname, infile)
        stocklist[shortname] = stock_code

    return stocklist


def appendCsv(rtn_code, OUTPUT_FILE):
    if rtn_code != 0:
        return

    TMP_FILE = OUTPUT_FILE + 'tmp'

    f = open(OUTPUT_FILE, "ab")
    ftmp = open(TMP_FILE, "r")
    f.write(ftmp.read())
    f.close()
    ftmp.close()


def getDataDir(datadir, lvl=2):
    if datadir.startswith('/') or datadir.startswith('\\'):
        # Using absolute path; e.g. /d/klse/data
        return datadir
    # Using relative path such as ./data
    if lvl == 1:
        return "../" + datadir

    return "../../" + datadir


def exportQuotes(dt):
    cmd = "mongoexport -d %s -c %s --type=csv -q \"{'1':{'$gt':'%s'}}\" "
    cmd += "--fields \"0,1,2,3,4,5,6\" --noHeaderLine --out quotes.csv"
    cmd = cmd % (S.MONGODB, S.MONGOEOD, dt)
    print cmd
    os.system(cmd)


if __name__ == '__main__':
    line = "3A,0012,THREE-A RESOURCES BHD,507"
    name, var = line.partition(',')[::2]
    if ',' in var:
        var, dummy = var.partition(',')[::2]
    print name
    print var
    pass
