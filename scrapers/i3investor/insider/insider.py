'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -d,--date=<tradingdt>    Use provided trading date to search

Created on Mar 7, 2020

@author: hwase
'''
from BeautifulSoup import BeautifulSoup
from common import formStocklist, loadCfg, printable
from utils.dateutils import getToday
from docopt import docopt
import requests
import settings as S
import yagmail
import yaml

I3_INSIDER_DIRECTOR_URL = 'https://klse.i3investor.com/servlets/stk/annchdr/'
I3_INSIDER_SHAREHOLDER_URL = 'https://klse.i3investor.com/servlets/stk/annchsh/'


def connectUrl(url):
    global soup
    try:
        page = requests.get(url, headers=S.HEADERS)
        assert(page.status_code == 200)
        html = page.content
        soup = BeautifulSoup(html)
    except Exception as e:
        print(e)
        soup = ''
    return soup


def unpackTD(anndt, name, dt, notice, shares, price, direct, indirect, total, view):
    '''
    Sample table:
    <tr role="row" class="odd">
        <td class="center sorting_2" nowrap="nowrap">24-May-2019</td>
        <td class="left sorting_3">  YAYASAN GURU TUN HUSSEIN ONN  </td>
        <td class="center sorting_1" nowrap="nowrap">16-May-2019</td>
        <td class="center sorting_3" width="80px"> <span class="up">Notice of Interest</span> </td>
        <td class="right" nowrap="nowrap"> <span class="up">6,000,000</span> </td>
        <td class="center" nowrap="nowrap">0.000</td>
        <td class="right" nowrap="nowrap">5.92</td>
        <td class="right" nowrap="nowrap">0.00</td>
        <td class="right" nowrap="nowrap">5.92</td>
        <td class="center" nowrap="nowrap"> <a href="/insider/substantialShareholderNoticeOfInterest/5276/24-May-2019/13035_1229846127.jsp" title="View Detail" target="_blank"> <img class="sp view16" src="//cdn1.i3investor.com/cm/icon/trans16.gif" alt="View Detail"> </a> </td>
    </tr>
    return anndt, name, dt, notice, int(shares.replace(',', '')), float(price), \
    '''
    if S.DBG_INSIDER:
        print ("DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8}").format(
            anndt, name, dt, notice, shares, price, direct, indirect, total)
    return anndt, name, dt, notice, shares, \
        price, direct, indirect, total
    '''
        float(price.replace('-', '0.00').replace(',', '')), \
        float(direct.replace('-', '0.00').replace(',', '')), \
        float(indirect.replace('-', '0.00').replace(',', '')), \
        float(total.replace('-', '0.00').replace(',', ''))
    '''


def scrapeInsider(counter, scode, soup, lastdt, showLatest=False):
    if soup is None or len(soup) <= 0:
        print ('ERR: no result for <' + counter + '>')
        return None
    insiders = []
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + counter + "." + scode + '>')
        return None
    count = 0
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        if S.DBG_INSIDER:
            print("DBG:")
            for x in td:
                print repr(x)
        # u'\u2019' is the last char in DATO' which can't be encoded to ascii
        # insider = [x.text.replace(u'\u2019', '').strip().encode("ascii") for x in td]
        insider = [printable(x).strip().encode("ascii") for x in td]
        if len(insider) == 10:
            anndt, name, dt, notice, shares, price, direct, indirect, total = unpackTD(*insider)
            view = "https:/" + td[9].find('a').get('href').encode("ascii")
            if S.DBG_ALL or S.DBG_INSIDER:
                # print("%s, %s, %s, %s, %s, %s, %.2f, %.2f, %.2f, %.2f, %s" %
                print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
                      (counter, anndt, name, dt, notice, shares, price, direct, indirect, total, view))
            tdstr = " > " + counter + ", " + name + ", " + dt + ", " + notice + ", " \
            + shares + ", " + price + ", " + view
            if dt != lastdt:
                if showLatest:
                    if S.DBG_ALL or S.DBG_INSIDER:
                        print("%s, %s, %s, %s, %s, %s, %f, %f, %f, %f, %s" %
                              (counter, anndt, name, dt, notice, shares, price, direct, indirect, total, view))
                    insiders.append(tdstr)
                '''
                count += 1
                if count > 9:
                    break
                '''
                continue
            else:
                insiders.append(tdstr)
    return insiders


def crawlInsider(counter, tradingDate):
    counter = counter.upper()
    slist = formStocklist(counter, klse)
    dirUrl = I3_INSIDER_DIRECTOR_URL + slist[counter] + ".jsp"
    shdUrl = I3_INSIDER_SHAREHOLDER_URL + slist[counter] + ".jsp"
    if S.DBG_ALL or S.DBG_INSIDER:
        print ("\t" + counter + " " + slist[counter] + " " + dirUrl)
    dirList = scrapeInsider(counter, slist[counter], connectUrl(dirUrl), tradingDate)
    if S.DBG_ALL or S.DBG_INSIDER:
        print ("\t" + counter + " " + slist[counter] + " " + shdUrl)
    shdList = scrapeInsider(counter, slist[counter], connectUrl(shdUrl), tradingDate)
    return dirList, shdList


def process(stocks="", tradingDate=getToday('%d-%b-%Y')):
    print("Trading date: " + tradingDate)
    if len(stocks):
        if "," in stocks:
            stocks = stocks.split(",")
        else:
            stocks = [stocks]
        for counter in stocks:
            dirlist, shdlist = crawlInsider(counter, tradingDate)
            if len(dirlist) > 0:
                print ("{header}{lst}".format(header="\tdirectors:", lst=dirlist))
            if len(shdlist) > 0:
                print ("{header}{lst}".format(header="\tshareholders", lst=shdlist))
    else:
        stream = open("scrapers/i3investor/insider/insider.yaml", 'r')
        docs = yaml.load_all(stream, Loader=yaml.FullLoader)
        for doc in docs:
            for name, items in doc.items():
                # print (name + " : " + str(items))
                addr = items["email"]
                print (name + ": " + addr)
                for trackinglist in items.iterkeys():
                    if trackinglist == "email":
                        continue
                    print ("  " + trackinglist + " : ")
                    for counter in items[trackinglist]:
                        dirlist, shdlist = crawlInsider(counter, tradingDate)
                    if len(dirlist) > 0:
                        dirlist.insert(0, "Tracking list: " + trackinglist.upper())
                        print ("{header}{lst}".format(header="\tdirectors:", lst=dirlist))
                        yagmail.SMTP("insider4trader@gmail.com").send(addr, 'Insider tradings:Director', dirlist)
                    if len(shdlist) > 0:
                        shdlist.insert(0, "Tracking list: " + trackinglist.upper())
                        print ("{header}{lst}".format(header="\tshareholders", lst=shdlist))
                        yagmail.SMTP("insider4trader@gmail.com").send(addr, 'Insider tradings:Shareholder', shdlist)
                    print


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    global klse
    klse = "scrapers/i3investor/klse.txt"

    tradingdt = args['--date']
    stocks = ""
    if args['COUNTER']:
        stocks = args['COUNTER'][0].upper()
    if tradingdt is not None:
        process(stocks, tradingdt)
    else:
        process(stocks)

    print ('\n...end processing')
