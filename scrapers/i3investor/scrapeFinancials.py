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
    if len(stkcode) != 1:
        print "ERR:Invalid stkcode = ", stkcode
        return

    global soup
    stkFinUrl = I3FINURL + stkcode
    try:
        page = requests.get(stkFinUrl, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
        soup = ''
    return soup


def unpackTD(anndate, quarter, revenue, pbt, np, np2sh, npmargin, roe, eps, dps, naps, qoq, yoy):
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
    anndate = datetime.datetime.strptime(anndate, "%d/%M/%Y").strftime('%Y-%m-%d')
    quarter = datetime.datetime.strptime(quarter, "%d/%M/%Y").strftime('%Y-%m-%d')
    return anndate, quarter, revenue, pbt, np, np2sh, npmargin, roe, eps, dps, naps, qoq, yoy


def scrapeStkFin(soup):
    if soup is None or len(soup) <= 0:
        print 'ERR: no result'
        return

    fin = {}
    table = soup.find('table', {'class': 'nc'})
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        if tr.attrs.get("class") == "totals":
            fy = tr.text.strip().split(':')[1]
            print fy
            fy = datetime.datetime.strptime(fy, "%d/%M/%Y").strftime('%Y-%m-%d')
            print fy
        else:
            tds = tr.findAll('td')
            td = [x.text.strip() for x in tds]
            anndate, quarter, revenue, pbt, np, np2sh, npmargin, \
                roe, eps, dps, naps, qoq, yoy = unpackTD(*td)
            if S.DBG_ALL:
                print fy, anndate, quarter, revenue, pbt, np
            fin[anndate] = [fy, quarter, revenue, pbt, np, np2sh, npmargin, \
                roe, eps, dps, naps, qoq, yoy]

    return fin


def unpackFIN(popen, phigh, plow, pclose, pvol):
    return "{:.4f}".format(float(popen)), "{:.4f}".format(float(phigh)), "{:.4f}".format(float(plow)), \
        "{:.4f}".format(float(pclose)), int(pvol.replace(',', ''))


if __name__ == '__main__':
    S.DBG_ALL = False
    stkfin = scrapeStkFin(connectStkFin('7106'))
    fh = open(stkfin + ".fin", "w")
    for key in sorted(stkfin.iterkeys()):
        fin = key + ',' + ','.join(map(str, unpackFIN(*(stkfin[key]))))
        print fin
        fh.write(fin+ ',nl\n')
    fh.close()
    pass
