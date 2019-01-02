'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -S,--simulation=<sim>   Simulate day to day changes with values "start.end.step" e.g. 600,300,2
                            Also accepts dates in the form of "DATE1:DATE2:STEP"; e.g. 2018-10-01 or 2018-01-02:2018-07-20:5
    -s,--synopsis           Synopsis of MVP [default: False]
    -m,--pmaps              pattern maps (not to be used with -s option) [default: False]
    -o,--ohlc               OHLC chart (not to be used with -s option) [default: False]
    -C,--concurrency        Concurrency On/Off (use when debugging) [default: False]
    -c,--chartdays=<cd>     Days to display on chart [default: 600]
    -d,--displaychart       Display chart [default: False]
    -D,--debug=(dbgopt)     Enable debug mode (A)ll, (p)attern charting, (s)ignal, (u)nit test input generation
    -e,--datadir=<dd>       Use data directory provided

    -w,--weekly             Include weekly columns else month only [default: False]
    -l,--list=<clist>       List of counters (dhkmwM) to retrieve from config.json
    -b,--blocking=<bc>      Set MVP blocking count value [default: 1]
    -p,--plotpeaks          Switch ON plotting peaks [default: False]
    -t,--tolerance=<mt>     Set MVP matching tolerance value [default: 3]
    -P,--peaksdist=<pd>     Peaks distance [default: -1]
    -T,--threshold=<pt>     Peaks threshold [default: -1]
    -f,--filter             Switch ON MVP Divergence Matching filter [default: False]
    -h,--help               This page

Created on Oct 16, 2018

