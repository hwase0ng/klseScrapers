# Copyright (c) 2011, Mark Chenoweth
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Note: Yahoo for KLCI has been broken since Feb 2018

import sys
import settings as S
import Utils.dateutils as du
import calendar
from datetime import datetime, date
import requests
import re
from Utils.dateutils import getToday, getNextDay, getLastDate
import csv
from requests.exceptions import ConnectionError
from common import formStocklist, loadKlseCounters, appendCsv

sys.path.append('../../')


def getYahooCookie(url):
    # search with regular expressions
    # "CrumbStore":\{"crumb":"(?<crumb>[^"]+)"\}
    # url = 'https://uk.finance.yahoo.com/quote/AAPL/history'  # url for a ticker symbol, with a download link
    try:
        r = requests.get(url)  # download page
    except ConnectionError as ce:
        print "\tConnectionError:", ce
        return '', ''

    txt = r.text  # extract html
    try:
        cookie = r.cookies['B']  # the cooke we're looking for is named 'B'
    except KeyError as ke:
        print "getYahooCookie KeyError: ", ke
        print url
        cookie = ''
    if S.DBG_ALL or S.DBG_YAHOO:
        print 'DBG:getYahooCookie: ', cookie

    # Now we need to extract the token from html.
    # the string we need looks like this: "CrumbStore":{"crumb":"lQHxbbYOBCq"}
    # regular expressions will do the trick!

    pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')

    for line in txt.splitlines():
        m = pattern.match(line)
        if m is not None:
            crumb = m.groupdict()['crumb']

    if S.DBG_ALL or S.DBG_YAHOO:
        print 'DBG:getYahooCrumb=', crumb
    return cookie, crumb


class Quote(object):

    DATE_FMT = '%Y-%m-%d'
    TIME_FMT = '%H:%M:%S'

    def __init__(self, lastdt):
        self.url = ''
        self.symbol = ''
        self.sname = ''
#       self.date,self.time,self.open_,self.high,self.low,self.close,self.volume = ([] for _ in range(7))
        self.date, self.open_, self.high, self.low, self.close, self.volume = (
            [] for _ in range(6))
        self.csverr = ''
        self.lastdate = lastdt
        self.lastcsv = ''
#       self.cookie,self.crumb = self.getYahooCookie()

    def getCsvErr(self):
        return self.csverr

    def append(self, dt, open_, high, low, close, volume):
        self.date.append(dt.date())
#       self.time.append(dt.time())
        self.open_.append(float(open_))
        self.high.append(float(high))
        self.low.append(float(low))
        self.close.append(float(close))
        self.volume.append(int(volume))

    def to_csv(self):
        # return ''.join(["{0},{1},{2},{3:.2f},{4:.2f},{5:.2f},{6:.2f},{7}\n".format(self.symbol,
        return ''.join(["{0},{1},{2:.4f},{3:.4f},{4:.4f},{5:.4f},{6}\n".format(
            self.sname,
            self.date[bar].strftime('%Y-%m-%d'),  # self.time[bar].strftime('%H:%M:%S'),
            self.open_[bar], self.high[bar], self.low[bar],
            self.close[bar], self.volume[bar])
            for bar in xrange(len(self.close))])

    def write_csv(self, filename):
        with open(filename, 'w') as f:
            f.write(self.to_csv())

    def read_csv(self, filename):
        # self.symbol = ''
        #        self.date,self.time,self.open_,self.high,self.low,self.close,self.volume = ([] for _ in range(7))
        self.sname, self.date, self.open_, self.high, self.low, self.close, self.volume = ([] for _ in range(7))
        for line in open(filename, 'r'):
            # symbol,ds,ts,open_,high,low,close,volume = line.rstrip().split(',')
            sname, ds, open_, high, low, close, volume = line.rstrip().split(',')
