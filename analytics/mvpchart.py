'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays N  Days to display on chart
    -p,--portfolio    Select portfolio from config.json
    -w,--watchlist    Select watchlist from config.json
    -h,--help         This page

Created on Oct 16, 2018

@author: hwase0ng
'''

from common import getCounters, loadCfg, formStocklist, loadKlseCounters
from docopt import docopt
from pandas import read_csv
from matplotlib import pyplot
import settings as S


def mvpChart(counter):
        csvfl = S.DATA_DIR + "MVP/mvp-" + counter + ".csv"
        # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
        df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['Date'],
                      names=['Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                             'Total Vol', 'Total Price', 'DayB4 Motion', 'M', 'V', 'P'],
                      usecols=['Date', 'M', 'V', 'P'])
        # df.set_index('Date', drop=True, inplace=True)
        if S.DBG_ALL:
            print(df[-10:])
        df[chartDays:].plot(x='Date', figsize=(12, 6))
        pyplot.show()


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    global klse
    klse = "scrapers/i3investor/klse.txt"
    stocks = getCounters(args['COUNTER'], args['--portfolio'], args['--watchlist'], False)
    if len(stocks):
        stocklist = formStocklist(stocks, klse)
    else:
        S.DBG_YAHOO = True
        stocklist = loadKlseCounters(klse)

    global chartDays
    if args['--chartdays']:
        chartDays = int(args['--chartdays']) * -1
    else:
        chartDays = S.MVP_CHART_DAYS * -1

    for shortname in sorted(stocklist.iterkeys()):
        mvpChart(shortname)
