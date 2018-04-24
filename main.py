'''
Created on Apr 16, 2018

@author: hwase0ng
'''

import csv
import settings as S
from Utils.fileutils import getStockCode
from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
from scrapers.i3investor.scrapeStocksListing import writeStocksListing


def scrapeI3eod(sname, scode, lastdt):
    eodStock = scrapeEOD(connectRecentPrices(scode), lastdt)
    if eodStock is None:
        print "ERR:No Result for ", sname, scode
        return
    i3eod = []
    for key in sorted(eodStock.iterkeys()):
        i3eod += [sname + ',' + key + ',' + ','.join(map(str, unpackEOD(*(eodStock[key]))))]
    return i3eod


def i3LoadKlse():
    stocklist = {}
    with open('scrapers/i3investor/klse.txt') as f:
        reader = csv.reader(f)
        slist = list(reader)
        if S.DBG_ALL:
            print slist[:3]
        for counter in slist[:]:
            if S.DBG_ALL:
                print "\t", counter[0]
            stocklist[counter[0]] = counter[1]
    return stocklist


if __name__ == '__main__':
    stocks = 'AAX,PETRONM'
    stocks = ''

    S.DBG_ALL = False
    S.RESUME_FILE = True
    if not S.RESUME_FILE:
        START_DATE = S.ABS_START
    else:
        START_DATE = '2018-04-01'

    stocklist = {}
    if len(stocks) > 0:
        #  download only selected counters
        if "," in stocks:
            stocks = stocks.split(",")
        else:
            stocks = [stocks]

        for shortname in stocks:
            stock_code = getStockCode(shortname, "scrapers/i3investor/klse.txt")
            stocklist[shortname] = stock_code
    else:
        # Full download using klse.txt
        writeStocksListing("scraper/i3investor/klse.txt")
        stocklist = i3LoadKlse()

    for shortname in sorted(stocklist.iterkeys()):
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            print shortname, stock_code
            i3eod = scrapeI3eod(shortname, stock_code, START_DATE)
            for eod in i3eod:
                print eod
        else:
            print "ERR: Not found: ", shortname
    pass
