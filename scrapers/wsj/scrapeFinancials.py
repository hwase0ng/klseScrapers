'''
Created on May 8, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup
from common import loadMap, getDataDir, loadCfg, formStocklist
from utils.dateutils import change2KlseDateFmt
from dbcommons import initKlseDB, closeKlseDB

WSJFIN = 'https://quotes.wsj.com/MY/XKLS/?/financials/'
WSJTERM = {'A': 'annual', 'Q': 'quarter'}
WSJRPT = {'I': 'income-statement', 'B': 'balance-sheet', 'C': 'cash-flow'}
WSJCOL = {'I': 'klseis', 'B': 'klsebs', 'C': 'klsecf'}


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


def scrapeFinancials(soup, counter, term, report):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return None

    # klsecol = WSJCOL[report] + term
    table = soup.find('table', {'class': 'cr_dataTable'})
    if table is None:
        print "ERR:", counter, term, report
        return None

    qrs = {}
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        if len(td) == 0:
            for th in table.findAll('th'):
                tht = th.text
                if len(tht) <= 0:
                    continue
                if tht[0].isalpha() or tht[len(tht) - 1].isalpha():
                    # Skip "fiscalYr" class and 5-year trend
                    continue
                if term == 'Q':
                    qrs[counter][change2KlseDateFmt(tht, '%d-%b-%Y')] = True
                else:
                    qrs[counter][tht] = True
            '''
            for qr in qrs.iterkeys():
                if db[klsecol].find({counter: {term: qr}}).count() <= 0:
                    qrs[qr] = False
            print qrs
            '''
            continue
        qrs[counter][]
    return qrs


def unpackListing(scode, sname, xchange, sector):
    return scode, sname, xchange, sector


def writeStocksFinancials(stock, term, report):
    finurl = WSJFIN.replace('?', stock) + WSJTERM[term] + '/' + WSJRPT[report]
    print finurl
    rpt = scrapeFinancials(connectStocksListing(finurl), stock, term, report)

    if rpt is None:
        return

    '''
    stockCode = wsjmap[stock]
    outfile = stock + '.' + stockCode + '.' + term + '.' + report + '.fin'
    print outfile

    fh = open(outfile, "w")
    for key in sorted(rpt.iterkeys()):
        listing = key + ',' + ','.join(map(str, unpackListing(*(rpt[key]))))
        if S.DBG_ALL:
            print listing
        fh.write(listing + '\n')
    fh.close()
    '''


if __name__ == '__main__':
    loadCfg(getDataDir(S.DATA_DIR))
    db = initKlseDB()
    stocks = 'LCTITAN'
    if db is not None:
        if len(stocks) > 0:
            stocklist = formStocklist(stocks, '../i3investor/klse.txt')
        else:
            stocklist = loadMap('../i3investor/klse.txt', ',')

        for stock in sorted(stocklist.iterkeys()):
            for rpt in WSJRPT.iterkeys():
                for term in WSJTERM.iterkeys():
                    writeStocksFinancials(stock, term, rpt)
        closeKlseDB()
    else:
        print "No DB connection"
    pass
