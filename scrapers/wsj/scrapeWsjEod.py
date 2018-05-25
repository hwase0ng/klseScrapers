'''
Created on May 2, 2018

@author: hwase0ng
'''

import sys
from common import formStocklist, loadKlseCounters, appendCsv
import settings as S
import utils.dateutils as du
import requests
import pandas as pd
import numpy as np
import datetime
import math
from utils.dateutils import getLastDate, getToday, getDaysBtwnDates


class Quote(object):
    """An object that holds price data for a particular commodity, across a given date range. """
    BASE_URL = "https://quotes.wsj.com/ajax/historicalprices/4/"

    def __init__(self, name, start, end):
        self.csverr = ''
        self.name = name
        days = getDaysBtwnDates(start, end)
        self.days = days
        last_date = du.change2IcomDateFmt(start)
        end_date = du.change2IcomDateFmt(end)
        self.start = last_date
        self.end = end_date
        self.response = ''
        self.df = ''
        # self.response = self.scrape()

    def getCsvErr(self):
        return self.csverr

    def write_csv(self, filename):
        self.df.to_csv(filename, index=False, header=False)

    def scrape(self):
        try:
            data = {
                "MODE_VIEW": "page",
                "ticker": self.name,
                "country": "MY",
                "exchange": "XKLS",
                "instrumentType": "STOCK",
                "num_rows": self.days,
                "range_days": self.days,
                "startDate": self.start,
                "endDate": self.end,
                "_": "1525415904500"
            }

            EOD_URL = self.BASE_URL + self.name
            print self.BASE_URL
            print data

            r = requests.post(self.BASE_URL, data=data, headers=S.HEADERS)
            print r.status_code
            assert(r.status_code == 200)
            return r.text
        except KeyError:
            if S.DBG_ALL:
                print "KeyError: ", self.name
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


class scrapeHistoricalPrice(Quote):
    def __init__(self, sname, last_date, end_date=getToday("%Y-%m-%d")):
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

        super(scrapeHistoricalPrice, self).__init__(sname, last_date, end_date)
        '''
        last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d").strftime('%m/%d/%Y')
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime('%m/%d/%Y')
        '''
        self.response = self.scrape()
        # s0 = Quote(sname, last_date, end_date
        if isinstance(self.response, unicode):
            df = self.to_df()
            if isinstance(df, pd.DataFrame):
                df.index.name = 'index'
                self.df = df
                self.csverr = ''
                # df.to_csv(OUTPUT_FILE, index=False, header=False)
                print self.name + ":", last_date
            elif df is None:
                self.csverr = self.name + ':Skipped no result'
            else:
                # Use csverr from to_df()
                return
        else:
            self.csverr = sname + ":" + self.response


if __name__ == '__main__':
    # OUTPUT_FILE = sys.argv[1]
    S.DBG_ALL = False
    WRITE_CSV = True
    S.RESUME_FILE = False

    '''
    stocks = 'ALAQAR,AMFIRST,ARREIT,ATRIUM,AXREIT,CAP,CLIQ,CLOUD,CSL,FOCUSP,GDB,GFM,GNB,HLCAP,ICAP,JMEDU,KINSTEL,MSPORTS,NPS,PARLO,PERDANA,PETONE,PINEAPP,QES,RALCO,SONA,TIMWELL,TWRREIT,WEGMANS,WINTONI,XINQUAN'
    '''
    stocks = '3A'
    klse = "klse.txt"

    if len(stocks) > 0:
        #  download only selected counters
        stocklist = formStocklist(stocks, klse)
    else:
        # Full download using klse.txt
        writeKlseTxt = False
        if writeKlseTxt:
            writeStocksListing()
        stocklist = loadKlseCounters(klse)

    for shortname in sorted(stocklist.iterkeys()):
        stock_code = stocklist[shortname]
        if len(stock_code) == 0:
            print "ERR: Not found: ", shortname
            continue

        rtn_code = 0
        OUTPUT_FILE = '../../data/wsj/' + shortname + "." + stock_code + ".csv"
        TMP_FILE = OUTPUT_FILE + 'tmp'
        if S.RESUME_FILE:
            lastdt = getLastDate(OUTPUT_FILE)
            if len(lastdt) == 0:
                # File is likely to be empty, hence scrape from beginning
                lastdt = S.ABS_START
        else:
            lastdt = S.ABS_START
            lastdt = '2018-05-01'
        enddt = getToday('%Y-%m-%d')
        print 'Scraping {0},{1}: lastdt={2}, End={3}'.format(
            shortname, stock_code, lastdt, enddt)

        eod = scrapeHistoricalPrice(shortname, lastdt, enddt)

        if len(eod.getCsvErr()) > 0:
            print eod.getCsvErr()
        elif isinstance(eod.response, unicode):
            dfEod = eod.to_df()
            if isinstance(dfEod, pd.DataFrame):
                if WRITE_CSV:
                    dfEod.index.name = 'index'
                    dfEod.to_csv(TMP_FILE, index=False, header=False)
            else:
                print "ERR:" + dfEod + ": " + shortname + "," + lastdt
                rtn_code = -2
        else:
            print "ERR:" + eod.response + "," + lastdt
            rtn_code = -1

        appendCsv(rtn_code, OUTPUT_FILE)
        print "ERR: Not found: ", shortname
