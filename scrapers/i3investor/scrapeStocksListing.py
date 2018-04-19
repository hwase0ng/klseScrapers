'''
Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup

I3STOCKSURL = 'https://klse.i3investor.com/jsp/stocks.jsp?g=S&m=int&s='


def connectStocksListing(initial):
    if len(initial) != 1:
        print "ERR:Invalid initial = ", initial
        return

    global soup
    stocksListingUrl = I3STOCKSURL + initial
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
    table = soup.find('table', {'class': 'nc'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        leftTag = tr.findAll('td', {'class': 'left'})
        if leftTag is not None and len(leftTag) > 0:
            stockShortName = leftTag[0].text
            stockName = leftTag[1].text
            stockLink = tr.find('a').get('href')
            # Sample stockLink: /servlets/stk/1234.jsp
            stockCode = stockLink[14:-4]
            td = tr.findAll('td')
            tds = [x.text.strip() for x in td]
            mktCap = int(tds[2].replace(',', ''))
            if S.DBG_ALL:
                print stockShortName, stockName, stockCode, mktCap
            stocks[stockShortName] = [stockCode, stockName, mktCap]
    return stocks


def unpackListing(scode, sname, mktcap):
    return scode, sname, mktcap


if __name__ == '__main__':
    S.DBG_ALL = False
    initials = '0ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    stocksListing = {}
    for initial in list(initials):
        listing = scrapeStocksListing(connectStocksListing(initial))
        stocksListing.update(listing)
    fh = open("klse.txt", "w")
    for key in sorted(stocksListing.iterkeys()):
        stock = key + ',' + ','.join(map(str, unpackListing(*(stocksListing[key]))))
        print stock
        fh.write(stock + '\n')
    fh.close()
    pass
