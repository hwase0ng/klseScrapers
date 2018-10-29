'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays=<cd>   Days to display on chart [default: 200]
    -d,--displaychart     Display chart, not save
    -l,--list=<clist>     List of counters (dhkmwM) to retrieve from config.json
    -b,--blocking=<bc>    Set MVP blocking count value [default: 1]
    -f,--filter           Switch ON MVP Divergence Matching filter [default: False]
    -t,--tolerance=<mt>   Set MVP matching tolerance value [default: 3]
    -p,--plotpeaks        Switch ON plotting peaks
    -D,--peaksdist=<pd>   Peaks distance [default: 20]
    -h,--help             This page

Created on Oct 16, 2018

@author: hwase0ng
'''

from common import retrieveCounters, loadCfg, formStocklist, \
    loadKlseCounters, match_approximate2, getSkipRows
from utils.dateutils import getDaysBtwnDates
from docopt import docopt
from matplotlib import pyplot as plt, dates as mdates
from pandas import read_csv
from peakutils import peak
import numpy as np
import operator
import settings as S


def getMpvDate(dfdate):
    mpvdt = str(dfdate.to_pydatetime()).split()
    return mpvdt[0]


def dfLoadMPV(counter, chartDays):
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


def indpeaks(cmpv, vector, threshold=0.1, dist=S.MVP_PEAKS_DISTANCE, factor=1):
    pIndexes = peak.indexes(np.array(vector),
                            thres=threshold / max(vector), min_dist=dist)
    nIndexes = peak.indexes(np.array(vector * -1),
                            thres=threshold * factor, min_dist=dist)
    if S.MVP_DIVERGENCE_MATCH_FILTER:
        newIndex = match_approximate2(pIndexes, nIndexes, 1, True, vector, cmpv)
        pIndexes, nIndexes = newIndex[0], newIndex[1]
    return pIndexes, nIndexes


def findpeaks(df, mh, ph, vh):
    cIndexesP, cIndexesN = indpeaks('C', df['close'], 0.2)
    mIndexesP, mIndexesN = indpeaks('M', df['M'], mh / 100, S.MVP_PEAKS_DISTANCE, -1)
    pIndexesP, pIndexesN = indpeaks('P', df['P'], ph * 0.01)
    vIndexesP, vIndexesN = indpeaks('V', df['V'], float(vh / 50) if vh > 20 else float(vh / 30))
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
    '''
    # Nested dictionary structure:
    # 1. Position indexes:
    #    posindex = {pos1: [xdate1, yval1], pos2: [xdate2, yval2], .... }
    # 2. Sequence indexes:
    #    seqindex = {0: [xdate1, yval1], 1: [xdate2, yval2], ... }
    '''
    posindex, seqindex = {}, {}
    for i, index in enumerate(indexes):
        x.append(getMpvDate(datesVector[index]))
        y.append(cmpvVector[index])
        posindex[index] = [x[-1], y[-1]]
        seqindex[i] = [getMpvDate(datesVector[index]), cmpvVector[index]]
    return x, y, posindex, seqindex


def plotpeaks(df, ax, cIP, cIN, cCP, cCN):
    ciP = cIP['C']
    ciN = cIN['C']
    miP = cIP['M']
    miN = cIN['M']
    piP = cIP['P']
    piN = cIN['P']
    viP = cIP['V']
    viN = cIN['V']
    cxp, cyp, ciP, sciP = locatepeaks(df['date'], df['close'], ciP)
    cxn, cyn, ciN, sciN = locatepeaks(df['date'], df['close'], ciN)
    mxp, myp, miP, smiP = locatepeaks(df['date'], df['M'], miP)
    mxn, myn, miN, smiN = locatepeaks(df['date'], df['M'], miN)
    pxp, pyp, piP, spiP = locatepeaks(df['date'], df['P'], piP)
    pxn, pyn, piN, spiN = locatepeaks(df['date'], df['P'], piN)
    vxp, vyp, viP, sviP = locatepeaks(df['date'], df['V'], viP)
    vxn, vyn, viN, sviN = locatepeaks(df['date'], df['V'], viN)

    # Nested dictionary structure:
    #   cIP = {'C': [[{pos1: [xdate1, yval1], pos2: [xdate2, yval2], ... ],
    #                [{0: [xdate1, yval1], 1: [xdate2, yval2], ... ]]}
    #          'M': [{pos1: [xdate1, yval1], pos2: [xdate2, yval2], ....
    #          'V': ...
    #          'P': ...
    cIP = {'C': [ciP, sciP], 'M': [miP, smiP], 'P': [piP, spiP], 'V': [viP, sviP]}
    cIN = {'C': [ciN, sciN], 'M': [miN, smiN], 'P': [piN, spiN], 'V': [viN, sviN]}

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

    return cIP, cIN, cCP, cCN


def formCmpvlines(cindexes, ccount):
    cmpvlist = sorted(ccount.items(), key=operator.itemgetter(1), reverse=True)
    cmpvlines = {}
    for i in range(len(cmpvlist) - 1):
        for j in range(i + 1, len(cmpvlist) - 1):
            if S.DBG_ALL:
                print i, j, cmpvlist[i][0], cmpvlist[j][0]
            cmpv = cindexes[cmpvlist[i][0]][0]
            poslist1 = list(cmpv.keys())
            cmpv = cindexes[cmpvlist[j][0]][0]
            poslist2 = list(cmpv.keys())
            cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = match_approximate2(
                sorted(poslist1), sorted(poslist2), S.MVP_DIVERGENCE_MATCH_TOLERANCE)
    '''
    cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = \
        np.in1d(cmpvindexes[cmpvlist[i][0]], cmpvindexes[cmpvlist[j][0]])
    Sample cmpvlines:
    'CP': array([ False, False, False, False, False, False, False, False, True, False, False,  True, False]),
    'CM': array([ False, False, False, False, False,  True, False, False, True, False, False, False, False]),
    'PM': array([ False,  True, False, False, False,  True, False, False])}
    '''
    return cmpvlines


def plotlines(axes, cmpvlines, pindexes, peaks):
    cmpv = {'C': 0, 'M': 1, 'P': 2, 'V': 3}
    colormap = {'C': 'b', 'M': 'darkorange', 'P': 'g', 'V': 'r'}
    for k, v in cmpvlines.iteritems():
        c1, c2 = v[0], v[1]
        if sum(val for val in c1) < 2:
            # no lines to draw if less than 2 matching points
            continue
        p1, p2 = [], []
        '''
        items = np.nonzero(v)[0]  # filters for all the Trues when using np.in1d()
        for val in items:
            item = pindexes[k[0]][val]
            xdate, yval = item[1], item[2]
            p1.append([xdate, yval])
            # p2's position is identified using p1's date value
            p2.append([xdate, dindexes[k[1]][xdate]])
        '''
        for i, pos in enumerate(c1):
            # parsing chart1 position index
            item = pindexes[k[0]][0][pos]
            xdate, yval = item[0], item[1]
            p1.append([xdate, yval])
            # parsing chart2 position index
            item = pindexes[k[1]][0][c2[i]]
            xdate, yval = item[0], item[1]
            p2.append([xdate, yval])
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
        for k2, v2 in pindexes[k[0]][1].iteritems():
            # parsing chart1 sequence index
            # k2 = seq, v2 = [date, pos]
            xlist1[v2[0]] = k2
            ylist1.append(v2[1])
        for k2, v2 in pindexes[k[1]][1].iteritems():
            # parsing chart2 sequence index
            # k2 = seq, v2 = [date, pos]
            xlist2[v2[0]] = k2
            ylist2.append(v2[1])
        for i in xrange(len(d1) - 1, 0, -1):
            # start from the back
            if (d1[i] > 0 and d2[i] < 0) or \
               (d1[i] < 0 and d2[i] > 0):
                '''
                divergence detected, filters non-sensible divergence
                   e.g. points too far apart,
                        too many higher/lower peaks in between points
                '''
                p1date1, p1date2 = p1x[i], p1x[i + 1]
                p1y1, p1y2 = p1y[i], p1y[i + 1]
                point1, point2 = xlist1[p1date1], xlist1[p1date2]
                c1y = np.array(ylist1[point1:point2])

                p2date1, p2date2 = p2x[i], p2x[i + 1]
                p2y1, p2y2 = p2y[i], p2y[i + 1]
                point1, point2 = xlist2[p2date1], xlist2[p2date2]
                c2y = np.array(ylist2[point1:point2])
                if S.DBG_ALL:
                    print p1date1, p1date2, min(p1y1, p1y2), max(p1y1, p1y2), c1y, peaks
                if peaks:
                    c1count = c1y[c1y > min(p1y1, p1y2)]
                    c2count = c2y[c2y > min(p2y1, p2y2)]
                    if max(len(c1count), len(c2count)) > S.MVP_DIVERGENCE_BLOCKING_COUNT:
                        if S.DBG_ALL:
                            print max(len(c1count), len(c2count)), c1y, c2y
                        continue
                    lstyle = ":" if d1[i] > 0 else "--"
                else:
                    c1count = c1y[c1y < max(p1y1, p1y2)]
                    c2count = c2y[c2y < max(p2y1, p2y2)]
                    if max(len(c1count), len(c2count)) > S.MVP_DIVERGENCE_BLOCKING_COUNT:
                        if S.DBG_ALL:
                            print max(len(c1count), len(c2count)), c1y, c2y
                        continue
                    lstyle = "--" if d1[i] > 0 else ":"
                axes[cmpv[k[0]]].annotate("", xy=(p1date1, p1y1), xycoords='data',
                                          xytext=(p1date2, p1y2),
                                          arrowprops=dict(arrowstyle="-", color=colormap[k[1]],
                                                          linestyle=lstyle,
                                                          connectionstyle="arc3,rad=0."),
                                          )
                axes[cmpv[k[1]]].annotate("", xy=(p2date1, p2y1), xycoords='data',
                                          xytext=(p2date2, p2y2),
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


def line_divergence(axes, cIP, cIN, cCP, cCN):
    cmpvlinesP = formCmpvlines(cIP, cCP)
    cmpvlinesN = formCmpvlines(cIN, cCN)
    plotlines(axes, cmpvlinesP, cIP, True)
    plotlines(axes, cmpvlinesN, cIN, False)
    del cIP
    del cIN
    del cCP
    del cCN


def mvpChart(counter, scode, chartDays, showchart=False):
    df, skiprow, fname = dfLoadMPV(counter, chartDays)
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

    axes = df.plot(x='date', figsize=(15, 7), subplots=True, grid=False)  # title=mpvdate + ': MPV Chart of ' + counter)
    # Disguise axis X label as title to save on chart space
    axes[3].set_xlabel("MPV Chart of " + counter + "." + scode + ": " + mpvdate, fontsize=12)
    ax1 = plt.gca().axes.get_xaxis()
    ax1.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.set_label_coords(0.84, -0.7)
    '''
    axlabel = ax1.get_label()
    axlabel.set_visible(False)
    '''

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

    plt.tight_layout()
    if showchart:
        plt.show()
    else:
        plt.savefig(fname)
    plt.close()


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    if args['--filter']:
        S.MVP_DIVERGENCE_MATCH_FILTER = True
    if args['--plotpeaks']:
        S.MVP_PLOT_PEAKS = False
    if args['--blocking']:
        S.MVP_DIVERGENCE_BLOCKING_COUNT = int(args['--blocking'])
    if args['--tolerance']:
        S.MVP_DIVERGENCE_MATCH_TOLERANCE = int(args['--tolerance'])
    if args['--peaksdist']:
        S.MVP_PEAKS_DISTANCE = int(args['--peaksdist'])
    if args['--chartdays']:
        chartDays = int(args['--chartdays'])

    global klse
    klse = "scrapers/i3investor/klse.txt"
    if args['COUNTER']:
        stocks = args['COUNTER'][0].upper()
    else:
        stocks = retrieveCounters(args['--list'])

    if len(stocks):
        stocklist = formStocklist(stocks, klse)
        if not len(stocklist):
            # Hack to bypass restriction on KLSE counters
            if len(stocks) == 1:
                stocklist[stocks] = 0
            else:
                stocks = stocks.split(',')
                for stock in stocks:
                    stocklist[stock] = 0
    else:
        stocklist = loadKlseCounters(klse)

    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "INF:Skip: ", shortname
            continue
        mvpChart(shortname, stocklist[shortname], chartDays, args['--displaychart'])
