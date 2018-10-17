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
from matplotlib import pyplot as plt
import settings as S


def mvpChart(counter):
        fname = S.DATA_DIR + "mpv/mpv-" + counter
        csvfl = fname + ".csv"
        # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
        df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['date'],
                      names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                             'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'],
                      usecols=['date', 'close', 'M', 'P', 'V'])
        # df.set_index('Date', drop=True, inplace=True)
        mvpdate = df.iloc[-1]['date']
        mvpdt = str(mvpdate.to_pydatetime()).split()
        if S.DBG_ALL:
            print(df.tail(10))
            print type(mvpdate), mvpdate
            print type(mvpdt), mvpdt
        axes = df[chartDays:].plot(x='date', figsize=(15, 7), subplots=True, grid=False,
                                   title=mvpdt[0] + ': MPV Chart of ' + counter)
        ax1 = plt.gca().axes.get_xaxis()
        axlabel = ax1.get_label()
        axlabel.set_visible(False)
        axes[1].axhline(10, color='k')
        axes[2].axhline(0, color='k')
        axes[3].axhline(25, color='k')
        # plt.show()
        plt.savefig(fname + ".png")
        plt.close()


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
