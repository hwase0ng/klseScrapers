'''
Created on Apr 16, 2018

@author: hwase0ng

Note: This version is adapted from a source found in Internet which I could no longer traced to
      provide its due credit. Please do inform me if you are the original author of this code.
'''

import sys
from common import formStocklist, loadKlseCounters
import settings as S
import Utils.dateutils as du
import requests
import pandas as pd
import numpy as np
import datetime
import math
from scrapers.investingcom.scrapeStocksListing import writeStocksListing
from Utils.dateutils import getLastDate, getToday
from scrapers.yahoo.yahoo import getYahooCookie, YahooQuote

sys.path.append('../../')


class Quote(object):
    """An object that holds price data for a particular commodity, across a given date range. """
    BASE_URL = "https://www.investing.com/instruments/HistoricalDataAjax"

    def __init__(self, name, start, end, idmap):
        self.csverr = ''
        self.start = start
        self.end = end
        self.ID_MAPPING = idmap
        self.name = name
        self.response = ''
        self.s1 = ''
        # self.response = self.scrape()

    def getCsvErr(self):
        return self.csverr

    def write_csv(self, filename):
        self.s1.to_csv(filename, index=False, header=False)

    def scrape(self):
        """
        Given a Commodity object with a date range and a commodity id,
        scrape historical data from the investing.com site

        Stores a string with the result gotten from the site
        HEADERS = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
        }
        """

        try:
            data = {
                "curr_id": self.ID_MAPPING[self.name],
                "smlID": "300004",
                "st_date": self.start,
                "end_date": self.end,
                "interval_sec": "Daily",
                "sort_col": "date",
                "sort_ord": "ASC",
                "action": "historical_data"
            }

            r = requests.post(self.BASE_URL, data=data, headers=S.HEADERS)
            assert(r.status_code == 200)
            return r.text
        except KeyError:
            if S.DBG_ALL:
                print "KeyError: " + self.name
            return "KeyError: No ID mapping for " + self.name
        except Exception as e:
            print "Exception:", e
            raise e

    def to_df(self):
        """
        returns a pandas DataFrame object based on parsed data from a
        Commodity object's HTML
        """
        try:
            df = pd.read_html(self.response)
            df = df[0]  # Ignore footer table
            if S.DBG_ICOM:
                df.to_csv(S.WORK_DIR + "/" + self.name + ".inf")
            price = df['Price'][0]
            # print self.name, type(price), price
            if math.isnan(price):
                # No result found
                return None
            df["Date"] = pd.to_datetime(df["Date"])
            df.insert(0, "Commodity", np.nan)
            df["Commodity"] = self.name
            df.insert(6, "Close", np.nan)
            df["Close"] = df["Price"]
            df.insert(7, "Volume", np.nan)

            if self.name.startswith('USD'):
                df['Volume'] = 0
            elif self.name.startswith('FTFBM'):
                df['Volume'] = df["Vol."]
            else:
                mp = {'K': ' * 10**3', 'M': ' * 10**6'}
                # vol = df['Vol.'][0]
                # print type(vol), vol
                df['Vol.'] = df['Vol.'].replace('-', '0.1K')
                df['Vol.'] = df['Vol.'].replace(0, '0.1K')   # replace all 0 vol with 100 shares
                '''
                Convert k to 1000 and m to 1000000
                Important: Can only support max 5 months of EOD to convert
                '''
                df["Volume"] = pd.eval(df["Vol."].replace(mp.keys(), mp.values(), regex=True).str.replace(r'[^\d\.\*]+', ''))

            df.drop('Price', axis=1, inplace=True)
            df.drop('Change %', axis=1, inplace=True)
            if 'Vol.' in df.columns:
                # FOREX has no "Vol." column
                df.drop('Vol.', axis=1, inplace=True)
            df.sort_values(by='Date', inplace=True)
        except ValueError as ve:
            df = 'ValueError'
            self.csverr = self.name + ": ValueError (No data for date range) " + ' (' + str(ve) + ')'
            if S.DBG_ICOM:
                with open(S.WORK_DIR + "value.err", 'ab') as f:
                    f.write('\n=============================\n')
                    f.write(self.name + "\n")
                    f.write(self.response)
        except Exception as e:
            # This happens when records being processed are larger than 3 months data,
            # try reducing the period
            if S.DBG_ICOM:
                with open(S.WORK_DIR + "value.err", 'ab') as f:
                    f.write('\n=============================\n')
                    f.write(self.name + "\n")
                    f.write(self.response)
            self.csverr = self.name + ":" + self.start + "," + self.end + ":" + str(e)
            df = 'Exception'
            # raise e

        return df


