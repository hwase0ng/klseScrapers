'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -d,--date         Check processing mode

Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import requests
from BeautifulSoup import BeautifulSoup
from common import loadCfg
from docopt import docopt
from utils.dateutils import change2KlseDateFmt

I3PRICEURL = 'https://klse.i3investor.com/servlets/stk/rec/'


def connectRecentPrices(stkcode):
    if len(stkcode) < 4:
        print "ERR:Invalid stock code = ", stkcode
        return

    global soup
    recentPricesUrl = I3PRICEURL + stkcode + ".jsp"
    try:
        page = requests.get(recentPricesUrl, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
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
    # dt = datetime.datetime.strptime(dt, "%d/%m/%Y").strftime('%Y-%m-%d')
    dt = change2KlseDateFmt(dt, "%d/%m/%Y")
    prange = [x.strip() for x in price_range.split('-')]
    return dt, price_open, prange[1], prange[0], price_close, volume


def scrapeRecentEOD(soup, sname, scode, lastdt, checkLastTrading=False):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result for {0},{1}'.format(sname, scode)
        return None
    i3eod = {}
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        print 'INFO: No recent price is available for {0},{1}'.format(sname, scode)
        return None
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        eod = [x.text.strip() for x in td]
        if len(eod) == 6:
            dt, price_open, price_high, price_low, price_close, volume = unpackTD(*eod)
            if checkLastTrading:
                # a quick hack for now
                return dt, price_open, price_close, volume
            if dt == lastdt and int(volume.replace(',', '')) > 0:
                i3eod[dt] = [price_open, price_high, price_low, price_close, volume]
                break
            else:
                continue
            # print type(dt), type(price_open), type(price_high), type(price_low), type(price_close), type(volume)
            if S.DBG_ALL:
                print dt, price_open, price_high, price_low, price_close, volume
        elif len(eod) > 0:
            print "ERR:", eod
    return i3eod


def unpackEOD(popen, phigh, plow, pclose, pvol):
    return "{:.4f}".format(float(popen)), "{:.4f}".format(float(phigh)), \
        "{:.4f}".format(float(plow)), "{:.4f}".format(float(pclose)), \
        int(pvol.replace(',', ''))


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    S.DBG_ALL = False
    if args['--date']:
        lastdate = args['--date']
    else:
        lastdate = "2019-04-18"
    i3 = scrapeRecentEOD(connectRecentPrices("6998"), "test", 6998, lastdate)
    if i3 is not None:
        for key in sorted(i3.iterkeys()):
            print key + ',' + ','.join(map(str, unpackEOD(*(i3[key]))))
    pass