@author: hwase0ng
'''

from common import retrieveCounters, loadCfg, formStocklist, \
    loadKlseCounters, match_approximate2, getSkipRows, matchdates
from docopt import docopt
from matplotlib import pyplot as plt, dates as mdates
from mpl_finance import candlestick_ohlc
from multiprocessing import Process, cpu_count
from mvpsignals import scanSignals
from pandas import read_csv, Grouper
from peakutils import peak
from utils.dateutils import getDaysBtwnDates, pdTimestamp2strdate, pdDaysOffset,\
    weekFormatter
from utils.fileutils import tail2, wc_line_count, grepN, mergefiles,\
    purgeOldFiles
import numpy as np
import operator
import os
import settings as S
import traceback


def dfLoadMPV(counter, chartDays, start=0):
    prefix = S.DATA_DIR + S.MVP_DIR
    incsv = prefix + counter + ".csv"
    if start > 0:
        prefix = prefix + "simulation/"
    outname = prefix + "synopsis/" + counter
    if start > 0:
        row_count = wc_line_count(incsv)
        if row_count < S.MVP_CHART_DAYS:
            skiprow = -1
        else:
            lines = tail2(incsv, start)
            # heads = lines[:chartDays] if SYNOPSIS else lines
            incsv += "tmp"
            with open(incsv, 'wb') as f:
                for item in lines:
                    f.write("%s" % item)
            skiprow = 0
    else:
        skiprow, row_count = getSkipRows(incsv, chartDays)

    if skiprow < 0 or row_count <= 0:
        print "File not available:", incsv
        return None, skiprow, None
    # series = Series.from_csv(incsv, sep=',', parse_dates=[1], header=None)
    if OHLC:
        usecols = ['date', 'open', 'high', 'low', 'close', 'volume', 'M', 'P', 'V']
    else:
        usecols = ['date', 'close', 'V', 'M', 'P']
    df = read_csv(incsv, sep=',', header=None, parse_dates=['date'], skiprows=skiprow, usecols=usecols,
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    return df, skiprow, outname


def dfGetDates(df, start, end):
    dfmpv = df[(df['date'] >= start) & (df['date'] <= end)]
    dfmpv = dfmpv.reset_index()
    return dfmpv


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
        mpvdate = pdTimestamp2strdate(df.iloc[idxMV[j]]['date'])
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
                next_mpvdate = pdTimestamp2strdate(df.iloc[idxMV[j - 1]]['date'])
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
    try:
        pIndexes = peak.indexes(np.array(vector),
                                thres=threshold / max(vector), min_dist=dist)
        nIndexes = peak.indexes(np.array(vector * -1),
                                thres=threshold * factor, min_dist=dist)
        if MVP_DIVERGENCE_MATCH_FILTER:
            newIndex = match_approximate2(pIndexes, nIndexes, 1, True, vector, cmpv)
            pIndexes, nIndexes = newIndex[0], newIndex[1]
    except Exception as e:
        print e
        print cmpv
    return pIndexes, nIndexes


def findpeaks(df, cmpvHL, weekly=False, dwfm=-1):
    if SYNOPSIS:
        df = df.reset_index()
    cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow = cmpvHL
    # -1 = day chart, 0 = weekly, 1 = forth nightly, 2 = monthly
    if MVP_PEAKS_DISTANCE > 0:
        pdist = MVP_PEAKS_DISTANCE
    else:
        if weekly:
            pdist = 3 if dwfm < 0 else \
                5 if dwfm == 0 else \
                4 if dwfm == 1 else \
                1  # 2018-11-30 was 3 but changed for PETRONM 2016-08-02 and DUFU 2012-05-22
        else:
            pdist = 3 if dwfm < 0 else 1
    if MVP_PEAKS_THRESHOLD > 0:
        cpt = MVP_PEAKS_THRESHOLD
        mpt = MVP_PEAKS_THRESHOLD
        ppt = MVP_PEAKS_THRESHOLD
        vpt = MVP_PEAKS_THRESHOLD
    else:
        cpt = ((cHigh - cLow) / 2) / 10
        mpt = ((mHigh - mLow) / 2) / 8   # 2018-11-30 was 50 but changed for PETRONM 2016-08-02
        ppt = ((pHigh - pLow) / 2) / 10
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
        y3 = float("{:.3f}".format(cmpvVector[index]))
        x.append(pdTimestamp2strdate(datesVector[index]))
        y.append(y3)
        posindex[index] = [x[-1], y[-1]]
        seqindex[i] = [pdTimestamp2strdate(datesVector[index]), cmpvVector[index]]
    return x, y, posindex, seqindex


def plotpeaks(df, ax, cIP, cIN, cCP, cCN):
    ciP, ciN = cIP['C'], cIN['C']
    miP, miN = cIP['M'], cIN['M']
    piP, piN = cIP['P'], cIN['P']
    viP, viN = cIP['V'], cIN['V']
    if SYNOPSIS:
        df = df.reset_index()
    if OHLC:
        cxp, cyp, ciP, sciP = None, None, None, None
        cxn, cyn, ciN, sciN = None, None, None, None
    else:
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
        '''
        if vxp is not None:
            ax[1].scatter(x=vxp, y=vyp, marker='.', c='r', edgecolor='b')
        if vxn is not None:
            ax[1].scatter(x=vxn, y=vyn, marker='.', c='b', edgecolor='r')
        '''
        if mxp is not None:
            ax[2].scatter(x=mxp, y=myp, marker='.', c='r', edgecolor='b')
        if mxn is not None:
            ax[2].scatter(x=mxn, y=myn, marker='.', c='b', edgecolor='r')
        if pxp is not None:
            ax[3].scatter(x=pxp, y=pyp, marker='.', c='r', edgecolor='b')
        if pxn is not None:
            ax[3].scatter(x=pxn, y=pyn, marker='.', c='b', edgecolor='r')

    return cIP, cIN, cCP, cCN, cmpvXYPN


def formCmpvlines(cindexes, ccount):
    del cindexes['V'], ccount['V']
    cmpvlist = sorted(ccount.items(), key=operator.itemgetter(1), reverse=True)
    cmpvlines = {}
    for i in range(len(cmpvlist)):
        for j in range(i + 1, len(cmpvlist)):
            if DBG_ALL:
                print i, j, cmpvlist[i][0], cmpvlist[j][0]
            cmpv = cindexes[cmpvlist[i][0]][0]
            if cmpv is None:
                continue
            poslist1 = list(cmpv.keys())
            cmpv = cindexes[cmpvlist[j][0]][0]
            if cmpv is None:
                continue
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
    divdict = {}
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
        divcount = drawlines(axes, k, peaks, pindexes, p1x, p2x, p1y, p2y)
        if divcount > 0:
            divdict[k] = divcount
    return divdict


def annotatelines(axes, k, lstyle, p1date1, p1date2, p2date1, p2date2, p1y1, p1y2, p2y1, p2y2):
    cmpv = {'C': 0, 'V': 1, 'M': 2, 'P': 3}
    colormap = {'C': 'b', 'M': 'darkorange', 'P': 'g', 'V': 'r'}
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


def drawlinesV2(axes, k, peaks, p1x, p2x, p1y, p2y):

    def find_divergence(matchlist):
        p1date1, p1date2, p2date1, p2date2 = None, None, None, None
        matchdt, divcount, tolerance, nodiv, matchpos = None, 0, 0, 0, -1
        for v in sorted(matchlist, reverse=True):
            if matchlist[v][0] == 0:
                nodiv += 1
                continue
            if p1date1 is None:
                if not swapP:
                    p1date1, p2date1 = p1x[v], p2x[matchlist[v][0]]
                    p1y1, p2y1 = p1y[v], p2y[matchlist[v][0]]
                else:
                    # TASCO 2012-06-08
                    p1date1, p2date1 = p2x[v], p1x[matchlist[v][0]]
                    p1y1, p2y1 = p2y[v], p1y[matchlist[v][0]]
                matchdt = matchlist[v][2]
                matchpos = matchlist[v][0]
                tolerance, nodiv = matchlist[v][1], 0
            elif matchlist[v][0] == matchpos:
                continue
            else:
                if not swapP:
                    p1date2, p2date2 = p1x[v], p2x[matchlist[v][0]]
                    p1y2, p2y2 = p1y[v], p2y[matchlist[v][0]]
                else:
                    # TASCO 2012-06-08
                    p1date2, p2date2 = p2x[v], p1x[matchlist[v][0]]
                    p1y2, p2y2 = p2y[v], p1y[matchlist[v][0]]
                if p1y1 > p1y2 and p2y1 > p2y2 or \
                        p1y1 < p1y2 and p2y1 < p2y2:
                    nodiv += 1
                    if nodiv > 3:
                        # KAWAN 2017-10-17 nodiv > 2
                        break
                    continue
                divcount += 1
                tolerance += matchlist[v][1]
                '''
                # Regular divergence                   Hidden divergence:
                #   Bias,     Price,       Oscillator      Bias,     Price,       Oscillator
                #   ----------------------------------    -----------------------------------
                #   Bullish,  Lower Low,   Higher Low      Bullish,  Higher Low,  Lower Low
                #   Bearish,  Higher High, Lower High      Bearish,  Lower High,  Higher High
                #
                #  i.e. PEAK divergence = Bearish, VALLEY divergence = BULLISH
                '''
                if matchlist[v][1] == 0:
                    lstyle = "-" if peaks else "-."
                else:
                    lstyle = "--" if peaks else ":"
                if not swapP:
                    annotatelines(axes, k, lstyle,
                                  p1date1, p1date2, p2date1, p2date2,
                                  p1y1, p1y2, p2y1, p2y2)
                else:
                    # TASCO 2012-06-08
                    annotatelines(axes, k, lstyle,
                                  p2date1, p2date2, p1date1, p1date2,
                                  p2y1, p2y2, p1y1, p1y2)
                if divcount > 2:
                    # restrict matchings to max 3
                    break
        return matchdt, 1, divcount, tolerance, matchpos

    if p1x is None or p2x is None:
        return []
    swapP, matchlist = matchdates(p1x, p2x)
    matchdt, divtype, divcount, tolerance, matchpos = find_divergence(matchlist)
    return [matchlist, matchdt, divtype, divcount, tolerance, matchpos]


def plotlinesV2(wfm, axes, cmpvXYPN):

    def match_nondiv(p1y, p2y, n1y, n2y):
        p1y1, p2y1 = p1y[-1], p2y[-1]
        p1y2, p2y2 = p1y[-2], p2y[-2]
        n1y1, n2y1 = n1y[-1], n2y[-1]
        n1y2, n2y2 = n1y[-2], n2y[-2]
        if p1y1 < p1y2 and p2y1 < p2y2 and n1y1 >= n1y2 and n2y1 >= n2y2:
            # P&M Lower peaks with higher valleys
            divtype = 3
        elif p1y1 > p1y2 and p2y1 > p2y2 and n1y1 >= n1y2 and n2y1 >= n2y2:
            # P&M Higher peaks with higher valleys
            divtype = 4
        elif p1y1 > p1y2 and p2y1 > p2y2 and n1y1 <= n1y2 and n2y1 <= n2y2:
            # P&M Higher peaks with lower valleys
            divtype = 5
        elif p1y1 < p1y2 and p2y1 < p2y2 and n1y1 <= n1y2 and n2y1 <= n2y2:
            # P&M Lower peaks with lower valleys
            divtype = 6
        elif p1y1 > p1y2 and n1y1 > n1y2 and p2y1 < p2y2 and n1y1 < n1y2:
            # Higher Ms vs Lower Ps
            divtype = 7
        elif p1y1 < p1y2 and n1y1 < n1y2 and p2y1 > p2y2 and n1y1 > n1y2:
            # Lower Ms vs Higher Ps
            divtype = 8
        else:
            divtype = 0
        return divtype, p1y1, p1y2, p2y1, p2y2, n1y1, n1y2, n2y1, n2y2

    def find_nondivergence(pmatch, nmatch):
        [plist, p1x, p2x, p1y, p2y] = pmatch
        [nlist, n1x, n2x, n1y, n2y] = nmatch
        if p1x is None or p2x is None or n1x is None or n2x is None or \
                len(p1x) < 2 or len(p2x) < 2 or len(n1x) < 2 or len(n2x) < 2:
            return None, 0, 0, 0
        matchdt, divcount, tolerance, divtype = None, 0, 0, 0
        divtype, p1y1, p1y2, p2y1, p2y2, n1y1, n1y2, n2y1, n2y2 = \
            match_nondiv(p1y, p2y, n1y, n2y)

        if divtype:
            p1date1, p2date1 = p1x[-1], p2x[-1]
            p1date2, p2date2 = p1x[-2], p2x[-2]
            n1date1, n2date1 = n1x[-1], n2x[-1]
            n1date2, n2date2 = n1x[-2], n2x[-2]
            divcount = 1
            lstyle = "--" if peaks else ":"
            annotatelines(axes, k, lstyle,
                          p1date1, p1date2, p2date1, p2date2,
                          p1y1, p1y2, p2y1, p2y2)
            annotatelines(axes, k, lstyle,
                          n1date1, n1date2, n2date1, n2date2,
                          n1y1, n1y2, n2y1, n2y2)
        return "", divtype, divcount, tolerance

    [cmpvXP, cmpvXN, cmpvYP, cmpvYN] = cmpvXYPN
    '''
    cxp, mxp, pxp = cmpvXP[0], cmpvXP[1], cmpvXP[2]
    cxn, mxn, pxn = cmpvXN[0], cmpvXN[1], cmpvXN[2]
    cyp, myp, pyp = cmpvYP[0], cmpvYP[1], cmpvYP[2]
    cyn, myn, pyn = cmpvYN[0], cmpvYN[1], cmpvYN[2]
    '''
    if wfm == 2:
        if S.DBG_ALL:
            print "For setting breakpoint to debug month chart only"
    lineseq = [['CM', True, 0, 1], ['CM', False, 0, 1],
               ['CP', True, 0, 2], ['CP', False, 0, 2],
               ['MP', True, 1, 2], ['MP', False, 1, 2]]
    pmatch, nmatch = {}, {}
    pdiv, ndiv, odiv, mpdates = {}, {}, {}, {}
    for i in lineseq:
        peaks = i[1]
        if peaks:
            k, p1x, p2x, p1y, p2y = i[0], cmpvXP[i[2]], cmpvXP[i[3]], cmpvYP[i[2]], cmpvYP[i[3]]
            if k == 'MP':
                if p1x is not None and len(p1x):
                    mpdates['Mp'] = p1x
                if p2x is not None and len(p2x):
                    mpdates['Pp'] = p2x
        else:
            k, p1x, p2x, p1y, p2y = i[0], cmpvXN[i[2]], cmpvXN[i[3]], cmpvYN[i[2]], cmpvYN[i[3]]
            if k == 'MP':
                if p1x is not None and len(p1x):
                    mpdates['Mn'] = p1x
                if p2x is not None and len(p2x):
                    mpdates['Pn'] = p2x
        if wfm == 2 and k == 'MP':
            if S.DBG_ALL:
                print "For setting breakpoint to debug month chart only"
        matchdata = drawlinesV2(axes, k, peaks, p1x, p2x, p1y, p2y)
        if len(matchdata):
            [matchlist, matchdt, divtype, divcount, matchtol, matchpos] = matchdata
        else:
            matchlist, matchdt, divtype, divcount, matchtol, matchpos = None, None, 0, 0, 0, 0
        if divcount > 0:
            if matchpos > -3:
                # Only consider first 3 peaks/valleys
                if peaks:
                    pdiv[k] = [matchdt, divtype, divcount, matchtol, matchpos]
                    if p1x[-1] > matchdt:
                        pmatch[k] = [matchlist, p1x, p2x, p1y, p2y]
                else:
                    ndiv[k] = [matchdt, divtype, divcount, matchtol, matchpos]
                    if p1x[-1] > matchdt or p2x[-1] > matchdt:
                        nmatch[k] = [matchlist, p1x, p2x, p1y, p2y]
        else:
            if peaks:
                pmatch[k] = [matchlist, p1x, p2x, p1y, p2y]
            else:
                nmatch[k] = [matchlist, p1x, p2x, p1y, p2y]
    if 1 == 0:
        # 2018-12-30 not using this for now
        if "MP" in pmatch and "MP" in nmatch:
            matchdt, divtype, divcount, matchtol = find_nondivergence(pmatch["MP"], nmatch["MP"])
            if divcount > 0:
                odiv[k] = [matchdt, divtype, divcount, matchtol, -1]
    return pdiv, ndiv, odiv, mpdates


def line_divergenceV2(wfm, axes, cIP, cIN, cCP, cCN, cmpvXYPN):
    del cIP, cIN, cCP, cCN
    pdiv, ndiv, odiv, mpdates = plotlinesV2(wfm, axes, cmpvXYPN)
    return cmpvXYPN, [pdiv, ndiv, odiv, mpdates]


def drawlines(axes, k, peaks, pindexes, p1x, p2x, p1y, p2y):
    divcount = 0
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
            divcount += 1
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
            annotatelines(axes, k, lstyle,
                          p1date1, p1date2, p2date1, p2date2,
                          p1y1, p1y2, p2y1, p2y2)
    return divcount


def line_divergence(axes, cIP, cIN, cCP, cCN, cmpvXYPN):
    cmpvlinesP = formCmpvlines(cIP, cCP)
    cmpvlinesN = formCmpvlines(cIN, cCN)
    pdiv = plotlines(axes, cmpvlinesP, cIP, True)
    ndiv = plotlines(axes, cmpvlinesN, cIN, False)
    del cIP
    del cIN
    del cCP
    del cCN
    del cmpvlinesP
    del cmpvlinesN
    return cmpvXYPN, pdiv, ndiv


def plotSignals(pmaps, counter, datevector, ax0):
    def getChartPOS(size):
        _, _, ymin, ymax = ax0.axis()
        portion = (ymax - ymin) / size
        chartpos = [ymax]
        for i in range(size):
            chartpos.append(chartpos[i] - portion)
        chartsig = chartpos[:2]
        return ymin, ymax, chartsig, chartpos[3:]

    prefix = S.DATA_DIR + S.MVP_DIR + "signals/"
    infile = prefix + counter + "-signals.csv"
    df = read_csv(infile, sep=',', header=None, parse_dates=['trxdt'],
                  names=['trxdt', 'counter',
                         'sssname', 'sssval', 'pnsig',
                         'cmpv', 'mvals', 'siglist', 'lastp'])
    df.set_index(df['trxdt'], inplace=True)
    ymin, ymax, spos, cpos = getChartPOS(14 + 3)
    hltb = ['0', 'h', 'l', 't', 'b']
    for dt in datevector:
        try:
            mpvdate = pdTimestamp2strdate(dt)
            dfsignal = df.loc[mpvdate]
            sssname, sssval, pnsig, mvals = \
                dfsignal.sssname, dfsignal.sssval, dfsignal.pnsig, dfsignal.mvals
            if type(sssname) is not str:
                print "INF: duplicated signals detected in", infile, mpvdate
                dfsignal = dfsignal.iloc[0]
                sssname, sssval, pnsig, mvals = \
                    dfsignal.sssname, dfsignal.sssval, dfsignal.pnsig, dfsignal.mvals
            if not pmaps:
                if sssname in ["Dbg", "NUL"]:
                    continue
            try:
                ssig = str(sssval).split('.')
                sval, sstate = ssig[0], ssig[1]
                pnval = str(pnsig).split('.')
                nsig, nstate, psig, pstate = pnval[0], pnval[1], pnval[2], pnval[3]
                if pmaps:
                    mvals = mvals[1:-1].replace('^', '.')
                    mval = mvals.split(".")
                    ilen = len(mval)
                    if ilen > len(cpos):
                        print "Len needs adjustment:", ilen, len(cpos)
                        ilen = len(cpos)
                    if nsig:
                        symbolclr = "y." if int(nstate) == 0 else "rX" if int(nsig) > 0 else "g^"
                        fontclr = "black" if int(nsig) > 0 else "green"
                        if int(nsig) != 0:
                            ax0.plot(dt, spos[0], symbolclr, markersize=7)
                            ax0.text(dt, spos[0], str(nsig), color=fontclr, fontsize=9)
                    if psig:
                        symbolclr = "y." if int(pstate) == 0 else "rX" if int(psig) > 0 else "g^"
                        fontclr = "black" if int(psig) > 0 else "green"
                        if int(psig) != 0:
                            ax0.plot(dt, spos[1], symbolclr, markersize=7)
                            ax0.text(dt, spos[1], str(psig), color=fontclr, fontsize=9)
                    if sval:
                        symbolclr = "y." if int(sstate) == 0 else "rX" if int(sval) > 0 else "g^"
                        fontclr = "black" if int(sval) > 0 else "green"
                        if int(sval) != 0:
                            ax0.plot(dt, ymin, symbolclr, markersize=7)
                            ax0.text(dt, ymin, str(sval), color=fontclr, fontsize=9)
                    for i in range(0, ilen):
                        fontclr = "black" if i in [0, 8, 9, 10] else \
                            "brown" if i in [5, 6, 7] else \
                            "blue" if i > 10 else "orange"
                        mtext = "." if int(mval[i]) == 0 else \
                            hltb[int(mval[i])] if i in [1, 2, 3, 4] else mval[i]
                        ax0.text(dt, cpos[i], mtext, color=fontclr, fontsize=9)
                else:
                    ttspos, othpos, bbspos = cpos[0], cpos[1], cpos[-1]
                    if sval:
                        symbolclr = "y." if sstate == 0 else "rX" if sval > 0 else "g^"
                        fontclr = "black" if sval > 0 else "green"
                        ttspos = ymin if sval < 0 else ymax
                        ax0.plot(dt, ttspos, symbolclr)
                        ax0.text(dt, ttspos, str(sval), color=fontclr, fontsize=9)
                    '''
                    if bbsval:
                        ax0.plot(dt, bbspos, "bd")
                        ax0.text(dt, bbspos, str(bbsval), color="blue", fontsize=9)
                    if othval:
                        ax0.plot(dt, othpos, "c+")
                        ax0.text(dt, othpos, str(othval), color="black", fontsize=9)
                    '''
            except Exception as e:
                print 'plotSignals exception:', mpvdate
                print e
        except KeyError as ke:
            continue


def mvpChart(counter, scode, chartDays=S.MVP_CHART_DAYS,
             weekly=False, pmaps=False, showchart=False, simulation=""):
    def getMpvDf(counter, chartDays, start=0):
        df, skiprows, fname = dfLoadMPV(counter, chartDays, start)
        if skiprows < 0 or len(df.index) <= 0:
            print "No chart for ", counter, skiprows
            return None, skiprows, fname, None
        lastTrxnDate = pdTimestamp2strdate(df.iloc[-1]['date'])
        return df, skiprows, fname, lastTrxnDate

    def plotchart(dfchart, fname):
        mpvdate = pdTimestamp2strdate(dfchart.iloc[-1]['date'])
        print "Charting: ", counter, mpvdate
        '''
        if len(dfchart.index) >= abs(chartDays):
            firstidx = dfchart.index.get_loc(dfchart.iloc[chartDays].name)
        else:
        '''
        if DBG_ALL:
            print(dfchart.tail(10))
            print type(mpvdate), mpvdate
            # print dfchart.index.get_loc(dfchart.iloc[chartDays].name)

        # columns, rows
        figsize = (14, 7) if not showchart or pmaps else (11, 5)
        mondays, alldays, _, weekFmt = weekFormatter()
        if not OHLC:
            axes = dfchart.plot(x='date', figsize=figsize, subplots=True, grid=True)
            ax = plt.gca().axes.get_xaxis()
            ax.set_label_coords(0.84, -0.7)
            # axis1.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.set_major_locator(mondays)
            ax.set_minor_locator(alldays)
            ax.set_major_formatter(weekFmt)
        else:
            fig = plt.figure(figsize=figsize)
            fig.set_canvas(plt.gcf().canvas)
            ax1 = plt.subplot2grid((7, 1), (0, 0), rowspan=4, fig=fig)
            ax2 = plt.subplot2grid((7, 1), (4, 0), sharex=ax1)
            ax3 = plt.subplot2grid((7, 1), (5, 0), sharex=ax1)
            ax4 = plt.subplot2grid((7, 1), (6, 0), sharex=ax1)
            axes = []
            axes.append(ax1)
            axes.append(ax2)
            axes.append(ax3)
            axes.append(ax4)
            # ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            # ax4.xaxis.set_major_locator(mticker.MaxNLocator(10))
            # ax4.fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
            ax4.xaxis.set_major_locator(mondays)
            ax4.xaxis.set_minor_locator(alldays)
            ax4.xaxis.set_major_formatter(weekFmt)
            # dayFormatter = DateFormatter('%d')
            # ax4.xaxis.set_minor_formatter(dayFormatter)
            ax1.grid(True)
            ax2.grid(True)
            ax3.grid(True)
            ax4.grid(True)
            candlestick_ohlc(ax1, zip(mdates.date2num(dfchart['date'].dt.to_pydatetime()),
                                      dfchart['open'], dfchart['high'], dfchart['low'], dfchart['close']),
                             width=0.7, colorup='#77d879', colordown='#db3f3f')
            ax4.xaxis_date()
            # ax1.plot_date(dfchart['date'], dfchart['close'], '-', color='b', label='C')
            ax2.plot_date(dfchart['date'], dfchart['M'], '-', color='orange', label='M')
            ax3.plot_date(dfchart['date'], dfchart['P'], '-', color='g', label='P')
            ax4.plot_date(dfchart['date'], dfchart['V'], '-', color='r', label='V')

            # for label in ax4.xaxis.get_ticklabels():
            #     label.set_rotation(45)
            plt.setp(ax1.get_xticklabels(), visible=False)
            plt.setp(ax2.get_xticklabels(), visible=False)
            plt.setp(ax3.get_xticklabels(), visible=False)
        # Disguise axis X label as title to save on chart space
        title = "MPV Chart of " + counter + "." + scode + ": " + mpvdate
        axes[3].set_xlabel(title, fontsize=12)
        axes[3].figure.canvas.set_window_title(title)
        '''
        axlabel = axis1.get_label()
        axlabel.set_visible(False)
        '''

        cHigh = dfchart.iloc[dfchart['close'].idxmax()]['close']
        cLow = dfchart.iloc[dfchart['close'].idxmin()]['close']
        mHigh = annotateMVP(dfchart, axes[1], "M", 10)
        mLow = dfchart.iloc[dfchart['M'].idxmin()]['M']
        pHigh = dfchart.iloc[dfchart['P'].idxmax()]['P']
        pLow = dfchart.iloc[dfchart['P'].idxmin()]['P']
        vHigh = annotateMVP(dfchart, axes[3], "V", 24)
        vLow = dfchart.iloc[dfchart['V'].idxmin()]['V']
        cmpvHL = [cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow]
        # line_divergence(axes, *plotpeaks(dfchart, axes, *findpeaks(dfchart, cmpvHL, weekly)))
        try:
            line_divergence(axes, *plotpeaks(dfchart, axes, *findpeaks(dfchart, cmpvHL, weekly)))
        except Exception as e:
            # just print error and continue without the required line in chart
            print 'line divergence exception:'
            print e
        plotSignals(pmaps, counter, dfchart['date'], axes[0])
        try:
            if mHigh > 8:
                axes[1].axhline(10, color='r', linestyle='--')
            axes[1].axhline(5, color='k', linestyle='--')
            axes[2].axhline(0, color='k', linestyle='--')
            if vHigh > 20:
                axes[3].axhline(25, color='k', linestyle='--')
            # plotSignals(pmaps, counter, dfchart['date'], axes[0])
            plt.tight_layout()
        except Exception as e:
            # just print error and continue without the required line in chart
            print 'axhline exception:'
            print e

        if showchart:
            plt.show()
        else:
            plt.savefig(fname + ".png")
        plt.close()

    if simulation is None or len(simulation) == 0:
        df, skiprow, fname, _ = getMpvDf(counter, chartDays)
        if df is None:
            return
        plotchart(df, fname)
    else:
        nums = simulation.split(",") if "," in simulation else numsFromDate(counter, simulation)
        if len(nums) <= 0:
            print "Input not found:", simulation
            return
        start, end, step = int(nums[0]), int(nums[1]), int(nums[2])
        dfmpv, title, fname, lastdate = getMpvDf(counter, chartDays, start)
        dates = simulation.split(":")
        end = dates[0]
        while True:
            # start = getDayOffset(end, chartDays * -1)
            start = pdDaysOffset(end, chartDays * -1)
            dflist = dfGetDates(dfmpv, start, end)
            if dflist is not None and len(dflist) > 10:
                plotchart(dflist, fname + "_" + end)
            if len(dates) < 2 or end >= dates[1]:
                break
            else:
                # end = getDayOffset(end, step)
                end = pdDaysOffset(end, step)
                if end > dates[1]:
                    end = dates[1]
        return False


def numsFromDate(counter, datestr, cdays=S.MVP_CHART_DAYS):
    prefix = S.DATA_DIR + S.MVP_DIR
    incsv = prefix + counter + ".csv"
    row_count = wc_line_count(incsv)
    dates = datestr.split(":") if ":" in datestr else [datestr]
    linenum = grepN(incsv, dates[0])  # e.g. 2012-01-01
    if linenum < 0:
        linenum = grepN(incsv, dates[0][:9])  # e.g. 2012-01-0
        if linenum < 0:
            linenum = grepN(incsv, dates[0][:7])  # e.g. 2012-01
            if linenum < 0:
                linenum = grepN(incsv, dates[0][:6])  # e.g. 2012-0
                if linenum < 0:
                    linenum = grepN(incsv, dates[0][:5])  # e.g. 2012-
    if DBG_ALL:
        print incsv, row_count, dates, linenum
    if linenum < 0:
        return []
    start = row_count - linenum + cdays
    stop = start + 1
    if len(dates) > 1:
        linenum = grepN(incsv, dates[1])  # e.g. 2018-10-30
        if linenum < 0:
            linenum = grepN(incsv, dates[1][:9])  # e.g. 2018-10-3
        if linenum > 0:
            stop = row_count - linenum + cdays
    step = int(dates[2]) if len(dates) > 2 else 1
    nums = str(start) + "," + str(stop) + "," + str(step)
    print "Start,Stop,Step =", nums
    return nums.split(',')


def mvpSynopsis(counter, scode, chartDays=S.MVP_CHART_DAYS, weekly=False,
                concurrency=False, showchart=False, simulation=""):
    def getMpvDf(counter, chartDays, start=0):
        df, skiprows, fname = dfLoadMPV(counter, chartDays, start)
        return df, skiprows, fname

    def getSynopsisDFs(counter, scode, chartDays, df, skiprows):
        try:
            # df, skiprows, fname = dfLoadMPV(counter, chartDays, start)
            dfm = None
            if skiprows >= 0 and df is not None:
                if weekly:
                    dfw = df.groupby([Grouper(key='date', freq='W')]).mean()
                    dff = df.groupby([Grouper(key='date', freq='2W')]).mean()
                dfm = df.groupby([Grouper(key='date', freq='M')]).mean()

                if DBG_ALL:
                    print dfm[-3:]
        except Exception as e:
            print "Dataframe exception: ", counter
            print e
        finally:
            lasttrxn = []
            if df is not None:
                lastTrxnDate = pdTimestamp2strdate(df.iloc[-1]['date'])
                lastClosingPrice = float(df.iloc[-1]['close'])
            if dfm is not None:
                lastC, firstC = float("{:.4f}".format(dfm.iloc[-1]['close'])), float("{:.4f}".format(dfm.iloc[0]['close']))
                lastM, firstM = float("{:.4f}".format(dfm.iloc[-1]['M'])), float("{:.4f}".format(dfm.iloc[0]['M']))
                lastP, firstP = float("{:.4f}".format(dfm.iloc[-1]['P'])), float("{:.4f}".format(dfm.iloc[0]['P']))
                lastV, firstV = float("{:.4f}".format(dfm.iloc[-1]['V'])), float("{:.4f}".format(dfm.iloc[0]['V']))
                lasttrxn = [lastTrxnDate, lastClosingPrice,
                            lastC, lastM, lastP, lastV, firstC, firstM, firstP, firstV]
                del df
            else:
                return None, None, None

        print " Synopsis:", counter, lastTrxnDate
        dflist = {}
        if weekly:
            dflist[0] = dfw.fillna(0)
            dflist[1] = dff.fillna(0)
            dflist[2] = dfm.fillna(0)
        else:
            dflist[0] = dfm.fillna(0)

        title = lastTrxnDate + " (" + str(chartDays) + "d) [" + scode + "]"

        return dflist, title, lasttrxn

    def housekeep():
        if "simulation" in fname:
            directory = mpvdir + "simulation/signals/"
        else:
            directory = mpvdir + "signals/"
        sfiles = counter + "-signals.csv"
        mergefiles(directory, sfiles)
        purgeOldFiles(fname + ".*", 0)

    # -----------------------------------------------------------#

    mpvdir = S.DATA_DIR + S.MVP_DIR
    if simulation is None or len(simulation) == 0:
        df, skiprow, fname = getMpvDf(counter, chartDays)
        dflist, title, lasttrxn = getSynopsisDFs(counter, scode, chartDays, df, skiprow)
        if dflist is None:
            return
        return doPlotting(mpvdir, DBG_SIGNAL, dflist, showchart,
                          counter, title, lasttrxn, fname, [])
    else:
        nums = simulation.split(",") if "," in simulation else numsFromDate(counter, simulation, chartDays)
        if len(nums) <= 0:
            print "Input not found:", simulation
            return
        start, end, step = int(nums[0]), int(nums[1]), int(nums[2])
        df, skiprow, fname = getMpvDf(counter, chartDays, start)
        dates = simulation.split(":")
        end = dates[0]
        jobs, cpus = [], cpu_count()
        while True:
            # start = getDayOffset(end, chartDays * -1)
            start = pdDaysOffset(end, chartDays * -1)
            dfmpv = dfGetDates(df, start, end)
            if len(dfmpv.index) > 100:
                dflist, title, lasttrxn = getSynopsisDFs(counter, scode, chartDays, dfmpv, skiprow)
                if dflist is None:
                    continue
                if concurrency:
                    p = Process(target=doPlotting,
                                args=(mpvdir, DBG_SIGNAL, dflist, showchart,
                                      counter, title, lasttrxn, fname, nums, concurrency))
                    p.start()
                    jobs.append(p)
                    if len(jobs) > cpus - 1:
                        for p in jobs:
                            p.join()
                        jobs = []
                else:
                    doPlotting(mpvdir, DBG_SIGNAL,
                               dflist, showchart, counter, title, lasttrxn, fname, nums)
            if len(dates) < 2 or end > dates[1]:
                if concurrency:
                    if len(jobs):
                        for p in jobs:
                            p.join()
                    housekeep()
                break
            else:
                end = pdDaysOffset(end, step)
            '''
            if start > end:
                start -= step
            else:
                break
            '''
        return False


def doPlotting(datadir, dbg, dfplot, showchart, counter, plttitle, lsttxn, outname, numslen, parallel=False):
    if parallel:
        global SYNOPSIS, DBG_ALL, OHLC
        global MVP_PLOT_PEAKS, MVP_PEAKS_DISTANCE, MVP_PEAKS_THRESHOLD
        global MVP_DIVERGENCE_MATCH_FILTER, MVP_DIVERGENCE_BLOCKING_COUNT, MVP_DIVERGENCE_MATCH_TOLERANCE
        SYNOPSIS, OHLC, DBG_ALL = True, False, False
        MVP_PLOT_PEAKS = True
        MVP_PEAKS_DISTANCE = -1
        MVP_PEAKS_THRESHOLD = -1
        MVP_DIVERGENCE_MATCH_FILTER, MVP_DIVERGENCE_BLOCKING_COUNT, MVP_DIVERGENCE_MATCH_TOLERANCE = \
            False, 1, 3
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

    if len(dfplot) > 1:
        # columns, rows
        figsize = (10, 6) if showchart else (15, 9)
    else:
        figsize = (12, 6) if showchart else (16, 10)
    fig, axes = plt.subplots(4, len(dfplot), figsize=figsize, sharex=False, num=plttitle)
    fig.canvas.set_window_title(plttitle)
    _, pnList, div = plotSynopsis(dfplot, axes)

    pid = os.getpid() if parallel else 0
    if pid:
        print "PID:", pid, lsttxn[0]
    signals = scanSignals(datadir, dbg, counter, outname, pnList, div, lsttxn, pid)
    if len(signals):
        title = plttitle + " [" + signals + "]"
    else:
        title = plttitle + " [" + counter + "]"
    fsize = 10 if showchart else 15
    fig.suptitle(title, fontsize=fsize)
    if dbg:
        print '\t', title

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if showchart:
        plt.show()
    else:
        if len(signals):
            if len(numslen) > 0:
                outname = outname + "-" + lsttxn[0]
            plt.savefig(outname + "-synopsis.png")
    plt.close()
    return len(signals) > 0


def plotSynopsis(dflist, axes):
    for i in range(len(dflist)):
        if len(dflist) > 1:
            dflist[i]['close'].plot(ax=axes[0, i], color='b', label='C')
            dflist[i]['V'].plot(ax=axes[1, i], color='r', label='V', kind='bar')
            dflist[i]['M'].plot(ax=axes[2, i], color='orange', label='M')
            dflist[i]['P'].plot(ax=axes[3, i], color='g', label='P')

            axes[0, 0].legend(loc="upper left")
            axes[1, 0].legend(loc="upper left")
            axes[2, 0].legend(loc="upper left")
            axes[3, 0].legend(loc="upper left")
            axes[3, 0].set_xlabel("W")
            axes[3, 1].set_xlabel("2W")
            axes[3, 2].set_xlabel("1M")
        else:
            dflist[i]['close'].plot(ax=axes[0], color='b', label='C')
            dflist[i]['V'].plot(ax=axes[1], color='r', label='V', kind='bar')
            dflist[i]['M'].plot(ax=axes[2], color='orange', label='M')
            dflist[i]['P'].plot(ax=axes[3], color='g', label='P')
            for i in range(4):
                axes[i].legend(loc="upper left")
                # axes[i].grid(True)
            # axes[3].set_xlabel("M")
            axlabel = axes[i].xaxis.get_label()
            axlabel.set_visible(False)
            x, y = [], []
            for p in axes[1].patches:
                x.append(p.get_x())
                y.append(p.get_height())
                axes[1].annotate("{:.2f}".format(p.get_height()),
                                 (p.get_x() * 1.001, p.get_height() * 1.009), size=7)
            axes[1].plot(x, y, 'c:')
            '''
            years, months, monthsFmt, yearsFmt = monthFormatter()
            axes[3].xaxis.set_minor_locator(months)
            axes[3].xaxis.set_minor_formatter(monthsFmt)
            axes[3].xaxis.set_major_locator(years)
            axes[3].xaxis.set_major_formatter(yearsFmt)
            locator = AutoDateLocator()
            formatter = AutoDateFormatter(locator)
            axes[3].xaxis_date()
            axes[3].xaxis.set_major_formatter(formatter)
            axes[3].xaxis.set_major_locator(locator)
            # dayFormatter = DateFormatter('%d')
            '''

    '''
    mHigh = annotateMVP(dfw, axes[1, 1], "M", 7)
    vHigh = annotateMVP(dfw, axes[3, 1], "V", 20)
    pHigh = dfw.loc[dfw['P'].idxmax()]['P']
    '''
    hlList, pnList = [], []
    # pdiv, ndiv, odiv = {}, {}, {}
    div = {}
    for i in range(len(dflist)):
        ax = {}
        for j in range(4):
            if j != 3:
                if len(dflist) > 1:
                    axlabel = axes[j, i].get_xaxis()
                else:
                    axlabel = axes[j].get_xaxis()
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
            if len(dflist) > 1:
                ax[j] = axes[j, i]
            else:
                ax = axes

        cHigh = dflist[i].loc[dflist[i]['close'].idxmax()]['close']
        cLow = dflist[i].loc[dflist[i]['close'].idxmin()]['close']
        vHigh = dflist[i].loc[dflist[i]['V'].idxmax()]['V']
        vLow = dflist[i].loc[dflist[i]['V'].idxmin()]['V']
        mHigh = dflist[i].loc[dflist[i]['M'].idxmax()]['M']
        mLow = dflist[i].loc[dflist[i]['M'].idxmin()]['M']
        pHigh = dflist[i].loc[dflist[i]['P'].idxmax()]['P']
        pLow = dflist[i].loc[dflist[i]['P'].idxmin()]['P']

        cmpvHL = [cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow]
        hlList.append(cmpvHL)
        # cmpvXYPN, div = line_divergenceV2(i, ax, *plotpeaks(dflist[i], ax,
        #                                                     *findpeaks(dflist[i], cmpvHL, i)))
        try:
            cmpvXYPN, div = line_divergenceV2(i, ax, *plotpeaks(dflist[i], ax,
                                                                *findpeaks(dflist[i], cmpvHL, dwfm=i)))
            pnList.append(cmpvXYPN)
        except Exception as e:
            # just print error and continue without the required line in chart
            print 'line divergence exception:', i
            print e
    try:
        if len(dflist) > 1:
            for i in range(len(dflist)):
                axes[1, i].axhline(0, color='k', linestyle=':')
                if vHigh < 0.5:
                    axes[1, i].axhline(0, color='k', linestyle=':')
                elif vHigh > 20:
                    axes[1, i].axhline(25, color='k', linestyle=':')
                axes[2, i].axhline(5, color='k', linestyle=':')
                if mHigh > 8:
                    axes[2, i].axhline(10, color='r', linestyle=':')
                axes[3, i].axhline(0, color='k', linestyle=':')
        else:
            axes[1].axhline(0, color='k', linestyle=':')
            if vHigh < 0.5:
                axes[1].axhline(0, color='k', linestyle=':')
            elif vHigh > 20:
                axes[1].axhline(25, color='k', linestyle=':')
            axes[2].axhline(5, color='k', linestyle=':')
            if mHigh > 8:
                axes[2].axhline(10, color='r', linestyle=':')
            axes[3].axhline(0, color='k', linestyle=':')
    except Exception as e:
        # just print error and continue without the required line in chart
        print 'axhline exception:'
        print e

    return hlList, pnList, div


def globals_from_args(args):
    global MVP_PLOT_PEAKS, MVP_PEAKS_DISTANCE, MVP_PEAKS_THRESHOLD
    global MVP_DIVERGENCE_MATCH_FILTER, MVP_DIVERGENCE_BLOCKING_COUNT, MVP_DIVERGENCE_MATCH_TOLERANCE
    global klse, DBG_ALL, DBG_SIGNAL, SYNOPSIS, OHLC
    klse = "scrapers/i3investor/klse.txt"

    dbgmode = "" if args['--debug'] is None else args['--debug']
    DBG_ALL = True if "a" in dbgmode else False
    DBG_SIGNAL = 1 if "s" in dbgmode else 2 if "u" in dbgmode else 3 if "p" in dbgmode else 0
    MVP_PLOT_PEAKS = True if args['--plotpeaks'] else False
    MVP_PEAKS_DISTANCE = -1 if not args['--peaksdist'] else float(args['--peaksdist'])
    MVP_PEAKS_THRESHOLD = -1 if not args['--threshold'] else float(args['--threshold'])
    MVP_DIVERGENCE_MATCH_FILTER = True if args['--filter'] else False
    MVP_DIVERGENCE_BLOCKING_COUNT = int(args['--blocking']) if args['--blocking'] else 1
    MVP_DIVERGENCE_MATCH_TOLERANCE = int(args['--tolerance']) if args['--tolerance'] else 3
    OHLC = True if args['--ohlc'] else False
    SYNOPSIS = True if args['--synopsis'] else False
    chartDays = int(args['--chartdays']) if args['--chartdays'] else S.MVP_CHART_DAYS
    if args['--datadir']:
        S.DATA_DIR = args['--datadir']
        if not S.DATA_DIR.endswith("/"):
            S.DATA_DIR += "/"
    '''
    # removed this as it causes different results due to different number of peaks/valleys
    if SYNOPSIS and chartDays == S.MVP_CHART_DAYS:
        # daily charting is defaulted to 200, add 100 for synopsis charting
        chartDays += 100
    '''
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
                mvpSynopsis(shortname, stocklist[shortname], chartDays, args['--weekly'],
                            args['--concurrency'], args['--displaychart'], args['--simulation'])
            else:
                mvpChart(shortname, stocklist[shortname], chartDays, args['--weekly'],
                         args['--pmaps'], args['--displaychart'], simulation=args['--simulation'])
        except Exception:
            traceback.print_exc()