class InvestingQuote(Quote):
    def __init__(self, idmap, sname, last_date, end_date=getToday("%Y-%m-%d")):
        if last_date == end_date:
            self.csverr = sname + ": Skipped downloaded (" + last_date + ")"
            return None
        last_date = du.getNextDay(last_date)
        if last_date > end_date:
            self.csverr = sname + ": Invalid dates (" + last_date + "," + end_date + ")"
            return None
        # Do not download today's EOD if market is still open
        if end_date == getToday("%Y-%m-%d"):
            now = datetime.datetime.now()
            if sname.startswith('USD'):
                if now.hour > 22:
                    # US starts after 10pm Malaysia time
                    end_date = du.getYesterday("%Y-%m-%d")
            elif now.hour < 18:
                # only download today's EOD if it is after 6pm local time
                end_date = du.getYesterday("%Y-%m-%d")

        '''
        last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d").strftime('%m/%d/%Y')
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime('%m/%d/%Y')
        '''
        last_date = du.change2IcomDateFmt(last_date)
        end_date = du.change2IcomDateFmt(end_date)
        super(InvestingQuote, self).__init__(sname, last_date, end_date, idmap)
        self.response = self.scrape()
        # s0 = Quote(sname, last_date, end_date, idmap)
        if isinstance(self.response, unicode):
            s1 = self.to_df()
            if isinstance(s1, pd.DataFrame):
                s1.index.name = 'index'
                self.s1 = s1
                self.csverr = ''
                # s1.to_csv(OUTPUT_FILE, index=False, header=False)
                print self.name + ":", last_date
            elif s1 is None:
                self.csverr = self.name + ':Skipped no result'
            else:
                # Use csverr from to_df()
                return
        else:
            self.csverr = sname + ":" + self.response


def loadIdMap(klsemap='klse.idmap'):
    ID_MAPPING = {}
    try:
        with open(klsemap) as idmap:
            for line in idmap:
                name, var = line.partition("=")[::2]
                ID_MAPPING[name.strip()] = int(var)
            if S.DBG_ALL:
                print dict(ID_MAPPING.items()[0:3])
        '''
        with open("klse.txt") as f:
            for line in f:
                idmap = line.split(',')
                name = idmap[0]
                var = idmap[3]
                ID_MAPPING[name.strip()] = int(var)
            if S.DBG_ALL:
                print dict(ID_MAPPING.items()[0:10])
        '''
    except EnvironmentError:
        print "Missing idmap.ini file"
        sys.exit(1)
    except KeyError:
        print "loadIdMap KeyError:", name
        sys.exit(2)
    return ID_MAPPING


if __name__ == '__main__':
    # OUTPUT_FILE = sys.argv[1]
    idmap = loadIdMap()

    S.DBG_ALL = False
    S.DBG_ICOM = False
    WRITE_CSV = True
    S.RESUME_FILE = True

    '''
    stocks = 'ALAQAR,AMFIRST,ARREIT,ATRIUM,AXREIT,CAP,CLIQ,CLOUD,CSL,FOCUSP,GDB,GFM,GNB,HLCAP,ICAP,JMEDU,KINSTEL,MSPORTS,NPS,PARLO,PERDANA,PETONE,PINEAPP,QES,RALCO,SONA,TIMWELL,TWRREIT,WEGMANS,WINTONI,XINQUAN'
    '''
    stocks = ''
    klse = "../i3investor/klse.txt"

    if len(stocks) > 0:
        #  download only selected counters
        stocklist = formStocklist(stocks, klse)
    else:
        # Full download using klse.txt
        writeStocksListing = False
        if writeStocksListing:
            writeStocksListing()
        stocklist = loadKlseCounters(klse)

    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "Skip: ", shortname
            continue
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            rtn_code = 0
            OUTPUT_FILE = '../../data/investingcom/' + shortname + "." + stock_code + ".csv"
            TMP_FILE = OUTPUT_FILE + 'tmp'
            if S.RESUME_FILE:
                lastdt = getLastDate(OUTPUT_FILE)
                if len(lastdt) == 0:
                    # File is likely to be empty, hence scrape from beginning
                    lastdt = S.ABS_START
            else:
                lastdt = S.ABS_START
            enddt = getToday('%Y-%m-%d')
            print 'Scraping {0},{1}: lastdt={2}, End={3}'.format(
                shortname, stock_code, lastdt, enddt)
            eod = InvestingQuote(idmap, shortname, lastdt, enddt)
            if S.DBG_ALL:
                for item in eod:
                    print item
            if len(eod.getCsvErr()) > 0:
                print eod.getCsvErr()
                # If KeyError, counter not available in investing.com, try yahoo finance
                print "Scraping from yahoo: ", shortname
                cookie, crumb = getYahooCookie('https://uk.finance.yahoo.com/quote/AAPL/')
                q = YahooQuote(cookie, crumb, shortname, stock_code + ".KL", lastdt, enddt)
                if len(q.getCsvErr()) > 0:
                    st_code, st_reason = q.getCsvErr().split(":")
                    rtn_code = int(st_code)
                else:
                    if WRITE_CSV:
                        q.write_csv(TMP_FILE)
                    else:
                        print q
            elif isinstance(eod.response, unicode):
                dfEod = eod.to_df()
                if isinstance(dfEod, pd.DataFrame):
                    if S.DBG_ICOM:
                        print dfEod[:5]
                    if WRITE_CSV:
                        dfEod.index.name = 'index'
                        dfEod.to_csv(TMP_FILE, index=False, header=False)
                else:
                    print "ERR:" + dfEod + ": " + shortname + "," + lastdt
                    rtn_code = -2
            else:
                print "ERR:" + eod.response + "," + lastdt
                rtn_code = -1

            if rtn_code == 0:
                f = open(OUTPUT_FILE, "ab")
                ftmp = open(TMP_FILE, "r")
                f.write(ftmp.read())
                f.close()
                ftmp.close()
        else:
            print "ERR: Not found: ", shortname
