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
from utils.dateutils import getToday, change2KlseDateFmt
from docopt import docopt
import csv
import requests
import settings as S
import yagmail
import yaml

I3_URL = "https://klse.i3investor.com"
I3_INSIDER_DIRECTOR_URL = 'https://klse.i3investor.com/servlets/stk/annchdr/'
I3_INSIDER_SHAREHOLDER_URL = 'https://klse.i3investor.com/servlets/stk/annchsh/'
I3_LATESTAR_URL = 'https://klse.i3investor.com/financial/annual/latest.jsp'
I3_LATESTQR_URL = 'https://klse.i3investor.com/financial/quarter/latest.jsp'
I3_QR_URL = 'https://klse.i3investor.com/servlets/stk/annqtyres/'


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


def unpackInsiderTD(anndt, name, dt, notice, shares, price, direct, indirect, total, view):
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
        print ('Insider ERR: no result for <' + counter + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + counter + "." + scode + '>')
        return None
    insiders = []
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
            anndt, name, dt, notice, shares, price, direct, indirect, total = unpackInsiderTD(*insider)
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
        print ("\tInsider: " + counter + " " + slist[counter] + " " + dirUrl)
    dirList = scrapeInsider(counter, slist[counter], connectUrl(dirUrl), tradingDate)
    if S.DBG_ALL or S.DBG_INSIDER:
        print ("\tInsider: " + counter + " " + slist[counter] + " " + shdUrl)
    shdList = scrapeInsider(counter, slist[counter], connectUrl(shdUrl), tradingDate)
    return dirList, shdList


def unpackQR(fy, announcementDate, qd, qn,
             rev, pbt, np, np2sh, div, nw, dpp, npmargin, roe,
             nosh, rps, adjRps, eps, adjEps, dps, adjDPS, naps, adjNaps,
             qoq, yoy,
             eoqDate, eoqPrice, eoqPRps, eoqPEps, eoqPNaps, eoqEY, eoqDY,
             anniversaryDate, annPrice, annPRps, annPEps, annPNaps, annEY, annDY):
    if S.DBG_QR:
        print ("DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}").format(
            qd, qn, rev, pbt, np, div, roe, eps, dps, annEY, annDY, qoq, yoy)
    return [qd, qn, rev, pbt, np, div, roe, eps, dps, annEY, annDY, qoq, yoy]


def scrapeQR(counter, scode, soup):
    if soup is None or len(soup) <= 0:
        print ('QR ERR: no result for <' + counter + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No QR data is available for <' + counter + "." + scode + '>')
        return None
    qrlist = []
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        qr = [x.text.strip().replace('&nbsp; ', '').encode("ascii") for x in td]
        if S.DBG_QR:
            print("DBG:")
            for x in qr:
                print repr(x)
        if len(qr) > 0:
            qrlist = unpackQR(*qr)
            break
    return qrlist


def crawlQR(counter):
    counter = counter.upper()
    slist = formStocklist(counter, klse)
    qrUrl = I3_QR_URL + slist[counter] + ".jsp"
    if S.DBG_ALL or S.DBG_QR:
        print ("\tQR: " + counter + " " + slist[counter] + " " + qrUrl)
    qr = scrapeQR(counter, slist[counter], connectUrl(qrUrl))
    return qr


def formatQR(counter, qd, qn, rev, pbt, np, div, roe, eps, dps, annEY, annDY, qoq, yoy):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
              (counter, qd, qn, rev, pbt, np, div, roe, eps, dps, annEY, annDY, qoq, yoy))
    tdstr = " > " + counter + ", " + qd + ", Q" + qn + ", rev:" + rev + ", pbt:" \
    + pbt + ", np:" + np + ", div:" + div + ", roe:" + roe + ", eps:" + eps + ", dps:" \
    + dps + ", annEY:" + annEY + ", annDY:" + annDY + ", qoq:" + qoq + ", yoy:" + yoy
    return tdstr


def unpackLatestQR(num, stock, announcementDate, fy, qd, qn,
                   price, change, pchange,
                   rev, pbt, np, np2sh, div, nw,
                   dpp, npmargin, roe,
                   rps, eps, dps, naps,
                   qoq, yoy):
    if S.DBG_QR:
        print ("DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}").format(
            stock, announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy)
    return [stock, announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy]


