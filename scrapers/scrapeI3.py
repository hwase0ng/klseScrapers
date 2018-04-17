'''
Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import datetime
import requests
from BeautifulSoup import BeautifulSoup


def connectRecentPrices(stkcode):
    if len(stkcode) != 4 or not stkcode.isdigit():
        return

    global soup
    recentPricesUrl = S.I3PRICEURL + stkcode + ".jsp"
    try:
        page = requests.get(recentPricesUrl, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print e
        soup = ''
    return soup


def unpackTD(dt, price_open, price_range, price_close, change, volume):
    '''
    Sample table:
    <tr>
        <td class="left">13/04/2018</td>
        <td class="right">2.92</td>
        <td class="right">2.92 - 2.98</td>
        <td class="right">2.98</td>
        <td class="right" nowrap="nowrap"><span class="up">0.00 (0.00%)</span></td>
        <td class="right">10,500</td>
    </tr>
    '''
    dt = datetime.datetime.strptime(dt, "%d/%m/%Y").strftime('%Y-%m-%d')
    prange = [x.strip() for x in price_range.split('-')]
    return dt, price_open, prange[1], prange[0], price_close, volume


def scrapeEOD(soup):
    if len(soup) <= 0:
        return
    table = soup.find('table', {'class': 'nc'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        eod = [x.text.strip() for x in td]
        if len(eod) == 6:
            dt, price_open, price_high, price_low, price_close, volume = unpackTD(*eod)
            # print type(dt), type(price_open), type(price_high), type(price_low), type(price_close), type(volume)
            if S.DBG_ALL:
                print dt, price_open, price_high, price_low, price_close, volume
        elif len(eod) > 0:
            print "ERR:", eod


if __name__ == '__main__':
    scrapeEOD(connectRecentPrices("5010"))
    pass
