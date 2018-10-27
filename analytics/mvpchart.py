'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays N    Days to display on chart (defaulted 200 in settings.py)
    -d,--displaychart   Display chart, not save
    -k,--klse           Select KLSE related from settings.py
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
    csvfl = fname + ".csv"
    skiprow, _ = getSkipRows(csvfl, chartDays)
    if skiprow < 0:
        return None, skiprow, None
    # series = Series.from_csv(csvfl, sep=',', parse_dates=[1], header=None)
    df = read_csv(csvfl, sep=',', header=None, index_col=False, parse_dates=['date'],
                  skiprows=skiprow, usecols=['date', 'close', 'M', 'P', 'V'],
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    return df, skiprow, fname + ".png"


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
        return None, None, None, None
    x, y = [], []
    posindex, dateindex = {}, {}
    for i, index in enumerate(indexes):
        x.append(getMpvDate(datesVector[index]))
        y.append(cmpvVector[index])
        posindex[i] = [index, x[-1], y[-1]]
        dateindex[x[-1]] = y[-1]
    return x, y, posindex, dateindex


def plotpeaks(df, ax, cIP, cIN, cCP, cCN):
    ciP = cIP['C']
    ciN = cIN['C']
    miP = cIP['M']
    miN = cIN['M']
    piP = cIP['P']
    piN = cIN['P']
    viP = cIP['V']
    viN = cIN['V']
    cxp, cyp, ciP, dciP = locatepeaks(df['date'], df['close'], ciP)
    cxn, cyn, ciN, dciN = locatepeaks(df['date'], df['close'], ciN)
    mxp, myp, miP, dmiP = locatepeaks(df['date'], df['M'], miP)
    mxn, myn, miN, dmiN = locatepeaks(df['date'], df['M'], miN)
    pxp, pyp, piP, dpiP = locatepeaks(df['date'], df['P'], piP)
    pxn, pyn, piN, dpiN = locatepeaks(df['date'], df['P'], piN)
    vxp, vyp, viP, dviP = locatepeaks(df['date'], df['V'], viP)
    vxn, vyn, viN, dviN = locatepeaks(df['date'], df['V'], viN)

    # Nested dictionary structure:
    #   cIP = {'C': {0: [pos1, xdate1, yval1], 1: [pos2, xdate2, yval2]}, ....
    #          'M': {0: [pos1, xdate1, yval1], 1: [pos2, xdate2, yval2]}, ....
    #          'V': {0: [pos1, xdate1, yval1], 1: [pos2, xdate2, yval2]}, ....
    #          'P': {0: [pos1, xdate1, yval1], 1: [pos2, xdate2, yval2]}, ....
    #  dcIP = {'C': {xdate1: yval1, xdate2: yval2, ...
    #          'M': {xdate1: yval1, xdate2: yval2, ...
    cIP = {'C': ciP, 'M': miP, 'P': piP, 'V': viP}
    cIN = {'C': ciN, 'M': miN, 'P': piN, 'V': viN}
    dcIP = {'C': dciP, 'M': dmiP, 'P': dpiP, 'V': dviP}
    dcIN = {'C': dciN, 'M': dmiN, 'P': dpiN, 'V': dviN}

    if S.MVP_PLOT_PEAKS:
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

    return cIP, cIN, dcIP, dcIN, cCP, cCN


def formCmpvlines(cindexes, ccount):
    cmpvlist = sorted(ccount.items(), key=operator.itemgetter(1), reverse=True)
    cmpvlines = {}
    for i in range(len(cmpvlist) - 1):
        for j in range(i + 1, len(cmpvlist) - 1):
            if S.DBG_ALL:
                print i, j, cmpvlist[i][0], cmpvlist[j][0]
            list1, list2 = [], []
            cmpv = cindexes[cmpvlist[i][0]]
            # v = [pos, date, yval], v[0] yields pos
            for _, v in cmpv.iteritems():
                list1.append(v[0])
            cmpv = cindexes[cmpvlist[j][0]]
            for _, v in cmpv.iteritems():
                list2.append(v[0])
            cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = np.in1d(list1, list2)
    '''
    Sample cmpvlines:
    'CP': array([ False, False, False, False, False, False, False, False, True, False, False,  True, False]),
    'CM': array([ False, False, False, False, False,  True, False, False, True, False, False, False, False]),
    'PM': array([ False,  True, False, False, False,  True, False, False])}
    '''
    return cmpvlines


def plotlines(axes, cmpvlines, pindexes, dindexes, peaks):
    cmpv = {'C': 0, 'M': 1, 'P': 2, 'V': 3}
    colormap = {'C': 'b', 'M': 'darkorange', 'P': 'g', 'V': 'r'}
    for k, v in cmpvlines.iteritems():
        if sum(val for val in v) < 2:
            # no lines to draw if less than 2 matching points
            continue
        p1, p2 = [], []
        items = np.nonzero(v)[0]  # filters for all the Trues
        for val in items:
            item = pindexes[k[0]][val]
            xdate, yval = item[1], item[2]
            p1.append([xdate, yval])
            # p2's position is identified using p1's date value
            p2.append([xdate, dindexes[k[1]][xdate]])
        p3 = np.transpose(np.asarray(p1, dtype=object))
        p4 = np.transpose(np.asarray(p2, dtype=object))
        p1x, p1y = list(p3[0]), list(p3[1])
        p2x, p2y = list(p4[0]), list(p4[1])
        # compute the difference between neighboring y elements
        d1 = list(np.ediff1d(p1y))
        d2 = list(np.ediff1d(p2y))
        # new list for quick comparison between points
        xlist1, xlist2 = {}, {}
        ylist1, ylist2 = [], []
        for k2, v2 in pindexes[k[0]].iteritems():
            xlist1[v2[1]] = k2
            ylist1.append(v2[2])
        for k2, v2 in pindexes[k[1]].iteritems():
            xlist2[v2[1]] = k2
            ylist2.append(v2[2])
        for i in xrange(len(d1) - 1, 0, -1):
            # start from the back
            if (d1[i] > 0 and d2[i] < 0) or \
               (d1[i] < 0 and d2[i] > 0):
                '''
                divergence detected, filters non-sensible divergence
                   e.g. points too far apart,
                        too many higher/lower peaks in between points
                '''
                date1, date2 = p1x[i], p1x[i + 1]
                y1, y2 = p1y[i], p1y[i + 1]
                point1, point2 = xlist1[date1], xlist1[date2]
                c1y = np.array(ylist1[point1:point2])
                c2y = np.array(ylist2[point1:point2])
                if S.DBG_ALL:
                    print date1, date2, min(y1, y2), max(y1, y2), c1y, peaks
                if peaks:
                    c1count = c1y[c1y > min(y1, y2)]
                    c2count = c2y[c2y > min(y1, y2)]
                    if max(len(c1count), len(c2count)) > S.MVP_DIVERGENCE_COUNT:
                        continue
                    lstyle = "-" if d1[i] > 0 else "--"
                else:
                    c1count = c1y[c1y < max(y1, y2)]
                    c2count = c2y[c2y < max(y1, y2)]
                    if max(len(c1count), len(c2count)) > S.MVP_DIVERGENCE_COUNT:
                        continue
                    lstyle = "--" if d1[i] > 0 else "-"
                axes[cmpv[k[0]]].annotate("", xy=(date1, y1), xycoords='data',
                                          xytext=(date2, y2),
                                          arrowprops=dict(arrowstyle="-", color=colormap[k[1]],
                                                          linestyle=lstyle,
                                                          connectionstyle="arc3,rad=0."),
                                          )
                date1, date2 = p2x[i], p2x[i + 1]
                y1, y2 = p2y[i], p2y[i + 1]
                axes[cmpv[k[1]]].annotate("", xy=(date1, y1), xycoords='data',
                                          xytext=(date2, y2),
                                          arrowprops=dict(arrowstyle="-", color=colormap[k[0]],
                                                          linestyle=lstyle,
                                                          connectionstyle="arc3,rad=0."),
                                          )
                '''
                axes[cmpv[k[0]]].plot([p1x[i], p1x[i + 1]],
                                      [p1y[i], p1y[i + 1]])
                axes[cmpv[k[1]]].plot([p2x[i], p2x[i + 1]],
                                      [p2y[i], p2y[i + 1]])
                '''


def line_divergence(axes, cIP, cIN, dcIP, dcIN, cCP, cCN):
    cmpvlinesP = formCmpvlines(cIP, cCP)
    cmpvlinesN = formCmpvlines(cIN, cCN)
    plotlines(axes, cmpvlinesP, cIP, dcIP, True)
    plotlines(axes, cmpvlinesN, cIN, dcIN, False)
    del cIP
    del cIN
    del dcIP
    del dcIN
    del cCP
    del cCN


def mvpChart(counter, chartDays=S.MVP_CHART_DAYS, showchart=False):
    df, skiprow, fname = dfFromCsv(counter, chartDays)
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
        plt.savefig(fname)
    plt.close()


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    global klse
    klse = "scrapers/i3investor/klse.txt"
    stocks = getCounters(args['COUNTER'], args['--klse'],
                         args['--portfolio'], args['--watchlist'], False)
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
