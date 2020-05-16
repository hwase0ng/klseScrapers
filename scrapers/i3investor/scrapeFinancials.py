'''
Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import datetime
import requests
from BeautifulSoup import BeautifulSoup
from datetime import date
from dateutil.relativedelta import relativedelta
from common import formStocklist, loadKlseCounters, getDataDir

I3FINURL = 'https://klse.i3investor.com/servlets/stk/fin/'
I3LATESTFINURL = 'http://klse.i3investor.com/financial/quarter/latest.jsp'


def connect_stk_fin(stk_code):
    if len(stk_code) == 0:
        stkFinUrl = I3LATESTFINURL
    elif len(stk_code) != 4:
        print "ERR:Invalid stkcode = ", stk_code
        return
    else:
        stkFinUrl = I3FINURL + stk_code + ".jsp"

    if S.DBG_ALL:
        print stkFinUrl
    try:
        page = requests.get(stkFinUrl, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
        soup = ''
    return soup


def scrape_latest_fin(soup, last_scan):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return

    stkList = {}
    table = soup.find('table', {'class': 'nc'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        leftTag = tr.findAll('td', {'class': 'left'})
        if leftTag is not None and len(leftTag) > 0:
            anndate = datetime.datetime.strptime(leftTag[1].text,
                                                 "%d-%b-%Y").strftime('%Y-%m-%d')
            if anndate > last_scan:
                stockShortName = leftTag[0].text
                stockLink = tr.find('a').get('href')
                # Sample stockLink: /servlets/stk/fin/1234.jsp
                stockCode = stockLink[18:-4]
                stkList[stockShortName] = stockCode
            else:
                break
    return stkList


def unpack_td(td):
    """
    Sample table:
    <tr class="totals"><td colspan="38"><b>Financial Year: 30-Jun-2018</b></td></tr>
    <tr role="row" class="odd">
        <td class="left sorting_1" valign="top" nowrap="nowrap"> 14-Feb-2018 </td>
        <td class="left" valign="top" nowrap="nowrap"> 31-Dec-2017 </td>
        <td class="right" valign="top" nowrap="nowrap"> 335,914 </td>
        <td class="right" valign="top" nowrap="nowrap"> 57,634 </td>
        ...
        <td class="left" valign="top" nowrap="nowrap" style="font-size: 10px; ">
           <a href="/financial/YoY/quarter/7106/31-Dec-2017_2828644263.jsp" target="_blank">
           <span class="up"> <img class="sp arrow_up" src="//cdn1.i3investor.com/cm/icon/trans16.gif">
           &nbsp; 59.07% </span> </a> </td>
    </tr>
    """
    fy = td[0]
    anndate = td[1]
    quarter = td[2]
    qnum = td[3]
    revenue = td[4]
    pbt = td[5]
    np = td[6]
    dividend = td[8]
    npmargin = td[11]
    roe = td[12]
    eps = td[16]
    adjeps = td[17]
    dps = td[18]
    try:
        fy = datetime.datetime.strptime(fy, "%d-%b-%Y").strftime('%Y-%m-%d')
        quarter = datetime.datetime.strptime(quarter, "%d-%b-%Y").strftime('%Y-%m-%d')
        if len(anndate) == 0:
            year = int(quarter[0:4])
            month = int(quarter[5:7])
            day = int(quarter[8:10])
            anndate = date(year, month, day) + relativedelta(months=+2)
            anndate = anndate.strftime('%Y-%m-%d')
        else:
            anndate = datetime.datetime.strptime(anndate, "%d-%b-%Y").strftime('%Y-%m-%d')
    except Exception as e:
        print e
        print "ERR:", fy + ',' + anndate + ',' + quarter
    return fy, anndate, quarter, qnum, revenue, pbt, np, dividend, npmargin, \
        roe, eps, adjeps, dps


def scrape_stk_fin(soup, last_scan):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return

    fin = {}
    table = soup.find('table', {'class': 'nc'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        tds = tr.findAll('td')
        td = [x.text.strip() for x in tds]
        if len(td) > 10:
            fy, anndate, quarter, qnum, revenue, pbt, np, dividend, npmargin, \
                roe, eps, adjeps, dps = unpack_td(td)
            if S.DBG_ALL:
                print fy, anndate, quarter, qnum, revenue, pbt, np, dividend, \
                    npmargin, roe, eps, adjeps, dps
            if len(last_scan) == 0 or anndate > last_scan:
                revenue = revenue.replace(',', '')
                pbt = pbt.replace(',', '')
                np = np.replace(',', '')
                if revenue.isdigit() and int(revenue.replace(',', '')) > 0:
                    fin[anndate] = [fy, quarter, qnum, revenue, pbt, np, dividend,
                                    npmargin, roe, eps, adjeps, dps]
        else:
            if S.DBG_ALL and len(td) > 0:
                print "TD:", td

    return fin


def unpack_fin(anndate, fy, quarter, qnum, revenue, pbt, np, dividend, npmargin, roe, eps, adjeps, dps):
    if not dividend.find('-'):
        dividend = dividend.replace(',', '')
    return fy, anndate, quarter, qnum, int(revenue.replace(',', '')), \
        int(pbt.replace(',', '')), int(np.replace(',', '')), \
        dividend, npmargin, roe, eps, adjeps, dps


if __name__ == '__main__':
    S.DBG_ALL = False
    lastFinDate = ''
    stocks = 'KOBAY'

    stk_list = []
    if len(lastFinDate) > 0:
        stk_list = scrape_latest_fin(connect_stk_fin(''), lastFinDate)
    else:
        klse = S.KLSE_LIST
        if len(stocks) > 0:
            #  download only selected counters
            stk_list = formStocklist(stocks, klse)
        else:
            stk_list = loadKlseCounters(klse)

    for stk_name in stk_list:
        stk_code = stk_list[stk_name]
        print 'Downloading financial for', stk_name, stk_code
        if len(stk_code) == 4:
            stkfin = scrape_stk_fin(connect_stk_fin(stk_code), lastFinDate)
            if stkfin is not None:
                fh = open(getDataDir(S.DATA_DIR) + stk_name + '.' + stk_code + ".fin", "w")
                for key in sorted(stkfin.iterkeys()):
                    fin = ','.join(map(str, unpack_fin(key, *(stkfin[key]))))
                    print fin
                    fh.write(fin + '\n')
                fh.close()
            else:
                print 'Skipped:', stk_name, stk_code

    pass
