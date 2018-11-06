'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays=<cd>     Days to display on chart [default: 200]
    -d,--displaychart       Display chart [default: False]
    -D,--debug              Enable debug mode [default: False]
    -l,--list=<clist>       List of counters (dhkmwM) to retrieve from config.json
    -b,--blocking=<bc>      Set MVP blocking count value [default: 1]
    -f,--filter             Switch ON MVP Divergence Matching filter [default: False]
    -s,--synopsis           Synopsis of MVP [default: False]
    -t,--tolerance=<mt>     Set MVP matching tolerance value [default: 3]
    -p,--plotpeaks          Switch ON plotting peaks [default: False]
    -P,--peaksdist=<pd>     Peaks distance [default: -1]
    -T,--threshold=<pt>     Peaks threshold [default: -1]
    -S,--simulation=<sim>   Simulate day to day changes with values "start.end.step"
    -h,--help               This page

Created on Oct 16, 2018

@author: hwase0ng
'''

from common import retrieveCounters, loadCfg, formStocklist, \
    loadKlseCounters, match_approximate2, getSkipRows
from docopt import docopt
from matplotlib import pyplot as plt, dates as mdates
from mvpsignals import scanSignals
from pandas import read_csv, Grouper
from peakutils import peak
from utils.dateutils import getDaysBtwnDates
from utils.fileutils import tail2, wc_line_count, grepN
import numpy as np
import operator
import settings as S
import traceback


def getMpvDate(dfdate):
    mpvdt = str(dfdate.to_pydatetime()).split()
    return mpvdt[0]


def dfLoadMPV(counter, chartDays, start=0):
    prefix = S.DATA_DIR + S.MVP_DIR
    incvs = prefix + counter + ".csv"
    if start > 0:
        prefix = prefix + "simulation/"
    outname = prefix + counter
    if start > 0:
        row_count = wc_line_count(incvs)
        if row_count < S.MVP_CHART_DAYS:
            skiprow = -1
        else:
            lines = tail2(incvs, start)
            heads = lines[:chartDays]
            incvs += "tmp"
            with open(incvs, 'wb') as f:
                for item in heads:
                    f.write("%s" % item)
            skiprow = 0
    else:
        skiprow, _ = getSkipRows(incvs, chartDays)

    if skiprow < 0:
        return None, skiprow, None
    # series = Series.from_csv(incvs, sep=',', parse_dates=[1], header=None)
    df = read_csv(incvs, sep=',', header=None, parse_dates=['date'],
                  skiprows=skiprow, usecols=['date', 'close', 'M', 'P', 'V'],
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    return df, skiprow, outname


def annotateMVP(df, axes, MVP, cond):
    if SYNOPSIS:
        df = df.reset_index()
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
        if DBG_ALL:
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

    if mvHighest == 0:
        mvHighest = df.iloc[df[MVP].idxmax()][MVP]
    return mvHighest


def indpeaks(cmpv, vector, threshold, dist, factor=1):
    if vector is None or not len(vector) or threshold == 0:
        return [], []
    pIndexes = peak.indexes(np.array(vector),
                            thres=threshold / max(vector), min_dist=dist)
    nIndexes = peak.indexes(np.array(vector * -1),
                            thres=threshold * factor, min_dist=dist)
    if MVP_DIVERGENCE_MATCH_FILTER:
        newIndex = match_approximate2(pIndexes, nIndexes, 1, True, vector, cmpv)
        pIndexes, nIndexes = newIndex[0], newIndex[1]
    return pIndexes, nIndexes


def findpeaks(df, cmpvHL, dwfm=-1):
    if SYNOPSIS:
        df = df.reset_index()
    cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow = cmpvHL
    # -1 = day chart, 0 = weekly, 1 = forth nightly, 2 = monthly
    if MVP_PEAKS_DISTANCE > 0:
        pdist = MVP_PEAKS_DISTANCE
    else:
        pdist = 3 if dwfm < 0 else \
            5 if dwfm == 0 else \
            4 if dwfm == 1 else \
            3
    if MVP_PEAKS_THRESHOLD > 0:
        cpt = MVP_PEAKS_THRESHOLD
        mpt = MVP_PEAKS_THRESHOLD
        ppt = MVP_PEAKS_THRESHOLD
        vpt = MVP_PEAKS_THRESHOLD
    else:
        cpt = ((cHigh - cLow) / 2) / 10
        mpt = ((mHigh - mLow) / 2) / 50
        ppt = ((pHigh - pLow) / 2) / 100
        vpt = ((vHigh - vLow) / 2) / 20
    cIndexesP, cIndexesN = indpeaks('C', df['close'], cpt, pdist, -1)
    mIndexesP, mIndexesN = indpeaks('M', df['M'], mpt, pdist, 1 if mLow > 0 else -1)
    pIndexesP, pIndexesN = indpeaks('P', df['P'], ppt, pdist, 1 if pLow > 0 else -1)
    vIndexesP, vIndexesN = indpeaks('V', df['V'], vpt, pdist)
    if DBG_ALL:
        print pdist, cpt, mpt, ppt, vpt
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
    ciP, ciN = cIP['C'], cIN['C']
    miP, miN = cIP['M'], cIN['M']
    piP, piN = cIP['P'], cIN['P']
    viP, viN = cIP['V'], cIN['V']
    if SYNOPSIS:
        df = df.reset_index()
    cxp, cyp, ciP, sciP = locatepeaks(df['date'], df['close'], ciP)
    cxn, cyn, ciN, sciN = locatepeaks(df['date'], df['close'], ciN)
    mxp, myp, miP, smiP = locatepeaks(df['date'], df['M'], miP)
    mxn, myn, miN, smiN = locatepeaks(df['date'], df['M'], miN)
    pxp, pyp, piP, spiP = locatepeaks(df['date'], df['P'], piP)
    pxn, pyn, piN, spiN = locatepeaks(df['date'], df['P'], piN)
    vxp, vyp, viP, sviP = locatepeaks(df['date'], df['V'], viP)
    vxn, vyn, viN, sviN = locatepeaks(df['date'], df['V'], viN)

    # Being used by synopsis chart signal scanning
    cmpvXP = [cxp, mxp, pxp, vxp]
    cmpvXN = [cxn, mxn, pxn, vxn]
    cmpvYP = [cyp, myp, pyp, vyp]
    cmpvYN = [cyn, myn, pyn, vyn]
    cmpvXYPN = [cmpvXP, cmpvXN, cmpvYP, cmpvYN]

    # Nested dictionary structure:
    #   cIP = {'C': [[{pos1: [xdate1, yval1], pos2: [xdate2, yval2], ... ],
    #                [{0: [xdate1, yval1], 1: [xdate2, yval2], ... ]]}
    #          'M': [{pos1: [xdate1, yval1], pos2: [xdate2, yval2], ....
    #          'V': ...
    #          'P': ...
    cIP = {'C': [ciP, sciP], 'M': [miP, smiP], 'P': [piP, spiP], 'V': [viP, sviP]}
    cIN = {'C': [ciN, sciN], 'M': [miN, smiN], 'P': [piN, spiN], 'V': [viN, sviN]}

    if MVP_PLOT_PEAKS:
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

    return cIP, cIN, cCP, cCN, cmpvXYPN


def formCmpvlines(cindexes, ccount):
    cmpvlist = sorted(ccount.items(), key=operator.itemgetter(1), reverse=True)
    cmpvlines = {}
    for i in range(len(cmpvlist) - 1):
        for j in range(i + 1, len(cmpvlist) - 1):
            if DBG_ALL:
                print i, j, cmpvlist[i][0], cmpvlist[j][0]
            cmpv = cindexes[cmpvlist[i][0]][0]
            poslist1 = list(cmpv.keys())
            cmpv = cindexes[cmpvlist[j][0]][0]
            poslist2 = list(cmpv.keys())
            cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = match_approximate2(
                sorted(poslist1), sorted(poslist2), MVP_DIVERGENCE_MATCH_TOLERANCE)
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
                if DBG_ALL:
                    print p1date1, p1date2, min(p1y1, p1y2), max(p1y1, p1y2), c1y, peaks
                if peaks:
                    c1count = c1y[c1y > min(p1y1, p1y2)]
                    c2count = c2y[c2y > min(p2y1, p2y2)]
                    if max(len(c1count), len(c2count)) > MVP_DIVERGENCE_BLOCKING_COUNT:
                        if DBG_ALL:
                            print max(len(c1count), len(c2count)), c1y, c2y
                        continue
                    lstyle = ":" if d1[i] > 0 else "--"
                else:
                    c1count = c1y[c1y < max(p1y1, p1y2)]
                    c2count = c2y[c2y < max(p2y1, p2y2)]
                    if max(len(c1count), len(c2count)) > MVP_DIVERGENCE_BLOCKING_COUNT:
                        if DBG_ALL:
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


def line_divergence(axes, cIP, cIN, cCP, cCN, cmpvXYPN):
    cmpvlinesP = formCmpvlines(cIP, cCP)
    cmpvlinesN = formCmpvlines(cIN, cCN)
    plotlines(axes, cmpvlinesP, cIP, True)
    plotlines(axes, cmpvlinesN, cIN, False)
    del cIP
    del cIN
    del cCP
    del cCN
    return cmpvXYPN


def mvpChart(counter, scode, chartDays=S.MVP_CHART_DAYS, showchart=False):
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
    if DBG_ALL:
        print(df.tail(10))
        print type(mpvdate), mpvdate
        # print df.index.get_loc(df.iloc[chartDays].name)

    figsize = (10, 5) if showchart else (15, 7)
    axes = df.plot(x='date', figsize=figsize, subplots=True, grid=False)  # title=mpvdate + ': MPV Chart of ' + counter)
    # Disguise axis X label as title to save on chart space
    title = "MPV Chart of " + counter + "." + scode + ": " + mpvdate
    axes[3].set_xlabel(title, fontsize=12)
    axes[3].figure.canvas.set_window_title(title)
    ax1 = plt.gca().axes.get_xaxis()
    ax1.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.set_label_coords(0.84, -0.7)
    '''
    axlabel = ax1.get_label()
    axlabel.set_visible(False)
    '''

    cHigh = df.iloc[df['close'].idxmax()]['close']
    cLow = df.iloc[df['close'].idxmin()]['close']
    mHigh = annotateMVP(df, axes[1], "M", 10)
    mLow = df.iloc[df['M'].idxmin()]['M']
    pHigh = df.iloc[df['P'].idxmax()]['P']
    pLow = df.iloc[df['P'].idxmin()]['P']
    vHigh = annotateMVP(df, axes[3], "V", 24)
    vLow = df.iloc[df['V'].idxmin()]['V']
    cmpvHL = [cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow]
    try:
        line_divergence(axes, *plotpeaks(df, axes, *findpeaks(df, cmpvHL)))
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
        plt.savefig(fname + ".png")
    plt.close()


def getSynopsisDFs(counter, scode, chartDays, start=0):
    fname = ""
    try:
        df, skiprows, fname = dfLoadMPV(counter, chartDays, start)
        if skiprows >= 0:
            dfw = df.groupby([Grouper(key='date', freq='W')]).mean()
            dff = df.groupby([Grouper(key='date', freq='2W')]).mean()
            dfm = df.groupby([Grouper(key='date', freq='M')]).mean()

            if DBG_ALL:
                print len(dfw), len(dff), len(dfm)
                print dfw[-3:]
                print dff[-3:]
                print dfm[-3:]
    except Exception as e:
        print "Dataframe exception: ", counter, fname
        print e
        return None, None, None, None, None, None
    finally:
        lasttrxn = []
        if df is not None:
            lastTrxnDate = getMpvDate(df.iloc[-1]['date'])
            lastClosingPrice = float(df.iloc[-1]['close'])
            lastTrxnM = float(df.iloc[-1]['M'])
            lastTrxnP = float(df.iloc[-1]['P'])
            lastTrxnV = float(df.iloc[-1]['V'])
            lasttrxn = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
            del df
        else:
            return None, None, None, None, None, None

    print " Synopsis:", counter, lastTrxnDate
    dflist = {}
    dflist[0] = dfw.fillna(0)
    dflist[1] = dff.fillna(0)
    dflist[2] = dfm.fillna(0)

    title = "MPV Synopsis of " + counter + " (" + scode + "): " + \
        lastTrxnDate + " (" + str(chartDays) + " days)"

    return dflist, title, fname, lasttrxn


def numsFromDate(counter, datestr):
    prefix = S.DATA_DIR + S.MVP_DIR
    incvs = prefix + counter + ".csv"
    row_count = wc_line_count(incvs)
    linenum = grepN(incvs, datestr)  # e.g. 2018-10-30
    start = row_count - linenum + S.MVP_CHART_DAYS + 100
    nums = str(start) + "," + str(start + 1) + ",1"
    return nums.split(',')


def mvpSynopsis(counter, scode, chartDays=S.MVP_CHART_DAYS, showchart=False, simulation=""):
    def doPlotting(outname):
        '''
        # sharex is causing the MONTH column to be out of alignment
        # Adding/removing records does not help to rectify this issue
        lastdfm = dfm.index[len(dfm) - 1]
        lastdff = dff.index[len(dff) - 1]
        lastdfw = dfw.index[len(dfw) - 1]
        if lastdfw > lastdfm or lastdff > lastdfm:
            new_date = datetools.to_datetime('2018-11-30')
            newrow = DataFrame(dfm[-1:].values, index=[new_date], columns=dfm.columns)
            dfm = dfm.append(newrow)
            print dfm[-3:]
        '''

        figsize = (10, 5) if showchart else (15, 7)
        fig, axes = plt.subplots(4, 3, figsize=figsize, sharex=False, num=title)
        fig.suptitle(title)
        fig.canvas.set_window_title(title)
        hlList, pnList = plotSynopsis(dflist, axes)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        if showchart:
            plt.show()
        else:
            if scanSignals(counter, outname, hlList, pnList, lasttrxn):
                if len(nums) > 0:
                    outname = outname + "-" + lasttrxn[0]
                plt.savefig(outname + "-synopsis.png")
        plt.close()

    if simulation is None or len(simulation) == 0:
        nums = []
        dflist, title, fname, lasttrxn = getSynopsisDFs(counter, scode, chartDays)
        if dflist is None:
            return
        doPlotting(fname)
    else:
        nums = simulation.split(",") if "," in simulation else numsFromDate(counter, simulation)
        start, end, step = int(nums[0]), int(nums[1]), int(nums[2])
        while True:
            dflist, title, fname, lasttrxn = getSynopsisDFs(counter, scode, chartDays, start)
            if dflist is None:
                continue
            doPlotting(fname)
            if start > end:
                start -= step
            else:
                break


def plotSynopsis(dflist, axes):
    for i in range(3):
        dflist[i]['close'].plot(ax=axes[0, i], color='b', label='C')
        dflist[i]['M'].plot(ax=axes[1, i], color='orange', label='M')
        dflist[i]['P'].plot(ax=axes[2, i], color='g', label='P')
        dflist[i]['V'].plot(ax=axes[3, i], color='r', label='V')

    axes[0, 2].legend(loc="upper left")
    axes[1, 2].legend(loc="upper left")
    axes[2, 2].legend(loc="upper left")
    axes[3, 2].legend(loc="upper left")
    axes[3, 0].set_xlabel("Week")
    axes[3, 1].set_xlabel("Forthnight")
    axes[3, 2].set_xlabel("Month")

    '''
    mHigh = annotateMVP(dfw, axes[1, 1], "M", 7)
    vHigh = annotateMVP(dfw, axes[3, 1], "V", 20)
    pHigh = dfw.loc[dfw['P'].idxmax()]['P']
    '''
    hlList, pnList = [], []
    try:
        for i in range(3):
            ax = {}
            for j in range(4):
                if j != 3:
                    axlabel = axes[j, i].get_xaxis()
                    axlabel.set_visible(False)
                '''
                axes[j, i].xaxis.grid(True)

                mHigh = annotateMVP(dflist[i], axes[j, i], "M", 7)
                vHigh = annotateMVP(dflist[i], axes[j, i], "V", 20)
                pHigh = dflist[i].loc[dflist[i]['P'].idxmax()]['P']

                # ax[0] = axes[0, 0], axes[0, 1], axes[0, 2]
                # ax[1] = axes[1, 0], axes[1, 1], axes[1, 2]
                # ax[2] = axes[2, 0], axes[2, 1], axes[2, 2]
                # ax[3] = axes[3, 0], axes[3, 1], axes[3, 2]
                '''
                ax[j] = axes[j, i]

            cHigh = dflist[i].loc[dflist[i]['close'].idxmax()]['close']
            cLow = dflist[i].loc[dflist[i]['close'].idxmin()]['close']
            mHigh = dflist[i].loc[dflist[i]['M'].idxmax()]['M']
            mLow = dflist[i].loc[dflist[i]['M'].idxmin()]['M']
            pHigh = dflist[i].loc[dflist[i]['P'].idxmax()]['P']
            pLow = dflist[i].loc[dflist[i]['P'].idxmin()]['P']
            vHigh = dflist[i].loc[dflist[i]['V'].idxmax()]['V']
            vLow = dflist[i].loc[dflist[i]['V'].idxmin()]['V']

            cmpvHL = [cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow]
            hlList.append(cmpvHL)
            cmpvXYPN = line_divergence(ax, *plotpeaks(dflist[i], ax,
                                                      *findpeaks(dflist[i], cmpvHL, i)))
            pnList.append(cmpvXYPN)
    except Exception as e:
        # just print error and continue without the required line in chart
        print 'line divergence exception:', i
        print e
    try:
        for i in range(3):
            axes[1, i].axhline(5, color='k', linestyle=':')
            if mHigh > 6:
                axes[1, i].axhline(10, color='r', linestyle=':')
            if pHigh > 4:
                axes[1, i].axhline(5, color='k', linestyle=':')
                if pHigh > 10:
                    axes[1, i].axhline(10, color='r', linestyle=':')
            if vHigh < 0.5:
                axes[3, i].axhline(0, color='k', linestyle=':')
            elif vHigh > 20:
                axes[3, i].axhline(25, color='k', linestyle=':')
    except Exception as e:
        # just print error and continue without the required line in chart
        print 'axhline exception:'
        print e

    return hlList, pnList


def globals_from_args(args):
    global MVP_PLOT_PEAKS, MVP_PEAKS_DISTANCE, MVP_PEAKS_THRESHOLD
    global MVP_DIVERGENCE_MATCH_FILTER, MVP_DIVERGENCE_BLOCKING_COUNT, MVP_DIVERGENCE_MATCH_TOLERANCE
    global klse, DBG_ALL, SYNOPSIS
    klse = "scrapers/i3investor/klse.txt"

    DBG_ALL = True if args['--debug'] else False
    MVP_PLOT_PEAKS = True if args['--plotpeaks'] else False
    MVP_PEAKS_DISTANCE = -1 if not args['--peaksdist'] else float(args['--peaksdist'])
    MVP_PEAKS_THRESHOLD = -1 if not args['--threshold'] else float(args['--threshold'])
    MVP_DIVERGENCE_MATCH_FILTER = True if args['--filter'] else False
    MVP_DIVERGENCE_BLOCKING_COUNT = int(args['--blocking']) if args['--blocking'] else 1
    MVP_DIVERGENCE_MATCH_TOLERANCE = int(args['--tolerance']) if args['--tolerance'] else 3
    SYNOPSIS = True if args['--synopsis'] else False
    chartDays = int(args['--chartdays']) if args['--chartdays'] else S.MVP_CHART_DAYS
    if SYNOPSIS and chartDays == S.MVP_CHART_DAYS:
        # daily charting is defaulted to 200, add 100 for synopsis charting
        chartDays += 100
    if args['COUNTER']:
        stocks = args['COUNTER'][0].upper()
    else:
        stocks = retrieveCounters(args['--list'])

    return stocks, chartDays


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    stocks, chartDays = globals_from_args(args)

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
        try:
            if SYNOPSIS:
                mvpSynopsis(shortname, stocklist[shortname], chartDays,
                            args['--displaychart'], args['--simulation'])
            else:
                mvpChart(shortname, stocklist[shortname], chartDays,
                         args['--displaychart'])
        except Exception:
            traceback.print_exc()
