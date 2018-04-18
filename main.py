'''
Created on Apr 16, 2018

@author: hwase0ng
'''

from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
import settings as S


def getStockDetails(stock):
    sdata = stock.split(".")
    stock_name = sdata[0]
    stock_code = sdata[1] + "." + sdata[2]
    return stock_name, stock_code


def scrapeI3(sname, scode, lastdt):
    eodStock = scrapeEOD(connectRecentPrices(scode), lastdt)
    if eodStock is None:
        print "ERR:No Result"
        return
    for key in sorted(eodStock.iterkeys()):
        print sname + ',' + key + ',' + ','.join(map(str, unpackEOD(*(eodStock[key]))))
    return eodStock


def find(substr, infile):
    lines = filter(lambda x: substr in x, open(infile))
    return lines


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
        for stock_name in stocklist:
            listing = find(stock_name, "scrapers/i3investor/klse.txt")
            if len(listing) > 0:
                stock = listing[0].split(',')
                stock_code = stock[1]
                print stock_name, stock_code
                scrapeI3(stock_name, stock_code, START_DATE)
            else:
                print "ERR: Not found: ", stock_name
    pass