def getQoQLinks(jsplink):
    soupQR = connectUrl(I3_URL + jsplink)
    if soupQR is None or len(soupQR) <= 0:
        print ('getQoQLinks ERR: no result')
        return None
    divs = soupQR.find("div", {"id": "container"})
    div = divs.find("div", {"id": "content"})
    tables = div.findAll('table')
    pdflinks = []
    found = False
    for table in tables:
        for tr in table.findAll('tr'):
            for td in tr.findAll('td'):
                divs = td.findAll('div')
                for div in divs:
                    for tr in div.findAll('tr'):
                        for td in tr.findAll('td'):
                            links = td.findAll('a')
                            for link in links:
                                pdflink = link.get('href')
                                if pdflink is None:
                                    continue
                                if "staticfile" in pdflink:
                                    found = True
                                    pdflinks.append(I3_URL + pdflink)
                                else:
                                    if found:
                                        break
                            if found:
                                break
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if found:
            break
    return pdflinks


def scrapeLatestQR(soup, tradingDate):
    if soup is None or len(soup) <= 0:
        print ('LatestQR ERR: no result')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No Latest QR data is available')
        return None
    qrlist = {}
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        latestQR = [x.text.strip().replace('&nbsp; ', '').encode("ascii") for x in td]
        if S.DBG_QR:
            print("DBG:")
            for x in latestQR:
                print repr(x)
        if len(latestQR) > 0:
            [stock, announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy] = unpackLatestQR(*latestQR)
            if announcementDate == tradingDate:
                if stock not in qrlist:
                    links = tr.findAll('a')
                    jsplink = ""
                    for link in links:
                        jsplink = link.get('href')
                        if "QoQ" in jsplink:
                            jsplink = getQoQLinks(jsplink)
                            if len(jsplink) > 0:
                                break
                    qrlist[stock] = [announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy, jsplink]
                else:
                    print ("INFO: Duplicated announcement: " + stock + ":" + qd + ":Q" + qn)
            else:
                anndt = change2KlseDateFmt(announcementDate, "%d-%b-%Y")
                trddt = change2KlseDateFmt(tradingDate, "%d-%b-%Y")
                if S.DBG_QR:
                    print("DBG:dates:{0}:{1}".format(anndt, trddt))
                if anndt < trddt:
                    break
    return qrlist


def crawlLatestQR(tradingDate=getToday("%d-%b-%Y")):
    latestQR = scrapeLatestQR(connectUrl(I3_LATESTQR_URL), tradingDate)
    return latestQR


def unpackLatestAR(stock, fy, anndate, announcementDate, latestann, view):
    if S.DBG_QR:
        print ("DBG:{0},{1},{2},{3},{4}").format(
            stock, fy, anndate, announcementDate, latestann)
    return [stock, fy, anndate, announcementDate, latestann]


def getYoYLinks(jsplink):
    soupQR = connectUrl(I3_URL + jsplink)
    if soupQR is None or len(soupQR) <= 0:
        print ('getYoYLinks ERR: no result')
        return None
    divs = soupQR.find("div", {"id": "container"})
    div = divs.find("div", {"id": "content"})
    tables = div.findAll('table')
    pdflinks = []
    found = False
    for table in tables:
        for tr in table.findAll('tr'):
            for td in tr.findAll('td'):
                links = td.findAll('a')
                for link in links:
                    pdflink = link.get('href')
                    if pdflink is None:
                        continue
                    if "staticfile" in pdflink:
                        found = True
                        pdflinks.append(I3_URL + pdflink)
                    else:
                        if found:
                            break
                if found:
                    break
            if found:
                break
        if found:
            break
    return pdflinks


