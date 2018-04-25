'''
Created on Apr 16, 2018

@author: hwase0ng
'''

import csv
import settings as S
from Utils.fileutils import getStockCode
from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
from scrapers.i3investor.scrapeStocksListing import writeStocksListing
from Utils.dateutils import getLastDate


def scrapeI3eod(sname, scode, lastdt):
    eodStock = scrapeEOD(connectRecentPrices(scode), lastdt)
    if eodStock is None or not eodStock:
        print "ERR:No Result for ", sname, scode
        return None
    i3eod = []
    for key in sorted(eodStock.iterkeys()):
        if key <= lastdt:
            print "Skip downloaded: ", key, lastdt
            continue
        i3eod += [sname + ',' + key + ',' + ','.join(map(str, unpackEOD(*(eodStock[key]))))]
    return i3eod


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


def getStartDate(OUTPUT_FILE):
    if S.RESUME_FILE:
        startdt = getLastDate(OUTPUT_FILE)
        if len(startdt) == 0:
            # File is likely to be empty, hence scrape from beginning
            startdt = S.ABS_START
    else:
        startdt = S.ABS_START
    return startdt


if __name__ == '__main__':
    '''
    stocks = 'AAX,PETRONM'
    '''
    stocks = ''

    S.DBG_ALL = False
    S.RESUME_FILE = True

    klse = "scrapers/i3investor/klse.txt"
    if len(stocks) > 0:
        #  download only selected counters
        stocklist = formStocklist(stocks, klse)
    else:
        # Full download using klse.txt
        writeStocksListing = False
        if writeStocksListing:
            print "Scraping i3 stocks listing ..."
            writeStocksListing(klse)
        stocklist = loadKlseCounters(klse)

    for shortname in sorted(stocklist.iterkeys()):
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            rtn_code = -1
            OUTPUT_FILE = 'data/i3/' + shortname + "." + stock_code + ".csv"
            TMP_FILE = OUTPUT_FILE + 'tmp'
            startdt = getStartDate(OUTPUT_FILE)
            print 'Scraping {0},{1}: lastdt={2}'.format(
                shortname, stock_code, startdt)
            i3eod = scrapeI3eod(shortname, stock_code, startdt)
            if i3eod is None or not i3eod:
                continue
            rtn_code = 0
            f = open(TMP_FILE, "wb")
            for eod in i3eod:
                f.write(eod + '\n')
                if S.DBG_ALL:
                    print eod
            f.close()
        else:
            print "ERR: Not found: ", shortname
            rtn_code = -1

        if rtn_code == 0:
            f = open(OUTPUT_FILE, "ab")
            ftmp = open(TMP_FILE, "r")
            f.write(ftmp.read())
            f.close()
            ftmp.close()
    pass
