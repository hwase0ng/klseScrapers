'''
Created on Apr 27, 2018

@author: hwase0ng
'''
from utils.dateutils import getToday, getDayOffset
import csv
import json
import sys
import settings as S
import socket
import os
from utils.fileutils import cd


class FifoList:
    def __init__(self):
        self.data = []

    def append(self, data):
        self.data.append(data)

    def pop(self):
        return self.data.pop(0)


class FifoDict:
    def __init__(self):
        self.data = {}
        self.nextin = 0
        self.nextout = 0

    def append(self, data):
        self.nextin += 1
        self.data[self.nextin] = data

    def pop(self):
        self.nextout += 1
        result = self.data[self.nextout]
        del self.data[self.nextout]
        if S.DBG_ALL:
            print 'out:', self.nextout, result
        return result


def loadSetting(c):
    chromedir = c["main"]["CHROME_DIR"]
    if len(chromedir) > 0:
        S.CHROME_DIR = chromedir
    S.BKUP_DIR = c["main"]["BKUP_DIR"]
    S.MT4_DIR = c["main"]["MT4_DIR"]
    try:
        # Allows DATA_DIR to be overwritten here
        datadir = c["main"]["DATA_DIR"]
        if len(datadir) > 0 and datadir.endswith('/'):
            S.DATA_DIR = datadir
    except Exception:
        pass
    S.I3_UID = c["i3"]["UID"]
    S.I3_PWD = c["i3"]["PWD"]
    S.I3_KLSE_URL = c["i3"]["KLSE_URL"]
    S.I3_HOLDINGS = c["i3"]["HOLDINGS"]
    S.I3_WATCHLIST = c["i3"]["WATCHLIST"]
    S.I3_PORTFOLIO_URL = S.I3_KLSE_URL + c["i3"]["PORTFOLIO_URL"]


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


def loadRelatedMap():
    idmap = {}
    others = S.KLSE_RELATED.split(',')
    for item in others:
        other = item.split('.')
        idmap[other[0]] = other[1]
    return idmap


def loadMap(klsemap, sep=","):
    ID_MAPPING = loadRelatedMap()
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


def loadKlseRelated():
    stocklist = {}
    counters = S.KLSE_RELATED.split(',')
    for counter in counters:
        counter = counter.split('.')
        stocklist[counter[0]] = counter[1]
    return stocklist


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

    imap = loadMap(infile, ',')
    for shortname in stocks:
        # stock_code = getStockCode(shortname, infile)
        stock_code = imap[shortname]
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


def getDataDir(datadir):
    if datadir.startswith('/') or datadir.startswith('\\'):
        # Using absolute path; e.g. /d/klse/data
        return datadir
    # Using relative path such as ./data
    cwd = os.getcwd().split(os.sep)
    ind = cwd.index('klseScrapers')
    cwdlen = len(cwd)
    if ind == cwdlen - 1:
        return os.path.join(".", datadir)
    elif ind == cwdlen - 2:
        return os.path.join("..", datadir)

    return os.path.join("..", "..", datadir)


def getI3Dir():
    cwd = os.getcwd().split(os.sep)
    cwdlen = len(cwd)
    if cwd[cwdlen - 1] == 'klseScrapers':
        return 'scrapers/i3investor/'
    elif cwd[cwdlen - 1] == 'i3investor':
        return './'
    return ''


def isOpen(ip, port):
    s = socket.socket(socket. AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((ip, port))
        s.shutdown(2)
        return True
    except Exception:
        return False


def getMt4StartDate():
    mt4Start = getDayOffset(getToday('%Y-%m-%d'), S.MT4_DAYS * -1)
    # Fixed to 1st Jan of year
    mt4Start = mt4Start[:4] + "-01-01"
    return mt4Start


def getCounters(counterlist, klse, pf, wl, verbose=True):
    counters = ''
    if klse:
        slist = loadKlseRelated()
        clist = list(slist.keys())
        counters = ','.join(clist)
    if pf:
        if len(counters) > 0:
            counters += ',' + S.I3_HOLDINGS
        else:
            counters = S.I3_HOLDINGS
    if wl and len(S.I3_WATCHLIST) > 0:
        if len(counters) > 0:
            counters += ',' + S.I3_WATCHLIST
        else:
            counters = S.I3_WATCHLIST

    if len(counterlist) > 0:
        if len(counters) > 0:
            counters += ',' + ','.join(counterlist)
        else:
            counters = ','.join(counterlist)

    if len(counters) > 0:
        return counters.upper()

    if verbose:
        print " INF:Counter is empty"
    return counters


if __name__ == '__main__':
    '''
    line = "3A,0012,THREE-A RESOURCES BHD,507"
    name, var = line.partition(',')[::2]
    if ',' in var:
        var, dummy = var.partition(',')[::2]
    print name
    print var
    '''
    print getDataDir('data/')
    with cd('scrapers'):
        print getDataDir('data/')
    with cd('scrapers/i3'):
        print getDataDir('data/')
    pass
