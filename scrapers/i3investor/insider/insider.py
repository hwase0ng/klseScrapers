"""
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER                     Optional counters
Options:
    -d,--date=<trading_date>    Use provided trading date to search
    -s,--skip=<name>            skip email to name
    -t,--test=<test_name>       run test on selected function

Created on Mar 7, 2020

@author: hwaseong
"""
from common import loadCfg
from scrapers.i3investor.insider.formatLatest import *
from scrapers.i3investor.insider.latest import crawl_latest
from scrapers.i3investor.insider.latestAnnualReports import *
from scrapers.i3investor.insider.latestQuarterlyReports import *
from scrapers.i3investor.insider.stk import crawl_insider
from utils.dateutils import getToday
from docopt import docopt
import settings as S
import styles as T
import yagmail
import yaml


def process_latest(trading_date=getToday('%d-%b-%Y'), formatted_output=False):
    dir_list, shd_list, com_list = crawl_latest(trading_date, formatted_output)
    return dir_list, shd_list, com_list


def process(stock_list="", trading_date=getToday('%d-%b-%Y')):
    latest_dir, latest_shd, latest_com = process_latest(trading_date)
    print("Trading date: " + trading_date)
    latestAR = crawl_latest_ar(trading_date)
    latestQR = crawl_latest_qr(trading_date)
    if len(stock_list):
        if "," in stock_list:
            stocks = stock_list.split(",")
        else:
            stocks = [stock_list]
        dir_list, shd_list, qr_list, ar_list = [], [], [], []
        for stock in stocks:
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
                qr_list.append(format_latest_qr(stock, *qr))
            if stock in latestAR:
                ar = latestAR[stock]
                ar_list.append(format_latest_ar(stock, *ar))
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
                print (name + ": " + ", ".join(addr))
                for tracking_list in items.iterkeys():
                    if tracking_list == "email":
                        continue
                    print ("\t" + tracking_list + " : ")
                    dir_list, shd_list, com_list, qr_list, ar_list = [], [], [], [], []
                    dir_title = "Latest Directors Transactions"
                    shd_title = "Latest Substantial Shareholders Transactions"
                    com_title = "Latest Company Transactions"
                    for stock in items[tracking_list]:
                        stock = stock.upper()
                        res = match_selection(stock, latest_dir, dir_title)
                        if len(res) > 0:
                            for item in res:
                                dir_list.append(item)
                        shd = match_selection(stock, latest_shd, shd_title)
                        if len(shd) > 0:
                            for item in shd:
                                shd_list.append(item)
                        com = match_selection(stock, latest_com, com_title)
                        if len(com) > 0:
                            for item in com:
                                com_list.append(item)
                        if stock in latestQR:
                            qr = latestQR[stock]
                            qr_list.append(format_latest_qr(stock, *qr))
                        if stock in latestAR:
                            ar = latestAR[stock]
                            ar_list.append(format_latest_ar(stock, *ar))
                    if len(dir_list) > 0:
                        format_table(dir_title, dir_list)
                    if len(shd_list) > 0:
                        format_table(shd_title, shd_list)
                    if len(com_list) > 0:
                        format_table(com_title, com_list)
                    if len(qr_list) > 0:
                        qr_title = "Quarterly Results"
                        format_ar_qr(qr_title, qr_list)
                    if len(ar_list) > 0:
                        ar_title = "Annual Reports"
                        format_ar_qr(ar_title, ar_list)
                    list_result = dir_list + shd_list + com_list + qr_list + ar_list
                    if len(list_result) > 0:
                        list_result.insert(0, T.browserref)
                        subject = "INSIDER UPDATE on {} for portfolio: {}".format(
                            getToday("%d-%b-%Y"), tracking_list.upper()
                        )
                        yagmail.SMTP(S.MAIL_SENDER, S.MAIL_PASSWORD).send(addr, subject, list_result)


def match_selection(counter, latest_list, list_title):
    if len(latest_list) == 0:
        return ""
    director = "Directors" in list_title
    company = "Company" in list_title
    insiders = []
    for list_item in latest_list:
        if counter == list_item[0]:
            if company:
                [stock, announce_date, from_date, to_date,
                 chg_type, shares, min_price, max_price, total, view] = list_item
                insiders.append(format_company(True, stock, announce_date,from_date, to_date,
                                               chg_type, shares, min_price, max_price, total, view))
            else:
                if director:
                    [stock, announce_date, name, chg_date, chg_type, shares, price, view] = list_item
                else:
                    price = ""
                    [stock, announce_date, name, chg_date, chg_type, shares, view] = list_item
                insiders.append(format_insider(True, director, stock, announce_date, name, chg_date,
                                               chg_type, shares, price, view))
    return insiders


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    trading_date = args['--date']
    counters = ""
    if args['COUNTER']:
        counters = args['COUNTER'][0].upper()
    if args['--test'] == "latest":
        html_output = True
        latestDIR, latestSHD, latestCOM = process_latest(trading_date, html_output)
        result = latestDIR + latestSHD + latestCOM
        if html_output:
            result.insert(0, T.browserref)
            yagmail.SMTP(S.MAIL_SENDER, S.MAIL_PASSWORD). \
                send("roysten.tan@gmail.com", "INSIDER UPDATE: " + getToday("%d-%b-%Y"), result)
        else:
            for i in result:
                print i
    else:
        if trading_date is not None:
            process(counters, trading_date)
        else:
            process(counters)

    print ('\n...end processing')
