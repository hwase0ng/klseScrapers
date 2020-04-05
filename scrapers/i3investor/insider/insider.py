"""
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER                     Optional counters
Options:
    -d,--date=<trading_date>    Use provided trading date to search
    -s,--skip=<name>            skip email to name

Created on Mar 7, 2020

@author: hwaseong
"""
from common import loadCfg
from scrapers.i3investor.insider.latest import crawl_latest
from scrapers.i3investor.insider.latestAnnualReports import *
from scrapers.i3investor.insider.latestQuarterlyReports import *
from scrapers.i3investor.insider.stk import crawl_insider
from utils.dateutils import getToday
from docopt import docopt
import settings as S
import yagmail
import yaml


def process_latest(trading_date=getToday('%d-%b-%Y')):
    latestDIR, latestSHD, latestCOM = crawl_latest(trading_date)
    return latestDIR, latestSHD, latestCOM


def process(stock_list="", trading_date=getToday('%d-%b-%Y')):
    latestDIR, latestSHD, latestCOM = process_latest(trading_date)
    print("Trading date: " + trading_date)
    latestAR = crawl_latest_ar(trading_date)
    latestQR = crawl_latest_qr(trading_date)
    if len(stock_list):
        if "," in stock_list:
            stocks = stock_list.split(",")
        else:
            stocks = [stock_list]
        for stock in stocks:
            stock = stock.upper()
            dir_list, shd_list = crawl_insider(stock, trading_date)
            if len(dir_list) > 0:
                print ("{header}{lst}".format(header="\tdirectors:", lst=dir_list))
            if len(shd_list) > 0:
                print ("{header}{lst}".format(header="\tshareholders", lst=shd_list))
            # qr = crawlQR(counter)
            # if len(qr) > 0:
            #     print ("{header}{lst}".format(header="QR", lst=formatQR(counter, *qr)))
            if stock in latestQR:
                qr = latestQR[stock]
                print (format_latest_qr(stock, *qr))
            if stock in latestAR:
                ar = latestAR[stock]
                print (format_latest_ar(stock, *ar))
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
                    dir_list, shd_list, qrlist, arlist = [], [], [], []
                    for stock in items[trackinglist]:
                        stock = stock.upper()
                        di, shd = crawl_insider(stock, trading_date)
                        if di is not None and len(di) > 0:
                            for item in di:
                                dir_list.append(item)
                        if shd is not None and len(shd) > 0:
                            for item in shd:
                                shd_list.append(item)
                        if stock in latestQR:
                            qr = latestQR[stock]
                            qrlist.append(format_latest_qr(stock, *qr))
                        if stock in latestAR:
                            ar = latestAR[stock]
                            arlist.append(format_latest_ar(stock, *ar))
                    send_mail(stock, dir_list, trackinglist, addr, "directors", "Insider tradings:Director")
                    send_mail(stock, shd_list, trackinglist, addr, "shareholders", "Insider tradings:Shareholder")
                    # qr = crawlQR(counter)
                    # sendmail(formatQR(counter, *qr), trackinglist, addr, "QR", "Quarterly Result")
                    send_mail(stock, qrlist, trackinglist, addr, "Latest QR", "Insider: Quarterly Result")
                    send_mail(stock, arlist, trackinglist, addr, "Latest AR", "Insider: Annual Report")
                    print


def format_table(htext, item, tracking):
    tableStyle = "<style> \
                    table { \
                      width:100%; \
                    } \
                    table, th, td { \
                      border: 1px solid black; \
                      border-collapse: collapse; \
                    } \
                    th, td { \
                      padding: 15px; \
                      text-align: left; \
                    } \
                    table#t01 tr:nth-child(even) { \
                      background-color: #eee; \
                    } \
                    table#t01 tr:nth-child(odd) { \
                     background-color: #fff; \
                    } \
                    table#t01 th { \
                      background-color: black; \
                      color: white; \
                    } \
                 </style>"

    if htext == "Latest AR":
        htext = '<table id="t01" style=\"width:100%\">\n'
        htext += "<tr>\n"
        htext += "<th>Stock</th>\n"
        htext += "<th>Finance year</th>\n"
        htext += "<th>Audited Anniverary Date</th>\n"
        htext += "<th>AR Anniverary Date</th>\n"
        htext += "<th>Latest Anniverary Date</th>\n"
        htext += "<th>PDF</th>\n"
        htext += "</tr>\n"
        item.insert(0, htext)
    elif htext == "Latest QR":
        htext = '<table id="t01" style=\"width:100%\">\n'
        htext += "<tr>\n"
        htext += "<th>Stock</th>\n"
        htext += "<th>Announcement Date</th>\n"
        htext += "<th>Quarter</th>\n"
        htext += "<th>Q#</th>\n"
        htext += "<th>Revenue</th>\n"
        htext += "<th>PBT</th>\n"
        htext += "<th>NP</th>\n"
        htext += "<th>DIV</th>\n"
        htext += "<th>ROE</th>\n"
        htext += "<th>EPS</th>\n"
        htext += "<th>DPS</th>\n"
        htext += "<th>QoQ</th>\n"
        htext += "<th>YoY</th>\n"
        htext += "<th>PDF</th>\n"
        htext += "</tr>\n"
        item.insert(0, htext)
    else:
        htext = '<table id="t01" style=\"width:100%\">\n'
        htext += "<tr>\n"
        htext += "<th>Stock</th>\n"
        htext += "<th>Name</th>\n"
        htext += "<th>Date</th>\n"
        htext += "<th>Notice</th>\n"
        htext += "<th>No. of Shares</th>\n"
        htext += "<th>Price</th>\n"
        htext += "<th>View</th>\n"
        htext += "</tr>\n"
        item.insert(0, htext)
    item.insert(0, tableStyle)
    item.insert(0, "")
    header = "<h2>{}</h2>".format(tracking.upper())
    item.insert(0, header)
    item.append("</table>")


def send_mail(counter, item, tracking, addr, htext, emailTitle):
    if item is None:
        print "\t\tERR:" + counter + ": Item is None," + tracking + "," + addr + "," + htext + "," + emailTitle
        return
    if len(item) > 0:
        print ("{header}{lst}".format(header="\t" + htext, lst=item))
        format_table(htext, item, tracking)
        yagmail.SMTP("insider4trader@gmail.com", password="vwxaotmoawdfwxzx").send(addr, emailTitle, item)


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    trading_date = args['--date']
    counters = ""
    if args['COUNTER']:
        counters = args['COUNTER'][0].upper()
    latestDIR, latestSHD, latestCOM = process_latest(trading_date)
    yagmail.SMTP("insider4trader@gmail.com", password="vwxaotmoawdfwxzx").send("roysten.tan@gmail.com", "INSIDER",
                                                                               latestDIR + latestSHD + latestCOM)
    # if trading_date is not None:
    #     process(counters, trading_date)
    # else:
    #     process(counters)

    print ('\n...end processing')
