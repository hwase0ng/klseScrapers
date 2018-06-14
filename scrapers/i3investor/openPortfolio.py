'''
Usage: openPortfolio [-pwish] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -p,--portfolio    Select portfolio from config.json
    -w,--watchlist    Select watchlist from config.json
    -i,--i3           Open in i3investor.com
    -s,--sb           Open in my.stockbit.com
    -h,--help         This page

This app opens counter[s] in browser, if counter not specified, then refer config.json
'''
import settings as S
import requests
from lxml import html
from BeautifulSoup import BeautifulSoup
from common import loadCfg, getDataDir, formStocklist, getCounters
import webbrowser
from docopt import docopt

LOGIN_URL = "/loginservlet.jsp"
REFERER_URL = "/jsp/admin/login.jsp"


def connectPortfolio(uid, pwd):

    payload = {
        "uid": uid,
        "pwd": pwd,
    }

    try:
        with requests.session() as session:
            result = session.post(LOGIN_URL, data=payload, headers=S.HEADERS)
            print result.text
            assert(result.status_code == 200)
            page = session.get(S.I3_PORTFOLIO_URL, headers=S.HEADERS)
            assert(page.status_code == 200)
            html = page.content
            soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
        soup = ''
    return soup


def compilePortfolioLinks(soup):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return None
    divclass = soup.find('div', {'class': 'dataTables_wrapper'})
    if divclass is None:
        print 'ERR: no result for div'
        return None
    table = divclass.find('table', {'class': 'nc dataTable', 'id': 'pfenttable'})
    if table is None:
        print 'ERR: no result for table'
        return None

    global chartlink
    chartlink = []
    for tr in table.findAll('tr'):
        leftTag = tr.findAll('td', {'class': 'left'})
        if leftTag is None or len(leftTag) == 0:
            continue
        stockShortName = leftTag[0].text.replace(';', '')
        stockLink = tr.find('a').get('href')
        # Sample stockLink: /servlets/stk/1234.jsp
        stockCode = stockLink[14:-4]
        chartlink += [leftTag.find('a').get('href')]
        print stockShortName, stockCode, stockLink, chartlink


def openPortfolioLinks(chartlinks):
    new = 1
    if len(S.CHROME_DIR) > 0:
        browser = webbrowser.get(S.CHROME_DIR)
    for url in chartlinks:
        if S.DBG_ALL:
            print url
        if len(S.CHROME_DIR) > 0:
            browser.open(url, new=new, autoraise=True)
        else:
            webbrowser.open(url, new=new, autoraise=True)
        new = 2


def compileLinks(i3, sb, counters):
    i3chartlinks = []
    sbchartlinks = []
    SB_URL = 'https://my.stockbit.com/#/symbol/KLSE-'
    stocklist = formStocklist(counters, './klse.txt')
    for key in stocklist.iterkeys():
        if i3:
            i3chartlinks.append(S.I3_KLSE_URL + '/servlets/stk/chart/' +
                                stocklist[key] + '.jsp')
        if sb:
            sbchartlinks.append(SB_URL + key + '/chartbit')

    return i3chartlinks, sbchartlinks


if __name__ == '__main__':
    args = docopt(__doc__)
    loadCfg(getDataDir(S.DATA_DIR))
    counters = getCounters(args['COUNTER'], args['--portfolio'],
                           args['--watchlist'])
    if len(counters) > 0:
        i3chartlinks, sbchartlinks = compileLinks(args['--i3'],
                                                  args['--sb'], counters)
    else:
        LOGIN_URL = S.I3_KLSE_URL + LOGIN_URL
        REFERER_URL = S.I3_KLSE_URL + REFERER_URL
        compilePortfolioLinks(connectPortfolio(S.I3_UID, S.I3_PWD))

    if i3chartlinks is not None and len(i3chartlinks) > 0:
        openPortfolioLinks(i3chartlinks)
    if sbchartlinks is not None and len(sbchartlinks) > 0:
        openPortfolioLinks(sbchartlinks)
