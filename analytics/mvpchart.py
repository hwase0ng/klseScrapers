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
from matplotlib import pyplot as plt, dates as mdates
from mvp import getSkipRows
from pandas import read_csv
from peakutils import peak
import numpy as np
import operator
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
    if S.DBG_ALL:
        print threshold, max(vector), threshold / max(vector), vector[0], vector[0] * -1
    pIndexes = peak.indexes(np.array(vector),
                            thres=threshold / max(vector), min_dist=dist)
    nIndexes = peak.indexes(np.array(vector * -1),
                            thres=threshold, min_dist=dist)
    return pIndexes, nIndexes


def findpeaks(df, mh, ph, vh):
    cIndexesP, cIndexesN = indpeaks(df['close'])
    mIndexesP, mIndexesN = indpeaks(df['M'])
    pIndexesP, pIndexesN = indpeaks(df['P'], ph * -1)
    vIndexesP, vIndexesN = indpeaks(df['V'], float(vh / 5) if vh > 20 else float(vh / 3))
    if S.DBG_ALL:
        print('C Peaks are: %s, %s' % (cIndexesP, cIndexesN))
        print('M Peaks are: %s, %s' % (mIndexesP, mIndexesN))
        print('P Peaks are: %s, %s' % (pIndexesP, pIndexesN))
        print('V Peaks are: %s, %s' % (vIndexesP, vIndexesN))
    cmpvIndexesP = {'C': cIndexesP, 'M': mIndexesP, 'P': pIndexesP, 'V': vIndexesP}
    cmpvIndexesN = {'C': cIndexesN, 'M': mIndexesN, 'P': pIndexesN, 'V': vIndexesN}
    clenP, mlenP, plenP, vlenP = len(cIndexesP), len(mIndexesP), len(pIndexesP), len(vIndexesP)
    clenN, mlenN, plenN, vlenN = len(cIndexesN), len(mIndexesN), len(pIndexesN), len(vIndexesN)
    cmpvCountP = {'C': clenP, 'M': mlenP, 'P': plenP, 'V': vlenP}
    cmpvCountN = {'C': clenN, 'M': mlenN, 'P': plenN, 'V': vlenN}
    return cmpvIndexesP, cmpvIndexesN, cmpvCountP, cmpvCountN


def locatepeaks(datesVector, cmpvVector, indexes):
    if len(indexes) <= 0:
        return None, None
    x = []
    y = []
    for i in indexes:
        x.append(getMpvDate(datesVector[i]))
        y.append(cmpvVector[i])
    return x, y


def plotpeaks(df, ax, cIP, cIN, cCP, cCN, plotp=True):
    ciP = cIP['C']
    ciN = cIN['C']
    miP = cIP['M']
    miN = cIN['M']
    piP = cIP['P']
    piN = cIN['P']
    viP = cIP['V']
    viN = cIN['V']
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

    return cIP, cIN, cCP, cCN, \
        cxp, cyp, cxn, cyn, mxp, myp, mxn, myn, \
        pxp, pyp, pxn, pyn, vxp, vyp, vxn, vyn


def formCmpvlines(cindexes, ccount):
    cmpvlist = sorted(ccount.items(), key=operator.itemgetter(1), reverse=True)
    cmpvlines = {}
    for i in range(len(cmpvlist) - 1):
        for j in range(i + 1, len(cmpvlist) - 1):
            if S.DBG_ALL:
                print i, j, cmpvlist[i][0], cmpvlist[j][0]
            cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = \
                np.in1d(cindexes[cmpvlist[i][0]], cindexes[cmpvlist[j][0]])
    '''
    Sample cmpvlines:
    'CP': array([ False, False, False, False, False, False, False, False, True, False, False,  True, False]),
    'CM': array([ False, False, False, False, False,  True, False, False, True, False, False, False, False]),
    'PM': array([ False,  True, False, False, False,  True, False, False])}
    '''
    return cmpvlines


def markPoint(k, pos, cx, cy, mx, my, px, py, vx, vy):
    p = [cx[pos], cy[pos]] if k == 'C' else \
        [mx[pos], my[pos]] if k == 'M' else \
        [px[pos], py[pos]] if k == 'P' else \
        [vx[pos], vy[pos]]
    return p


