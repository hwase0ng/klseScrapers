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
from utils.dateutils import getDaysBtwnDates
from docopt import docopt
from pandas import read_csv
from matplotlib import pyplot as plt
import settings as S


def getMpvDate(dfdate):
    mpvdt = str(dfdate.to_pydatetime()).split()
    return mpvdt[0]


def mvpChart(counter):
        fname = S.DATA_DIR + "mpv/mpv-" + counter
        csvfl = fname + ".csv"
        # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
        df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['date'],
                      names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                             'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'],
                      usecols=['date', 'close', 'M', 'P', 'V'])
        # df.set_index('Date', drop=True, inplace=True)
        mpvdate = getMpvDate(df.iloc[-1]['date'])
        idxM = df.index[df['M'] > 10]
        idxV = df.index[df['V'] > 24]
        firstidx = df.index.get_loc(df.iloc[chartDays].name)
        if S.DBG_ALL:
            print(df.tail(10))
            print type(mpvdate), mpvdate
            print idxV[-5:]
            print df.index.get_loc(df.iloc[chartDays].name)

        axes = df[chartDays:].plot(x='date', figsize=(15, 7), subplots=True, grid=False,
                                   title=mpvdate + ': MPV Chart of ' + counter)
        ax1 = plt.gca().axes.get_xaxis()
        axlabel = ax1.get_label()
        axlabel.set_visible(False)
        axes[1].axhline(10, color='k', linestyle='--')
        axes[2].axhline(0, color='k', linestyle='--')
        axes[3].axhline(25, color='k', linestyle='--')

        group_motion = []
        for i in range(1, len(idxM)):
            j = i * -1
            if idxM[j] < firstidx:
                break
            mpvdate = getMpvDate(df.iloc[idxM[j]]['date'])
            motion = df.iloc[idxM[j]]['M']
            if S.DBG_ALL:
                print j, mpvdate, motion
            if i + 1 < len(idxM):
                next_mpvdate = getMpvDate(df.iloc[idxM[j - 1]]['date'])
                if getDaysBtwnDates(next_mpvdate, mpvdate) < 5:
                    group_motion.append([mpvdate[5:], str(motion)])
                    continue
                else:
                    group_motion.append([mpvdate[5:], str(motion)])
            else:
                group_motion.append([mpvdate[5:], str(motion)])

            strMotion = ""
            group_motion.reverse()
            for k in range(len(group_motion)):
                strMotion += "> " + "<".join(group_motion[k])
                if (k + 1) < len(group_motion) and (k + 1) % 3 == 0:
                    strMotion += ">\n"
            group_motion = []
            strMotion = strMotion[2:] + ">"
            xyx = mpvdate[:5] + strMotion[-10:-4]
            xyy = int(strMotion[-3:-1])
            axes[1].annotate(strMotion, size=8, xycoords='data', xy=(xyx, xyy),
                             xytext=(10, 10), textcoords='offset points',
                             arrowprops=dict(arrowstyle='-|>'))
        for i in range(1, len(idxV)):
            j = i * -1
            if idxV[j] < firstidx:
                break
            mpvdate = getMpvDate(df.iloc[idxV[j]]['date'])
            vol = df.iloc[idxV[j]]['V']
            if S.DBG_ALL:
                print j, mpvdate, vol
            axes[3].annotate(mpvdate[5:] + "(" + str(vol) + ")",
                             xycoords='data', xy=(mpvdate, vol),
                             xytext=(10, 10), textcoords='offset points',
                             arrowprops=dict(arrowstyle='-|>'))
        plt.show()
        # plt.savefig(fname + ".png")
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