def scrapeLatestAR(soup, tradingDate):
    if soup is None or len(soup) <= 0:
        print ('LatestAR ERR: no result')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No Latest AR data is available')
        return None
    arlist = {}
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        latestAR = [x.text.strip().replace('&nbsp; ', '').encode("ascii") for x in td]
        if S.DBG_QR:
            print("DBG:")
            for x in latestAR:
                print repr(x)
        if len(latestAR) > 0:
            [stock, fy, anndate, announcementDate, latestann] = unpackLatestAR(*latestAR)
            if announcementDate == tradingDate:
                if stock not in arlist:
                    links = tr.findAll('a')
                    jsplink = ""
                    for link in links:
                        jsplink = link.get('href')
                        if "annual" in jsplink:
                            jsplink = getYoYLinks(jsplink)
                            if len(jsplink) > 0:
                                break
                    arlist[stock] = [fy, anndate, announcementDate, latestann, jsplink]
                else:
                    print ("INFO: Duplicated announcement: " + stock + ":" + latestann + ":" + announcementDate)
            else:
                anndt = change2KlseDateFmt(announcementDate, "%d-%b-%Y")
                trddt = change2KlseDateFmt(tradingDate, "%d-%b-%Y")
                if S.DBG_QR:
                    print("DBG:dates:{0}:{1}".format(anndt, trddt))
                if anndt < trddt:
                    break
    return arlist


def crawlLatestAR(tradingDate=getToday("%d-%b-%Y")):
    latestAR = scrapeLatestAR(connectUrl(I3_LATESTAR_URL), tradingDate)
    return latestAR


def formatLatestQR(counter, announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy, jsplink):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
              (counter, announcementDate, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy))
        for link in jsplink:
            print('\t' + link)
    tdstr = " > " + counter + ", announced:" + announcementDate + ", QR:" + qd + ", Q" + qn \
    + ", rev:" + rev + ", pbt:" + pbt + ", np:" + np + ", div:" + div + ", roe:" + roe \
    + ", eps:" + eps + ", dps:" + dps + ", qoq:" + qoq + ", yoy:" + yoy + ", link="
    for pdflink in jsplink:
        tdstr += '\n\tlink=' + pdflink
    return tdstr


def formatLatestAR(counter, fy, anndate, announcementDate, latestann, view):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s" %
              (counter, fy, anndate, announcementDate, latestann))
    tdstr = " > " + counter + ", FY:" + fy + ", anniversary:" + anndate + ", announced:" \
    + announcementDate + ", latestAnniversary:" + latestann
    for pdflink in view:
        tdstr += '\n\tlink=' + pdflink
    return tdstr


def process(stocks="", tradingDate=getToday('%d-%b-%Y')):
    print("Trading date: " + tradingDate)
    latestAR = crawlLatestAR(tradingDate)
    latestQR = crawlLatestQR(tradingDate)
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
            # qr = crawlQR(counter)
            # if len(qr) > 0:
            #     print ("{header}{lst}".format(header="QR", lst=formatQR(counter, *qr)))
            if counter in latestQR:
                qr = latestQR[counter]
                print (formatLatestQR(counter, *qr))
            if counter in latestAR:
                ar = latestAR[counter]
                print (formatLatestAR(counter, *ar))
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
                        sendmail(counter, dirlist, trackinglist, addr, "directors", "Insider tradings:Director")
                        sendmail(counter, shdlist, trackinglist, addr, "shareholders", "Insider tradings:Shareholder")
                        # qr = crawlQR(counter)
                        # sendmail(formatQR(counter, *qr), trackinglist, addr, "QR", "Quarterly Result")
                        if counter in latestQR:
                            qr = latestQR[counter]
                            sendmail(counter, formatLatestQR(counter, *qr), trackinglist, addr, "Latest QR", "Quarterly Result")
                        if counter in latestAR:
                            ar = latestAR[counter]
                            sendmail(counter, formatLatestAR(counter, *ar), trackinglist, addr, "Latest AR", "Annual Report")
                    print


def sendmail(counter, item, tracking, addr, htext, mtext):
    if item is None:
        print counter + ": Item is None," + tracking + "," + addr + "," + htext + "," + mtext
        return
    if len(item) > 0:
        item.insert(0, "Tracking list: " + tracking.upper())
        print ("{header}{lst}".format(header="\t:" + htext, lst=item))
        yagmail.SMTP("insider4trader@gmail.com").send(addr, mtext, item)


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
