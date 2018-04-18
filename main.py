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
    i3 = scrapeEOD(connectRecentPrices(scode), lastdt)
    if i3 is None:
        print "ERR:No Result"
        return
    for key in sorted(i3.iterkeys()):
        print sname + ',' + key + ',' + ','.join(map(str, unpackEOD(*(i3[key]))))


if __name__ == '__main__':
    '''
    stocks = 'FTFBM100.0200.KL.csv,FTFBMKLCI.0201.KL.csv,FTFBMMES.0202.KL.csv,FTFBMSCAP.0203.KL.csv'
    stocks = 'DAIBOCI.8125.KL.csv,HOHUP.5169.KL.csv,IVORY.5175.KL.csv,N2N.0108.KL.csv,PMBTECH.7172.KL.csv'
    '''
    stocks = 'AAX.5238.KL.csv'

    S.DBG_ALL = False
    S.RESUME_FILE = True
    if not S.RESUME_FILE:
        START_DATE = S.ABS_START
    else:
        START_DATE = '2018-03-01'

    if len(stocks) > 0:
        #  download only selected counters
        if "," in stocks:
            stocklist = stocks.split(",")
        else:
            stocklist = [stocks]
        for stock in stocklist:
            stock_name, stock_code = getStockDetails(stock)
            print stock_name, stock_code
            scrapeI3(stock_name, stock_code, START_DATE)
    pass
