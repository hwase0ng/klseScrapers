'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays N  Days to display on chart (defaulted 200 in settings.py)
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
from mvp import getSkipRows
import settings as S


def getMpvDate(dfdate):
    mpvdt = str(dfdate.to_pydatetime()).split()
    return mpvdt[0]


def mvpChart(counter, chartDays=S.MVP_CHART_DAYS):
    print "Charting: ", counter
    fname = S.DATA_DIR + "mpv/mpv-" + counter
    csvfl = fname + ".csv"
    skiprow = getSkipRows(csvfl, chartDays)
    # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
    df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['date'],
                  skiprows=skiprow, usecols=['date', 'close', 'M', 'P', 'V'],
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    if len(df.index) <= 0:
        return
    mpvdate = getMpvDate(df.iloc[-1]['date'])
    idxM = df.index[df['M'] > 10]
    idxV = df.index[df['V'] > 24]
    '''
    if len(df.index) >= abs(chartDays):
        firstidx = df.index.get_loc(df.iloc[chartDays].name)
    else:
    '''
    firstidx = 0
    if S.DBG_ALL:
        print(df.tail(10))
        print type(mpvdate), mpvdate
        print idxV[-5:]
        # print df.index.get_loc(df.iloc[chartDays].name)

    # axes = df[chartDays:].plot(x='date', figsize=(15, 7), subplots=True, grid=False,
    axes = df.plot(x='date', figsize=(15, 7), subplots=True, grid=False,
                   title=mpvdate + ': MPV Chart of ' + counter)
    ax1 = plt.gca().axes.get_xaxis()
    axlabel = ax1.get_label()
    axlabel.set_visible(False)
    try:
        axes[1].axhline(10, color='r', linestyle='--')
        axes[1].axhline(5, color='k', linestyle='--')
        axes[2].axhline(0, color='k', linestyle='--')
        axes[3].axhline(25, color='k', linestyle='--')
    except Exception as e:
        # just print error and continue without required line in chart
        print 'axhline'
        print e

    group_motion = []
    for i in range(1, len(idxM) + 1):
        j = i * -1
        if i > len(df.index) or idxM[j] < firstidx:
            break
        mpvdate = getMpvDate(df.iloc[idxM[j]]['date'])
        motion = df.iloc[idxM[j]]['M']
        if S.DBG_ALL:
            print j, mpvdate, motion
        if i < len(idxM):
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
            if (k + 1) < len(group_motion) and (k + 1) % 2 == 0:
                strMotion += ">\n"
        group_motion = []
        strMotion = strMotion[2:] + ">"
        # xyx = mpvdate[:5] + strMotion[-10:-4]
        # xyy = int(strMotion[-3:-1])
        if len(strMotion) < 11:
            strM = strMotion
        else:
            strM = strMotion[-11:]
        idxVstart = strM.index('<')
        try:
            idxVend = strM.index('.')
        except Exception:
            idxVend = len(strM) - 1
        xyx = mpvdate[:5] + strM[idxVstart - 5: idxVstart]
        xyy = int(strM[idxVstart + 1: idxVend])

        try:
            axes[1].annotate(strMotion, size=8, xycoords='data', xy=(xyx, xyy),
                             xytext=(10, 10), textcoords='offset points',
                             arrowprops=dict(arrowstyle='-|>'))
        except Exception as e:
            print 'axes[1].annotate'
            print e
            pass
    group_volume = []
    for i in range(1, len(idxV) + 1):
        j = i * -1
        if idxV[j] < firstidx:
            break
        mpvdate = getMpvDate(df.iloc[idxV[j]]['date'])
        vol = df.iloc[idxV[j]]['V']
        vol = int(vol)
        if S.DBG_ALL:
            print j, mpvdate, vol
        if i < len(idxV):
            next_mpvdate = getMpvDate(df.iloc[idxV[j - 1]]['date'])
            if getDaysBtwnDates(next_mpvdate, mpvdate) < 5:
                group_volume.append([mpvdate[5:], str(vol)])
                continue
            else:
                group_volume.append([mpvdate[5:], str(vol)])
        else:
            group_volume.append([mpvdate[5:], str(vol)])

        strVolume = ""
        group_volume.reverse()
        for k in range(len(group_volume)):
            strVolume += "> " + "<".join(group_volume[k])
            if (k + 1) < len(group_volume) and (k + 1) % 2 == 0:
                strVolume += ">\n"
        group_volume = []
        strVolume = strVolume[2:] + ">"
        if len(strVolume) < 13:
            strvol = strVolume
        else:
            strvol = strVolume[-13:]
        idxVstart = strvol.index('<')
        idxVend = len(strvol) - 1
        xyx = mpvdate[:5] + strvol[idxVstart - 5: idxVstart]
        xyy = int(strvol[idxVstart + 1: idxVend])

        try:
            axes[3].annotate(strVolume,  # mpvdate[5:] + "(" + str(vol) + ")",
                             xycoords='data', xy=(xyx, xyy),  # xy=(mpvdate, vol),
                             xytext=(10, 10), textcoords='offset points',
                             size=8, arrowprops=dict(arrowstyle='-|>'))
        except Exception as e:
            print 'axes[1].annotate'
            print e
            pass
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
        stocklist = loadKlseCounters(klse)

    if args['--chartdays']:
        chartDays = int(args['--chartdays'])
    else:
        chartDays = S.MVP_CHART_DAYS

    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "INF:Skip: ", shortname
            continue
        mvpChart(shortname, chartDays)
