'''
Created on Apr 27, 2018

@author: hwase0ng
'''
from utils.dateutils import getToday, getDayOffset, generate_dates
from utils.fileutils import wc_line_count
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
    S.I3_MVP = c["i3"]["MVP"]
    S.I3_MOMENTUM = c["i3"]["MOMENTUM"]
    S.I3_DIVIDEND = c["i3"]["DIVIDEND"]
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
        try:
            if "." in shortname:
                # KLSE related from settings.py
                names = shortname.split('.')
                stocklist[names[0]] = names[1]
            else:
                stock_code = imap[shortname]
                stocklist[shortname] = stock_code
        except KeyError:
            print "Applied hack for missing entry:", shortname
            # Hack to bypass restriction on KLSE counters
            stocklist[shortname] = "0"

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


def retrieveCounters(clist):
    if clist is None or not len(clist):
        return ''
    valids = "dhkmwM"
    if not any((c in clist) for c in valids):
        print clist, "is not one of", valids
        print "defaulting to m for MVP"
        clist = "m"
    counters = []
    if 'd' in clist:
        counters += S.I3_DIVIDEND.split(',')
    if 'h' in clist:
        counters += S.I3_HOLDINGS.split(',')
    if 'k' in clist:
        counters += S.KLSE_RELATED.split(',')
    if 'm' in clist:
        counters += S.I3_MVP.split(',')
    if 'w' in clist:
        counters += S.I3_WATCHLIST.split(',')
    if 'M' in clist:
        counters += S.I3_MOMENTUM.split(',')
    return ",".join(counters)


# obsolete, use retrieveCounters instead
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


def getSkipRows(csvfl, skipdays=S.MVP_DAYS):
    row_count = wc_line_count(csvfl)
    if row_count < 0:
        return -1, -1  # File not found
    if row_count < skipdays:
        skiprow = 0
    else:
        skiprow = row_count - skipdays
    return skiprow, row_count


def match_approximate(a, b, approx):
    c, d = [], []
    bEnd = False
    bfifo = FifoDict()
    for i in b:
        bfifo.append(i)
    y = 0
    for x in a:
        if bEnd:
            continue
        while True:
            if y == 0 or x - y > approx:
                try:
                    y = bfifo.pop()
                except KeyError:
                    bEnd = True
                    break
            if abs(x - y) <= approx:
                c.append(x)
                d.append(y)
                break
            if y > x:
                break
    return [c, d]


# Credit to the following implementation goes to Matt Messersmith:
#   https://stackoverflow.com/questions/53022670/how-to-compare-2-sorted-numeric-lists-in-python-where-each-corresponding-element
def match_approximate2(a, b, approx, invert=False, vector=None, cmpv=None):
    a_ind, b_ind = 0, 0
    resulta, resultb = [], []
    while a_ind < len(a) and b_ind < len(b):
        aItem, bItem = a[a_ind], b[b_ind]
        if abs(aItem - bItem) <= approx:
            if not invert:
                resulta.append(aItem)
                resultb.append(bItem)
            else:
                yrange = max(vector) - min(vector)
                ydist = abs(vector[aItem] - vector[bItem])
                if ydist > yrange / 10:
                    resulta.append(aItem)
                    resultb.append(bItem)
                else:
                    if S.DBG_ALL:
                        print "Invert filters:", cmpv, aItem, bItem, \
                            vector[aItem], vector[bItem], yrange, ydist
            a_ind += 1
            b_ind += 1
            continue
        if aItem < bItem:
            if invert:
                resulta.append(aItem)
            a_ind += 1
        else:
            if invert:
                resultb.append(bItem)
            b_ind += 1

    '''
    def match_last_element(a, a_ind, last_elt_of_b, resulta, resultb):
        while a_ind != len(a):
            if abs(a[a_ind] - last_elt_of_b) <= approx:
                resulta.append(a[a_ind])
                resultb.append(b[b_ind])
                a_ind += 1
            else:
                break

    if a_ind != len(a):
        match_last_element(a, a_ind, b[-1], resulta, resultb)
    else:
        match_last_element(b, b_ind, a[-1], resulta, resultb)
    '''
    if invert:
        while a_ind != len(a):
            resulta.append(a[a_ind])
            a_ind += 1
        while b_ind != len(b):
            resulta.append(b[b_ind])
            b_ind += 1

    return [resulta, resultb]


def combineList(listoflists):
    xpositive, xnegative, ypositive, ynegative = \
        listoflists[0], listoflists[1], listoflists[2], listoflists[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    datelist, ylist = sorted(xpositive + xnegative), []
    for dt in datelist:
        try:
            pos = xpositive.index(dt)
            ylist.append(ypositive[pos])
        except ValueError:
            pos = xnegative.index(dt)
            ylist.append(ynegative[pos])
    return ylist


def matchdates(list1, list2, approx=31):
    matchdict = {}
    for i, val in enumerate(list1):
        matchtolerance = 0
        try:
            j = list2.index(val)
        except ValueError:
            j = -1
            if approx:
                dtstart = getDayOffset(val, approx * -1)
                dtend = getDayOffset(val, approx)
                for newval in list2:
                    if newval < dtstart:
                        continue
                    if newval > dtend:
                        break
                    matchtolerance = 1
                    j = list2.index(newval)
                    break
        matchval = 0 if j < 0 else j - len(list2)
        matchdict[i - len(list1)] = [matchval, matchtolerance, val]
    return matchdict


if __name__ == '__main__':
    '''
    line = "3A,0012,THREE-A RESOURCES BHD,507"
    name, var = line.partition(',')[::2]
    if ',' in var:
        var, dummy = var.partition(',')[::2]
    print name
    print var
    print getDataDir('data/')
    with cd('scrapers'):
        print getDataDir('data/')
    with cd('scrapers/i3'):
        print getDataDir('data/')
    '''
    '''
    lists = [['2018-03-31', '2018-04-05'], ['2018-01-05', '2018-04-01'], [1.2, 1.5], [1.1, 2.0]]
    print combineList(lists)
    lists = [['2018-03-01', '2018-03-05', '2018-04-30'], ['2018-01-05', '2018-04-01'], [1.2, 1.5, 1.7], [1.1, 2.0]]
    print combineList(lists)
    lists = [['2018-03-31', '2018-04-05'], ['2018-04-01'], [1.2, 1.5], [2.0]]
    print combineList(lists)
    '''
    mdatesp = ['2013-03-31', '2013-10-31', '2013-12-31', '2014-03-03']
    pdatesp = ['2013-01-31', '2013-03-31', '2013-06-30', '2013-09-30', '2013-12-31']
    mdatesn = ['2013-07-31', '2013-11-30', '2014-02-28']
    pdatesn = ['2013-02-28', '2013-04-30', '2013-07-31', '2013-11-30', '2014-02-28']
    print matchdates(mdatesn, pdatesn)
    m = matchdates(mdatesp, pdatesp)
    print m
    for k, v in enumerate(sorted(m, reverse=True)):
        print k, v, m[v]
