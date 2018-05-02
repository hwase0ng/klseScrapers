'''
Created on May 2, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup
from Utils.dateutils import getToday

WSJSTOCKSURL = 'https://quotes.wsj.com/company-list/country/malaysia'


def connectStocksListing():
    global soup
    stocksListingUrl = WSJSTOCKSURL
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
        # Sample stockLink: <a href="https://quotes.wsj.com/MY/XKLS/SEM">
        stockLink = tr.find('a').get('href')
        stockShortName = stockLink[31:]
        td = tr.findAll('td')
        stockName = td[0].contents[1]['class'].text.upper
        tds = [x.text.strip() for x in td]
        xchange = tds[1]
        sector = tds[2]
        if S.DBG_ALL:
            print stockShortName, stockName, xchange, sector
        stocks[stockShortName] = [stockCode, stockName, xchange, sector]
    return stocks


def unpackListing(scode, sname, xchange, sector):
    return scode, sname, xchange, sector


def writeStocksListing(outfile='klse.txt'):
    stocksListing = scrapeStocksListing(connectStocksListing())

    fh = open(outfile, "w")
    for key in sorted(stocksListing.iterkeys()):
        stock = key + ',' + ','.join(map(str, unpackListing(*(stocksListing[key]))))
        if S.DBG_ALL:
            print stock
        fh.write(stock + '\n')
    fh.close()


def unpackTD(shortname, longname, cap, price_open, price_range, price_close, change, cpc, volume):
    '''
    Sample table:
    <tr role="row" class="odd"> <td class="left sorting_1"><a href="/servlets/stk/7054.jsp">AASIA</a>
        </td> <td class="left" nowrap=""><a href="/servlets/stk/7054.jsp">ASTRAL ASIA BHD</a></td>
        <td class="right">125</td>
        <td class="right">0.19</td>
        <td class="right">0.19</td>
        <td class="right" nowrap="nowrap"><span class="up">0.00</span></td>
        <td class="right">10,000</td>
    </tr>
    '''
    prange = [x.strip() for x in price_range.split('-')]
    return shortname, price_open, prange[1], prange[0], price_close, volume


def scrapeLatestPrice(soup):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return None
    i3eod = {}
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        print 'ERR: table is empty'
        return None
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        eod = [x.text.strip() for x in td]
        if len(eod) == 9:
            shortname, price_open, price_high, price_low, price_close, volume = unpackTD(*eod)
            if int(volume.replace(',', '')) > 0:
                # <a href="/servlets/stk/7054.jsp">AASIA</a>
                stockLink = tr.find('a').get('href')
                stkcd = stockLink[14:-4]
                i3eod[shortname + '.' + stkcd] = [
                    price_open, price_high, price_low, price_close, volume]
            else:
                continue
            # print type(dt), type(price_open), type(price_high), type(price_low), type(price_close), type(volume)
            if S.DBG_ALL:
                print shortname, stkcd, price_open, price_high, price_low, price_close, volume
        elif len(eod) > 0:
            print "ERR:Unknown len:", eod
    return i3eod


def unpackEOD(popen, phigh, plow, pclose, pvol):
    return "{:.4f}".format(float(popen)), "{:.4f}".format(float(phigh)), \
        "{:.4f}".format(float(plow)), "{:.4f}".format(float(pclose)), \
        int(pvol.replace(',', ''))


def writeLatestPrice(writeEOD=False, workdir='.'):
    initials = '0ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    stocksListing = {}
    for initial in list(initials):
        eod = scrapeLatestPrice(connectStocksListing(initial))
        stocksListing.update(eod)

    for key in sorted(stocksListing.iterkeys()):
        stk = key.split('.')
        shortname = stk[0]
        stockCode = stk[1]
        outfile = workdir + shortname + '.' + stockCode + '.csv'
        today = getToday('%Y-%m-%d')
        eod = shortname + ',' + today + ',' + ','.join(
            map(str, unpackEOD(*(stocksListing[key]))))
        if writeEOD:
            fh = open(outfile, "ab")
            fh.write(eod + '\n')
            fh.close()
        else:
            print eod


if __name__ == '__main__':
    S.DBG_ALL = False
    writeStocksListing()
    writeLatestPrice(False, '../../data/i3/')
    pass
