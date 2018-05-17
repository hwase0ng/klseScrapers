'''
Created on Apr 27, 2018

@author: hwase0ng
'''
from Utils.fileutils import getStockCode
import csv
import settings as S


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


def getDataDir(datadir):
    if datadir.beginswith('/') or datadir.beginswith('\\'):
        # Using absolute path; e.g. /d/klse/data
        return datadir
    # Using relative path such as ./data
    return "../../" + datadir


if __name__ == '__main__':
    line = "3A,0012,THREE-A RESOURCES BHD,507"
    name, var = line.partition(',')[::2]
    if ',' in var:
        var, dummy = var.partition(',')[::2]
    print name
    print var
    pass
