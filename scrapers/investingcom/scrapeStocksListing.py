'''
Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup
from utils.fileutils import getStockShortNameById, getStockCode

# EQUITIESURL = "https://www.investing.com/equities/malaysia"
EQUITIESURL = "https://www.investing.com/equities/StocksFilter?noconstruct=1&smlID=618&sid=&tabletype=price&index_id=all"


def connectStocksListing():
    global soup
    stocksListingUrl = EQUITIESURL
    try:
        page = requests.get(stocksListingUrl, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
        soup = ''
    return soup


def scrapeStocksListing(soup):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return

    stocks = []
    table = soup.find('table', {'id': 'cross_rate_markets_stocks_1'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        if len(td) > 0:
            if S.DBG_ALL:
                for tag in td:
                    print type(tr), type(td)
                    print tag.contents
            stockName = tr.find('a').get('title').upper()
            stockId = td[1].contents[1]['data-id']
            stockShortName = getStockShortNameById(stockId, "klse.idmap").upper()
            if len(stockShortName) > 0:
                stockCode = getStockCode(stockShortName, '../i3investor/klse.txt')
            else:
                stockCode = ''
            if S.DBG_ALL:
                print stockShortName, stockCode, stockName, stockId
            stocks.append([stockShortName, stockCode, stockName, stockId])
    return stocks


def unpackListing(sname, scode, lname, currid):
    return sname, scode, lname, currid


def writeStocksListing(outfile='klse.txt'):
    listing = scrapeStocksListing(connectStocksListing())
    if listing is not None:
        fh = open(outfile, "w")
        for data in sorted(listing):
            stock = ','.join(map(str, unpackListing(*(data))))
            if S.DBG_ALL:
                print "writeStocksListing:", stock
            fh.write(stock + '\n')
        fh.close()


if __name__ == '__main__':
    S.DBG_ALL = False
    writeStocksListing()
    pass
