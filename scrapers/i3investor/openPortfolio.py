'''
Created on Jun 9, 2018

@author: hwase0ng
'''
import settings as S
import requests
from lxml import html
from BeautifulSoup import BeautifulSoup
from common import loadCfg, getDataDir

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


if __name__ == '__main__':
    loadCfg(getDataDir(S.DATA_DIR))
    LOGIN_URL = S.I3_KLSE_URL + LOGIN_URL
    REFERER_URL = S.I3_KLSE_URL + REFERER_URL
    compilePortfolioLinks(connectPortfolio("roysten", "way2go"))
