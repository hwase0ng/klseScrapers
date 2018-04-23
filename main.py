'''
Created on Apr 16, 2018

@author: hwase0ng
'''

from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
import settings as S
from Utils.fileutils import getStockCode


def scrapeI3eod(sname, scode, lastdt):
    eodStock = scrapeEOD(connectRecentPrices(scode), lastdt)
    if eodStock is None:
        print "ERR:No Result for ", sname, scode
        return
    i3eod = []
    for key in sorted(eodStock.iterkeys()):
        i3eod += [sname + ',' + key + ',' + ','.join(map(str, unpackEOD(*(eodStock[key]))))]
    return i3eod


if __name__ == '__main__':
    stocks = 'AAX,PETRONM'

    S.DBG_ALL = False
    S.RESUME_FILE = True
    if not S.RESUME_FILE:
        START_DATE = S.ABS_START
    else:
        START_DATE = '2018-04-01'

    if len(stocks) > 0:
        #  download only selected counters
        if "," in stocks:
            stocklist = stocks.split(",")
        else:
            stocklist = [stocks]
        for shortname in stocklist:
            stock_code = getStockCode(shortname, "scrapers/i3investor/klse.txt")
            if len(stock_code) > 0:
                print shortname, stock_code
                i3eod = scrapeI3eod(shortname, stock_code, START_DATE)
                for eod in i3eod:
                    print eod
            else:
                print "ERR: Not found: ", shortname
    pass