#       self.symbol = symbol
#       dt = datetime.strptime(ds+' '+ts,self.DATE_FMT+' '+self.TIME_FMT)
        dt = datetime.strptime(ds, self.DATE_FMT)
        self.append(dt, open_, high, low, close, volume)
        return True

    def formUrl_old(self, symbol, start_date, end_date):
        start_year, start_month, start_day = start_date.split('-')
        start_month = str(int(start_month) - 1)
        end_year, end_month, end_day = end_date.split('-')
        end_month = str(int(end_month) - 1)
        url_string = "http://ichart.finance.yahoo.com/table.csv?s={0}".format(
            symbol)
        url_string += "&a={0}&b={1}&c={2}".format(start_month,
                                                  start_day, start_year)
        url_string += "&d={0}&e={1}&f={2}".format(end_month, end_day, end_year)
        return url_string

    def formUrl(self, crumb, symbol, start_date, end_date):
        start_year, start_month, start_day = start_date.split('-')
#       start_month = str(int(start_month)-1)
        end_year, end_month, end_day = end_date.split('-')
#       end_month = str(int(end_month)-1)
        sDate = datetime(int(start_year), int(start_month), int(start_day),
                         0, 0)
        eDate = datetime(int(end_year), int(end_month), int(end_day), 0, 0)
#       datetime(*sDate).timestamp() # convert to seconds since epoch

        # prepare input data as a tuple
#       data = (int(datetime(*sDate).timestamp()),
#               int(datetime(*eDate).timestamp()),
#               crumb)
        data = (calendar.timegm((sDate.timetuple())),
                calendar.timegm((eDate.timetuple())),
                crumb)
        url_string = "https://query1.finance.yahoo.com/v7/finance/download/" + symbol
        url_string += "?period1={0}&period2={1}&interval=1d&events=history&crumb={2}".format(*data)

        if S.DBG_ALL:
            print("DBG:formUrl:" + url_string)

        return url_string

    def __repr__(self):
        return self.to_csv()


class YahooQuote(Quote):
    ''' Daily quotes from Yahoo. Date format='yyyy-mm-dd' '''
    def __init__(self, cookie, crumb, sname, symbol, last_date,
                 end_date=date.today().isoformat()):
        super(YahooQuote, self).__init__(last_date)
        self.sname = sname.upper()
        self.symbol = symbol.upper()
        if last_date == getToday("%Y-%m-%d"):
            #  Will get 400 Bad Request
            if S.DBG_YAHOO:
                print "DBG:Skipped downloaded", last_date
            return None
        start_date = getNextDay(last_date)
        if S.DBG_ALL or S.DBG_YAHOO:
            print "DBG:YahooQuote:1:", symbol, self.symbol, last_date, start_date
        # Do not download today's EOD if market is still open
        if end_date == du.getToday("%Y-%m-%d"):
            now = datetime.now()
            if now.hour < 18:  # only download today's EOD if it is after 6pm local time
                end_date = du.getYesterday("%Y-%m-%d")
#       self.url = self.formUrl_old(symbol,last_date,end_date)
        self.url = self.formUrl(crumb, symbol, start_date, end_date)
        if S.DBG_ALL or S.DBG_YAHOO:
            print "DBG:YahooQuote:2:", self.url