def plotlines(axes, cmpvlines, cx, cy, mx, my, px, py, vx, vy, color):
    cmpv = {'C': 0, 'M': 1, 'P': 2, 'V': 3}
    for k, v in cmpvlines.iteritems():
        if sum(val for val in v) < 2:
            continue
        p1, p2 = [], []
        items = np.nonzero(v)[0]
        for val in items:
            p1.append(markPoint(k[0], val, cx, cy, mx, my, px, py, vx, vy))
            val = cx.index(p1[-1][0]) if k[1] == 'C' else \
                mx.index(p1[-1][0]) if k[1] == 'M' else \
                px.index(p1[-1][0]) if k[1] == 'P' else \
                vx.index(p1[-1][0])
            if val < 0:
                print "Error:", p1[-1][0]
                return False
            p2.append(markPoint(k[1], val, cx, cy, mx, my, px, py, vx, vy))
        p3 = np.transpose(np.asarray(p1, dtype=object))
        p4 = np.transpose(np.asarray(p2, dtype=object))
        p1x = list(p3[0])
        p2x = list(p4[0])
        p1y = list(p3[1])
        p2y = list(p4[1])
        d1 = list(np.ediff1d(p1y))
        d2 = list(np.ediff1d(p2y))
        for i in xrange(len(d1) - 1, 0, -1):
            # start from the back
            if (d1[i] > 0 and d2[i] < 0) or \
               (d1[i] < 0 and d2[i] > 0):
                # divergence detected
                if color == 'r':
                    lstyle = "-" if d1[i] > 0 else "--"
                else:
                    lstyle = "--" if d1[i] > 0 else "-"
                axes[cmpv[k[0]]].annotate("", xy=(p1x[i], p1y[i]),
                                          xycoords='data',
                                          xytext=(p1x[i + 1], p1y[i + 1]),
                                          arrowprops=dict(arrowstyle="-", color=color,
                                                          linestyle=lstyle,
                                                          connectionstyle="arc3,rad=0."),
                                          )
                axes[cmpv[k[1]]].annotate("", xy=(p2x[i], p2y[i]),
                                          xycoords='data',
                                          xytext=(p2x[i + 1], p2y[i + 1]),
                                          arrowprops=dict(arrowstyle="-", color=color,
                                                          linestyle=lstyle,
                                                          connectionstyle="arc3,rad=0."),
                                          )
                '''
                axes[cmpv[k[0]]].plot([p1x[i], p1x[i + 1]],
                                      [p1y[i], p1y[i + 1]])
                axes[cmpv[k[1]]].plot([p2x[i], p2x[i + 1]],
                                      [p2y[i], p2y[i + 1]])
                '''


def line_divergence(axes, cIP, cIN, cCP, cCN,
                    cxp, cyp, cxn, cyn, mxp, myp, mxn, myn,
                    pxp, pyp, pxn, pyn, vxp, vyp, vxn, vyn):
    cmpvlinesP = formCmpvlines(cIP, cCP)
    cmpvlinesN = formCmpvlines(cIN, cCN)
    plotlines(axes, cmpvlinesP, cxp, cyp, mxp, myp, pxp, pyp, vxp, vyp, 'r')
    plotlines(axes, cmpvlinesN, cxn, cyn, mxn, myn, pxn, pyn, vxn, vyn, 'g')


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
    if mHigh == 0:
        mHigh = df.iloc[df['M'].idxmax()]['M']
    vHigh = annotateMVP(df, axes[3], "V", 24)
    if vHigh == 0:
        vHigh = df.iloc[df['V'].idxmax()]['V']
    pHigh = df.iloc[df['P'].idxmax()]['P']
    try:
        line_divergence(axes,
                        *plotpeaks(df, axes,
                                   *findpeaks(df, mHigh, pHigh, vHigh)))
    except Exception as e:
        # just print error and continue without the required line in chart
        print 'line divergence exception:'
        print e
    try:
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
        print 'axhline exception:'
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
