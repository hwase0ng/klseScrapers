'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays N    Days to display on chart (defaulted 200 in settings.py)
    -d,--displaychart   Display chart, not save
    -p,--portfolio      Select portfolio from config.json
    -w,--watchlist      Select watchlist from config.json
    -h,--help           This page

Created on Oct 16, 2018

@author: hwase0ng
'''

from common import getCounters, loadCfg, formStocklist, loadKlseCounters
from utils.dateutils import getDaysBtwnDates
from docopt import docopt
from pandas import read_csv
from matplotlib import pyplot as plt, dates as mdates
from mvp import getSkipRows
import numpy as np
from peakutils import peak
import settings as S


def getMpvDate(dfdate):
    mpvdt = str(dfdate.to_pydatetime()).split()
    return mpvdt[0]


def annotateMVP(df, axes, MVP, cond):
    idxMV = df.index[df[MVP] > cond]
    if len(idxMV) == 0:
        return 0
    group_mvp = []
    dHigh = ""
    mvHigh = 0
    mvHighest = 0
    for i in range(1, len(idxMV) + 1):
        j = i * -1
        if i > len(df.index) or idxMV[j] < 0:
            break
        mpvdate = getMpvDate(df.iloc[idxMV[j]]['date'])
        mv = df.iloc[idxMV[j]][MVP]
        mv = int(mv)
        if S.DBG_ALL:
            print j, mpvdate, mv
        if i <= len(idxMV):
            group_mvp.append([mpvdate[5:], str(mv)])
            if mv > mvHigh:
                mvHigh = mv
                dHigh = mpvdate
                mid = len(group_mvp) - 1
            if i < len(idxMV):
                next_mpvdate = getMpvDate(df.iloc[idxMV[j - 1]]['date'])
                if getDaysBtwnDates(next_mpvdate, mpvdate) < 8:
                    continue
        if len(group_mvp) == 0:
            mvHigh = mv
            dHigh = mpvdate
            group_mvp.append([mpvdate[5:], str(mv)])

        strMVP = ""
        if len(group_mvp) > 4:
            strMVP = "<".join(group_mvp[-1]) + "> " + \
                "<".join(group_mvp[mid]) + "> " + "<".join(group_mvp[0]) + ">"
        else:
            group_mvp.reverse()
            for k in range(len(group_mvp)):
                strMVP += "> " + "<".join(group_mvp[k])
                if (k + 1) < len(group_mvp) and (k + 1) % 2 == 0:
                    strMVP += ">\n"
            strMVP = "   " + strMVP[2:] + ">"
        group_mvp = []

        try:
            axes.annotate(strMVP, size=8, xycoords='data', xy=(dHigh, mvHigh),
                          xytext=(10, 10), textcoords='offset points',
                          arrowprops=dict(arrowstyle='-|>'))
        except Exception as e:
            print 'axes.annotate', MVP, cond
            print e
        finally:
            if mvHigh > mvHighest:
                mvHighest = mvHigh
            dHigh = ""
            mvHigh = 0

    return mvHighest


def dfFromCsv(counter, chartDays=S.MVP_CHART_DAYS):
    fname = S.DATA_DIR + S.MVP_DIR + counter
    fname2 = S.DATA_DIR + S.MVP_DIR + "c" + counter
    csvfl = fname + ".csv"
    skiprow, _ = getSkipRows(csvfl, chartDays)
    if skiprow < 0:
        return None, skiprow, None
    # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
    df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['date'],
                  skiprows=skiprow, usecols=['date', 'close', 'M', 'P', 'V'],
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    return df, skiprow, fname2


def indpeaks(vector, threshold=0.1, dist=5):
    pIndexes = peak.indexes(np.array(vector),
                            thres=threshold / max(vector), min_dist=dist)
    nIndexes = peak.indexes(np.array(vector * -1),
                            thres=threshold / max(vector), min_dist=dist)
    return pIndexes, nIndexes


def findpeaks(df, mh, ph, vh):
    cIndexesP, cIndexesN = indpeaks(df['close'])
    mIndexesP, mIndexesN = indpeaks(df['M'])
    pIndexesP, pIndexesN = indpeaks(df['P'], ph * -1)
    vIndexesP, vIndexesN = indpeaks(df['V'])
    if S.DBG_ALL:
        print('C Peaks are: %s, %s' % (cIndexesP, cIndexesN))
        print('M Peaks are: %s, %s' % (mIndexesP, mIndexesN))
        print('P Peaks are: %s, %s' % (pIndexesP, pIndexesN))
        print('V Peaks are: %s, %s' % (vIndexesP, vIndexesN))
    return cIndexesP, cIndexesN, mIndexesP, mIndexesN, pIndexesP, pIndexesN, vIndexesP, vIndexesN


def locatepeaks(datesVector, cmpvVector, indexes):
    if len(indexes) <= 0:
        return None, None
    x = []
    y = []
    for i in indexes:
        x.append(getMpvDate(datesVector[i]))
        y.append(cmpvVector[i])
    return x, y


def plotpeaks(df, ax, ciP, ciN, miP, miN, piP, piN, viP, viN, plotp=True):
    cxp, cyp = locatepeaks(df['date'], df['close'], ciP)
    cxn, cyn = locatepeaks(df['date'], df['close'], ciN)
    mxp, myp = locatepeaks(df['date'], df['M'], miP)
    mxn, myn = locatepeaks(df['date'], df['M'], miN)
    pxp, pyp = locatepeaks(df['date'], df['P'], piP)
    pxn, pyn = locatepeaks(df['date'], df['P'], piN)
    vxp, vyp = locatepeaks(df['date'], df['V'], viP)
    vxn, vyn = locatepeaks(df['date'], df['V'], viN)

    if plotp:
        if cxp is not None:
            ax[0].scatter(x=cxp, y=cyp, marker='.', c='r', edgecolor='b')
        if cxn is not None:
            ax[0].scatter(x=cxn, y=cyn, marker='.', c='b', edgecolor='r')
        if mxp is not None:
            ax[1].scatter(x=mxp, y=myp, marker='.', c='r', edgecolor='b')
        if mxn is not None:
            ax[1].scatter(x=mxn, y=myn, marker='.', c='b', edgecolor='r')
        if pxp is not None:
            ax[2].scatter(x=pxp, y=pyp, marker='.', c='r', edgecolor='b')
        if pxn is not None:
            ax[2].scatter(x=pxn, y=pyn, marker='.', c='b', edgecolor='r')
        if vxp is not None:
            ax[3].scatter(x=vxp, y=vyp, marker='.', c='r', edgecolor='b')
        if vxn is not None:
            ax[3].scatter(x=vxn, y=vyn, marker='.', c='b', edgecolor='r')

    return cxp, cyp, cxn, cyn, mxp, myp, myp, myn, pxp, pyp, pxn, pyn, vxp, vyp, vyp, vyn


def mvpChart(counter, chartDays=S.MVP_CHART_DAYS, showchart=False):
    df, skiprow, fname2 = dfFromCsv(counter, chartDays)
    if skiprow < 0 or len(df.index) <= 0:
        print "No chart for ", counter, skiprow
        return
    print "Charting: ", counter
    mpvdate = getMpvDate(df.iloc[-1]['date'])
    '''
    if len(df.index) >= abs(chartDays):
        firstidx = df.index.get_loc(df.iloc[chartDays].name)
    else:
    '''
    if S.DBG_ALL:
        print(df.tail(10))
        print type(mpvdate), mpvdate
        # print df.index.get_loc(df.iloc[chartDays].name)

    # axes = df[chartDays:].plot(x='date', figsize=(15, 7), subplots=True, grid=False,
    axes = df.plot(x='date', figsize=(15, 7), subplots=True, grid=False,
                   title=mpvdate + ': MPV Chart of ' + counter)
    ax1 = plt.gca().axes.get_xaxis()
    ax1.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    axlabel = ax1.get_label()
    axlabel.set_visible(False)

    mHigh = annotateMVP(df, axes[1], "M", 10)
    vHigh = annotateMVP(df, axes[3], "V", 24)
    pHigh = df.iloc[df['P'].idxmax()]['P']
    try:
        plotpeaks(df, axes, *findpeaks(df, mHigh, pHigh, vHigh))
        if mHigh > 6:
            axes[1].axhline(10, color='r', linestyle='--')
        else:
            axes[1].axhline(-5, color='r', linestyle='--')
        axes[1].axhline(5, color='k', linestyle='--')
        axes[2].axhline(0, color='k', linestyle='--')
        if vHigh > 20:
            axes[3].axhline(25, color='k', linestyle='--')
    except Exception as e:
        # just print error and continue without the required line in chart
        print 'axhline'
        print e

    if showchart:
        plt.show()
    else:
        plt.savefig(fname2 + ".png")
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
        mvpChart(shortname, chartDays, args['--displaychart'])