#       csv = urllib.urlopen(self.url).readlines()
#       if not csv[0].startswith("Date,Open,"):
        resUrl = requests.get(self.url, cookies={'B': cookie})
        if resUrl.status_code != 200:
            self.csverr = str(resUrl.status_code) + ":" + resUrl.reason
            print "ERR:", symbol, ":", self.url
            print "ERR:" + self.csverr
        else:
            self.csverr = ''
            '''
            csv = resUrl.text
            csv.reverse()
            for bar in xrange(0,len(csv)-1):
                ds,open_,high,low,close,volume,adjc =
                    csv[bar].rstrip().split(',')
            '''
            iterator = resUrl.iter_lines()
            skipline = next(iterator)
            if S.DBG_ALL:
                print "SKIP:YohooQuote:", skipline
            for csv in iterator:
                if S.DBG_ALL:
                    print "DBG", csv
                if "null" in csv:
                    if S.DBG_YAHOO:
                        print "SKIP:", csv
                    continue
                ds, open_, high, low, close, adjc, volume = (
                    csv.rstrip().split(','))
                if S.DBG_YAHOO:
                    print "DBG:", ds, open_, high, low, close, adjc, volume
                    #  print "DBG:", type(ds), type(open_), type(high), type(low),
                    #  type(close), type(adjc), type(volume)

                #  Start of data validation
                if float(volume) <= 0:
                    if S.DBG_YAHOO:
                        print 'DBG:Skipped 0 volume as a result of non-trading day:', ds
                    continue
                if ds < start_date:
                    if S.DBG_YAHOO:
                        print "DBG:Skipped older date:", ds
                    continue
                if ds > getToday("%Y-%m-%d"):
                    if S.DBG_YAHOO:
                        print "DBG:Skipped future dividends:", ds
                    continue
                if ds == self.lastdate:
                    if S.DBG_YAHOO:
                        print "INF:Skipped duplicated date:", sname, ds
                        print '\tcsv:', csv
                        print '\tlst:', self.lastcsv
                    continue
                self.lastdate = ds
                self.lastcsv = csv
                '''
                if not isnumberlist([high, low, close, adjc]):
                    if S.DBG_YAHOO:
                        print "SKIP:", ds, open_, high, low, close, adjc
                    continue
                '''
                open_, high, low, close, adjc = [
                    float(x) for x in [open_, high, low, close, adjc]]
                if open_ > high or close > high:
                    print "ERR:Invalid High:H<O,C, Patched.", sname, csv
                    if high < open_:
                        high = open_
                    if high < close:
                        high = close
                if open_ < low or close < low:
                    print "ERR:Invalid Low:L>O,C, Patched.", sname, csv
                    if low > open_:
                        low = open_
                    if low > close:
                        low = close
                if low * 10000 < 1.0 or high * 10000 < 1.0:
                    if open_ * 10000 < 1.0 and close * 10000 < 1.0:
                        print "ERR:0 values detected - SKIPPED", sname, csv
                        continue
                    else:
                        print "INF:0 value detected - PATCHED", sname, csv
                        if low * 10000 < 1.0:
                            if open_ < close:
                                low = open_
                            else:
                                low = close
                        else:
                            if high * 10000 < 1.0:
                                if open_ > close:
                                    high = open_
                                else:
                                    high = close
                if not S.PRICE_WITHOUT_SPLIT:
                    if close != adjc:
                        factor = adjc / close
                        open_, high, low, close = [
                            x * factor for x in [open_, high, low, close]]
                dt = datetime.strptime(ds, '%Y-%m-%d')
                self.append(dt, open_, high, low, close, volume)
            if S.DBG_ALL:
                print "YahooQuote:End"


if __name__ == '__main__':
    S.RESUME_FILE = False
    if not S.RESUME_FILE:
        lastdt = S.ABS_START

    klse = "../i3investor/klse.txt"
    stocks = ''
    if len(stocks) > 0:
        #  download only selected counters
        stocklist = formStocklist(stocks, klse)
    else:
        # Full download using klse.txt
        stocklist = loadKlseCounters(klse)

    cookie, crumb = getYahooCookie('https://uk.finance.yahoo.com/quote/AAPL/')

    for shortname in sorted(stocklist.iterkeys()):
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            OUTPUT_FILE = '../../data/yahoo/' + shortname + "." + stock_code + ".csv"
            if S.RESUME_FILE:
                lastdt = getLastDate(OUTPUT_FILE)
                if len(lastdt) == 0:
                    # File is likely to be empty, hence scrape from beginning
                    lastdt = S.ABS_START
            print shortname, stock_code
            print "Scraping", shortname, stock_code, lastdt, '$'
            q = YahooQuote(cookie, crumb, shortname, stock_code + ".KL",
                           lastdt, "2018-02-01")
            if len(q.getCsvErr()) > 0:
                st_code, st_reason = q.getCsvErr().split(":")
                rtn_code = int(st_code)
                print rtn_code, st_reason
            else:
                print q
                writeCsv = True
                if writeCsv:
                    if S.RESUME_FILE:
                        TMP_FILE = OUTPUT_FILE + 'tmp'
                        q.write_csv(TMP_FILE)
                        appendCsv(0, OUTPUT_FILE)
                    else:
                        q.write_csv(OUTPUT_FILE)
        else:
            print "ERR: Not found: ", shortname, stock_code
