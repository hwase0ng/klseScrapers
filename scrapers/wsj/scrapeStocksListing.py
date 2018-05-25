'''
Created on May 2, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup
from utils.fileutils import getStockCode
from common import loadMap

WSJSTOCKSURL = 'https://quotes.wsj.com/company-list/country/malaysia'


def connectStocksListing(url):
    global soup
    stocksListingUrl = url
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

    stocks = {}
    table = soup.find('table', {'class': 'cl-table'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        if len(td) == 0:
            continue
        # Sample stockLink: <a href="https://quotes.wsj.com/MY/XKLS/SEM">
        stockLink = tr.find('a').get('href')
        stockShortName = stockLink[31:]
        # if any(stockShortName in s for s in klsefilter):
        if stockShortName in klsefilter:
            print "INFO:Ignored counter:", stockShortName
            continue
        stockName = tr.find('span', {'class': 'cl-name'}).text.upper().replace('AMP;', '')
        try:
            newname = wsjmap[stockShortName]
            if S.DBG_ALL:
                print "new name:", stockShortName, newname
            stockShortName = newname
        except KeyError:
            pass
        try:
            stockCode = i3map[stockShortName]
        except KeyError:
            print "INFO:Unmatched stock:", stockShortName + ',', stockName
            continue
        '''
        stockCode = getStockCode(stockShortName, '../i3investor/klse.txt', wsjmap)
        if len(stockCode) == 0:
            print "INFO:Skipped unmatched stock:", stockShortName + ',', stockName
        '''
        tds = [x.text.strip() for x in td]
        xchange = tds[1]
        sector = tds[2]
        if len(sector) == 0:
            sector = '-'
        if S.DBG_ALL:
            print stockShortName, stockCode, stockName, xchange, sector
        stocks[stockShortName] = [stockCode, stockName, xchange, sector]

    nextpg = getNextPage(soup)
    return stocks, nextpg


def unpackListing(scode, sname, xchange, sector):
    return scode, sname, xchange, sector


def getNextPage(soup):
    pages = soup.find("div", "nav-right")
    li = pages.find("li", "next")
    nextpg = li.a.get('href')
    if nextpg == '#':
        return None
    return nextpg


def writeStocksListing(outfile='klse.txt'):
    global wsjmap, i3map, klsefilter
    wsjmap = loadMap("klse.wsj", "=")
    i3map = loadMap("../i3investor/klse.txt", ",")
    with open('../klse.filter') as f:
        klsefilter = f.read().splitlines()
        if S.DBG_ALL:
            print "Filter=", klsefilter
    stocksListing = {}
    nextpg = WSJSTOCKSURL
    while(nextpg is not None):
        listing, nextpg = scrapeStocksListing(connectStocksListing(nextpg))
        stocksListing.update(listing)

    fh = open(outfile, "w")
    for key in sorted(stocksListing.iterkeys()):
        listing = key + ',' + ','.join(map(str, unpackListing(*(stocksListing[key]))))
        if S.DBG_ALL:
            print listing
        fh.write(listing + '\n')
    fh.close()


if __name__ == '__main__':
    S.DBG_ALL = False
    writeStocksListing()
    pass
