'''
Created on Apr 13, 2018

@author: hwase0ng
'''

import settings as S
import datetime
import requests
from BeautifulSoup import BeautifulSoup

I3FINURL = 'https://klse.i3investor.com/servlets/stk/fin/'


def connectStkFin(stkcode):
    if len(stkcode) != 4:
        print "ERR:Invalid stkcode = ", stkcode
        return

    global soup
    stkFinUrl = I3FINURL + stkcode + ".jsp"
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


def unpackTD(td):
    '''
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
    '''
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
    fy = datetime.datetime.strptime(fy, "%d-%b-%Y").strftime('%Y-%m-%d')
    anndate = datetime.datetime.strptime(anndate, "%d-%b-%Y").strftime('%Y-%m-%d')
    quarter = datetime.datetime.strptime(quarter, "%d-%b-%Y").strftime('%Y-%m-%d')
    return fy, anndate, quarter, qnum, revenue, pbt, np, dividend, npmargin, \
        roe, eps, adjeps, dps


def scrapeStkFin(soup):
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
                roe, eps, adjeps, dps = unpackTD(td)
            if S.DBG_ALL:
                print fy, anndate, quarter, qnum, revenue, pbt, np, dividend, npmargin, \
                    roe, eps, adjeps, dps
            fin[anndate] = [fy, quarter, qnum, revenue, pbt, np, dividend, npmargin,
                            roe, eps, adjeps, dps]
        else:
            if S.DBG_ALL and len(td) > 0:
                print "TD:", td

    return fin


def unpackFIN(anndate, fy, quarter, qnum, revenue, pbt, np, dividend, npmargin, roe, eps, adjeps, dps):
    if not dividend.find('-'):
        dividend = dividend.replace(',', '')
    return fy, anndate, quarter, qnum, int(revenue.replace(',', '')), \
        int(pbt.replace(',', '')), int(np.replace(',', '')), \
        dividend, npmargin, roe, eps, adjeps, dps


if __name__ == '__main__':
    S.DBG_ALL = False
    stkcode = '7106'
    stkfin = scrapeStkFin(connectStkFin(stkcode))
    if stkfin is not None:
        fh = open(stkcode + ".fin", "w")
        for key in sorted(stkfin.iterkeys()):
            fin = ','.join(map(str, unpackFIN(key, *(stkfin[key]))))
            print fin
            fh.write(fin + '\n')
        fh.close()
    pass
