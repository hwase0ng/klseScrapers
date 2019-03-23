'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to scan signal
Options:
    -d,--datadir=<dd>       Use data directory provided
    -D,--debug=(dbgopt)     Enable debug mode (A)ll, (p)attern charting, (s)ignal, (u)nit test input generation
    -l,--list=<clist>       List of counters (dhkmwM) to retrieve from config.json
    -p,--plot               Plot charts
    -s,--showchart          Display chart [default: False]
    -S,--simulation=<sim>   Accepts dates in the form of "DATE1:DATE2:STEP"; e.g. 2018-10-01 or 2018-01-02:2018-07-20:5
    -h,--help               This page

Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S
from analytics.mvpchart import jsonPlotSynopsis
from common import loadCfg, retrieveCounters, formStocklist, loadKlseCounters
from utils.dateutils import getBusDaysBtwnDates, pdDaysOffset
from utils.fileutils import grepN, loadfromjson, jsonLastDate, wc_line_count
from docopt import docopt
from matplotlib import pyplot as plt
import traceback
import os


def scanSignals(mpvdir, dbg, counter, sdict, pid=0):
    def extractX():
        pnM = pnlist[2] if len(pnlist) > 1 else pnlist[0]
        xp, xn, = pnM[0], pnM[1]  # 0=XP, 1=XN, 2=YP, 3=YN
        return [xp, xn]

    def printsignal(workdir, trxndate):
        if not len(workdir):
            # call from pytest
            return
        # prefix = "" if DBGMODE == 2 else '\t'
        # print prefix + signal
        postfix = "csv." + trxndate if pid else "csv"
        if not pid:
            workdir = S.DATA_DIR + S.MVP_DIR
        outfile = workdir + "signals/" + counter + "-signals." + postfix
        linenum = grepN(outfile, trxndate)  # e.g. 2012-01-01
        if linenum > 0:
            # Already registered
            return
        if not len(label):
            return
        if dbg:
            with open(outfile, "ab") as fh:
                bbsline = trxndate + "," + signals
                fh.write(bbsline + '\n')
        if not dbg:
            # Stop this until system is ready for production use
            sss = workdir + "signals/" + label + "." + trxndate + ".csv"
            with open(sss, "ab") as fh:
                fh.write(signals + '\n')

    global DBGMODE
    DBGMODE = dbg
    pnlist = sdict['pnlist']
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    # lastClosingPrice is not aggregated while the rest are from the weekly aggregation!
    if pnlist is None or not len(pnlist):
        print "Skipped:", counter
        return ""
    if len(pnlist) < 1:
        print "Skipped len:", counter, len(pnlist)
        return ""

    '''
    matchdate, cmpvlists, composelist, hstlist, strlist = \
        collectCompositions(pnlist, lastTrxnData)
    if cmpvlists is None:
        return ""
    composeC, composeM, composeP, composeV = \
        composelist[0], composelist[1], composelist[2], composelist[3]
    # posC, posM, posP, posV = composeC[0], composeM[0], composeP[0], composeV[0]
    '''
    bottomrevs, bbs, bbs_stage = 0, 0, 0
    sss, sstate, psig, pstate, nsig, nstate, patterns, \
        mvalP, pvalP, vvalP, mvalN, pvalN, vvalN = extractSignals(counter, sdict, extractX())
    '''
    bottomrevs, bbs, bbs_stage = \
        bottomBuySignals(lastTrxnData, matchdate, cmpvlists, composelist, div)
    '''
    if not (sss or bbs or bbs_stage):
        if not dbg:
            return ""

    strlist, lastTrxnData = sdict['strlist'], sdict['lsttxn']
    strC, strM, strP, strV = strlist[0], strlist[1], strlist[2], strlist[3]
    # [tolerance, pdays, ndays, matchlevel] = matchdate
    p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    if patterns is not None:
        [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13] = patterns
    lastprice = lastTrxnData[1]
    signaldet = "(c%s.m%s.p%s.v%s),(%d.%d.%d.%d^%d.%d.%d^%d.%d.%d^%d.%d.%d),(%d.%d.%d^%d.%d.%d),%.2f" % \
        (strC[:1], strM[:1], strP[:1], strV[:1],
         p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13,
         mvalP, pvalP, vvalP, mvalN, pvalN, vvalN, lastprice)
    # tolerance, pdays, ndays, matchlevel)
    signalsss, label = "NUL,0.0,0.0.0.0", ""
    if sss or psig or nsig:
        label = "TBD" if sss >= 900 or sstate == 0 else \
                "TSS" if sss < 0 else "BBS" if sss > 0 else \
                "TSS" if psig < 0 or nsig < 0 else \
                "BBS" if psig > 0 or nsig > 0 else \
                "NUL"
        signalsss = "%s,%d.%d,%d.%d.%d.%d" % (label, sss, sstate, nsig, nstate, psig, pstate)

    signals = "%s,%s,%s" % (counter, signalsss, signaldet)
    if dbg == 2:
        # print '\n("%s", %s, %s, %s, "%s"),\n' % (counter, pnlist, div, lastTrxnData, signals.replace('\t', ''))
        print '("%s", "%s", "%s"),' % (counter, lastTrxnData[0], signals.replace('\t', ''))
    else:
        printsignal(mpvdir, lastTrxnData[0])
    return signals


def extractSignals(counter, sdict, xpn):

    def MislowPlowN():
        if plistM[-1] == min(plistM[-3:]):
            if nlistM[-1] == min(nlistM[-3:]):
                return True
        return False

    def PislowPlowN():
        if plistP[-1] == min(plistP[-3:]):
            if nlistP[-1] == min(nlistP[-3:]):
                return True
        return False

    def MishighPhighN():
        if plistM[-1] == max(plistM[-3:]):
            if nlistM[-1] == max(nlistM[-3:]):
                return True
        return False

    def PishighPhighN():
        if plistP[-1] == max(plistP[-3:]):
            if nlistP[-1] == max(nlistP[-3:]):
                return True
        return False

    def MishighPlowN():
        if plistM[-1] == max(plistM[-3:]):
            if nlistM[-1] == min(nlistM[-3:]):
                return True
        return False

    def PishighPlowN():
        if plistP[-1] == max(plistP[-3:]):
            if nlistP[-1] == min(nlistP[-3:]):
                return True
        return False

    def MislowPhighN():
        if plistM[-1] == min(plistM[-3:]):
            if nlistM[-1] == max(nlistM[-3:]):
                return True
        return False

    def PislowPhighN():
        if plistP[-1] == min(plistP[-3:]):
            if nlistP[-1] == max(nlistP[-3:]):
                return True
        return False

    def MishigherP_PislowerP():
        if plistM[-1] > min(plistM[-3:]):
            if plistP[-1] == min(plistP[-3:]):
                return True
        return False

    def MislowerP_PishigherP():
        if plistM[-1] == min(plistM[-3:]):
            if plistP[-1] > min(plistP[-3:]):
                return True
        return False

    def MishigherN_PislowerN():
        if nlistM[-1] > min(nlistM[-3:]):
            if nlistP[-1] == min(nlistP[-3:]):
                return True
        return False

    def MislowerN_PishigherN():
        if nlistM[-1] == min(nlistM[-3:]):
            if nlistP[-1] > min(nlistP[-3:]):
                return True
        return False

    def isN3UP():
        n3up = 0
        if tripleM in [2, 5, 7] and tripleP in [2, 5, 7]:
            n3up = 2
            if tripleV in [2, 5, 7]:
                n3up = 3
        return n3up

    def isP3UP():
        if max(plistM[-3:]) == plistM[-1] and max(plistP[-3:]) == plistP[-1]:
            return True
        return False

    def isPN3UP():
        if max(plistM[-3:]) == plistM[-1] and max(nlistM[-3:]) == nlistM[-1] and \
                max(plistP[-3:]) == plistP[-1] and max(nlistP[-3:]) == nlistP[-1]:
            return True
        return False

    def isPN3DOWN():
        if min(plistM[-3:]) == plistM[-1] and min(nlistM[-3:]) == nlistM[-1] and \
                min(plistP[-3:]) == plistP[-1] and min(nlistP[-3:]) == nlistP[-1]:
            return True
        return False

    def ispeak(cmpv):
        xpc, xnc = xpn[0][cmpv], xpn[1][cmpv]  # cmpv: 0=C, 1=M, 2=P, 3=V
        if xpc is None or xnc is None:
            if xpc is None and xnc is not None:
                return False, "", xnc
            if xnc is None and xpc is not None:
                return True, xpc, ""
            return False, "", ""
        xp, xn = xpc[-1], xnc[-1]
        if xp > xn:
            return True, xp, xn
        return False, xp, xn

    def isprev3topM():
        if mvalley:
            if max(plistM[-3:]) == max(plistM):
                return True
        else:
            if max(plistM[-3:-1]) == max(plistM[:-1]):
                return True
        return False

    def isprev3topP():
        if pvalley:
            if max(plistP[-3:]) == max(plistP):
                return True
        else:
            if max(plistP[-3:-1]) == max(plistP[:-1]):
                return True
        return False

    def isprev3topV():
        if vvalley:
            if max(plistV[-3:]) == max(plistV):
                return True
        else:
            if max(plistV[-3:-1]) == max(plistV[:-1]):
                return True
        return False

    def isprev3bottomM():
        if mpeak:
            if min(nlistM[-3:]) == min(nlistM):
                return True
        else:
            if min(nlistM[-3:-1]) == min(nlistM[:-1]):
                return True
        return False

    def isprev3bottomP():
        if ppeak:
            if min(nlistP[-3:]) == min(nlistP):
                return True
        else:
            if min(nlistP[-3:-1]) == min(nlistP[:-1]):
                return True
        return False

    def isprev3bottomV():
        if vpeak:
            if min(nlistV[-3:]) == min(nlistV):
                return True
        else:
            if min(nlistV[-3:-1]) == min(nlistV[:-1]):
                return True
        return False

    def isDivergentSync():
        def countdate():
            xpm, xpp = xpn[0][1], xpn[0][2]  # cmpv: 0=C, 1=M, 2=P, 3=V
            xnm, xnp = xpn[1][1], xpn[1][2]  # cmpv: 0=C, 1=M, 2=P, 3=V
            if xpm is None or xpp is None or xnm is None or xnp is None:
                return 0, 0
            if len(xpm) < 4 or len(xpp) < 4:
                return 0, 0
            if len(xpm) < len(xpp):
                date1, date2 = xpm[-4], xpm[-1]
                cntref = xpp
                matchref = xpm
            else:
                date1, date2 = xpp[-4], xpp[-1]
                cntref = xpm
                matchref = xpp
            skipcnt, matchcnt, cnt = 0, 0, 0
            for dt in reversed(cntref):
                if dt > date2:
                    skipcnt += 1
                    continue
                if dt < date1:
                    break
                cnt += 1
                if dt in matchref or dt in xnm or dt in xnp:
                    matchcnt += 1
            return cnt + skipcnt - 4, matchcnt

        cmpsync, mpsync = 0, 0
        if (cpeak and mpeak and ppeak and
            pdateC == pdateM and pdateM == pdateP) or (cvalley and mvalley and pvalley and
                                                       ndateC == ndateM and ndateM == ndateP):
            cmpsync = 1
        elif pdateC == pdateM or pdateC == pdateP:
            cmpsync = 2

        datecnt, match = countdate()
        if datecnt < 3 and match > 1:
            mpsync = 1
            cmpsync = 3
        return cmpsync, mpsync

    def isretrace():
        retrace = 0
        if plenM < 2:
            return retrace
        if max(plistM[-3:]) > 10 and nlistM[-1] > 5 and isprev3bottomP():
            retrace = 1
        elif nlistM[-1] >= 5 and nlistM[-1] < 7.5:
            if mvalley and plistM[-1] >= 10:
                retrace = 2
            elif mpeak and plistM[-1] < plistM[-2] and plistM[-2] >= 10:
                retrace = 3
        elif prevbottomM and bottomP:
            if mpeak and plistM[-1] < 10 and tripleM in p3d:
                # 2013-03-13 ORNA
                retrace = 4
        return retrace

    def minmaxC():
        minC, maxC = None, None
        if plistC is not None:
            maxC = max(plistC) if lastC < max(plistC) else lastC
            if maxC < firstC:
                maxC = firstC
        else:
            maxC = firstC if firstC > lastC else lastC
        if nlistC is not None:
            minC = min(nlistC) if lastC > min(nlistC) else lastC
            if minC > firstC:
                minC = firstC
        else:
            minC = firstC if firstC < lastC else lastC
        range4 = float("{:.2f}".format((maxC - minC) / 4))
        lowbar = minC + range4 + (range4 * 20 / 100)
        lowbar2 = minC + range4 + (range4 * 40 / 100)
        midbar = (minC + maxC) / 2
        highbar = maxC - range4 - (range4 * 20 / 100)
        return minC, maxC, range4, lowbar, lowbar2, midbar, highbar

    def minmaxP():
        minP, maxP = None, None
        if plistP is not None:
            maxP = max(plistP) if lastP < max(plistP) else lastP
            if maxP < firstP:
                maxP = firstP
        else:
            maxP = firstP if firstP > lastP else lastP
        if nlistP is not None:
            minP = min(nlistP) if lastP > min(nlistP) else lastP
            if minP > firstP:
                minP = firstP
        else:
            minP = firstP if firstP < lastP else lastP
        midP = (minP + maxP) / 2
        return minP, maxP, midP

    def shapesDiscovery():
        def tripleChecks():
            def triplecount(plist, nlist):
                tripleMPV, pcountup, pcountdown, ncountup, ncountdown = 0, 0, 0, 0, 0
                for i in range(-3, -1):
                    if plist[i] <= plist[i + 1]:
                        pcountup += 1
                    if plist[i] >= plist[i + 1]:
                        pcountdown += 1
                    if len(nlist) > 2:
                        if nlist[i] <= nlist[i + 1]:
                            ncountup += 1
                        if nlist[i] >= nlist[i + 1]:
                            ncountdown += 1
                '''
                      N0   N^   Nv
                P^    1    2    3
                Pv    4    5    6
                Px    X    7    8
                '''
                if ncountup > 1 and pcountup < 2 and pcountdown < 2:
                    tripleMPV = 7
                elif ncountdown > 1 and pcountup < 2 and pcountdown < 2:
                    tripleMPV = 8
                elif pcountup > 1 and ncountup < 2 and ncountdown < 2:
                    tripleMPV = 1
                elif pcountup > 1 and ncountup > 1:
                    tripleMPV = 2
                elif pcountup > 1 and ncountdown > 1:
                    tripleMPV = 3
                elif pcountdown > 1 and ncountup < 2 and ncountdown < 2:
                    tripleMPV = 4
                elif pcountdown > 1 and ncountup > 1:
                    tripleMPV = 5
                elif pcountdown > 1 and ncountdown > 1:
                    tripleMPV = 6
                return tripleMPV

            def checkM():
                def narrowcount():
                    def mnarraowcount2():
                        if tripleM == 5:
                            return 9
                        if mpeak or tripleM not in [5, 7]:
                            return 0
                        ncount2 = []
                        for i in range(-1, -4, -1):
                            ncount2.append(plistM[i] - nlistM[i])
                        if ncount2[0] > ncount2[1] and ncount2[1] > ncount2[2]:
                            return 9
                        return 0

                    narrowM = mnarraowcount2()
                    if narrowM:
                        return narrowM
                    if plenM > 4 and nlenM > 4:
                        lenm = plenM + 1 if plenM < nlenM else nlenM + 1
                        for i in range(-1, -lenm, -1):
                            if plistM[i] <= 10 and plistM[i] >= 5 and \
                                    nlistM[i] <= 10 and nlistM[i] >= 5:
                                # PADINI 2012-09-28
                                # PETRONM 2015-10-07
                                # YSPSAH 20116-12-23
                                narrowM += 1
                            else:
                                break
                        if narrowM < 5:
                            narrowM = 0
                        elif narrowM > 8:
                            narrowM = 8
                    return narrowM

                plenM, nlenM, tripleM = 0, 0, 0
                if plistM is not None and nlistM is not None:
                    countM10, m10skip = 0, 0
                    plenM, nlenM = len(plistM), len(nlistM)
                    if plenM > 2:
                        tripleM = triplecount(plistM, nlistM)
                        for i in range(-1, -plenM, -1):
                            if plistM[i] >= 10:
                                countM10 += 1
                            else:
                                # ??? 2011-05 variant with one M lower than 10 in the middle
                                m10skip += 1
                                if m10skip > 1:
                                    break
                    if countM10 > 2:
                        # 2014-11-21 DUFU retrace completed
                        # 2017-08-02 UCREST topM valley divergence
                        # 2013-04-29 YSPSAH
                        tripleM = 9
                        # if countM10 > 3:
                        #     tripleM = 9

                    narrowM = narrowcount()
                return plenM, nlenM, tripleM, narrowM

            def checkP():
                def pnarrowcount():
                    def pnarraowcount2():
                        if tripleP == 5:
                            return 9
                        if ppeak or tripleP not in [5, 7]:
                            return 0
                        ncount2 = []
                        for i in range(-1, -4, -1):
                            ncount2.append(plistP[i] - nlistP[i])
                        if ncount2[0] < ncount2[1] and ncount2[1] < ncount2[2]:
                            # 2012-08-02 ORNA
                            # 2018-01-04 CARLSBG
                            return 9
                        return 0

                    ncount = pnarraowcount2()
                    if ncount:
                        return ncount
                    p5 = False
                    distanceP = maxP - minP
                    pstart = -2 if ppeak else -1
                    pnrange = []
                    pnrange.append((plistP[pstart] - nlistP[-1]) / distanceP)
                    pnrange.append((plistP[pstart] - nlistP[-2]) / distanceP)
                    pnrange.append((plistP[pstart - 1] - nlistP[-2]) / distanceP)
                    pnrange.append((plistP[pstart - 1] - nlistP[-3]) / distanceP)
                    nrange1, nrange2 = 0.20, 0.05
                    for i in range(len(pnrange)):
                        if pnrange[i] <= nrange1:
                            # 2013-04-30 MUDA
                            # 2015-08-04 PADINI
                            ncount += 1
                            if pnrange[i] <= nrange2:
                                # 2016-11-14 KLSE
                                p5 = True
                        else:
                            break
                    if ncount < 3 and not p5:
                        ncount = 0
                    return ncount

                def countp():
                    pcount = 0
                    if plistP[-1] < 0:
                        pcount = 1
                        if plenP > 1 and plistP[-2] < 0:
                            pcount = 2
                    elif nlistP[-1] > 0:
                        for i in range(-1, -lenp, -1):
                            if nlistP[i] >= 0:
                                pcount += 1
                            else:
                                break
                        if pcount < 3:
                            pcount = 0
                    return pcount

                plenP, nlenP, tripleP, narrowP, countP = 0, 0, 0, 0, 0
                if plistP is not None and nlistP is not None:
                    plenP, nlenP = len(plistP), len(nlistP)
                    lenp = plenP + 1 if plenP < nlenP else nlenP + 1
                    if plenP > 3:
                        tripleP = triplecount(plistP, nlistP)
                        narrowP = pnarrowcount()
                        countP = countp()
                return plenP, nlenP, tripleP, narrowP, countP

            def checkV():
                plenV, nlenV, tripleV = 0, 0, 0
                if plistV is not None and nlistV is not None:
                    plenV, nlenV = len(plistV), len(nlistV)
                    if plenV > 2:
                        tripleV = triplecount(plistV, nlistV)
                return plenV, nlenV, tripleV

            c = 1 if newhighC else 2 if topC else 3 if newlowC else 4 if bottomC else 0
            m = 1 if newhighM else 2 if topM else 3 if newlowM else 4 if bottomM else 0
            p = 1 if newhighP else 2 if topP else 3 if newlowP else 4 if bottomP else 0
            v = 1 if newhighV else 2 if topV else 3 if newlowV else 4 if bottomV else 0

            plenM, nlenM, tripleM, narrowM = checkM()
            plenP, nlenP, tripleP, narrowP, countP = checkP()
            plenV, nlenV, tripleV = checkV()
            return c, m, p, v, tripleM, tripleP, tripleV, narrowM, narrowP, countP, \
                [plenM, nlenM, plenP, nlenP, plenV, nlenV]

        def narrowcount():
            def volatilityCheck():
                minmax = maxC - minC
                if maxC == lastC and lastC - nlistC[-1] > minmax / 2.2:
                    # 2014-08-29 VSTECS minmax=0.5653
                    return 0, 0
                if plenC > 1 and plistC[-1] > highbar and plistC[-2] < lowbar:
                    # 2014-06-24 MUDA
                    return 0, 0
                # 2017-02-21 YSPSAH [0.179, 0.035, 0.356, 0.125, 0.0302, 0.031]
                lowvolatility1, lowvolatility2 = 0.25, 0.36
                pstart = -2 if cpeak else -1
                pnrange = []
                pnrange.append((plistC[pstart] - nlistC[-1]) / minmax)
                pnrange.append((plistC[pstart] - nlistC[-2]) / minmax)
                pnrange.append((plistC[pstart - 1] - nlistC[-2]) / minmax)
                pnrange.append((plistC[pstart - 1] - nlistC[-3]) / minmax)
                if len(plistC) > abs(pstart - 1):
                    pnrange.append((plistC[pstart - 2] - nlistC[-3]) / minmax)
                    if len(nlistC) > 3:
                        # 2017-01-09 KESM
                        pnrange.append((plistC[pstart - 2] - nlistC[-4]) / minmax)
                averange = (pnrange[0] + pnrange[1]) / 2
                tolerange = averange * 2
                if tolerange < lowvolatility2:
                    tolerange = lowvolatility2
                vcount, vcount2, alt = 0, 0, 0
                for i in range(len(pnrange)):
                    if pnrange[i] <= lowvolatility1:
                        vcount += 1
                    elif pnrange[i] < tolerange and pnrange[i] <= lowvolatility2:
                        # KLSE 2017-01-09 pnrange: [0.198, 0.186, 0.333, 0.321, 0.225, 0.315]
                        vcount2 += 0.3
                    else:
                        # 2013-01-28 KLSE <pnrange>: [0.125, 0.125, 0.0586, 0.309, 0.101, 0.684]
                        break
                if vcount2 > 0.5:
                    vcount += 1
                    alt = 1
                return vcount, alt

            if newlowC or topC or plistC[-1] > highbar:
                # 2014-11-07 DUFU
                # 2016-01-04 PADINI
                return 0
            ncount, alt = volatilityCheck()
            narrowc = 0
            if ncount < 4:
                ncount = 0
            elif ncount > 3:
                # 2017-01-06 GHLSYS
                if alt:
                    # 2017-01-09 KLSE
                    ncount = 1
                if max(nlistC[-3:]) < lowbar:
                    # 2017-01-11 KLSE
                    narrowc = 1
                elif max(nlistC[-3:]) > lowbar and min(nlistC[-3:]) < midbar:
                    # 2017-01-03 GHLSYS
                    narrowc = 2
                elif plistC[-3] > highbar:
                    if plistC[-2] > plistC[-1] and plistC[-1] > midbar:
                        if nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3]:
                            if nlistC[-1] > midbar:
                                # 2018-08-02 DUFU
                                narrowc = 2
            '''
            elif (newhighC or topC) and (prevbottomC or firstC == minC):
                # PADINI 2012-09-28 beginning of tops reversal
                ncount = 2
                startc = plenC * -1
                for i in range(startc, -1):
                    if plistC[i] > lowbar:
                        ncount = 0
                        break
            '''
            if ncount:
                pass
            elif (firstC == maxC or plistC[0] == maxC) and plistC[-1] < lowbar:
                # 2014-05-12 DUFU
                ncount = 4
                narrowc = 1
            elif plistC[0] == maxC or plistC[1] == maxC or firstC == maxC or \
                    (plenC > 5 and plistC[2] == maxC):
                ncount = 3
                for i in range(-3, 0):
                    if plistC[i] < lowbar:
                        continue
                    elif plistC[i] > lowbar2 and plistC[i] < midbar:
                        ncount -= 1
                    else:
                        ncount = 0
                        break
                if ncount:
                    if ncount < 2:
                        ncount = 0
                        narrowc = 0
                    else:
                        narrowc = 1 if posC < 2 else 2
            return narrowc  # ncount

        def bottomscount():
            tripleBottoms = 0
            if plenC < 3 or nlenC < 3:
                pass
            elif plistC[-1] < plistC[-2] and plistC[-2] < plistC[-3]:
                if nlistC[-1] > nlistC[-3] and nlistC[-2] > nlistC[-3]:
                    ''' --- lower peaks and higher valleys --- '''
                    if plistC[-3] < midbar and plistC[-1] < lowbar:
                        # 2013-09-09 KESM bottom buy
                        tripleBottoms = 1
                    elif nlistC[-3] > midbar and max(nlistC[-2:]) > highbar:
                        # 2014-01-30 N2N top buy
                        tripleBottoms = 3
                elif nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3]:
                    ''' --- lower peaks and lower valleys --- '''
                    if plistC[-3] < midbar and plistC[-1] < lowbar:
                        # 2011-10-12 DUFU
                        tripleBottoms = 1
                    elif plistC[-3] < highbar and plistC[-1] < midbar:
                        if plistC[-1] < lowbar:
                            # 2019-02-04 RSAWIT
                            tripleBottoms = 1
                        else:
                            # 2017-08-28 N2N
                            tripleBottoms = 2
                    elif nlistC[-1] > midbar and max(nlistC[-3:]) > highbar:
                        # 2014-02-05 PADINI newlowC, 2015-10-02
                        tripleBottoms = 3
                    elif nlistC[-3] > highbar and max(nlistC[-2:]) < lowbar:
                        # 2015-10-07 PADINI
                        tripleBottoms = 1

                    if not tripleBottoms:
                        if nlenC > 3 and nlistC[-3] < nlistC[-4]:
                            ''' --- lower peaks and lower valleys extension --- '''
                            if plenC > 3 and plistC[-4] > highbar and plistC[-3] > midbar and plistC[-1] < lowbar:
                                # 2018-07-23 DANCO
                                tripleBottoms = 1
                            elif nlistC[-1] > midbar and max(nlistC[-3:]) > highbar:
                                # 2018-06-13 DUFU retrace with valley follow by peak divergence
                                tripleBottoms = 3
                            elif nlenC > 3 and nlistC[-4] > midbar and nlistC[-1] < lowbar:
                                # 2014-04-25 PETRONM
                                tripleBottoms = 2
                elif nlenC > 3 and \
                        nlistC[-2] < nlistC[-4] and nlistC[-3] < nlistC[-4]:
                    ''' --- lower peaks and lower valleys variant --- '''
                    if plistC[-1] < lowbar and nlistC[0] > highbar:
                        # 2011-10-12 DUFU
                        tripleBottoms = 1
                    elif plistC[-2] < lowbar and nlistC[0] > highbar:
                        # 2012-04-10 DUFU
                        tripleBottoms = 1
                    elif nlistC[0] == minC or firstC == minC:
                        # 2012-08-14 ORNA
                        tripleBottoms = 3
                elif nlenC > 3 and \
                        nlistC[-1] < nlistC[-3] and nlistC[-1] < nlistC[-2] and \
                        nlistC[0] == min(nlistC) and plistC[0] == max(plistC):
                    ''' --- lower peaks and lower valleys variant 2 --- '''
                    if nlistC[0] < lowbar and plistC[0] > highbar and plistC[-1] < midbar:
                        # 2017-08-30 N2N (already handled above)
                        tripleBottoms = 2
            return tripleBottoms

        def topscount():
            def alternateTops():
                tops = 0
                for i in range(-1, -4, -1):
                    if plistC[i] > plistC[i - 1]:
                        tops += 1
                    elif plistC[i] > plistC[i - 2] and plistC[i] > plistC[i - 3]:
                        tops += 1
                    else:
                        break
                    if tops > 3:
                        break
                return tops

            tripleTops = 0
            if nlenC > 2 and \
                    plistC[-1] > plistC[-2] and plistC[-2] > plistC[-3] and \
                    nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3] and \
                    nlistC[-1] > maxC - range4 and posC > 2:
                # 2013-03-06 KLSE
                tripleTops = 1
            elif nlenC > 3 and min(plistC[-3:]) > highbar and \
                    min(nlistC[-3:]) > midbar and max(nlistC[-3:]) > highbar:
                if lastC > nlistC[-1]:
                    # 2019-01-07 IMASPRO
                    tripleTops = 1
                else:
                    # 2014-12-10 KLSE
                    tripleTops = 6

            if not tripleTops and \
                plistC[-1] > highbar and nlistC[0] < lowbar and \
                    (firstC < midbar or (nlistC[0] == minC and
                                         plistC[0] < minC + (2 * range4))):
                if nlenC == 2 and \
                        plistC[-1] > plistC[-2] and plistC[-2] > plistC[-3] and \
                        nlistC[-1] > nlistC[-2]:
                    # 2018-11-21 PADINI
                    tripleTops = 2
                elif plenC > 3 and nlenC > 2:
                    if plistC[-1] > plistC[-2] and plistC[-2] > plistC[-3] and \
                            nlistC[-1] > nlistC[-2] and (nlistC[-2] > nlistC[-3] or
                                                         nlistC[-2] > plistC[-4]):
                        # 2008-02-20 KLSE
                        # 2016-04-25 DUFU
                        tripleTops = 3
                        if lastC > nlistC[-1] and nlistC[-1] > plistC[-2] and nlistC[-2] > plistC[-3]:
                            # DUFU 2016-12-23
                            # KESM 2016-06-15 only works with chartdays > 500
                            tripleTops = 4

            if not tripleTops:
                if plenC > 5 and nlenC > 2:
                    if alternateTops() > 3 and \
                            (nlistC[-1] > nlistC[-2] or nlistC[-1] > nlistC[-3]):
                        # VSTECS 2014-01-29
                        tripleTops = 5
                    elif min(plistC[:3]) < lowbar and plistC[-2] == maxC and \
                            min(plistC[-3:]) > midbar and min(nlistC[-2:]) > midbar:
                        # 2014-12-04 ORNA
                        tripleTops = 6
                elif plenC > 3:
                    if plistC[-4] < lowbar and plistC[-3] > highbar and plistC[-2] == maxC and \
                            plistC[-1] > midbar and nlistC[-1] > midbar:
                        # 2015-10-27 MUDA
                        tripleTops = 7
                    elif min(nlistC[-3:]) > midbar or \
                            (min(plistC) > midbar and min(nlistC[-2:]) > midbar):
                        # 2008-06-02 KLSE
                        # 2008-08-29 KLSE
                        tripleTops = 7
                    '''
                    elif plenC > 4 and \
                            plistC[-5] < lowbar and \
                            plistC[-4] > midbar and plistC[-3] > midbar and \
                            plistC[-2] == maxC and plistC[-1] > highbar and \
                            nlistC[-1] > lowbar:
                        # 2019-01-10 KLSE - more like forming tripleBottoms
                        tripleTops = 8
                    '''

            return tripleTops

        narrowC, tripleBottoms, tripleTops = 0, 0, 0
        c, m, p, v, tripleM, tripleP, tripleV, narrowM, narrowP, countP, mpvlen = tripleChecks()
        plenC, nlenC = 0, 0
        if plistC is None or nlistC is None:
            pass
        else:
            plenC, nlenC = len(plistC), len(nlistC)
            if plenC > 2 and nlenC > 2:
                narrowC = narrowcount()
                tripleBottoms = bottomscount()
            if plenC > 2 and nlenC > 1:
                tripleTops = topscount()
            elif plenC > 1 and not newlowC:
                if firstC == maxC and plistC[0] < midbar and plistC[1] < lowbar:
                    narrowC = 9

        firstmp = mpdates["Mp"][-1] if "Mp" in mpdates else "1970-01-01"
        firstmn = mpdates["Mn"][-1] if "Mn" in mpdates else "1970-01-01"
        firstpp = mpdates["Pp"][-1] if "Pp" in mpdates else "1970-01-01"
        firstpn = mpdates["Pn"][-1] if "Pn" in mpdates else "1970-01-01"

        mpvlen.append(plenC)
        mpvlen.append(nlenC)
        return [c, m, p, v, tripleM, tripleP, tripleV,
                narrowC, narrowM, narrowP, countP, tripleBottoms, tripleTops], \
            [firstmp, firstmn, firstpp, firstpn], mpvlen

    def divergenceDiscovery():
        def divCMP():
            def getdivdt(divlist):
                cdate, mpdate = "", ""
                # 2018-09-06 MAGNI
                # dict: {'CP': ['2018-08-31', '2018-08-31', 1, 1, 0, -1],
                #        'MP': ['2018-08-31', '2018-07-31', 1, 2, 3, -1],
                #        'CM': ['2018-08-31', '2018-07-31', 1, 1, 2, -1]}
                if divlist is not None and len(divlist):
                    for k, v in divlist.iteritems():
                        if v[-1] < -1:
                            continue
                        if "C" not in k:
                            if v[0] > mpdate:
                                mpdate = v[0]
                            if v[1] > mpdate:
                                mpdate = v[1]
                        else:
                            if v[0] > cdate:
                                cdate = v[0]
                            if v[1] > mpdate:
                                mpdate = v[1]
                return cdate, mpdate

            def mpislater():
                # cdate = pdatec if cpeak and len(pdatec) else ndatec
                # mpdate = pdateMP if mpeak else ndateMP
                cdate = pdatec if len(pdatec) and pdatec > ndatec else ndatec
                mpdate = pdateMP if len(pdateMP) and pdateMP > ndateMP else ndateMP
                return mpdate > cdate

            cmpdiv, mpdiv = 0, 0
            pdatec, pdateMP = getdivdt(pdiv)
            ndatec, ndateMP = getdivdt(ndiv)
            mpnow = mpislater()
            if mpnow:
                mpdiv = 7 if pdateMP > ndateMP else 8
            if pdatec > ndatec:
                cmpdiv = 1 if "CP" in pdiv and "CM" in pdiv else \
                    2 if "CP" in pdiv else 3 if "CM" in pdiv else 7 if "MP" in pdiv else 0
            else:
                cmpdiv = 4 if "CP" in ndiv and "CM" in ndiv else \
                    5 if "CP" in ndiv else 6 if "CM" in ndiv else 8 if "MP" in pdiv else 0
            return cmpdiv, mpdiv, mpnow

        def divHighLow():
            def highlowM2():
                def findpos(opt, li):
                    if len(li) < 4:
                        return -99
                    pos = len(li) - 4
                    li2 = li[pos:]
                    if opt == 1:
                        if li2[0] == max(li2):
                            li2 = li2[1:]
                        m = max(li2)
                    else:
                        if li2[0] == min(li2):
                            li2 = li2[1:]
                        m = min(li2)
                    return m

                if not mpInSync:
                    return False
                m = findpos(1, plistM)
                p = findpos(2, plistP)
                if m == -99 or p == -99:
                    return 0
                if p == plistP[-2] or p == plistP[-3]:
                    if m == plistM[-2]:
                        # 2011-05-12 ORNA
                        return 1
                    elif m == plistM[-3]:
                        # 2015-03-05 ORNA
                        return 2
                return 0

            def highlowM():
                if not mpInSync:
                    return False
                if len(plistM) < 4 or len(plistP) < 4:
                    return False
                if plistM[-2] > plistM[-1] and plistM[-2] > plistM[-3] and \
                    (plistP[-1] > plistP[-2] and (plistP[-2] < plistP[-3] or
                                                  plistP[-2] < plistP[-4])):
                    # 2011-05-12 ORNA
                    return True
                return False

            def highlowP():
                if not mpInSync:
                    return False
                if len(plistM) < 4 or len(plistP) < 4:
                    return False
                if plistP[-2] > plistP[-1] and plistP[-2] > plistP[-3] and \
                    plistM[-1] > plistM[-2] and (plistM[-2] < plistM[-3] or
                                                 plistM[-2] < plistM[-4]):
                    # DUFU 2013-04-05 bearish
                    # VSTECTS 2013-03-04 bullish
                    return True
                return False

            highlowM = highlowM()
            highlowP = highlowP()
            return highlowM, highlowP

        def divLowHigh():
            def lowhighM():
                if not mpInSync:
                    return False
                if len(nlistM) < 3 or len(nlistP) < 4:
                    return False
                if nlistM[-2] < nlistM[-1] and nlistM[-2] < nlistM[-3] and \
                    nlistP[-2] > nlistP[-1] and (nlistP[-2] > nlistP[-3] or
                                                 nlistP[-2] > nlistP[-4]):
                    return True
                return False

            def lowHighP():
                if not mpInSync:
                    return False
                if len(nlistM) < 3 or len(nlistP) < 3:
                    return False
                if nlistP[-2] < nlistP[-1] and nlistP[-2] < nlistP[-3] and \
                    nlistM[-2] > nlistM[-1] and (nlistM[-2] > nlistM[-3] or
                                                 nlistM[-2] > nlistM[-4]):
                    # 2018-10-30 ORNA short rebound due to nlistP[-1] < 0
                    return True
                return False

            lowhighM = lowhighM()
            lowhighP = lowHighP()
            return lowhighM, lowhighP

        cmpdiv, mpdiv, mpnow = divCMP()
        highlowM, highlowP = divHighLow()
        lowhighM, lowhighP = divLowHigh()
        return cmpdiv, mpdiv, mpnow, highlowM, highlowP, lowhighM, lowhighP

    def evalMatrix():
        '''
            pM=2/1/0 (m>=10,m>=5,m<5), nM=2/1/0, pP=/1/0 (p>=0,p<0), nP=/1/0
                     nP    nM    pP    pM
            0     1    0    0    0    0
            1     2    0    0    0    1
            2     3    0    0    0    2
            3     4    0    0    1    0
            4     5    0    0    1    1
            5     6    0    0    1    2
            6     7    0    1    0    0
            7     8    0    1    0    1
            8     9    0    1    0    2
            9    10    0    1    1    0
            a    11    0    1    1    1
            b    12    0    1    1    2
            c    13    0    2    0    0
            d    14    0    2    0    1
            e    15    0    2    0    2
            f    16    0    2    1    0
            g    17    0    2    1    1
            h    18    0    2    1    2
            i    19    1    0    0    0
            j    20    1    0    0    1
            k    21    1    0    0    2
            l    22    1    0    1    0
            m    23    1    0    1    1
            n    24    1    0    1    2
            o    25    1    1    0    0
            p    26    1    1    0    1
            q    27    1    1    0    2
            r    28    1    1    1    0
            s    29    1    1    1    1
            t    30    1    1    1    2
            u    31    1    2    0    0
            v    32    1    2    0    1
            w    33    1    2    0    2
            x    34    1    2    1    0
            y    35    1    2    1    1
            z    36    1    2    1    2
        '''
        pm = "0" if plistM[-1] < 5 else "1" if plistM[-1] < 10 else "2"
        nm = "0" if nlistM[-1] < 5 else "1" if nlistM[-1] < 10 else "2"
        pp = "0" if plistP[-1] < 0 else "1"
        np = "0" if nlistP[-1] < 0 else "1"
        strmp = "".join([pm, nm, pp, np])
        matrix = "0" if strmp == "0000" else \
                 "1" if strmp == "0001" else \
                 "2" if strmp == "0002" else \
                 "3" if strmp == "0010" else \
                 "4" if strmp == "0011" else \
                 "5" if strmp == "0012" else \
                 "6" if strmp == "0100" else \
                 "7" if strmp == "0101" else \
                 "8" if strmp == "0102" else \
                 "9" if strmp == "0110" else \
                 "a" if strmp == "0111" else \
                 "b" if strmp == "0112" else \
                 "c" if strmp == "0200" else \
                 "d" if strmp == "0201" else \
                 "e" if strmp == "0202" else \
                 "f" if strmp == "0210" else \
                 "g" if strmp == "0211" else \
                 "h" if strmp == "0212" else \
                 "i" if strmp == "1000" else \
                 "j" if strmp == "1001" else \
                 "k" if strmp == "1002" else \
                 "l" if strmp == "1010" else \
                 "m" if strmp == "1011" else \
                 "n" if strmp == "1012" else \
                 "o" if strmp == "1100" else \
                 "p" if strmp == "1101" else \
                 "q" if strmp == "1102" else \
                 "r" if strmp == "1110" else \
                 "s" if strmp == "1111" else \
                 "t" if strmp == "1112" else \
                 "u" if strmp == "1200" else \
                 "v" if strmp == "1201" else \
                 "w" if strmp == "2202" else \
                 "x" if strmp == "1210" else \
                 "y" if strmp == "1211" else \
                 "z"
        return matrix

    def evalMatrix2():
        '''
            pM=2/1/0 (m>=10,m>=5,m<5), nM=2/1/0, pP=/1/0 (p>=0,p<0), nP=/1/0
                     pM    nM    pP    nP
            0     1    0    0    0    0
            1     2    0    0    0    1
            2     3    0    0    1    0
            3     4    0    0    1    1
            4     5    0    1    0    0
            5     6    0    1    0    1
            6     7    0    1    1    0
            7     8    0    1    1    1
            8     9    0    2    0    0
            9    10    0    2    0    1
            a    11    0    2    1    0
            b    12    0    2    1    1
            c    13    1    0    0    0
            d    14    1    0    0    1
            e    15    1    0    1    0
            f    16    1    0    1    1
            g    17    1    1    0    0
            h    18    1    1    0    1
            i    19    1    1    1    0
            j    20    1    1    1    1
            k    21    1    2    0    0
            l    22    1    2    0    1
            m    23    1    2    1    0
            n    24    1    2    1    1
            o    25    2    0    0    0
            p    26    2    0    0    1
            q    27    2    0    1    0
            r    28    2    0    1    1
            s    29    2    1    0    0
            t    30    2    1    0    1
            u    31    2    1    1    0
            v    32    2    1    1    1
            w    33    2    2    0    0
            x    34    2    2    0    1
            y    35    2    2    1    0
            z    36    2    2    1    1
        '''
        pm = "0" if plistM[-1] < 5 else "1" if plistM[-1] < 10 else "2"
        nm = "0" if nlistM[-1] < 5 else "1" if nlistM[-1] < 10 else "2"
        pp = "0" if plistP[-1] < 0 else "1"
        np = "0" if nlistP[-1] < 0 else "1"
        strmp = "".join([pm, nm, pp, np])
        matrix = "0" if strmp == "0000" else \
                 "1" if strmp == "0001" else \
                 "2" if strmp == "0010" else \
                 "3" if strmp == "0011" else \
                 "4" if strmp == "0100" else \
                 "5" if strmp == "0101" else \
                 "6" if strmp == "0110" else \
                 "7" if strmp == "0111" else \
                 "8" if strmp == "0200" else \
                 "9" if strmp == "0201" else \
                 "a" if strmp == "0210" else \
                 "b" if strmp == "0211" else \
                 "c" if strmp == "1000" else \
                 "d" if strmp == "1001" else \
                 "e" if strmp == "1010" else \
                 "f" if strmp == "1011" else \
                 "g" if strmp == "1100" else \
                 "h" if strmp == "1101" else \
                 "i" if strmp == "1110" else \
                 "j" if strmp == "1111" else \
                 "k" if strmp == "1200" else \
                 "l" if strmp == "1201" else \
                 "m" if strmp == "1210" else \
                 "n" if strmp == "1211" else \
                 "o" if strmp == "2000" else \
                 "p" if strmp == "2001" else \
                 "q" if strmp == "2010" else \
                 "r" if strmp == "2011" else \
                 "s" if strmp == "2100" else \
                 "t" if strmp == "2111" else \
                 "u" if strmp == "2110" else \
                 "v" if strmp == "2101" else \
                 "w" if strmp == "2200" else \
                 "x" if strmp == "2211" else \
                 "y" if strmp == "2210" else \
                 "z"
        return matrix

    def evalPNsignals():
        def nCompilation():
            nsignals = []
            # sig = "1" if newlowC or (bottomC and cpeak and plistC[-1] < lowbar) else "0"
            # nsignals.append(sig)
            sig = "1" if cmpdiv in bearpeak else "0"
            nsignals.append(sig)
            sig = "1" if cmpdiv == 7 or mpdiv == 7 else "0"
            nsignals.append(sig)
            sig = "1" if tripleM in n3u and lastM < nlistM[-1] else "0"
            nsignals.append(sig)
            sig = "1" if tripleP in n3u and lastP < nlistP[-1] else "0"
            nsignals.append(sig)
            sig = "1" if countP > 3 else "0"
            nsignals.append(sig)
            sig = "1" if highlowP else "0"
            nsignals.append(sig)
            sig = "1" if highlowM else "0"
            nsignals.append(sig)
            return nsignals

        def pCompilation():
            psignals = []
            # sig = "1" if newhighC or (topC and cvalley and nlistC[-1] > highbar) else "0"
            # psignals.append(sig)
            sig = "1" if cmpdiv in bullvalley else "0"
            psignals.append(sig)
            sig = "1" if cmpdiv == 8 or mpdiv == 8 else "0"
            psignals.append(sig)
            sig = "1" if tripleM in n3u and lastM > nlistM[-1] else "0"
            psignals.append(sig)
            sig = "1" if tripleP in n3u and lastP > nlistP[-1] else "0"
            psignals.append(sig)
            sig = "1" if countP > 0 and countP < 4 else "0"
            psignals.append(sig)
            sig = "1" if lowhighP else "0"
            psignals.append(sig)
            sig = "1" if lowhighM else "0"
            psignals.append(sig)
            '''
            sig = "1" if len(plistM) > 1 and not mpeak and \
                nlistM[-2] > 6 and plistM[-1] < 9 and nlistM[-1] > plistM[-2] else "0"
            psignals.append(sig)
            '''
            return psignals

        def nEvaluation():
            if "1" not in nsignals:
                return 0, 0
            nsig, nstate = 0, 0

            if int(nsignals[hlP]):
                if ppeak:
                    # 2013-04-05 DUFU
                    # 2016-07-26 MUDA
                    nsig, nstate = -2, 1
                else:
                    if nlistP[-1] < 0:
                        if nlistM[-1] > 5 and not newlowC:
                            # 2013-03-11 VSTECTS
                            nsig, nstate = 2, 2
                        else:
                            # 2012-04-30 MUDA
                            # 2016-11-06 MUDA newlowC
                            # 2016-11-21 MUDA (wrong hlP shape)
                            nsig, nstate = -2, 3
                    else:
                        nsig, nstate = -2, 0
            elif int(nsignals[hlM]):
                if topP or newlowV and not newhighC:
                    if nlistP[-1] < 0:
                        # 2018-04-03 MUDA
                        nsig, nstate = -3, 1
                    else:
                        # 2010-08-18 KLSE
                        nsig, nstate = 3, 1
                elif newhighC:
                    # 2018-05-08 MUDA
                    nsig, nstate = -3, 2
                else:
                    if nlistM[-1] < 0:
                        # 2017-05-09 MUDA short rebound
                        nsig, nstate = 3, 3
                        if lastM > plistM[-1]:
                            nsig, nstate = -3, 4
                    else:
                        # 2012-07-17 MUDA
                        # 2017-05-09 MUDA
                        nsig, nstate = -3, 5
            elif "1" in nsignals[1:] and (mvalley or pvalley):
                nval = 5 if tripleM in n3u else -5
                nsig = nval
                if plistM[-1] > 10:
                    if lastM < 7:
                        if lastC > plistC[-1] and lastC > plistC[-2]:
                            # 2018-10-31 DANCO
                            nsig, nstate = nval, 0
                        else:
                            nsig, nstate = -nval, 0
                elif plenM > 1 and nlenM > 1 and plistM[-2] > 10:
                    if nlistM[-1] > 5 and nlistM[-1] < 7:
                        if nlistM[-2] > 5 and nlistM[-2] < 7:
                            # MUDA 2013-07-30
                            nsig, nstate = -nval, 2
                        else:
                            nsig, nstate = nval, 3
                elif pvalley and nlenP > 1 and nlistP[-1] > nlistP[-2]:
                    nstate = 0
                elif newhighM or topM:
                    # 2010-01-27 KLSE
                    # 2010-04-28 KLSE
                    nval, nstate = -5, 4
                    if lastM < 5 or lastP < 0:
                        # 2010-06-02 KLSE (could not reach here due to mpeak)
                        nval, nstate = 5, 4
                else:
                    if nlistM[-1] < 0:
                        # 2016-01-21 ORNA
                        nstate = 4
                    else:
                        if nlistP[-1] > nlistP[-2]:
                            # 2010-07-07 KLSE
                            nsig, nstate = nval, 5
                        else:
                            # 2013-01-16 KLSE
                            nsig, nstate = -nval, 5
                    # if nlenM > 1 and nlistM[-1] > nlistM[-2]:
                    #     nstate = 0

            if nstate == 0 and not mpnow and cpeak and "1" not in psignals:
                sig, state = -1, 1
                if topM:
                    sig, state = -1, 1
                    if lastM < 5 or lastP < 0:
                        # 2010-06-02 KLSE
                        sig, state = 1, 1
                elif newlowP or bottomP:
                    if nlistM[-1] < 0:
                        if newlowM or bottomM:
                            # 2011-09-07 ORNA
                            state = 2
                        else:
                            # 2011-09-22 ORNA
                            state = 3
                            if mpInSync or cvalley:
                                # 2013-09-19 ORNA
                                state = -4
                    elif nlistP[-1] < 0:
                        # 2015-09-17 ORNA
                        state = -5
                elif nlistP[-1] < 0:
                    if nlistM[-1] < 5:
                        # 2015-12-11 ORNA
                        # 2016-01-28 ORNA
                        sig, state = -1, 6
                    else:
                        # 2015-05-13 KAWAN
                        sig, state = 1, 6
                    if newlowC:
                        # 2018-02-27 MUDA
                        sig, state = 1, 7
                elif plistM[-1] > 10:
                    # 2013-12-17 MUDA
                    sig, state = 1, 8
                elif tripleP in n3d:
                    if nlistP[-1] > 0:
                        # 2010-02-10 KLSE
                        sig, state = 1, 10
                    else:
                        sig, state = -1, 10
                else:
                    sig, state = -1, 11

                if state != 0:
                    nsig, nstate = sig, state

            '''
                elif nlistP[-1] > nlistP[-2]:
                    sig, state = -1, 5
            if nsig > 0 and nstate > 0 and not (mpeak or ppeak):
                if nlenP > 1 and nlistP[-1] > nlistP[-2]:
                    nstate = 0
                elif nlenM > 1 and nlistM[-1] > nlistM[-2]:
                    nstate = 0
            elif nsig < 0 and nstate and (cpeak or mpeak or ppeak):
                nstate = 0
            '''

            return nsig, nstate

        def pEvaluation():
            def evalLHC(sval):
                sig, state = sval, 0
                if cvalley and int(psignals[divC]):
                    if nlistP[-1] < 0:
                        if prevtopP:
                            # 2013-01-31 ORNA
                            sig, state = -sval, 1
                        else:
                            # 2013-12-19 ORNA
                            sig, state = sval, 2
                    elif highlowM:
                        # 2011-05-12 ORNA
                        sig = -sval if newhighC or newhighP or topP else sval
                        state = 3
                    elif newhighC and newhighM:
                        sig, state = -sval, 4
                    else:
                        # 2014-02-20 ORNA
                        sig = -sval if newhighP or topP else sval
                        state = 5
                elif nlistP[-1] < 0 or cpeak:
                    sig, state = -sval, 0
                else:
                    # 2013-03-12 MUDA
                    sig, state = sval, 6
                return sig, state

            if "1" not in psignals:
                return 0, 0
            psig, pstate = 0, 0

            '''
            # if int(psignals[lowhighC]):
            #     psig, pstate = evalLHC(2)
            if int(psignals[pcnt]):
                if countP < 3:
                    if plistM[-1] < 10 and plistM[-2] < 10:
                        psig, pstate = -2, 1
                    else:
                        psig, pstate = 2, 2
                else:
                    psig, pstate = 2, 3
            # elif int(psignals[n3uP]):
            #     # 2012-08-23 ORNA
            #     if nlistP[-1] > 0 and lastP > nlistP[-1]:
            #         psig, pstate = 3, 1
            #         if newhighC:
            #             # 2012-10-25 ORNA
            #             psig, pstate = -3, 2
            '''
            if mvalley and int(psignals[divMP]):
                if nlistP[-1] < 0:
                    if nlistM[-1] < 0:
                        # 2012-05-15 MUDA
                        psig, pstate = -4, 1
                    else:
                        psig, pstate = -4, 0
                else:
                    if nlistM[-1] > 0:
                        # 2012-06-06 KLSE
                        psig, pstate = 4, 1
                    else:
                        psig, pstate = 4, 0
            elif int(psignals[lhP]):
                if nlistP[-1] >= 0:
                    if nlistM[-1] < 5:
                        # 2009-04-01 KLSE
                        psig, pstate = 5, 1
                    else:
                        # 2012-10-03 KLSE
                        psig, pstate = -5, 1
                else:
                    if lastP < 0:
                        # 2016-11-21 MUDA
                        psig, pstate = -5, 2
                    else:
                        # 2018-10-30 ORNA short rebound due to nlistP[-1] < 0
                        # 2013-03-11 VSTECS
                        psig, pstate = -5, -2
            elif int(psignals[lhM]):
                if nlistP[-1] >= 0:
                    # 2011-07-21 ORNA
                    psig, pstate = 6, 1
                else:
                    if nlistM[-1] > 0:
                        # 2011-11-01 MUDA
                        psig, pstate = 6, 2
                    else:
                        psig, pstate = 6, 0
                        if newlowM and not newlowP:
                            # 2012-01-03 MUDA
                            psig, pstate = 6, 3
                        elif lastP < 0:
                            psig, pstate = -6, 4
                        else:
                            # 2008-07-02 KLSE
                            psig, pstate = -6, 5
            elif int(psignals[divC]) and int(nsignals[divMP]):
                # 2012-09-05 KLSE
                psig, pstate = 7, 0

            if pstate == 0 and mpnow and cvalley and "1" not in nsignals:
                psig, pstate = 1, 1
                if newhighC and bottomM:
                    # 2013-01-03 ORNA
                    psig, pstate = -1, 2
                elif topC and prevbottomC:
                    # 2011-10-25 MUDA
                    psig, pstate = -1, 0
                elif bottomM and bottomP:
                    if nlistM[-5] < 5 and nlistP[-1] < 0:
                        if lastM < 5 and lastP < 0:
                            # 2011-09-14 KLSE
                            psig, pstate = -1, 3
                        else:
                            # 2011-10-25 KLSE
                            psig, pstate = 1, 3
                    else:
                        psig, pstate = 1, 0
                elif tripleM in n3d:
                    if bottomM:
                        if nlistM[-1] > 5:
                            # 2011-09-29 ORNA
                            psig, pstate = -1, 4
                        else:
                            # 2011-10-19 KLSE with bottomP
                            psig, pstate = 1, 4
                    if nlistM[-1] < 5:
                        # 2012-01-04 ORNA
                        # 2016-11-15 MUDA (also lhP)
                        psig, pstate = 1, 0
                        # wrong signal for 2018-12 muda
                        # if lastM > plistM[-3]:
                        #     pstate = 1
                    elif tripleP in n3d and tripleV in n3d:
                        if nlistP[-1] < 0 and not bottomP:
                            # 2014-11-27 ORNA
                            psig, pstate = 1, 0
                            if lastP < 0 and lastP > nlistP[-1]:
                                pstate = 4
                elif isretrace():
                    psig, pstate = 1, -5
                else:
                    if nlistP[-1] >= 0:
                        psig, pstate = 1, 6
                    else:
                        psig, pstate = -1, 7

            return psig, pstate

        divC, divMP, n3uM, n3uP, pcnt = 0, 1, 2, 3, 4
        hlP, hlM, lhP, lhM = 5, 6, 5, 6
        nsignals = nCompilation()
        psignals = pCompilation()
        nsig, nstate = nEvaluation()
        psig, pstate = pEvaluation()

        if not psig and "1" in psignals and "1" not in nsignals:
            if int(psignals[divC]):
                if newhighV or topV:
                    # 2012-08-02 ORNA
                    psig, pstate = 99, 1
                    if newhighP:
                        psig, pstate = -99, 0
                    if newhighC and (topP or topV):
                        # 2015-01-29 ORNA
                        # 2011-06-28 MUDA
                        psig, pstate = -99, 1
                elif prevtopC and not (newhighM or newhighP):
                    psig, pstate = -99, 0
                    if mpeak or ppeak:
                        pstate = 2
                elif isretrace():
                    # 2013-03-13 ORNA lowerV and bottomV
                    # 2015-01-08 ORNA
                    psig, pstate = 99, 3
                else:
                    if nlistP[-1] < 0:
                        if newhighC:
                            # 2013-11-14 ORNA
                            psig, pstate = 99, -4
                        else:
                            if mpeak:
                                # 2018-04-19 DANCO
                                psig, pstate = -99, 5
                            else:
                                if tripleP in n3u:
                                    # 2018-06-07 DANCO
                                    psig, pstate = 99, -6
                                else:
                                    psig, pstate = 99, 0
                    elif nlistM[-1] < 5:
                        # 2011-06-01 KLSE
                        psig, pstate = -99, 7
                    else:
                        if newhighC:
                            # 2014-01-09 ORNA
                            psig, pstate = 99, 8
                        elif newhighM:
                            # 2009-08-19 KLSE
                            psig, pstate = 99, 9
                        else:
                            # 2017-03-14 MUDA
                            psig, pstate = -99, 10
            else:
                psig = -97 if cpeak else 97
                pstate = 0 if mpeak or ppeak else -1 if posC < 2 else 1
        elif not nsig and "1" in nsignals and "1" not in psignals:
            nsig = -98 if cpeak else 98
            if int(nsignals[divC]):
                nsig, nstate = -98, 2
                if newlowP and not newlowM:
                    # 2013-09-05 ORNA
                    nstate = 0
            else:
                nstate = 0 if cpeak or mpeak or ppeak else 1

        return psig, pstate, nsig, nstate, nsignals, psignals

    # ------------------------- START ------------------------- #

    def evalMPV():
        if plistV is None:
            print "plistV is none: %s" % (lastTrxn[0])
            return 0, 0, 0, 0, 0, 0
        if len(plistV) < 2:
            print "BAD plistV: %s" % (lastTrxn[0])
            return 0, 0, 0, 0, 0, 0
        mvalP = \
            1 if plistM[-1] <= 5 else \
            2 if plistM[-2] <= 5 else 0
        pvalP = \
            1 if plistP[-1] <= 0 else \
            2 if plistP[-2] <= 0 else 0
        vvalP = \
            1 if plistV[-1] <= 0 else \
            2 if plistV[-2] <= 0 else 0
        mvalN = \
            1 if nlistM[-1] >= 10 else \
            2 if nlistM[-2] >= 10 else 0
        pvalN = \
            1 if nlistP[-1] > 0 else \
            2 if nlistP[-2] > 0 else 0
        vvalN = \
            1 if nlistV[-1] > 0 else \
            2 if nlistV[-2] > 0 else 0
        return mvalP, pvalP, vvalP, mvalN, pvalN, vvalN

    def evalLowC2(sval):
        sig, state = 0, 0
        if plistM[-1] == max(plistM[-3:]):
            sval2 = sval + 2
            if nlistM[-1] == max(nlistM[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if nlistM[-1] > 10:
                        # 2014-03-07 DUFU
                        sig, state = sval2, 1
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == min(nlistP[-3:]):
                    if bottomP:
                        if isprev3bottomP():
                            if isprev3bottomM():
                                if topV:
                                    # 2019-01-02 KESM
                                    sig, state = sval2, 5
                elif nlistM[-1] > min(nlistM[-3:]):
                    if min(plistM[-3:]) <= 5:
                        if max(nlistP[-3:]) < 0:
                            if newlowM:
                                # 2009-03-18 KLSE
                                sig, state = sval2, 10
                    elif max(plistM[-3:]) < 10:
                        if nlistP[-1] < 0:
                            # 2018-06-22 DANCO
                            sig, state = sval2, 20
        elif plistM[-1] == min(plistM[-3:]):
            sval3 = sval + 3
            if nlistM[-1] == min(nlistM[-3:]):
                if PislowPlowN():
                    if bottomM or prevbottomM:
                        if newlowP:
                            if prevbottomM or newlowM or lastM <= 5:
                                # 2014-11-03 'F&N'
                                sig, state = sval3, 5
                            elif max(plistM[-3:]) < 10:
                                if vvalley or lastM > plistM[-1]:
                                    # 2014-10-16 F&N
                                    sig, state = sval3, 1
                                else:
                                    # 2014-10-02 F&N
                                    sig, state = sval3, -1
                elif PishighPhighN():
                    pass
                elif prevbottomM:
                    if isprev3topP():
                        if isprev3bottomP():
                            if min(nlistP[-3:]) > 0:
                                if nlistM[-1] < 5:
                                    # 2008-10-24 CARLSBG
                                    sig, state = sval3, 20
            elif plistP[-1] == min(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if isprev3topP():
                        if bottomM:
                            if nlistM[-1] > 5:
                                # 2018-03-22 DANCO
                                sig, state = -sval3, -30
                elif nlistP[-1] == min(nlistP[-3:]):
                    if max(plistM[-3:]) < 10:
                        if min(nlistM[-3:]) > 5:
                            # 2014-09-18 F&N
                            sig, state = -sval3, 32
                elif plistM[-1] <= 5:
                    if newlowM:
                        # 2008-10-06 KLSE
                        sig, state = -sval3, 40
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == min(nlistP[-3:]):
                    if plistM[-1] < 5:
                        # 2019-01-03 KESM
                        sig, state = sval3, 45
                    elif bottomP:
                        if isprev3bottomP():
                            # 2019-01-03 KESM
                            sig, state = sval3, 46
            elif isprev3bottomM():
                if isprev3topM():
                    if nlistM[-1] == max(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2014-10-03 CARLSBG nlistP[-1] > 0
                            sig, state = -sval3, 50
                    else:
                        # 2014-11-04 CARLSBG
                        sig, state = sval3, 50
                elif newlowM:
                    if newlowP:
                        # 2018-03-09 AXREIT
                        sig, state = sval3, 55
        elif plistP[-1] == max(plistP[-3:]):
            sval4 = sval + 4
            if nlistP[-1] == min(nlistP[-3:]):
                if bottomP:
                    if isprev3bottomP():
                        if isprev3bottomM():
                            if topV:
                                # 2019-01-02 KESM
                                sig, state = sval4, 10
            elif topP:
                if isprev3topP():
                    pass
                elif isprev3bottomP():
                    if nlistM[-1] == max(nlistM[-3:]):
                        if newhighV:
                            # 2009-04-01 N2N
                            sig, state = sval4, 1
        elif plistP[-1] == min(plistP[-3:]):
            sval5 = sval + 5
            if nlistP[-1] == min(nlistP[-3:]):
                if plistM[-1] == min(plistM[-3:]):
                    if nlistM[-1] > min(nlistM[-3:]):
                        if topV:
                            if prevbottomV:
                                # 2014-09-26 F&N
                                sig, state = -sval5, 5
            if nlistM[-1] == min(nlistM[-3:]):
                if newlowP:
                    # 2015-08-21 KLSE
                    sig, state = sval5, 10
            elif topV:
                # 2015-09-08 KLSE
                sig, state = -sval5, -10

        else:
            sval0 = sval
        return sig, state

    def evalLowC(sval):
        sig, state = 0, 0
        if bottomM:
            sval1 = sval + 1
            if not isprev3topM():
                if newlowP:
                    if not (isprev3bottomP() or isprev3topP()):
                        if plistM[-1] == min(plistM[-3:]):
                            if plistP[-1] == min(plistP[-3:]):
                                if nlistP[-1] == min(nlistP[-3:]):
                                    if vvalley or lastM > plistM[-1]:
                                        # 2014-10-16 F&N
                                        sig, state = sval1, 1
                                    else:
                                        # 2014-10-02 F&N topV
                                        sig, state = sval1, -1
                elif isprev3topP() and not (newlowP or bottomP):
                    if plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            if nlistM[-1] > 5:
                                # 2018-03-22 DANCO
                                sig, state = -sval1, -2
            elif isprev3bottomP():
                if isprev3topP():
                    if newlowV:
                        if isprev3topV():
                            # 2019-01-02 KLSE
                            sig, state = sval1, 0
        elif newhighM:
            sval2 = sval + 2
        elif newlowM or lastM == min(nlistM):
            sval3 = sval + 3
            if not (isprev3topM() or isprev3topP()):
                if newlowP:
                    if min(nlistM[-3:]) < 5:
                        if nlistP[-1] == min(nlistP[-3:]) and nlistP[-1] < 0:
                            if plistP[-1] > min(plistP[-3:]):
                                # 2018-03-09 AXREIT
                                sig, state = sval3, 1
                    elif plistM[-1] == min(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]):
                            if nlistM[-1] <= 5:
                                if bottomM:
                                    # 2014-11-03 F&N bottomM
                                    sig, state = sval3, 2
                                else:
                                    sig, state = sval3, 3
                        else:
                            if plistP[-1] == min(plistP[-3:]):
                                if nlistP[-1] == min(nlistP[-3:]):
                                    # 2014-09-26 F&N
                                    sig, state = -sval3, 3
                                    if tripleM in n3d and nlistM[-1] >= 5:
                                        # 2014-11-03 F&N
                                        sig, state = sval3, 4
                elif isprev3bottomM() and isprev3bottomP():
                    if plistM[-1] == max(plistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]):
                            # 2009-03-18 KLSE
                            sig, state = sval3, 5
                    elif plistM[-1] <= 5:
                        # 2008-10-06 KLSE
                        # 2008-12-01 KLSE
                        sig, state = -sval3, 5
        elif newlowP:
            sval4 = sval + 4
            if prevbottomP:
                if prevbottomM:
                    # 2014-11-04 F&N picked up under newlowM
                    sig, state = sval4, 1
            elif topV:
                if not (newlowM or bottomM):
                    if min(nlistM[-3:]) > 5:
                        # 2014-09-18 F&N
                        sig, state = -sval4, 2
                    elif isprev3bottomP():
                        # 2008-10-24 CARLSBG
                        # 2015-09-08 KLSE
                        sig, state = -sval4, -2
            elif newhighV or prevbottomM:
                if isprev3topP() and isprev3bottomP():
                    # 2015-08-21 KLSE
                    sig, state = sval4, 3
        elif bottomP:
            sval5 = sval + 5
            if topV and plistM[-1] < 5:
                # 2019-01-03 KESM
                sig, state = sval5, 1
        elif newhighV:
            sval6 = sval + 6
            if topP:
                if isprev3bottomP():
                    if isprev3topM():
                        if max(plistM[-3:]) > 10:
                            if max(nlistP[-3:]) < 0:
                                # 2009-04-01 N2N
                                sig, state = sval6, 1
        else:
            sval0 = sval + 0
            if prevtopM:
                if isprev3bottomP() and isprev3topP():
                    if nlistP[-1] > 0 and tripleP in n3u:
                        # 2014-03-07 DUFU
                        sig, state = sval0, 1
            elif isprev3bottomM():
                if isprev3topM():
                    if nlistM[-1] > 5:
                        if nlistP[-1] == min(nlistP[-3:]):
                            # 2014-11-04 CARLSBG
                            sig, state = sval0, 2
                elif not (bottomP or newlowP or topP or prevtopP):
                    if plistM[-1] == max(plistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]):
                            if min(nlistM[-3:]) > 5:
                                if nlistP[-1] == max(nlistP[-3:]) and nlistP[-1] < 0:
                                    # 2018-06-22 DANCO
                                    sig, state = sval0, 3
        return sig, state

    def evalBottomC(sval):
        sig, state = 0, 0
        if newhighM:
            sval1 = sval + 1
            if bottomM:
                if isprev3topM():
                    if isprev3bottomP():
                        # 2015-04-02 PADINI
                        sig, state = sval1, -1
            elif newhighP:
                if plistM[-1] == max(plistM[-3:]):
                    if plistP[-1] == max(plistP[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                if max(nlistM[-3:]) < 5:
                                    # 2009-04-22 KLSE
                                    sig, state = sval1, 1
                                else:
                                    # 2015-03-03 CARLSBG
                                    sig, state = -sval1, -1
            elif prevtopM:
                if prevtopP:
                    if nlistM[-1] == max(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2009-08-04 KLSE
                            sig, state = sval1, 2
            elif isprev3bottomM():
                if plistM[-1] < 10:
                    if (nlistM[-1] > 5 and (nlistM[-1] > nlistM[-2] or
                                            nlistM[-1] > nlistM[-3])):
                        if nlistP[-1] < 0:
                            if nlistP[-2] > 0:
                                # 2014-12-11 CARLSBG
                                sig, state = sval1, 3
                            elif narrowP == 4 or nlistP[-3] > 0:
                                # 2015-09-17 PADINI
                                sig, state = sval1, -3
                elif topP and not isprev3bottomP():
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            # 2013-12-24 DUFU
                            sig, state = -sval1, 4
            elif nlistP[-1] > 0 and nlistP[-2] < 0:
                if newhighP or newhighV:
                    # 2015-03-03 CARLSBG
                    sig, state = -sval1, -5
                elif topV and lastV < 0:
                    # 2015-04-16 CARLSBG
                    sig, state = -sval1, 5
            elif not (isprev3bottomP() or isprev3topP()):
                if min(nlistM[-3:]) > 5:
                    if max(nlistP[-3:]) < 0:
                        # 2013-05-13 KESM
                        sig, state = sval1, -6
                elif nlistM[-1] > 5:
                    if nlistP[-1] > 0:
                        # 2017-01-18 KLSE
                        sig, state = sval1, 7
        elif newlowM or lastM == min(nlistM):
            sval2 = sval + 2
            if vvalN == 1:
                if nlistP[-1] > 0 and \
                        nlistP[-1] == max(nlistP[-3:]) and \
                        plistP[-1] == max(plistP[-3:]):
                    # 2013-09-04 KESM plistV[-2] < 0 [kesm-1-start]
                    sig, state = sval2, 2
        elif newhighP:
            sval3 = sval + 3
            if bottomM:
                if bottomP:
                    if plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            # 2014-12-03 F&N
                            sig, state = sval3, 1
                elif isprev3topM():
                    if isprev3bottomP():
                        if prevtopV and newhighV:
                            # 2014-03-14 PADINI
                            sig, state = -sval3, -1
            elif bottomP:
                if plistM[-1] == min(plistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if max(plistM[-3:]) < 10:
                            # 2015-10-07 KLSE
                            sig, state = -sval3, 2
            elif not isprev3topM() and isprev3bottomM():
                if not (isprev3topP() or isprev3bottomP()):
                    if min(nlistM) > 5:
                        if plistM[-1] > 10 and nlistP[-1] < 0:
                            # 2018-09-04 DANCO
                            sig, state = -sval3, -3
        elif topM:
            sval4 = sval + 4
            if topP:
                if max(plistM[-3:]) < 10:
                    if min(nlistM[-3:]) > 5:
                        # 2015-05-06 CARLSBG
                        sig, state = -sval4, 1
                    elif max(nlistM[-3:]) < 5:
                        if nlistP[-1] == max(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                # 2009-07-07 KLSE
                                sig, state = sval4, 1
                elif nlistM[-1] > min(nlistM[-3:]):
                    if nlistP[-1] > min(nlistP[-3:]):
                        if nlistM[-1] < 5:
                            if nlistP[-1] > 0:
                                # 2009-06-25 KLSE
                                sig, state = sval4, 2
            elif prevtopP:
                if plistM[-1] > 10:
                    if min(nlistM[-3:]) > 5:
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2009-05-06 PADINI
                            sig, state = sval4, -3
            elif isprev3bottomM():
                if plistM[-1] < 10:
                    if (nlistM[-1] > 5 and (nlistM[-1] > nlistM[-2] or
                                            nlistM[-1] > nlistM[-3])):
                        if narrowP == 4:
                            # 2015-10-01 PADINI
                            sig, state = sval4, 4
            else:
                if nlistM[-1] == max(nlistM[-3:]):
                    if plistP[-1] == max(plistP[-3:]):
                        if min(nlistM[-3:]) < 5 and min(nlistP[-3:]) < 0:
                            if nlistM[-1] > 5 and nlistP[-1] > 0:
                                # 2017-02-02 KLSE long range until 2017-05-03
                                # correction: 2017-03-31 became isprev3bottomM
                                sig, state = sval4, 99
        elif bottomP:
            sval5 = sval + 5
        elif prevbottomM:
            sval6 = sval + 6
            if isprev3topM():
                if not (isprev3bottomP() or isprev3topP()):
                    # 2014-08-04 CARLSBG
                    sig, state = -sval6, 1
            elif isprev3topP():
                if isprev3bottomP():
                    if nlistM[-1] < 5:
                        if nlistP[-1] < 0:
                            if max(plistM[-3:]) < 8:
                                # 2015-08-05 KLSE newlowV
                                sig, state = -sval6, 2
        elif newhighV:
            sval7 = sval + 7
            if bottomV:
                if not (isprev3bottomM() or isprev3topM()):
                    if not (isprev3bottomP() or isprev3topP()):
                        if tripleP in p3d or tripleP in n3d:
                            # 2014-07-02 F&N
                            sig, state = -sval7, 1
            elif isprev3topM() and not isprev3bottomM():
                if isprev3topP() and isprev3bottomP():
                    if tripleM in p3d:
                        # 2009-07-31 CARLSBG
                        sig, state = -sval7, 2
        elif newlowV:
            sval8 = sval + 8
            if vvalN:
                if isprev3topV():
                    # 2011-12-09 DUFU
                    sig, state = -sval8, 1
                elif isprev3bottomM() and not isprev3bottomP():
                    if narrowP == 4:
                        # 2015-08-04 PADINI
                        sig, state = sval8, 1
            elif prevbottomV:
                if not (isprev3bottomM() or isprev3topM()):
                    if not (isprev3bottomP() or isprev3topP()):
                        if plistM[-1] == min(plistM[-3:]):
                            if nlistM[-1] == max(nlistM[-3:]):
                                if min(nlistM[-3:]) > 5:
                                    # 2014-06-10 F&N
                                    sig, state = -sval8, 2
                                else:
                                    # 2017-01-04 KLSE
                                    sig, state = sval8, 2
                        elif tripleP in p3d or tripleP in n3d:
                            if min(nlistM[-3:]) > 5:
                                # 2014-07-24 F&N
                                sig, state = -sval8, 3
                            else:
                                # 2017-01-03 KLSE
                                sig, state = sval8, 3
            elif isprev3bottomP():
                if isprev3topM() and isprev3topP():
                    if tripleM in p3d:
                        if nlistM[-1] == max(nlistM[-3:]) and \
                                nlistP[-1] == max(nlistP[-3:]):
                            # 2009-07-01 CARLSBG
                            sig, state = sval8, 4
        else:
            sval0 = sval
            if narrowP == 3 and tripleP == 2:
                if isprev3bottomM():
                    if isprev3bottomP():
                        if max(plistM[-3:]) < 10:
                            if plistM[-1] == min(plistM[-3:]):
                                if plistP[-1] == max(plistP[-3:]) and \
                                        nlistP[-1] == max(nlistP[-3:]):
                                    if nlistP[-1] < 0:
                                        if nlistM[-1] > 5:
                                            if pvalley:
                                                # 2014-02-25 CARLSBG
                                                sig, state = sval0, -1
                                            else:
                                                # 2014-03-27 CARLSBG
                                                sig, state = -sval0, -1
        return sig, state

    def evalRetrace(sval):
        sig, state = 0, 0
        if newhighM and newhighP and newhighV:
            if isprev3bottomM() and isprev3bottomP():
                if tripleM in n3u:
                    if narrowP == 9:
                        # 2018-08-02 DUFU
                        sig, state = sval, 99
        elif newlowM and newlowP and newlowV:
            if topP and topV:
                if isprev3bottomM():
                    # 2018-07-02 KLSE
                    sig, state = sval, 98
        elif bottomP:
            sval1 = sval + 1
            if prevtopP:
                if newlowM:
                    if topV and newlowV:
                        # 2018-07-04 KLSE
                        sig, state = sval1, 1
                elif plistM[-1] > 10:
                    if min(nlistM[-3:]) > 5:
                        if nlistM[-1] == min(nlistM[-3:]):
                            if min(nlistP[-3:]) > 0:
                                if vvalley and lastV > 0 and lastV > plistV[-1]:
                                    # 2014-11-20 DUFU
                                    sig, state = -sval1, -1
            elif isprev3topP():
                if bottomM:
                    if plistP[-1] < 0 and plistV[-1] < 0:  # pvalP == 1 and vvalP == 1:
                        if tripleM == 6 and tripleP in n3d:
                            # 2015-01-19 KESM [kesm-2-start]
                            sig, state = sval1, 2
                    elif plistV[-1] < 0:  # vvalP == 1:
                        if plistM[-1] == min(plistM[-3:]):
                            # 2015-08-06 DUFU bottomM
                            sig, state = sval1, 3
                elif newhighP:
                    if isprev3bottomM():
                        if nlistM[-1] > 5 and nlistM[-1] > min(nlistM[-3:]):
                            if plistP[-1] == min(plistP[-3:]):
                                # 2011-11-01 PADINI
                                sig, state = sval1, 4
                elif not newlowM:
                    if plistM[-1] == min(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]):
                            if plistP[-1] == min(plistP[-3:]):
                                if lastM <= 5 or lastP < 0:
                                    # 2016-03-16 KESM
                                    sig, state = sval1, -5
                                else:
                                    # 2016-04-25 KESM [kesm-3-start]
                                    sig, state = sval1, 5
                        elif plistM[-1] < 5:
                            # 2018-12-04 F&N
                            sig, state = sval1, 6
            elif bottomM:
                if isprev3bottomM():
                    if bottomP:
                        if topV and newlowV:
                            if topM or plistP[-1] < 0:
                                if topM:
                                    # 2019-01-02 PADINI
                                    sig, state = sval1, 7
                                else:
                                    # 2013-10-02 CARLSBG
                                    sig, state = -sval1, 7
                            elif max(plistM[-3:]) > 10:
                                # 2018-05-07 KESM
                                sig, state = -sval1, -8
                            else:
                                # 2011-10-10 KLSE
                                sig, state = sval1, 8
            elif isprev3bottomM():
                if plistP[-1] == min(plistP[-3:]):
                    if nlistM[-1] > 5 and nlistM[-1] > min(nlistM[-3:]):
                        # 2011-10-04 PADINI
                        sig, state = sval1, 9
                elif isprev3bottomP():
                    if topV:
                        if plistM[-1] == max(plistM[-3:]):
                            if plistM[-1] < 10:
                                if plistP[-1] == max(plistP[-3:]):
                                    # 2018-11-26 KESM
                                    sig, state = -sval1, 9
            elif isprev3bottomP():
                if plistP[-1] > plistP[-2]:
                    if max(plistM[-3:]) < 10:
                        if min(nlistM[-3:]) > 5:
                            if plistM[-1] == min(plistM[-3:]):
                                if nlistM[-1] == max(nlistM[-3:]):
                                    if newhighV or posP > 2:
                                        # 2015-02-04 KLSE
                                        sig, state = sval1, -10
                                    else:
                                        # 2015-01-07 KLSE
                                        sig, state = sval1, 10
        elif newhighM:
            sval2 = sval + 2
            if isprev3topM():
                if isprev3topP():
                    if nlistM[-1] == max(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if nlistM[-1] > 5 and nlistP[-1] > 0:
                                # 2009-12-04 PADINI
                                sig, state = sval2, 1
            elif isprev3bottomM():
                if isprev3bottomP():
                    if nlistM[-1] > 5:
                        if plistM[-1] == min(plistM[-3:]):
                            if nlistM[-1] == max(nlistM[-3:]):
                                if nlistP[-1] == max(nlistP[-3:]):
                                    if prevbottomV:
                                        # 2018-08-02 KESM
                                        sig, state = -sval2, 2
                    if not (topM or topP or isprev3topM() or isprev3topP()):
                        if tripleM in p3d:
                            # 2018-08-07 KESM
                            sig, state = -sval2, 3
                        if plistM[-1] == min(plistM[-3:]):
                            if nlistM[-1] < nlistM[-3]:
                                if nlistP[-1] < nlistP[-3]:
                                    # 2012-04-03 F&N
                                    sig, state = -sval2, 4
            elif isprev3topP():
                if not isprev3bottomM() and max(plistM) < 10:
                    if nlistM[-1] < 5 and nlistP[-1] < 0:
                        # 2016-07-05 CARLSBG
                        sig, state = sval2, 5
            elif not isprev3bottomP():
                if max(plistM[1:]) < 10 and tripleM in n3u:
                    if nlistM[-1] > 5 and nlistP[-1] < 0:
                        # 2017-11-02 F&N
                        sig, state = sval2, 6
        elif newlowM or lastM == min(nlistM):
            sval3 = sval + 3
            if newlowP:
                if topP:
                    if not isprev3bottomM():
                        if nlistM[-1] > 5 and max(plistM) < 10:
                            if lastM < 5:
                                # 2016-05-06 CARLSBG
                                sig, state = sval3, 1
                elif topM:
                    if prevbottomM:
                        if isprev3topP():
                            if isprev3bottomP():
                                # 2018-12-04 PADINI
                                sig, state = -sval3, 1
                elif isprev3topM():
                    if isprev3topP():
                        if plistP[-1] < 0:
                            # 2014-12-15 KESM kesm-2-start - reclassified under topC
                            sig, state = sval3, -1
                    elif isprev3bottomM():
                        if isprev3bottomP():
                            if plistM[-1] == min(plistM[-3:]):
                                if nlistM[-1] == max(nlistM[-3:]):
                                    # 2014-02-04 PADINI if prevtopV and nlistV[-1] > 0:
                                    sig, state = sval3, 2
                elif prevbottomM:
                    if max(plistM[-3:]) < 10 and plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] <= 0:
                            # 2017-12-05 DUFU
                            sig, state = -sval3, -3
                        elif topV and lastV < min(nlistV[-3:]):
                            # 2011-09-26 KLSE
                            sig, state = sval3, 3
                elif max(plistM[-3:]) < 10 and min(nlistM[-3:]) > 5:
                    if plistM[-1] == max(plistM[-3:]) and nlistM[-1] == min(nlistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]) and nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2017-10-06 DUFU
                                sig, state = -sval3, -4
                elif prevbottomP and plistP[-1] < 0:
                    # 2013-09-04 CARLSBG
                    sig, state = -sval3, 4
            elif topP:
                if nlistP[-1] == max(nlistP[-3:]):
                    if lastP < nlistP[-1]:
                        # 2016-05-16 CARLSBG
                        sig, state = sval3, 4
                    else:
                        # 2013-12-04 KESM
                        sig, state = sval3, -4
            elif topM:
                if prevbottomP:
                    if isprev3topP():
                        if isprev3bottomM():
                            if plistP[-1] > max(nlistP):
                                # 2018-10-22 KLSE
                                sig, state = -sval3, 5
                if nlistM[-1] == min(nlistM[-3:]) and nlistM[-1] < 5:
                    if plistP[-1] == max(plistP[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                # 2013-05-02 PADINI
                                sig, state = -sval3, -5
            elif isprev3topP():
                if isprev3bottomP():
                    if max(plistM[-3:]) < 10:
                        if nlistM[-1] == min(nlistM[-3:]) and nlistM[-1] > 5:
                            # 2015-05-11 KLSE
                            sig, state = -sval3, 6
            else:
                '''
                elif not (isprev3bottomM() or isprev3topM()):
                    if not (isprev3bottomP() or isprev3topP()):
                '''
                if max(plistM[-3:]) < 10:
                    if min(nlistM[-3:]) > 5:
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                if newhighV:
                                    # 2010-04-02 F&N
                                    sig, state = sval3, 8
                                elif min(nlistP[-3:]) > 0:
                                    if plistM[-1] > plistM[-2]:
                                        # 2017-11-02 KLSE
                                        sig, state = sval3, -8
                        elif plistP[-1] == min(plistP[-3:]):
                            if min(nlistP[-3:]) > 0:
                                # 2017-10-03 KLSE
                                sig, state = -sval3, 8
                elif plistM[-1] > 10 and nlistM[-1] > 0:
                    # 2015-12-02 F&N lastM == minM
                    sig, state = sval3, 9
        elif newhighP:
            sval4 = sval + 4
            if prevtopM:
                if isprev3bottomM():
                    if plistM[-1] > 10 and nlistM[-2] < 5:
                        if narrowP == 3:
                            # 2013-06-03 PADINI
                            sig, state = -sval4, 1
            elif isprev3topP():
                if tripleP in n3u:
                    if plistM[-1] == min(plistM[-3:]) and max(plistM) < 10:
                        if nlistM[-1] > 5 and min(nlistM[-3:]) > 5:
                            # 2016-03-02 CARLSBG
                            sig, state = sval4, 1
        elif newlowP:
            sval5 = sval + 5
            if bottomM:
                if max(plistM[-3:]) < 10:
                    if plistM[-1] == max(plistM[-3:]) and nlistM[-1] == min(nlistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]) and nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2017-10-20 DUFU
                                sig, state = -sval5, 1
            elif topP:
                if not isprev3bottomM():
                    if max(plistM) < 10:
                        if nlistM[-1] > 5:
                            if lastM < 5:
                                # 2016-05-06 CARLSBG
                                sig, state = sval5, 1
                    elif min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            if plistM[-1] == min(plistM[-3:]):
                                # 2014-09-05 DUFU
                                sig, state = -sval5, -2
                            else:
                                # 2015-03-02 DUFU
                                sig, state = sval5, 2
            elif topM:
                if nlistM[-1] > min(nlistM[-3:]):
                    if plistP[-1] < max(plistP[-3:]) and plistP[-1] > min(plistP[-3:]):
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                # 2009-02-24 F&N
                                sig, state = sval5, -3
                                if tripleM == 9 and (lastM <= 10 or lastP <= 0):
                                    # 2009-03-02 F&N
                                    sig, state = sval5, 3
            elif prevbottomP:
                if isprev3topM():
                    if prevbottomM:
                        if nlistM[-1] < 5 and nlistP[-1] < 0:
                            # 2018-10-17 CARLSBG
                            sig, state = sval5, 5
                    elif plistM[-1] == min(plistM[-3:]) and plistM[-1] > max(nlistM[-3:]):
                        if min(nlistM[-3:]) > 5 and nlistM[-1] > nlistM[-2]:
                            if tripleP == 6:
                                if plistP[-1] < 0:
                                    # 2011-10-03 CARLSBG
                                    sig, state = sval5, 6
                    elif tripleM == 9:
                        if nlistM[-1] > 10:
                            # 2009-03-18 F&N
                            sig, state = sval5, 7
            elif isprev3topM():
                if isprev3topP():
                    if plistM[-1] == min(plistM[-3:]) and plistM[-1] > max(nlistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]) and nlistM[-1] > 5:
                            if plistP[-1] == min(plistP[-3:]) and plistP[-1] < max(nlistP[-3:]):
                                if nlistP[-1] == min(nlistP[-3:]):
                                    # 2011-08-12 CARLSBG
                                    sig, state = -sval5, 8
                elif MislowPlowN():
                    if plistP[-1] > plistP[-2]:
                        if min(nlistM[-3:]) >= 5:
                            if min(nlistP[-3:]) >= 0:
                                if newhighV:
                                    # 2014-12-04 KLSE
                                    sig, state = -sval5, 9
                                else:
                                    # 2014-12-26 KLSE
                                    sig, state = sval5, -9
            elif isprev3bottomM():
                if isprev3bottomP():
                    if tripleP in p3d:
                        # 2011-08-19 PADINI
                        sig, state = -sval5, 10
                    elif topV:
                        if plistM[-1] == max(plistM[-3:]):
                            if plistM[-1] < 10:
                                if plistP[-1] == max(plistP[-3:]):
                                    if nlistP[-1] == max(nlistP[-3:]):
                                        # 2018-11-02 KESM
                                        sig, state = -sval5, 11
        elif bottomM:
            sval6 = sval + 6
            if prevtopM:
                if isprev3topP() and not isprev3bottomP():
                    if plistM[-1] >= 10 and nlistM[-1] < 5 and nlistP[-1] < 0:
                        # 2016-12-28 CARLSBG
                        sig, state = sval6, 1
                elif plistP[-1] == min(plistP[-3:]):
                    if nlistP[-1] == min(nlistP[-3:]):
                        if nlistP[-1] > 0 or newhighV:
                            # 2017-12-04 KLSE
                            sig, state = sval6, 2
            elif max(plistM[-3:]) < 10:
                if plistM[-1] == max(plistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2017-10-20 DUFU
                                sig, state = -sval6, 1
                        elif plistV[-1] < 0:
                            # 2017-11-01 DUFU
                            sig, state = -sval6, 2
                elif plistM[-1] == min(plistM[-3:]):
                    if nlistM[-1] > 5:
                        if not (isprev3topP() or isprev3bottomP()):
                            if min(nlistP[-3:]) > 0:
                                # 2010-05-04 F&N
                                sig, state = sval6, 3
                elif tripleP == 6:
                    if nlistP[-1] > 0 or newhighV:
                        # 2017-12-04 KLSE
                        sig, state = sval6, 4
        elif topP:
            sval7 = sval + 7
            if isprev3bottomP():
                if not (isprev3bottomM() or isprev3topM()):
                    # 2016-04-04 CARLSBG
                    sig, state = sval7, -1
                    if lastM < 5 or lastP < 0:
                        # 2016-05-16 CARLSBG
                        sig, state = sval7, 1
        elif topM:
            sval8 = sval + 8
            if nlistM[-1] < max(nlistM[-3:]):
                if plistP[-1] < max(plistP[-3:]) and plistP[-1] > min(plistP[-3:]):
                    if nlistP[-1] == min(nlistP[-3:]):
                        if nlistP[-1] > 0:
                            # 2009-02-02 F&N
                            sig, state = -sval8, 1
        elif newhighV or newlowV or bottomV or prevbottomV:
            sval9 = sval + 9
            if bottomV or prevbottomV:
                st = 50
                if lastV > max(plistV[-3:]):
                    if prevbottomM:
                        if prevbottomP:
                            if nlistM[-1] < 5 and nlistP[-1] < 0:
                                # 2012-02-09 F&N
                                sig, state = sval9, st + 1
                elif MislowPlowN():
                    if PislowPlowN():
                        # if min(nlistM[-3:]) >= 5:
                        # if min(nlistP[-3:]) >= 0:
                        if prevbottomV:
                            # 2014-11-04 KLSE
                            sig, state = -sval9, st + 1
                        else:
                            # 2018-07-10 PARAMON
                            sig, state = sval9, st + 2
            if prevbottomP:
                if plistP[-1] < 0:
                    if nlistM[-1] > min(nlistM[-3:]):
                        if min(nlistM[-3:]) > 5:
                            # 2017-02-02 PADINI
                            sig, state = sval9, 1
                elif plistP[-1] == max(plistP[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        if nlistM[-1] > 5:
                            # 2019-01-02 CARLSBG
                            sig, state = sval9, 2
            elif prevbottomM:
                if max(plistM[-3:]) < 10:
                    if plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]) and \
                                nlistP[-1] == max(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2014-02-05 CARLSBG
                                sig, state = sval9, 3
            elif isprev3topM():
                if isprev3bottomM():
                    if isprev3bottomP():
                        if plistP[-1] == min(plistP[-3:]):
                            if nlistP[-1] == max(nlistP[-3:]):
                                if newhighV:
                                    # 2012-06-26 F&N
                                    sig, state = -sval9, -3
                                else:
                                    # 2012-08-01 F&N
                                    sig, state = -sval9, 3
                            elif nlistP[-1] < 0:
                                # 2013-12-10 PADINI
                                sig, state = -sval9, 4
                elif isprev3topP():
                    if plistM[-1] == min(plistM[-3:]) and plistM[-1] > max(nlistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]) and nlistM[-1] > 5:
                            if plistP[-1] == min(plistP[-3:]) and plistP[-1] < max(nlistP[-3:]):
                                if nlistP[-1] == min(nlistP[-3:]):
                                    # 2011-08-02 CARLSBG
                                    sig, state = -sval9, 5
                elif MislowPlowN():
                    if plistP[-1] > plistP[-2]:
                        if min(nlistM[-3:]) >= 5:
                            if min(nlistP[-3:]) >= 0:
                                # 2014-12-02 KLSE
                                sig, state = -sval9, 6
            elif isprev3bottomM() and not isprev3topM():
                if isprev3bottomP() and not isprev3topP():
                    if nlistM[-1] == max(nlistM[-3:]) and plistM[-1] == max(plistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]) and plistP[-1] == max(plistP[-3:]):
                            # 2018-10-02 KESM
                            sig, state = -sval9, 6
                    elif plistV[-1] < 0 or tripleM in n3u:
                        if nlistP[-1] == max(nlistP[-3:]):
                            if newhighV or mvalley or ppeak:
                                # 2018-07-17 DUFU
                                sig, state = sval9, 6
                            else:
                                # 2018-05-03 DUFU
                                sig, state = sval9, -6
                elif isprev3topP():
                    if max(plistM[-3:]) < 10:
                        if plistP[-1] == min(plistP[-3:]):
                            if max(nlistP[-3:]) < 0:
                                # 2014-10-02 PADINI
                                sig, state = -sval9, 7
            elif isprev3topP():
                if isprev3bottomP():
                    if max(plistM[-3:]) < 10:
                        if nlistM[-1] == min(nlistM[-3:]) and nlistM[-1] > 5:
                            # 2015-05-05 KLSE
                            sig, state = -sval9, 8
            else:
                if narrowP == 4:
                    if plistM[-1] == max(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]):
                            if plistM[-1] > 10 and nlistM[-1] > 5:
                                if min(nlistM[-3:]) >= 0:
                                    # 2015-11-02 F&N
                                    sig, state = sval9, 9
                elif not (isprev3bottomM() or isprev3topM()):
                    if not (isprev3bottomP() or isprev3topP()):
                        if max(plistM) > 10 and min(nlistM[-3:]) > 5:
                            if narrowP == 4 and min(nlistP[-3:]) > 0:
                                if nlistC[-1] > highbar and lastC > nlistC[-1]:
                                    #  2015-11-02 F&N
                                    sig, state = sval9, 10
        else:
            sval0 = sval + 0
            if prevbottomM:
                if prevbottomP:
                    if plistP[-1] == min(plistP[-3:]):
                        if nlistM[-1] < 5:
                            if nlistP[-1] < 0:
                                if plistM[-1] > plistM[-2]:
                                    if plistM[-1] < 10 and plistP[-1] < max(nlistP[-3:]):
                                        # 2015-08-18 DUFU
                                        sig, state = sval0, 1
                                    else:
                                        # 2008-06-02 KLSE
                                        # 2011-06-10 PADINI
                                        sig, state = -sval0, 1
                                elif nlistP[-1] == min(nlistP[-3:]):
                                    if plistV[-1] < 0:
                                        # 2011-05-05 KLSE
                                        sig, state = sval0, 2
            elif prevbottomP:
                if isprev3topP():
                    if mvalley and plistM[-1] > 10:
                        if min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2014-11-06 DUFU
                                sig, state = sval0, 3
                    elif plistM[-1] < 10:
                        if max(plistM[-3:]) > 10:
                            if min(nlistM[-3:]) > 5:
                                if min(nlistP[-3:]) > 0:
                                    # 2014-12-18 DUFU
                                    sig, state = sval0, 4
            elif isprev3bottomM():
                if isprev3bottomP():
                    if not (isprev3topM() or isprev3topP()):
                        if nlistM[-1] < 5 and nlistP[-1] < 0:
                            if plistM[-1] < 5:
                                # 2008-08-29 KLSE
                                sig, state = -sval0, 5
                            elif plistM[-1] == min(plistM[-3:]):
                                if plistP[-1] == min(plistP[-3:]):
                                    # 2018-03-16 KESM
                                    sig, state = -sval0, 6
        return sig, state

    def evalHighC(sval):
        sig, state = 0, 0
        if newhighM:
            sval1 = sval + 1
            if newhighP:
                if bottomM:
                    if max(plistM[-3:]) < 10:
                        if nlistM[-1] < 5:
                            if min(nlistP[-3:]) > 0:
                                # 2018-01-03 KLSE
                                sig, state = sval1, 1
                elif isprev3topM():
                    if nlistM[-1] > 5 and nlistP[-1] > 0:
                        if isprev3bottomP():
                            if max(plistM[-3:]) < 10:
                                # 2016-07-08 KESM
                                sig, state = sval1, 2
                            else:
                                # 2009-08-03 CARLSBG
                                sig, state = -sval1, 2
                        else:
                            # 2018-03-01 CARLSBG
                            sig, state = -sval1, -3
            elif prevtopM:
                if topP:
                    if isprev3bottomP():
                        # 2016-10-07 KESM [kesm-3-add]
                        sig, state = sval1, 4
                elif isprev3topP():
                    if bottomM and isprev3bottomP():
                        if plistM[-1] >= 10 and nlistM[-1] < 5 and nlistP[-1] < 0:
                            # 2017-04-03 CARLSBG
                            sig, state = sval1, -4
                elif isprev3bottomM():
                    if isprev3bottomP():
                        if nlistM[-1] > nlistM[-2]:
                            if nlistP[-1] < nlistP[-2]:
                                # 2011-04-04 CARLSBG
                                sig, state = -sval1, -4
            elif prevtopP:
                if isprev3bottomP() and isprev3bottomM():
                    # 2015-08-03 KESM
                    sig, state = sval1, -5
            elif isprev3bottomM():
                if isprev3bottomP():
                    if plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            # 2011-07-04 KLSE
                            sig, state = -sval1, 6
        elif newhighP:
            sval2 = sval + 2
            if topM:
                if bottomP and prevbottomM:
                    # 2015-02-05 F&N
                    sig, state = -sval2, 1
            elif bottomM:
                if max(plistM[-3:]) < 10:
                    if nlistM[-1] < 5:
                        if min(nlistP[-3:]) > 0:
                            if newlowV:
                                # 2018-01-02 KLSE
                                sig, state = sval2, 1
                            else:
                                # 2018-01-19 KLSE
                                sig, state = -sval2, -1
            elif bottomP:
                if prevtopP:
                    if plistM[-1] == min(plistM[-3:]):
                        if min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2014-12-08 DUFU newhighV
                                sig, state = sval2, -1
            elif isprev3bottomP():
                if isprev3topM():
                    if max(plistM[-3:]) >= 10:
                        if nlistM[-1] == max(nlistM[-3:]):
                            if prevtopM:
                                if newhighV or topV:
                                    # 2012-03-02 N2N
                                    sig, state = sval2, -2
                                else:
                                    # 2012-02-27 N2N
                                    sig, state = sval2, 2
                            else:
                                # 2009-08-04 CARLSBG topV isprev3topM()
                                sig, state = sval2, -3
                        else:
                            # 2012-03-05 CARLSBG prevtopP
                            sig, state = sval2, 3
                    else:
                        # 2016-07-04 KESM
                        sig, state = sval2, 4
                elif isprev3bottomM():
                    if max(plistM[-3:]) < 10:
                        # 2015-05-15 KESM topP then bottomP
                        # 2015-06-24 PARAMON
                        # 2015-12-28 DUFU
                        sig, state = sval2, 5
                elif isprev3topP():
                    if max(plistM[-3:]) > 10:
                        # 2015-02-05 DUFU
                        sig, state = -sval2, 5
                else:
                    if plistP[-1] == max(plistP[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if plistM[-1] == min(plistM[-3:]):
                                if nlistM[-1] == max(nlistM[-3:]):
                                    # 2012-03-12 PADINI
                                    sig, state = sval2, -7
                                else:
                                    # 2012-02-03 PADINI
                                    sig, state = sval2, 7
                        else:
                            if lastM > 10:
                                # 2012-05-03 PADINI
                                sig, state = sval2, -9
                            else:
                                # 2012-05-17 PADINI
                                sig, state = sval2, 9
            elif isprev3bottomM():
                if plistM[-1] == max(plistM[-3:]):
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            # 2010-07-13 F&N
                            sig, state = -sval2, -11
                    elif plistP[-1] == min(plistP[-3:]):
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2013-05-09 KLSE
                                sig, state = -sval2, 13
            elif newhighV:
                if bottomV:
                    # 2018-09-04 PARAMON
                    sig, state = -sval2, 15
        elif newlowM:
            sval3 = sval + 3
            if topP:
                if prevbottomM:
                    if not (isprev3bottomP() or isprev3topP()):
                        if plistM[-1] < plistM[-2]:
                            if plistM[-1] < 10 and nlistM[-1] < 5:
                                # 2016-08-03 F&N
                                sig, state = -sval3, 1
                elif topP:
                    if isprev3topM():
                        if isprev3topP():
                            if topV:
                                # 2012-04-03 N2N
                                sig, state = sval3, -1
                    elif max(plistM[-3:]) > 10:
                        if min(nlistM[-3:]) > 5:
                            if nlistP[-1] == max(nlistP[-3:]):
                                # 2016-06-01 F&N
                                sig, state = sval3, 1
            elif prevbottomM:
                if plistM[-1] == max(plistM[-3:]):
                    if nlistM[-1] > 5:
                        if min(nlistP[-3:]) > 0:
                            # 2010-05-04 F&N
                            sig, state = sval3, 3
            elif not (isprev3topM() or isprev3bottomM()):
                if not (isprev3bottomP() or isprev3topP()):
                    if max(plistM[-3:]) < 10:
                        if min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2017-12-05 PADINI
                                sig, state = -sval3, -5
                    elif plistM[-1] < 10 and nlistM[-1] > 5:
                        if nlistP[-1] >= 0:
                            # 2016-03-11 F&N
                            # 2016-03-23 F&N
                            sig, state = sval3, 7
        elif topM:
            sval4 = sval + 4
            if topP and topV:
                if lastV < 0:
                    if not (newlowM or newlowP):
                        # 2016-09-30 KESM [kesm-3-add]
                        sig, state = sval4, 1
            elif prevbottomM:
                if isprev3topP():
                    if nlistM[-1] < 5 and plistM[-1] > plistM[-2]:
                        if nlistP[-1] < 0 and plistP[-1] < plistP[-2]:
                            # 2016-08-02 CARLSBG
                            sig, state = sval4, -1
                elif isprev3bottomP():
                    if plistM[-1] > 10:
                        if nlistM[-1] < 5:
                            # 2017-05-02 CARLSBG
                            sig, state = sval4, 2
            elif isprev3topP():
                if isprev3bottomP():
                    if plistP[-2] == max(plistP):
                        if plistM[-1] > 10:
                            if nlistP[-1] > 0:
                                if lastP > nlistP[-1]:
                                    # 2016-11-10 KESM
                                    sig, state = sval4, 3
        elif topP:
            sval5 = sval + 5
            if prevtopM:
                if topP and not newlowP:
                    if tripleM == 2:
                        if nlistP[-1] < 0:
                            # 2018-10-01 DUFU
                            sig, state = sval5, -1
            elif prevbottomM:
                if not (isprev3bottomP() or isprev3topP()):
                    if plistM[-1] < plistM[-2]:
                        if plistM[-1] < 10 and nlistM[-1] < 5:
                            # 2016-08-03 F&N newlowM
                            sig, state = -sval5, 1
                    elif max(plistM[-3:]) < 10:
                        if nlistM[-1] < 5:
                            if min(nlistP[-3:]) > 0:
                                # 2018-01-19 KLSE
                                sig, state = -sval5, 2
            elif isprev3topP():
                if isprev3topM():
                    if nlistM[-1] < 5:
                        if nlistP[-1] > max(plistP[:-2]):
                            if tripleM in p3d:
                                # 2018-07-13 F&N
                                sig, state = -sval5, 3
                            else:
                                # 2018-06-01 F&N
                                sig, state = -sval5, -3
                    elif plistM[-1] > 10:
                        if min(nlistM[-3:]) > 5:
                            # 2012-04-03 N2N newlowM
                            sig, state = sval5, -3
            elif isprev3bottomM():
                if plistM[-1] == max(plistM[-3:]):
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            if nlistM[-1] == max(nlistM[-3:]):
                                # 2010-08-02 F&N
                                sig, state = sval5, -4
                            else:
                                # 2010-10-29 F&N
                                sig, state = sval5, 4
        # elif bottomM:
        #     sval6 = sval + 6
        elif newlowV:
            sval7 = sval + 7
            if prevbottomP:
                if not (topP or prevtopP or isprev3topP()):
                    if plistP[-1] == max(plistP[-3:]):
                        # 2017-04-03 PADINI
                        sig, state = sval7, 1
            elif isprev3topM():
                if isprev3topP():
                    if nlistP[-1] > min(plistP[-3:]):
                        if min(nlistM) > 5:
                            if nlistM[-1] == max(nlistM[-3:]):
                                # 2016-12-01 KESM
                                sig, state = sval7, 2
                            else:
                                # 2012-03-23 CARLSBG
                                sig, state = -sval7, -2
                elif not isprev3bottomP():
                    if isprev3bottomM():
                        if plistM[-1] < 10 and nlistM[-1] > 5:
                            if nlistP[-1] > 0:
                                # 2017-11-01 CARLSBG reclassified under topC
                                sig, state = sval7, -2
                    else:
                        if tripleP == 2:
                            # 2017-04-13 DUFU
                            sig, state = sval7, 3
            elif isprev3bottomM():
                if isprev3topP():
                    if nlistM[-1] == max(nlistM[-3:]) and nlistM[-1] > min(plistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            if max(nlistP[-3:]) < 0:
                                # 2014-08-05 PADINI
                                sig, state = -sval7, 3
            elif isprev3bottomP():
                if max(plistP[-3:]) < max(plistP):
                    if tripleM in n3u and min(nlistM[-3:]) > 5:
                        # 2017-10-02 PADINI
                        sig, state = sval7, 4
            else:
                if plistM[-1] == max(plistM[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if min(nlistP[-3:]) > 0:
                                # 2014-01-02 KLSE
                                sig, state = -sval7, 5
        elif newhighV:
            sval8 = sval + 8
            if topP:
                if isprev3bottomM():
                    if max(plistM[-3:]) < 10:
                        if min(nlistM[-3:]) < 5:
                            if min(nlistP[-3:]) > 0:
                                # 2018-01-19 KLSE
                                sig, state = -sval8, 1
            elif isprev3topM():
                if not (isprev3bottomM() or isprev3topP() or isprev3bottomP()):
                    if tripleP in n3u:
                        if min(nlistP[-3:]) >= 0 and min(nlistM[-3:]) > 5:
                            if nlistP[-1] > min(plistP[-3:]):
                                # 2017-03-08 DUFU
                                sig, state = sval8, 1
                elif isprev3topP():
                    if nlistM[-1] == max(nlistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            # 2008-10-03 F&N
                            sig, state = -sval8, 1
                    elif min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            # 2012-08-01 N2N
                            sig, state = sval8, -2
            elif bottomM or topM or bottomP or topP or \
                    prevbottomM or prevtopM or prevbottomP or prevtopP:
                pass
            elif isprev3bottomM():
                if isprev3bottomP():
                    if max(plistM[-3:]) < 10:
                        if nlistM[-1] == max(nlistM[-3:]):
                            if plistP[-1] == max(plistP[-3:]):
                                if nlistP[-1] == max(nlistP[-3:]):
                                    if nlistP[-1] > 0:
                                        # 2019-02-07 CARLSBG
                                        sig, state = sval8, -1
            elif isprev3bottomP():
                pass
            elif isprev3topP():
                pass
            else:
                if max(plistM[-3:]) < 10 and min(nlistM[-3:]) > 5:
                    if min(nlistP[-3:]) > 0:
                        # 2012-08-01 PADINI
                        sig, state = -sval8, -8
        elif bottomV:
            sval9 = sval + 9
            if isprev3bottomM() or isprev3topM():
                pass
            else:
                if isprev3bottomP() or isprev3topP():
                    pass
                else:
                    if max(plistM[-3:]) < 10:
                        if tripleP in p3u:
                            if nlistP[-1] < nlistP[-2]:
                                # 2017-05-03 DUFU
                                sig, state = -sval9, -1
        else:
            sval0 = sval + 0
            if prevtopM:
                if prevtopP:
                    if tripleM == 2:
                        if nlistP[-1] == max(nlistP[-3:]):
                            if prevtopV:
                                # 2018-11-16 DUFU
                                sig, state = -sval0, 1
                            else:
                                # 2016-02-04 PADINI
                                sig, state = sval0, -1
                elif isprev3bottomM():
                    if isprev3bottomP():
                        if tripleM in n3u and nlistM[-1] > min(plistM[-3:]):
                            if plistP[-1] == max(plistP[-3:]):
                                if lastM > 10 or lastP > max(plistP[-3:]):
                                    # 2011-04-20 CARLSBG
                                    sig, state = -sval0, 2
                                else:
                                    # 2011-03-01 CARLSBG
                                    sig, state = sval0, 2
            elif prevbottomP:
                if isprev3topM():
                    if nlistM[-1] == max(nlistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]):
                            # 2009-06-16 F&N nlistM[-1] > 10
                            sig, state = sval0, 3
                elif isprev3bottomM():
                    if plistM[-1] < plistM[-2]:
                        if plistM[-1] < 10:
                            if nlistM[-1] < 5:
                                if max(plistM[-3:]) > 10:
                                    # 2018-01-02 KESM nlistM[-1] < 5: kesm-3-end duplicate of topC
                                    sig, state = -sval0, 4
            elif tripleV in n3d:
                if nlistM[-1] == min(nlistM[-3:]):
                    if nlistP[-1] > min(nlistP[-3:]):
                        if max(plistM[-3:]) < 10:
                            if plistP[-1] == max(plistP[-3:]):
                                # 2010-11-02 KLSE
                                sig, state = -sval0, -6
                            else:
                                # 2016-01-05 KESM [kesm-2-end]
                                sig, state = -sval0, 6
                        elif nlistM[-1] > 5:
                            if plistP[-1] == min(plistP[-3:]):
                                if min(nlistP[-3:]) > 0:
                                    # 2015-01-13 DUFU
                                    sig, state = sval0, 6
                elif isprev3bottomM():
                    if isprev3bottomP():
                        if max(plistM[-3:]) < 10:
                            if nlistM[-1] == max(nlistM[-3:]):
                                if plistP[-1] == max(plistP[-3:]):
                                    if nlistP[-1] == max(nlistP[-3:]):
                                        if nlistP[-1] > 0:
                                            if newhighV:
                                                # 2019-02-07 CARLSBG
                                                sig, state = sval0, -7
                                            else:
                                                # 2019-02-11 CARLSBG
                                                sig, state = sval0, 7
            elif isprev3topP() and isprev3bottomP():
                if not isprev3topM():
                    if nlistM[-1] < nlistM[-2] and nlistM[-1] < nlistM[-3]:
                        if min(nlistM[-3:]) > 5:
                            # 2016-01-07 KESM kesm-2-end
                            sig, state = -sval0, 8
                        else:
                            # 2008-01-04 KLSE
                            sig, state = -sval0, -8
            elif isprev3bottomM():
                if isprev3bottomP():
                    if plistM[-1] < plistM[-2]:
                        if plistM[-1] < 10:
                            if nlistM[-1] < 5:
                                if max(plistM[-3:]) > 10:
                                    # 2018-01-02 KESM nlistM[-1] < 5: kesm-3-end duplicate of topC
                                    sig, state = -sval0, 9
                                else:
                                    if mvalley:
                                        # 2011-06-06 KLSE
                                        sig, state = sval0, 9
                                    else:
                                        # 2011-07-29 KLSE
                                        sig, state = -sval0, 10
                            elif plistP[-1] == max(plistP[-3:]):
                                if nlistP[-1] == max(nlistP[-3:]):
                                    # 2016-01-05 DUFU max(plistM[-3:]) < 10
                                    sig, state = -sval0, -10
                elif max(plistM[-3:]) < 10:
                    if nlistM[-1] == min(nlistM[-3:]):
                        if not (isprev3bottomP() or isprev3topP()):
                            if plistP[-1] == max(plistP[-3:]):
                                if plistM[-1] == max(plistM[-3:]):
                                    # 2013-06-04 CARLSBG
                                    sig, state = -sval0, 12
                                else:
                                    # 2013-05-09 CARLSBG
                                    sig, state = sval0, 12
            else:
                if plistM[-1] == max(plistM[-3:]) and nlistM[-1] == min(nlistM[-3:]):
                    if plistP[-1] == max(plistP[-3:]) and nlistP[-1] == min(nlistP[-3:]):
                        if plistM[-1] > 10 and min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2010-04-13 CARLSBG
                                sig, state = -sval0, -13
                elif nlistM[-1] == min(nlistM[-3:]):
                    if nlistP[-1] == min(nlistP[-3:]):
                        if nlistM[-1] > 5 and nlistP[-1] > 0:
                            # 2007-06-26 KLSE
                            sig, state = -sval0, 14
        return sig, state

    def evalTopC(sval):
        sig, state = 0, 0
        if newlowM or lastM == min(nlistM):
            sval1 = sval + 1
            if topM:
                if prevbottomM:
                    if topP:
                        if prevbottomP:
                            if plistM[-1] > 10 and min(nlistM[-3:]) > 5:
                                # 2018-11-02 PADINI
                                sig, state = -sval1, 1
            elif topP:
                if isprev3bottomM():
                    if plistM[-1] == min(plistM[-3:]):
                        if min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2010-11-02 F&N
                                sig, state = sval1, 4
                elif nlistP[-1] == max(nlistP[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        # 2013-12-03 KESM
                        sig, state = sval1, -4
                        if prevtopV:
                            # 2009-10-01 CARLSBG
                            sig, state = sval1, 6
                    elif plistM[-1] == min(plistM[-3:]):
                        # 2018-08-02 F&N nlistM[-1] < 5
                        sig, state = -sval1, 6
                    elif nlistM[-1] > 5:
                        # 2013-12-31 KESM
                        sig, state = sval1, 7
            elif newlowP:
                if plistP[-1] < 0 and plistV[-1] < 0:
                    if plistM[-1] == min(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]):
                            if nlistM[-1] > 5:
                                # 2014-12-03 KESM topP
                                sig, state = sval1, -9
                                if vvalley and lastM < 5:
                                    # 2015-01-13 KESM
                                    sig, state = sval1, 9
                elif plistM[-1] < 5:
                    # 2018-11-16 F&N
                    sig, state = -sval1, 11
                elif plistM[-1] == min(plistM[-3:]):
                    if nlistM[-1] == min(nlistM[-3:]):
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistM[-1] > 5 and nlistP[-1] > 0:
                                if lastM < 5 and lastP < 0:
                                    # 2007-08-07 KLSE
                                    sig, state = sval1, -13
                                else:
                                    sig, state = -sval1, 13
                elif plistM[-1] == max(plistM[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        if max(plistM[-3:]) < 10:
                            # 2016-12-02 F&N
                            sig, state = sval1, 14
                        elif nlistP[-1] > 0:
                            # 2011-08-29 F&N
                            sig, state = -sval1, 14
            elif prevtopP:
                if prevbottomM:
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            # 2015-04-02 DUFU
                            sig, state = -sval1, -15
            elif prevbottomM:
                if bottomV:
                    if prevtopV:
                        if nlistP[-1] < 0 and min(nlistM) > 5:
                            # 2018-05-04 PADINI
                            sig, state = sval1, 17
                elif plistM[-1] == min(plistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if min(nlistP[-3:]) > 0:
                            # 2013-02-04 KLSE
                            sig, state = sval1, 18
            elif isprev3topM():
                if max(plistM[-3:]) < 10:
                    if nlistM[-1] == max(nlistM[-3:]):
                        if min(nlistP[-3:]) > 0:
                            if nlistP[-1] == max(nlistP[-3:]):
                                # 2017-06-01 KLSe
                                sig, state = -sval1, -19
                elif isprev3topP():
                    if plistM[-1] == min(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]) and min(nlistM) > 5:
                            if nlistP[-1] == min(nlistP[-3:]):
                                if nlistP[-1] > 0:
                                    pass
                            elif nlistP[-1] > 0:
                                # 2010-12-03 PADINI
                                sig, state = sval1, 19
                elif plistM[-1] == min(plistM[-3:]):
                    if nlistM[-1] == min(nlistM[-3:]):
                        if nlistM[-1] > 5:
                            if nlistP[-1] == min(nlistP[-3:]):
                                if nlistP[-1] < 0:
                                    # 2010-06-02 PADINI
                                    sig, state = sval1, 20
                            elif plistP[-1] == max(plistP[-3:]):
                                if nlistP[-1] < 0:
                                    # 2011-02-07 PADINI
                                    sig, state = -sval1, 20
                    elif plistP[-1] == min(plistP[-3:]):
                        if min(nlistP[-3:]) > 0:
                            # 2012-11-26 KLSE
                            sig, state = sval1, 21
            elif isprev3bottomM():
                if isprev3bottomP():
                    # 2016-02-22 DUFU
                    sig, state = -sval1, 23
                elif max(plistM[-3:]) < 10 and nlistM[-1] == max(nlistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-3] > plistP[-1]:
                                if vpeak:
                                    # 2013-01-03 CARLSBG
                                    sig, state = sval1, -24
                                else:
                                    # 2013-01-21 CARLSBG
                                    sig, state = sval1, 24
                elif plistM[-1] == min(plistM[-3:]):
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0 and nlistP[-1] == max(nlistP[-3:]):
                            # 2011-01-03 F&N
                            # 2018-12-07 PARAMON
                            sig, state = sval1, 25
            elif isprev3topP():
                if isprev3bottomP():
                    if plistM[-1] == min(plistM[-3:]):
                        if plistP[-1] == min(plistP[-3:]):
                            if nlistM[-1] == min(nlistM[-3:]) and min(nlistM) > 5:
                                if vpeak:
                                    # 2012-09-03 CARLSBG
                                    sig, state = sval1, -26
                                else:
                                    # 2012-09-27 CARLSBG
                                    sig, state = sval1, 26
            else:
                if plistM[-1] > 10:
                    if plistM[-1] == max(plistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]):
                            if nlistM[-1] == min(nlistM[-3:]) and nlistP[-1] == min(nlistP[-3:]):
                                # 2010-06-02 CARLSBG
                                sig, state = sval1, 27
                        else:
                            if nlistM[-1] == max(nlistM[-3:]):
                                if nlistP[-1] > nlistP[-2] and nlistP[-1] > 0:
                                    # 2017-08-02 KESM
                                    sig, state = sval1, -27
                elif plistM[-1] == min(plistM[-3:]):
                    if nlistM[-1] == min(nlistM[-3:]):
                        if nlistM[-1] > 5:
                            if nlistP[-1] == min(nlistP[-3:]):
                                if nlistP[-1] < 0:
                                    # 2010-06-02 PADINI
                                    sig, state = sval1, 28
                            elif plistP[-1] == max(plistP[-3:]):
                                if nlistP[-1] < 0:
                                    # 2011-02-07 PADINI
                                    sig, state = -sval1, 28
                    elif plistP[-1] == min(plistP[-3:]):
                        if min(nlistP[-3:]) > 0:
                            if max(plistM[-3:]) > 10:
                                # 2012-11-26 KLSE isprev3topM
                                sig, state = sval1, 29
                            else:
                                # 2018-02-28 PADINI
                                sig, state = -sval1, 29
        elif bottomM:
            sval2 = sval + 2
            if plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if plistM[-1] < plistM[-2]:
                        # 2016-03-01 DUFU
                        sig, state = -sval2, 99
            if sig:
                pass
            elif topP and not newlowP:
                if nlistP[-1] > 0:
                    # 2014-01-02 KESM
                    sig, state = sval2, 1
                else:
                    # 2018-07-04 PADINI
                    sig, state = -sval2, 1
            elif newlowP:
                if isprev3topP():
                    if plistM[-1] == max(plistM[-3:]):
                        if plistM[-1] > 10:
                            if nlistM[-1] > 5:
                                # 2015-05-22 DUFU min(nlistM) > 5, min(nlistP) > 0
                                sig, state = -sval2, 2
                    elif plistM[-1] == min(plistM[-3:]):
                        if nlistM[-1] < 5:
                            if plistP[-1] == min(plistP[-3:]):
                                if plistP[-1] < 0:
                                    # 2015-01-05 KESM
                                    sig, state = sval2, 3
                                else:
                                    # 2018-10-23 F&N
                                    sig, state = -sval2, 3
                            else:
                                # 2015-07-01 DUFU
                                sig, state = sval2, 4
            elif bottomP:
                if newhighP:
                    if plistV[-1] < 0:
                        # 2011-11-09 KLSE
                        sig, state = sval2, -5
                elif plistP[-1] < 0 and plistV[-1] < 0:  # vvalP == 1:
                    # 2015-01-19 KESM [kesm-2-start] reclassified under retrace
                    sig, state = sval2, 5
                elif nlistM[-1] < 5 and nlistP[-1] < 0:
                    if nlistM[-2] > 5 and nlistP[-2] > 0:
                        if isprev3bottomM() and isprev3bottomP():
                            # 2008-04-02 KLSE
                            sig, state = -sval2, -5
                        else:
                            if tripleM in p3d or tripleP in n3d:
                                # 2007-09-04 KLSE
                                sig, state = sval2, 6
                            elif isprev3topM():
                                if isprev3topP():
                                    # 2018-08-01 CARLSBG
                                    sig, state = -sval2, -6
                                else:
                                    sig, state = -sval2, 99
                            elif isprev3topP():
                                if plistM[-1] > 10:
                                    # 2011-12-05 F&N
                                    sig, state = sval2, 7
                                else:
                                    sig, state = -sval2, 98
                            else:
                                sig, state = -sval2, -7
            elif newhighP:
                if plistP[-1] == min(plistP[-3:]):
                    if nlistP[-1] == min(nlistP[-3:]):
                        if nlistP[-1] > 0:
                            # 2013-01-03 KLSE
                            sig, state = -sval2, 8
            elif prevbottomM or prevbottomP:
                if plistP[-1] < 0:
                    # 2016-10-05 F&N
                    sig, state = -sval2, 9
                elif isprev3topM():
                    if isprev3topP():
                        if tripleM in p3d or tripleP in n3d:
                            # 2007-11-01 KLSE
                            sig, state = sval2, -10
                        else:
                            # 2018-09-28 CARLSBG
                            sig, state = -sval2, 10
                elif plistM[-1] > 10:
                    # 2011-12-07 F&N
                    sig, state = sval2, 10
            elif isprev3bottomP():
                if plistP[-1] == max(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        if plistM[-1] < plistM[-2]:
                            # 2016-03-01 DUFU
                            sig, state = -sval2, 11
            elif isprev3bottomM():
                if max(nlistM[-3:]) < 10 and nlistM[-1] < 5:
                    if tripleP == 6:
                        # 2013-02-18 CARLSBG
                        sig, state = sval2, 12
            elif isprev3topP():
                if plistM[-1] == min(plistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if nlistP[-1] > 0:
                            # 2018-10-01 F&N
                            sig, state = -sval2, 13
            elif not (newlowP or bottomP):
                if plistM[-1] > 10 and plistM[-1] == max(plistM[-3:]):
                    if nlistM[-1] < 5 and nlistP[-1] < 0:
                        # 2017-09-06 KESM [kesm-3-add]
                        sig, state = sval2, 14
        elif topP:
            sval3 = sval + 3
            if newlowP or lastP == min(nlistP):
                if topM:
                    if nlistM[-1] > min(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2007-03-16 KLSE
                            # 2015-08-21 PARAMON
                            sig, state = sval3, 1
                elif newlowV or nlistP[-1] == max(nlistP[-3:]):
                    if max(plistM[-3:]) < 10:
                        # 2015-09-02 KESM newlowV [kesm-2-add]
                        sig, state = sval3, 2
                    elif nlistM[-1] == min(nlistM[-3:]):
                        if prevtopM:
                            # 2015-09-02 PARAMON
                            sig, state = sval3, 3
                        else:
                            # 2014-09-05 DUFU under retrace
                            sig, state = -sval3, -1
                    else:
                        # 2015-08-11 PARAMON
                        sig, state = -sval3, 1
                elif nlistP[-1] == min(nlistP[-3:]):
                    if newhighV:
                        # 2018-05-31 KLSE
                        sig, state = -sval3, -2
                    elif topV:
                        # 2018-06-04 KLSE
                        sig, state = -sval3, 2
            elif topM:
                if prevbottomM:
                    if plistM[-1] > 10:
                        if min(nlistM[-3:]) > 5:
                            if nlistP[-1] == min(nlistP[-3:]):
                                # 2018-09-07 PADINI
                                sig, state = -sval3, 3
                            elif nlistP[-1] == max(nlistP[-3:]):
                                # 2014-04-02 KESM
                                sig, state = sval3, 3
            elif prevtopM:
                if plistM[-1] > 10:
                    if nlistM[-1] == min(nlistM[-3:]):
                        if nlistM[-1] > 5:
                            # 2018-05-15 CARLSBG
                            sig, state = -sval3, -3
                    elif nlistM[-1] == max(nlistM[-3:]):
                        if min(nlistM[-3:]) > 5:
                            # 2014-04-24 KESM isprev3bottomM():
                            sig, state = sval3, -3
            elif isprev3topM():
                if not newlowP:
                    if isprev3bottomP():
                        # 2009-10-19 CARLSBG
                        sig, state = sval3, 4
                    elif plistM[-1] == min(plistM[-3:]):
                        # 2018-07-13 F&N
                        sig, state = -sval3, 5
                    elif max(plistM[-3:]) < 10:
                        # 2018-07-02 PADINI
                        sig, state = -sval3, 6
                    else:
                        # 2014-06-23 KESM
                        sig, state = sval3, -6
            elif isprev3topV():
                if plistM[-1] == min(plistM[-3:]):
                    if nlistP[-1] == min(nlistP[-3:]):
                        if newlowV:
                            # 2018-04-03 KLSE
                            sig, state = -sval3, -7
                        elif newhighV:
                            # 2018-05-07 KLSE
                            sig, state = -sval3, 7
        elif newhighP:
            sval4 = sval + 4
            if newhighM:
                if bottomP:
                    if prevtopP:
                        if isprev3bottomM():
                            # 2018-08-01 KLSE
                            sig, state = -sval4, -1
            elif prevtopP and not (bottomP or prevbottomP):
                if tripleP in p3u:
                    if nlistP[-1] == min(nlistP[-3:]):
                        # 2014-08-04 KESM
                        sig, state = -sval4, 1
        elif newlowP:
            sval5 = sval + 5
            if topP:
                if not (newhighM or newlowM or topM or bottomM or prevtopM or prevbottomM):
                    # 2015-09-02 KESM newlowV [kesm-2-add]
                    sig, state = sval5, 1
                elif newlowV:
                    # 2015-09-02 KESM newlowV [kesm-2-add]
                    sig, state = sval5, 2
            elif isprev3topP():
                if isprev3bottomP():
                    if min(nlistM) > 5:
                        if nlistP[-1] > min(plistP[-3:]):
                            # 2012-06-01 CARLSBG
                            sig, state = sval5, 3
                        elif not (isprev3topM() or isprev3bottomM()):
                            if tripleM == 2:
                                # 2011-08-09 F&N
                                sig, state = -sval5, 3
                    elif newlowV:
                        if topV:
                            # 2012-04-06 DAYANG
                            sig, state = -sval5, 4
                        else:
                            # 2013-09-02 KLSE
                            sig, state = sval5, 4
                    elif nlistM[-1] == max(nlistM[-3:]):
                        if nlistP[-1] == max(nlistP[-3:]):
                            if nlistM[-1] > 5 and nlistP[-1] > 0:
                                # 2013-09-04 KLSE
                                sig, state = sval5, 5
            elif isprev3bottomM() and not (topM or prevtopM):
                if isprev3bottomP() and not (topP or prevtopP):
                    if tripleM in p3d and tripleP in p3d:
                        # 2018-02-14 KESM [kesm-3-end]
                        sig, state = -sval5, 6
            elif newhighV:
                if plistM[-1] == max(plistM[-3:]):
                    if mvalley and nlistM[-1] > 5:
                        if nlistP[-1] == max(nlistP[-3:]):
                            if min(nlistP[-3:]) > 0:
                                # 2014-01-02 KLSE
                                sig, state = sval5, 7
        elif bottomP:
            sval6 = sval + 6
            if prevbottomM:
                if isprev3topM():
                    if not topM:
                        if plistP[-1] == max(plistP[-3:]):
                            # 2011-05-04 PADINI
                            sig, state = -sval6, 1
                elif isprev3bottomP():
                    if isprev3bottomM():
                        if plistM[-1] == max(plistM[-3:]):
                            # 2011-11-21 KLSE
                            sig, state = sval6, 1
                elif not isprev3topP():
                    if nlistM[-1] < 5 and nlistP[-1] < 0:
                        if max(nlistM[-3:]) < 5:
                            # 2018-06-18 KESM
                            sig, state = -sval6, 2
            elif isprev3bottomM():
                if max(plistM[-3:]) < 10:
                    if plistM[-1] == max(plistM[-3:]):
                        if nlistM[-1] < max(nlistM[-3:]):
                            # 2013-08-01 CARLSBG
                            sig, state = -sval6, 3
            elif prevtopP:
                if prevtopM:
                    if topV:
                        # 2015-09-28 PARAMON
                        sig, state = -sval6, -3
            elif isprev3topP():
                pass
            else:
                if tripleM in p3u:
                    if nlistM[-1] == min(nlistM[-3:]):
                        if nlistP[-1] < 0:
                            # 2017-09-06 DUFU
                            sig, state = -sval6, 4
                else:
                    if plistM[-1] < max(plistM[-3:]) and nlistM[-1] < max(nlistM[-3:]):
                        if plistP[-1] < max(plistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2016-11-02 PADINI (obsoleted)
                                sig, state = -sval6, 5
        elif newhighV:
            sval7 = sval + 7
            if prevtopV:
                if prevbottomM:
                    if prevbottomP:
                        if plistM[-1] == max(plistM[-3:]):
                            if plistP[-1] == max(plistP[-3:]):
                                # 2011-12-01 KLSE
                                sig, state = sval7, -1
                if min(nlistM[-3:]) > 5:
                    if nlistP[-1] == min(nlistP[-3:]):
                        if prevtopP:
                            # 2014-07-17 KESM [kesm-1-end]
                            sig, state = -sval7, -1
                        elif nlistP[-1] < 0:
                            # 2010-08-03 PADINI
                            sig, state = sval7, 1
                    elif narrowP == 9 and tripleP in n3u:
                        # 2018-01-05 CARLSBG
                        sig, state = sval7, 2
            elif prevtopP and not (bottomP or prevbottomP):
                if tripleP in p3u:
                    if nlistP[-1] == min(nlistP[-3:]):
                        # 2014-07-17 KESM [kesm-1-end]
                        sig, state = -sval7, -2
            elif isprev3topP():
                if isprev3bottomP():
                    if plistM[-1] == min(plistM[-3:]) and plistP[-1] == min(plistP[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]) and min(nlistM) > 5:
                            # 2012-08-06 CARLSBG
                            sig, state = sval7, -3
                    elif plistM[-1] == max(plistM[-3:]):
                        if nlistM[-1] == min(nlistM[-3:]):
                            if nlistP[-1] < nlistP[-2]:
                                # 2011-01-04 PADINI
                                sig, state = -sval7, -3
            elif prevtopM:
                if min(nlistM[-3:]) > 5:
                    if min(nlistP[-3:]) > 0:
                        if plistP[-1] == min(plistP[-3:]):
                            if pvalley:
                                # 2014-09-09 KLSE
                                sig, state = -sval7, 4
                            else:
                                # 2014-06-03 KLSE
                                sig, state = -sval7, -4
        elif newlowV or bottomV:
            sval8 = sval + 8
            if bottomV:
                st = 50
                if prevbottomM:
                    if prevbottomP:
                        if nlistM[-1] < 5 and nlistP[-1] < 0:
                            if lastV < plistV[-1]:
                                # 2012-01-04 F&N
                                sig, state = -sval8, -st - 1
                                if lastV > max(nlistV[-3:]):
                                    # 2012-01-10 F&N
                                    sig, state = -sval8, st + 1
                            elif lastV > plistV[-3:]:
                                # 2012-02-03 F&N in retrace
                                sig, state = sval8, st + 1
            elif plistV[-1] < 0:  # vvalP == 1:
                if isprev3topP():
                    if tripleM in n3u:
                        if not (newlowP or bottomP):
                            # 2017-03-01 KESM [kesm-3-add]
                            sig, state = sval8, 1
                elif isprev3bottomM():
                    if tripleP in p3d and tripleV in p3d:
                        if nlistP[-1] > 0 and nlistP[-1] > nlistP[-2]:
                            # 2016-11-04 DUFU
                            sig, state = sval8, 2
            elif isprev3bottomM():
                if isprev3topM():
                    if not (isprev3bottomP() or isprev3topP()):
                        if plistM[-1] < 10 and nlistM[-1] > 5:
                            if tripleP in n3u and nlistP[-1] > 0:
                                if topV:
                                    if newlowV:
                                        if mpeak:
                                            # 2017-10-03 CARLSBG
                                            sig, state = sval8, 3
                                        else:
                                            # 2017-11-01 CARLSBG
                                            sig, state = sval8, -3
                                else:
                                    # 2017-01-03 DUFU
                                    sig, state = sval8, 4
                elif max(plistM[-3:]) < 10 and nlistM[-1] == max(nlistM[-3:]):
                    if tripleP == 6:
                        # 2012-12-14 CARLSBG
                        # 2013-01-09 CARLSBG
                        sig, state = sval8, -5
            elif isprev3topP():
                if min(nlistM[-3:]) > 5:
                    if plistP[-1] > plistP[-2] and nlistP[-1] > nlistP[-2]:
                        if min(nlistM[-3:]) > 5 and nlistM[-1] == max(nlistM[-3:]):
                            # 2016-07-11 PADINI
                            sig, state = sval8, 6
                        else:
                            sig, state = -sval8, 6
                    elif max(plistM[-3:]) < 10:
                        if min(nlistM[-3:]) > 7:
                            # 2016-04-04 PADINI nlistV[-1] > 0
                            sig, state = sval8, 7
                        elif min(nlistP[-3:]) > 0:
                            # 2009-12-02 CARLSBG
                            # 2010-02-02 CARLSBG plistV[-2] < 0
                            sig, state = sval8, 8
                    elif plistP[-1] == min(plistP[-3:]):
                        if nlistP[-1] > 0:
                            if plistM[-1] == min(plistM[-3:]):
                                # 2012-11-01 KLSE
                                sig, state = -sval8, 9
                            else:
                                # 2011-04-07 F&N
                                sig, state = sval8, 9
            elif isprev3bottomP():
                if tripleP in p3u and nlistP[-1] == max(nlistP[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        # 2012-04-03 PADINI
                        sig, state = sval8, 11
            elif prevtopM:
                if min(nlistM[-3:]) > 5:
                    if min(nlistP[-3:]) > 0:
                        if plistP[-1] == min(plistP[-3:]):
                            # 2014-07-01 KLSE
                            sig, state = -sval8, 12
            else:
                if plistM[-1] == min(plistM[-3:]):
                    if plistP[-1] == min(plistP[-3:]):
                        if min(nlistM[-3:]) > 5:
                            if min(nlistP[-3:]) > 0:
                                # 2018-01-02 PADINI
                                sig, state = -sval8, 13
                            elif tripleP == 5:
                                # 2018-01-02 CARLSBG
                                sig, state = sval8, 13
            if not sig:
                if topV:
                    if plistV[-2] < 0 and nlistP[-1] > 0:  # vvalP == 2 and pvalN == 1:
                        if isprev3topM():
                            if isprev3bottomM():
                                if isprev3bottomP():
                                    # 2012-04-16 KLSE
                                    sig, state = sval8, -99
                                else:
                                    # 2017-11-01 CARLSBG
                                    sig, state = sval8, -98
        elif newhighM or topM:
            sval9 = sval + 9
            if topM:
                if prevbottomP:
                    if isprev3topP():
                        if isprev3bottomM():
                            # 2018-09-04 KLSE
                            sig, state = -sval9, 51
                elif prevbottomM:
                    if isprev3topM():
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2017-06-01 CARLSBG
                            sig, state = sval9, 51
                elif min(nlistM[-3:]) > 5:
                    if plistP[-1] > plistP[-2]:
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] > 0:
                                if lastM > 5 and lastP > 0:
                                    # 2010-05-03 KLSE
                                    sig, state = -sval9, 0
                                else:
                                    # 2010-06-02 KLSE
                                    sig, state = sval9, 52
                '''
                elif max(plistM[-3:]) < 10:
                    if isprev3bottomM():
                        if isprev3bottomP():
                            if topV or prevtopV:
                                # 2012-04-24 KLSE
                                sig, state = sval9, -53
                                if lastV > 0:
                                    # 2012-05-16 KLSE
                                    sig, state = sval9, 53
                '''
            elif not (newhighP or topP):
                if prevtopM:
                    if isprev3bottomM():
                        if isprev3bottomP():
                            if max(plistM[-3:]) < 10:
                                if nlistM[-1] > 5:
                                    if nlistP[-1] > 0:
                                        if lastM > 10:
                                            # 2012-07-11 KLSE
                                            sig, state = sval9, -1
                                        elif topV:
                                            # 2012-04-02 KLSE
                                            sig, state = sval9, -1
                                        else:
                                            # 2012-06-13 KLSE
                                            sig, state = sval9, 1
                        elif plistM[-1] == max(plistM[-3:]):
                            if nlistM[-1] == max(nlistM[-3:]):
                                if nlistP[-1] == max(nlistP[-3:]):
                                    # 2017-07-05 CARLSBG
                                    sig, state = sval9, -3
                elif isprev3topM():
                    if isprev3topP():
                        if tripleM in n3u:
                            if nlistP[-1] == min(nlistP[-3:]):
                                if nlistP[-1] <= 0:
                                    # 2017-04-06 KESM
                                    sig, state = sval9, 1
                        elif plistM[-1] == min(plistM[-3:]):
                            if nlistM[-1] == min(nlistM[-3:]):
                                if plistP[-1] > plistP[-2] and nlistP[-1] > nlistP[-2]:
                                    # 2016-08-04 PADINI
                                    sig, state = -sval9, -1
                                elif nlistP[-1] == min(nlistP[-3:]):
                                    # 2010-01-04 KLSE
                                    sig, state = -sval9, -2
                    elif isprev3bottomM():
                        if plistM[-1] == min(plistM[-3:]) and nlistM[-1] > nlistM[-2]:
                            if plistP[-1] == min(plistP[-3:]) and nlistP[-1] > nlistP[-2]:
                                # 2010-11-03 CARLSBG
                                sig, state = sval9, 2
                        elif plistM[-1] == max(plistM[-3:]):
                            if nlistM[-1] == max(nlistM[-3:]):
                                if nlistP[-1] == max(nlistP[-3:]):
                                    # 2017-07-05 CARLSBG
                                    sig, state = sval9, -3
                    elif max(plistM[-3:]) < 10:
                        if nlistM[-1] == max(nlistM[-3:]):
                            if min(nlistP[-3:]) > 0:
                                # 2010-09-02 KLSE
                                sig, state = sval9, 5
                        elif min(nlistM[-3:]) > 5:
                            if plistP[-1] == min(plistP[-3:]):
                                if nlistP[-1] == min(nlistP[-3:]):
                                    if nlistP[-1] > 0:
                                        # 2010-04-12 KLSE
                                        sig, state = -sval9, 6
        else:
            sval0 = sval + 0
            if prevtopM:
                if prevtopP:
                    if min(nlistM[-3:]) > 5:
                        if nlistP[-1] == min(nlistP[-3:]):
                            if nlistP[-1] < 0:
                                # 2015-07-22 CARLSBG
                                sig, state = -sval0, 1
                elif isprev3topM():
                    if plistM[-1] >= 10:
                        if min(nlistM[-3:]) > 5 and min(nlistP[-3:]) > 0:
                            if plistP[-1] == min(plistP[-3:]):
                                if nlistP[-1] > nlistP[-2]:
                                    # 2012-10-01 KLSE
                                    sig, state = -sval0, -1
                    elif tripleP in p3d and tripleP in n3u:
                        if isprev3bottomM():
                            if max(plistM[-3:]) < 10:
                                if nlistP[-1] > 0 and nlistP[-1] > nlistP[-2]:
                                    # 2016-12-02 DUFU
                                    sig, state = sval0, 1
                    elif nlistM[-1] > min(nlistM[-3:]):
                        if plistP[-1] > min(plistP[-3:]):
                            if nlistP[-1] > min(nlistP[-3:]):
                                if isprev3bottomM() or isprev3bottomP():
                                    if mvalley and pvalley and nlistP[-1] > 0:
                                        # 2012-06-01 KLSE
                                        sig, state = sval0, 2
                                    else:
                                        # 2012-04-18 KLSE
                                        sig, state = -sval0, 2
                                elif min(nlistP[-3:]) > 0:
                                    # 2010-07-01 KLSE
                                    sig, state = sval0, 3
            elif isprev3topM():
                if isprev3topP():
                    if isprev3bottomP():
                        if tripleM in n3u:
                            if not (newlowP or bottomP):
                                if plistV[-1] < 0:  # vvalP == 1:
                                    # 2017-02-13 KESM Fake drop
                                    # 2017-03-01 KESM [kesm-3-add]
                                    sig, state = sval0, 5
                    elif prevtopP and not (bottomP or prevbottomP):
                        if tripleP in p3u:
                            if nlistP[-1] == min(nlistP[-3:]):
                                if nlistP[-1] > 0:
                                    # 2014-07-08 KESM
                                    # 2014-07-17 KESM [kesm-1-end]
                                    sig, state = -sval0, -6
                                else:
                                    # 2015-07-22 CARLSBG
                                    sig, state = -sval0, 6
            elif prevtopP:
                if isprev3bottomP():
                    if isprev3bottomM():
                        if nlistP[-1] > 0 and nlistP[-2] < 0:
                            if max(plistM[-3:]) < 10:
                                # 2013-07-19 KLSE
                                sig, state = -sval0, 8
            elif prevbottomM:
                if prevbottomP:
                    if plistM[-1] == max(plistM[-3:]):
                        if plistP[-1] == max(plistP[-3:]):
                            if plistV[-1] < 0:
                                # 2011-12-15 KLSE
                                sig, state = sval0, 9
                elif not isprev3topM():
                    if not (isprev3bottomP() or isprev3topP()):
                        if nlistM[-1] < 5 and nlistP[-1] < 0:
                            if max(nlistM[-3:]) < 5:
                                # 2018-06-18 KESM
                                sig, state = -sval0, 10
                            else:
                                # 2013-04-01 CARLSBG
                                # 2016-05-06 DUFU
                                sig, state = sval0, 10
                elif isprev3bottomM():
                    if max(nlistM[-3:]) < 10 and nlistM[-1] < 5:
                        if tripleP in n3d:
                            if plistP[-1] == max(plistP[-3:]):
                                # 2013-04-01 CARLSBG won't reach here
                                sig, state = sval0, 12
            elif isprev3bottomM():
                if isprev3bottomP():
                    if nlistP[-1] > 0 and nlistP[-2] < 0:
                        if max(plistM[-3:]) < 10:
                            if prevtopC or cvalley:
                                # 2015-05-06 KESM topP then bottomP
                                # 2015-11-06 DUFU
                                # 2019-02-04 HEIM
                                sig, state = sval0, 14
                            else:
                                # 2016-02-04 DUFU
                                sig, state = -sval0, 14
                        elif nlistM[-1] < 5:
                            # 2018-02-26 KESM
                            sig, state = -sval0, 16
                        else:
                            # 2007-12-13 KLSE
                            # 2008-01-08 KLSE
                            sig, state = -sval0, -16
            elif prevbottomV:
                if isprev3topP():
                    if not (isprev3topM() or isprev3bottomM()):
                        if tripleM == 2:
                            # 2011-07-06 F&N
                            sig, state = -sval0, 20
            else:
                if plistM[-1] == max(plistM[-3:]) and nlistM[-2] == min(nlistM[-4:-1]):
                    if plistP[-1] == max(plistP[-3:]) and nlistP[-1] == min(nlistP[-3:]):
                        if plistM[-1] > 10 and min(nlistM[-4:]) > 5 and nlistM[-1] > 7:
                            if min(nlistP[-3:]) > 0:
                                # 2010-05-03 CARLSBG
                                sig, state = -sval0, 21
        return sig, state

    def eval(sval):
        sig, state = 0, 0
        if plistM[-1] == max(plistM[-3:]):
            sval2 = sval + 2
            if nlistM[-1] == max(nlistM[-3:]):
                pass
            elif nlistM[-1] == min(nlistM[-3:]):
                pass
            elif plistP[-1] == max(plistP[-3:]):
                pass
            elif plistP[-1] == min(plistP[-3:]):
                pass
            else:
                pass
        elif plistM[-1] == min(plistM[-3:]):
            sval3 = sval + 3
        elif plistP[-1] == max(plistP[-3:]):
            sval4 = sval + 4
        elif plistP[-1] == min(plistP[-3:]):
            sval5 = sval + 5
        return sig, state

    def evalHighC2(sval):
        sig, state = 0, 0
        if plistM[-1] == max(plistM[-3:]):
            sval2 = sval + 2
            if nlistM[-1] == max(nlistM[-3:]):
                pass
            elif nlistM[-1] == min(nlistM[-3:]):
                pass
            elif plistP[-1] == max(plistP[-3:]):
                pass
            elif plistP[-1] == min(plistP[-3:]):
                pass
            else:
                pass
        elif plistM[-1] == min(plistM[-3:]):
            sval3 = sval + 3
            if nlistP[-1] == max(nlistP[-3:]):
                pass
            elif nlistP[-1] == min(nlistP[-3:]):
                pass
        elif plistP[-1] == max(plistP[-3:]):
            sval4 = sval + 4
        elif plistP[-1] == min(plistP[-3:]):
            sval5 = sval + 5
            if nlistP[-1] == max(nlistP[-3:]):
                pass
            elif nlistP[-1] == min(nlistP[-3:]):
                if nlistM[-1] == min(nlistM[-3:]):
                    if bottomM:
                        if isprev3topM():
                            if nlistM[-1] < 5:
                                if min(nlistP[-3:]) > 0:
                                    # 2018-01-03 KLSE
                                    sig, state = sval5, 21
        return sig, state

    def evalUptrend(sval):
        sig, state = 0, 0
        if plistM[-1] == max(plistM[-3:]):
            sval2 = sval + 2
            if nlistM[-1] == max(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        if topM:
                            if topP:
                                # 2018-10-24 DUFU prevtopV
                                sig, state = sval2, 1
                        elif newhighP:
                            if prevtopM:
                                # 2012-01-20 N2N
                                sig, state = sval2, 5
            elif nlistM[-1] == min(nlistM[-3:]):
                pass
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if newhighP:
                        if topV:
                            if min(plistM[-3:]) < 5:
                                # 2009-05-04 KLSE
                                sig, state = sval2, 20
                            elif nlistM[-1] > 5:
                                # 2015-03-16 CARLSBG
                                sig, state = -sval2, -20
            elif plistP[-1] == min(plistP[-3:]):
                pass
            else:
                pass
        elif plistM[-1] == min(plistM[-3:]):
            sval3 = sval + 3
            if nlistM[-1] == max(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    pass
                elif plistP[-1] == min(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        pass
                    elif nlistP[-1] == min(nlistP[-3:]):
                        pass
                    else:
                        if isprev3bottomP():
                            if min(nlistM[-3:]) > 5:
                                if newhighM or newhighP:
                                    # 2016-07-08 KESM topV
                                    sig, state = sval3, 40
                elif nlistP[-1] == max(nlistP[-3:]):
                    if nlistM[-1] == max(nlistM[-3:]):
                        if isprev3topM():
                            if isprev3topP():
                                if isprev3bottomP():
                                    if nlistP[-1] > 0:
                                        if newhighP:
                                            # 2009-08-04 CARLSBG topV
                                            sig, state = sval3, -50
                                        else:
                                            # 2009-07-01 PADINI newlowV
                                            # 2009-07-29 PADINI
                                            sig, state = sval3, 50
            elif nlistM[-1] == min(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        if prevtopP:
                            if isprev3bottomP():
                                if newlowV:
                                    # 2015-04-01 KLSE
                                    sig, state = -sval3, -70
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if newhighM:
                        if topP:
                            # 2013-11-07 KESM
                            sig, state = sval3, 90
                        elif newhighP:
                            # 2013-11-13 KESM
                            sig, state = sval3, -90
                    elif newhighP:
                        if plistM[-1] > 10:
                            # 2014-07-31 DUFU
                            sig, state = sval3, -100
                        elif nlistP[-1] > 0:
                            if min(nlistM[-3:]) > 5:
                                if nlistP[-1] < min(plistP[-3:]):
                                    # 2013-10-02 KESM
                                    sig, state = sval3, 105
                                else:
                                    # 2013-07-15 GKENT
                                    sig, state = -sval3, 105
            elif plistP[-1] == min(plistP[-3:]):
                pass
        elif plistP[-1] == max(plistP[-3:]):
            sval4 = sval + 4
            if nlistP[-1] == max(nlistP[-3:]):
                if nlistM[-1] == max(nlistM[-3:]):
                    if prevtopP:
                        if isprev3bottomP():
                            if isprev3topM():
                                if isprev3bottomM():
                                    if min(nlistM[-3:]) < 5:
                                        if nlistP[-1] > 0:
                                            # 2016-02-24 KLSE
                                            sig, state = sval4, 1
                        if isprev3topM():
                            if plistM[-1] > 10:
                                if newhighP:
                                    # 2012-03-16 N2N newhighV
                                    sig, state = sval4, -1
                            elif min(nlistM[-3:]) > 5:
                                if isprev3bottomM():
                                    if min(nlistP[-3:]) > 0:
                                        # 2014-05-02 KESM
                                        sig, state = sval4, -3
                                else:
                                    # 2018-04-02 F&N
                                    sig, state = sval4, 3
                elif nlistM[-1] == min(nlistM[-3:]):
                    if nlistM[-1] < 5:
                        if prevtopP:
                            if isprev3topM():
                                if newhighP:
                                    if nlistM[-1] < 5:
                                        if nlistP[-1] > 0:
                                            # 2018-05-02 F&N
                                            sig, state = sval4, 10
                        elif isprev3topM():
                            pass
                    elif plistM[-1] < 10:
                        if topP:
                            # 2016-06-01 F&N
                            sig, state = sval4, 12
                elif topP:
                    if newlowM:
                        if plistV[-1] == min(plistV[-3:]) or newhighC:
                            # 2016-06-01 F&N
                            sig, state = sval4, 20
                        else:
                            # 2013-12-03 KESM picked up under retrace
                            sig, state = sval4, -22
                elif newhighP:
                    if nlistP[-1] > 0:
                        if min(nlistM[-3:]) > 5:
                            # 2013-11-29 KESM
                            sig, state = sval4, -30
            elif nlistP[-1] == min(nlistP[-3:]):
                pass
        elif plistP[-1] == min(plistP[-3:]):
            sval5 = sval + 5
            if nlistP[-1] == max(nlistP[-3:]):
                if nlistM[-1] == max(nlistM[-3:]):
                    if isprev3topM():
                        if min(nlistM[-3:]) > 5:
                            if newhighM:
                                if newhighP:
                                    # 2018-03-02 CARLSBG
                                    sig, state = -sval5, -1
            elif nlistP[-1] == min(nlistP[-3:]):
                if nlistM[-1] == min(nlistM[-3:]):
                    if bottomM:
                        if isprev3topM():
                            if nlistM[-1] < 5:
                                if min(nlistP[-3:]) > 0:
                                    if newhighM or newhighP:
                                        # 2018-01-03 KLSE
                                        sig, state = sval5, 21
        elif nlistM[-1] == max(nlistM[-3:]):
            sval6 = sval + 6
            if nlistP[-1] == max(nlistP[-3:]):
                if isprev3topM():
                    if isprev3bottomM():
                        pass
                    elif isprev3topP():
                        if isprev3bottomP():
                            if nlistP[-1] > 0:
                                # 2016-04-04 KLSE
                                sig, state = -sval6, 1
        return sig, state

    def evalBreakOut(sval):
        sig, state = 0, 0
        if plistM[-1] == max(plistM[-3:]):
            sval2 = sval + 2
            if nlistM[-1] == max(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        if topM:
                            if topP:
                                # 2018-10-24 DUFU prevtopV
                                sig, state = sval2, 1
                        elif newhighP:
                            if prevtopM:
                                # 2012-01-20 N2N
                                sig, state = sval2, 5
            elif nlistM[-1] == min(nlistM[-3:]):
                pass
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if newhighP:
                        if topV:
                            if min(plistM[-3:]) < 5:
                                # 2009-05-04 KLSE
                                sig, state = sval2, 20
                            elif nlistM[-1] > 5:
                                # 2015-03-16 CARLSBG
                                sig, state = -sval2, -20
            elif plistP[-1] == min(plistP[-3:]):
                pass
            else:
                pass
        elif plistM[-1] == min(plistM[-3:]):
            sval3 = sval + 3
            if nlistM[-1] == max(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    pass
                elif nlistP[-1] == max(nlistP[-3:]):
                    if isprev3topM():
                        if isprev3topP():
                            if isprev3bottomP():
                                if nlistP[-1] > 0:
                                    # 2009-07-29 PADINI
                                    sig, state = sval3, 10
            elif nlistM[-1] == min(nlistM[-3:]):
                if plistP[-1] == max(plistP[-3:]):
                    if nlistP[-1] == max(nlistP[-3:]):
                        if prevtopP:
                            if isprev3bottomP():
                                if newlowV:
                                    # 2015-04-01 KLSE
                                    sig, state = -sval3, -20
            elif plistP[-1] == max(plistP[-3:]):
                if nlistP[-1] == max(nlistP[-3:]):
                    if newhighM:
                        if topP:
                            # 2013-11-07 KESM
                            sig, state = sval3, 30
                        elif newhighP:
                            # 2013-11-13 KESM
                            sig, state = sval3, -30
                    elif newhighP:
                        if plistM[-1] > 10:
                            # 2014-07-31 DUFU
                            sig, state = sval3, -40
                        elif nlistP[-1] > 0:
                            if min(nlistM[-3:]) > 5:
                                # 2013-10-02 KESM
                                sig, state = sval3, 45
            elif plistP[-1] == min(plistP[-3:]):
                pass
        elif plistP[-1] == max(plistP[-3:]):
            sval4 = sval + 4
            if nlistP[-1] == max(nlistP[-3:]):
                if nlistM[-1] == max(nlistM[-3:]):
                    if prevtopP:
                        if isprev3bottomP():
                            if isprev3topM():
                                if isprev3bottomM():
                                    if min(nlistM[-3:]) < 5:
                                        if nlistP[-1] > 0:
                                            # 2016-02-24 KLSE
                                            sig, state = sval4, 1
                        if isprev3topM():
                            if plistM[-1] > 10:
                                if newhighP:
                                    # 2012-03-16 N2N newhighV
                                    sig, state = sval4, -1
                            elif min(nlistM[-3:]) > 5:
                                if isprev3bottomM():
                                    if min(nlistP[-3:]) > 0:
                                        # 2014-05-02 KESM
                                        sig, state = sval4, -3
                                else:
                                    # 2018-04-02 F&N
                                    sig, state = sval4, 3
                elif nlistM[-1] == min(nlistM[-3:]):
                    if nlistM[-1] < 5:
                        if prevtopP:
                            if isprev3topM():
                                if newhighP:
                                    if nlistM[-1] < 5:
                                        if nlistP[-1] > 0:
                                            # 2018-05-02 F&N
                                            sig, state = sval4, 10
                        elif isprev3topM():
                            pass
                    elif plistM[-1] < 10:
                        if topP:
                            # 2016-06-01 F&N
                            sig, state = sval4, 12
                elif topP:
                    if newlowM:
                        if plistV[-1] == min(plistV[-3:]) or newhighC:
                            # 2016-06-01 F&N
                            sig, state = sval4, 20
                        else:
                            # 2013-12-03 KESM picked up under retrace
                            sig, state = sval4, -22
                elif newhighP:
                    if nlistP[-1] > 0:
                        if min(nlistM[-3:]) > 5:
                            # 2013-11-29 KESM
                            sig, state = sval4, -30
            elif nlistP[-1] == min(nlistP[-3:]):
                pass
        elif plistP[-1] == min(plistP[-3:]):
            sval5 = sval + 5
            if nlistP[-1] == max(nlistP[-3:]):
                pass
            elif nlistP[-1] == min(nlistP[-3:]):
                if nlistM[-1] == min(nlistM[-3:]):
                    if bottomM:
                        if isprev3topM():
                            if nlistM[-1] < 5:
                                if min(nlistP[-3:]) > 0:
                                    # 2018-01-03 KLSE
                                    sig, state = sval5, 21
        elif nlistM[-1] == max(nlistM[-3:]):
            sval6 = sval + 6
            if nlistP[-1] == max(nlistP[-3:]):
                if isprev3topM():
                    if isprev3bottomM():
                        pass
                    elif isprev3topP():
                        if isprev3bottomP():
                            if nlistP[-1] > 0:
                                # 2016-04-04 KLSE
                                sig, state = -sval6, 1
        return sig, state

    def evalExtremes(sval):
        sig, state = 0, 0
        if newhighM and newhighP and newhighV:
            if isprev3bottomM() and isprev3bottomP():
                if tripleM in n3u:
                    if narrowP == 9:
                        # 2018-08-02 DUFU
                        sig, state = sval, 1
        if not sig:
            if newlowM and newlowP and newlowV:
                if topP and topV:
                    if isprev3bottomM():
                        # 2018-07-02 KLSE
                        sig, state = sval, 2
        if not sig:
            if topM and topP and topV:
                if newlowV:
                    if max(nlistM[-3:]) < 5:
                        if nlistP[-1] == max(nlistP[-3:]):
                            # 2009-07-07 KLSE
                            sig, state = sval, 3
                    elif min(nlistM[-3:]) > 5:
                        if nlistM[-1] == min(nlistM[-3:]) or \
                                isprev3bottomP():
                            # 2014-04-02 KESM
                            # 2016-09-06 KESM
                            sig, state = sval, 4
                        else:
                            # 2015-05-06 CARLSBG
                            sig, state = -sval, 4
                elif newlowP:
                    # 2015-08-21 PARAMON
                    sig, state = sval, 5
        if not sig:
            if tripleM in p3d and tripleP in p3d and tripleV in p3d:
                if newlowC or bottomC:
                    pass
                elif newhighP or bottomP:
                    # 2011-11-01 PADINI
                    sig, state = sval, 6
                elif isprev3bottomM() and isprev3bottomP():
                    if max(plistM[-3:]) > 10:
                        # 2018-03-16 KESM
                        sig, state = -sval, 5
                    elif newhighM:
                        # 2011-07-04 KLSE
                        sig, state = -sval, 6
                    '''
                    elif plistV[-1] < 0:
                        # 2011-05-05 KLSE
                        sig, state = sval, 6
                    '''
        if not sig:
            if vvalP == 2 and (bottomC or prevbottomC):
                if tripleP == 2 and max(nlistP[-3:]) < 0:
                    if max(plistM) <= 10:
                        # 2013-05-13 KESM
                        sig, state = sval, -7
        if not sig:
            if mvalN == 1:
                if prevtopM and isprev3topP():
                    if min(nlistM[-3:]) > 5:
                        if min(nlistP[-3:]) > 0:
                            if newlowC:
                                # 2014-03-06 DUFU
                                sig, state = sval, 8
        if not sig:
            if plistP[-1] < 0 or pvalP == 1:
                if topC:
                    if tripleM == 6 and tripleP in n3d:
                        if bottomM and bottomP:
                            # 2015-01-19 KESM
                            sig, state = sval, 9
        '''
        if not sig:
            if max(nlistP[-3:]) < 0:
                if tripleP in p3u and tripleM in p3d:
                    if plistP[-1] > 0 and plistP[-2] < 0:
                        if newhighV and prevtopV:
                            # 2014-02-05 CARLSBG
                            sig, state = sval, 10
                        else:
                            # 2014-02-25 CARLSBG
                            sig, state = sval, -10
                    elif newhighM and not newhighP:
                        # 2014-04-24 CARLSBG
                        sig, state = -sval, 10
        '''
        if not sig:
            if bottomC and newhighC and narrowM == 6:
                if posM in [0, 4] or posP in [0, 4] or posV in [0, 4] or \
                        topM or topP or bottomM or bottomP or bottomV or topV or \
                        prevtopM or prevtopP or prevbottomM or prevbottomP or prevbottomV or prevtopV:
                    pass
                elif max(plistM[-3:]) < 10 and min(nlistM[-3:]) > 5:
                    if min(nlistP[-3:]) > 0:
                        # 2012-08-23 PADINI
                        sig, state = -sval, -11
                        if lastM < min(nlistM[-3:]):
                            sig, state = -sval, 11
        if not sig:
            if prevtopV and nlistV[-1] > 0:
                if newlowM and newlowP:
                    if isprev3topM() and isprev3bottomM():
                        if isprev3bottomP():
                            # 2014-02-04 PADINI
                            sig, state = sval, 12
        if not sig:
            if tripleM == 9:
                if nlistM[-1] > 10:
                    if newlowP:
                        # 2009-03-18 F&N
                        sig, state = sval, 13
                    elif prevbottomP:
                        if plistP[-1] == max(plistP[-3:]):
                            # 2009-06-16
                            sig, state = sval, 14
        '''
                    elif newhighC:
                        # 2008-10-03 F&N (insufficient data)
                        sig, state = -sval, 14
        '''
        if not sig:
            if topV and newlowV:
                if bottomM and bottomP:
                    # topC
                    if topM or plistP[-1] < 0:
                        # 2019-01-02 PADINI
                        sig, state = -sval, 15
                    elif not (isprev3topM() or isprev3topP()):
                        if max(plistM[-3:]) > 10:
                            # 2018-05-03 KESM
                            sig, state = -sval, -15
                        else:
                            # 2011-10-10 KLSE
                            sig, state = sval, 15
                elif plistV[-2] < 0 and nlistP[-1] > 0:  # vvalP == 2 and pvalN == 1:
                    if isprev3bottomM():
                        if isprev3topM:
                            if isprev3bottomP():
                                # 2012-04-16 KLSE
                                sig, state = sval, -16
                            else:
                                if mvalley or lastM > plistM[-1]:
                                    # 2017-11-01 CARLSBG
                                    sig, state = sval, -17
                                else:
                                    # 2017-10-03 CARLSBG
                                    sig, state = sval, 17
        if not sig:
            if bottomV:
                if prevtopV:
                    if isprev3topM():
                        if isprev3topP():
                            if min(nlistM[-3:]) > 5:
                                if min(nlistP[-3:]) > 0:
                                    # 2012-08-01 N2N
                                    sig, state = sval, -18
        return sig, state

    lastTrxn, cmpvlists, composelist, hstlist, div = \
        sdict['lsttxn'], sdict['cmpvlists'], sdict['composelist'], \
        sdict['hstlist'], sdict['div']
    ssig, sstate, psig, pstate, nsig, nstate, neglist, poslist = 0, 0, 0, 0, 0, 0, "", ""
    # [tolerance, pdays, ndays, matchlevel] = matchdate
    [pdiv, ndiv, _, mpdates] = div
    composeC, composeM, composeP, composeV = \
        composelist[0], composelist[1], composelist[2], composelist[3]
    [posC, newhighC, newlowC, topC, bottomC, prevtopC, prevbottomC] = composeC
    [posM, newhighM, newlowM, topM, bottomM, prevtopM, prevbottomM] = composeM
    [posP, newhighP, newlowP, topP, bottomP, prevtopP, prevbottomP] = composeP
    [posV, newhighV, newlowV, topV, bottomV, prevtopV, prevbottomV] = composeV

    '''
    cmPpos, cpPpos, mpPpos, cmNpos, cpNpos, mpNpos = -99, -99, -99, -99, -99, -99
    cmPdate, cpPdate, mpPdate = "1970-01-01", "1970-01-01", "1970-01-01"
    cmNdate, cpNdate, mpNdate = "1970-01-01", "1970-01-01", "1970-01-01"
    if 'CM' in pdiv:
        [cmPdate, cmPtype, cmPcount, cmPtol, cmPpos] = pdiv['CM']
    if 'CP' in pdiv:
        [cpPdate, cpPtype, cpPcount, cpPtol, cpPpos] = pdiv['CP']
    if 'MP' in pdiv:
        [mpPdate, mpPtype, mpPcount, mpPtol, mpPpos] = pdiv['MP']
    if 'CM' in ndiv:
        [cmNdate, cmNtype, cmNcount, cmNtol, cmNpos] = ndiv['CM']
    if 'CP' in ndiv:
        [cpNdate, cpNtype, cpNcount, cpNtol, cpNpos] = ndiv['CP']
    if 'MP' in ndiv:
        [mpNdate, mpNtype, mpNcount, mpNtol, mpNpos] = ndiv['MP']
    '''

    lastprice, lastC, lastM, lastP, lastV, firstC, firstM, firstP, firstV = \
        lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4], lastTrxn[5], \
        lastTrxn[7], lastTrxn[8], lastTrxn[9], lastTrxn[10]
    cmpvMC, cmpvMM, cmpvMP, cmpvMV = cmpvlists[0], cmpvlists[1], cmpvlists[2], cmpvlists[3]
    plistC, nlistC, plistM, nlistM, plistP, nlistP, plistV, nlistV = \
        cmpvMC[2], cmpvMC[3], cmpvMM[2], cmpvMM[3], cmpvMP[2], cmpvMP[3], cmpvMV[2], cmpvMV[3]  # 0=XP, 1=XN, 2=YP, 3=YN

    minC, maxC, range4, lowbar, lowbar2, midbar, highbar = minmaxC()
    minP, maxP, midP = minmaxP()

    narrowC, narrowM, narrowP, countP, tripleM, tripleP, tripleV, tripleBottoms, tripleTops = \
        0, 0, 0, 0, 0, 0, 0, 0, 0
    p0, p1, p2, mpdiv, negstr, posstr = None, None, None, 0, "", ""
    '''
              Nx   N^   Nv
        P^    1    2    3
        Pv    4    5    6
        Px    X    7    8
    '''
    p3u, p3d, n3u, n3d = [1, 2, 3], [4, 5, 6], [2, 5, 7], [3, 6, 8]
    bearpeak, bullvalley = [1, 2, 3], [4, 5, 6]
    cpeak, pdateC, ndateC = ispeak(0)
    mpeak, pdateM, ndateM = ispeak(1)
    ppeak, pdateP, ndateP = ispeak(2)
    vpeak, pdateV, ndateV = ispeak(3)
    cvalley = not cpeak
    mvalley = not mpeak
    pvalley = not ppeak
    vvalley = not vpeak
    cmpInSync, mpInSync = isDivergentSync()
    mvalP, pvalP, vvalP, mvalN, pvalN, vvalN = evalMPV()
    firstDate, lastDate = lastTrxn[-5], lastTrxn[0]
    busdays = abs(getBusDaysBtwnDates(firstDate, lastDate))
    if plistM is None or plistP is None or nlistM is None or nlistP is None:
        nosignal = True
    elif (len(nlistP) < 5 or len(plistP) < 5) and busdays < 345:
        print "%s:Insufficient data:%s,%s,%d,%d,%d" % (counter, firstDate, lastDate,
                                                       busdays, len(nlistP), len(plistP))
        nosignal = True
    else:
        nosignal = False
        cmpdiv, mpdiv, mpnow, highlowM, highlowP, lowhighM, lowhighP = divergenceDiscovery()
        p0, p2, cmpvlen = shapesDiscovery()
        # matrix = evalMatrix()
        # p1 = p0 + [matrix, cmpdiv]
        [c, m, p, v, tripleM, tripleP, tripleV,
         narrowC, narrowM, narrowP, countP, tripleBottoms, tripleTops] = p0
        [firstmp, firstmn, firstpp, firstpn] = p2
        [plenM, nlenM, plenP, nlenP, plenV, nlenV, plenC, nlenC] = cmpvlen

    if nosignal or plistC is None or nlistC is None:   # or DBGMODE == 3:
        pass
    else:
        # psig, pstate, nsig, nstate, neglist, poslist = evalPNsignals()
        # negstr = "".join(neglist)
        # posstr = "".join(poslist)
        ssig, sstate = evalExtremes(90)
        if ssig:
            pass
        elif newlowC:
            ssig, sstate = evalLowC2(10)
            if not ssig:
                mia = 10
        else:
            mia = 0
            if not ssig or sstate > 900:
                # if newhighC or (firstC == maxC and lastC > max(plistC)) or lastC > highbar:
                if newhighC or lastC > highbar:
                    # 2014-07-30 DUFU
                    # 2016-01-28 PADINI
                    pass
                elif narrowC == 1 or (tripleBottoms and tripleBottoms < 3) or \
                        bottomC or (not newlowC and plistC[-1] < lowbar) or \
                        (not newhighC and nlistC[-1] < lowbar and firstC == maxC and lastC < firstC) or\
                        (cvalley and nlistC[-1] < lowbar):
                    # 2017-03-31 KLSE firstC == maxC
                    # 2019-02-04 KESM firstC < nlistC[-1]
                    ssig, sstate = evalBottomC(20)
                    if not ssig:
                        mia = 20
            if not ssig or sstate > 900:
                if newhighC or (firstC == maxC and lastC > highbar):
                    # tripleTops == 1 to bypass here?
                    # 2009-02-04 F&N
                    # 2017-10-03, 2017-01-02 CARLSBG
                    pass
                elif narrowC > 1 or tripleBottoms > 1 or tripleTops > 5 or \
                        (topC and lastC < highbar) or \
                        (topC and nlenC < 3 and lastC < plistC[-2]) or \
                        (prevtopC and not (newhighC or newlowC)) or \
                        (not (topC or prevtopC) and plistC[-1] > highbar and lastC > midbar) or \
                        (not (topC or prevtopC) and nlistC[-1] > highbar and lastC > min(nlistC)) or \
                        (plenC > 2 and plistC[-2] == max(plistC) and lastC < lowbar):
                    #   (firstC == maxC and lastC < highbar) or \
                    # 2013-12-24 DUFU firstC == maxC
                    # 2014-11-07 DUFU tripleTops instead
                    # 2014-12-15 KESM
                    # 2015-04-16 CARLSBG
                    # 2011-10-04 PADINI lastC < lowbar
                    # 2016-01-04 PADINI
                    # 2014-02-05 CARLSBG isprev3topC and lastC < lowbar
                    ssig, sstate = evalRetrace(30)
                    if not ssig and not mia:
                        mia = 30
            if not ssig or sstate > 900:
                if newhighC or (firstC == maxC and (lastC > max(plistC) or lastC > highbar)):
                    # 2014-08-05 PADINI lastC > highbar
                    if prevtopC and nlistC[-1] > highbar:
                        # 2016-05-03 PADINI
                        pass
                    else:
                        ssig, sstate = evalHighC(40)
                        # ssig, sstate = evalUptrend(40)
                        if not ssig and not mia:
                            mia = 40
            if not ssig or sstate > 900:
                if topC or prevtopC or tripleTops == 1 or \
                        (newhighC and plistC[-1] == max(plistC) and
                         plistC[-1] > midbar) or \
                        (prevtopC and nlistC[-1] > highbar) or \
                        (plenC > 1 and plistC[-1] > highbar and plenC > 1 and plistC[-2] < lowbar):
                    # skipped 2018-06-01 F&N newhighC
                    ssig, sstate = evalTopC(50)
                    if not ssig and not mia:
                        mia = 50
            if not ssig or sstate > 900:
                if (bottomC or narrowC == 9) and lastC > highbar or \
                        (plenC > 1 and nlistC[-2] == min(nlistC) and plistC[-1] < midbar) or \
                        (plistC[-1] < lowbar and plenC > 2 and lastC > max(plistC[-3:])) or \
                        (plistC[-1] < midbar and
                         nlistC[-1] == max(nlistC[-3:]) and nlistC[-1] > lowbar):
                    ssig, sstate = evalUptrend(60)
                    if not ssig and not mia:
                        mia = 60
        if not ssig:
            if posV in [0, 4] or bottomV or topV or prevbottomV or prevtopV or \
                    isprev3topV() or isprev3bottomV():
                if not mia:
                    mia = 79
                else:
                    mia = 70 + (mia / 10)
                ssig, sstate = mia, 0
            elif posM in [0, 4] or posP in [0, 4] or \
                    topM or topP or bottomM or bottomP or \
                    prevtopM or prevtopP or prevbottomM or prevbottomP:
                if not mia:
                    mia = 89
                else:
                    mia = 80 + (mia / 10)
                ssig, sstate = mia, 0

    # return ssig, sstate, psig, pstate, nsig, nstate, p1, negstr, posstr
    return ssig, sstate, psig, pstate, nsig, nstate, p0, \
        mvalP, pvalP, vvalP, mvalN, pvalN, vvalN


def checkposition(pntype, pnlist, firstpos, lastpos):
    def profilemapping(pntype, listoflists):
        xpositive, xnegative, ypositive, ynegative = \
            listoflists[0], listoflists[1], listoflists[2], listoflists[3]  # 0=XP, 1=XN, 2=YP, 3=YN
        if xpositive is None:
            xpositive = []
        if xnegative is None:
            xnegative = []
        if ypositive is None:
            ypositive = []
        if ynegative is None:
            ynegative = []
        datelist = sorted(xpositive + xnegative)
        psorted, nsorted = sorted(ypositive, reverse=True), sorted(ynegative)
        ylist, profiling = [], []
        for dt in datelist:
            try:
                pos = xpositive.index(dt)
                yval = ypositive[pos]
                ylist.append(yval)
                ppos = psorted.index(yval) + 1
                if pntype == 'C':
                    profiling.append('p' + str(ppos))
                elif pntype == 'M':
                    prefix = 'hp' if yval > 10 else 'mp' if yval > 5 else 'lp'
                    profiling.append(prefix + str(ppos))
                else:
                    prefix = 'pp' if yval > 0 else 'np'
                    profiling.append(prefix + str(ppos))
            except ValueError:
                pos = xnegative.index(dt)
                yval = ynegative[pos]
                ylist.append(yval)
                npos = nsorted.index(yval) + 1
                if pntype == 'C':
                    profiling.append('v' + str(npos))
                elif pntype == 'M':
                    prefix = 'hv' if yval > 10 else 'mv' if yval > 5 else 'lv'
                    profiling.append(prefix + str(npos))
                else:
                    prefix = 'pv' if yval > 0 else 'nv'
                    profiling.append(prefix + str(npos))
        return ylist, profiling

    profiling, snapshot = "", ""
    pos, newlow, newhigh, bottom, top, prevbottom, prevtop = \
        0, 0, False, False, False, False, False
    if len(pnlist) > 6 and pntype == 'C':
        nlist = pnlist[7]  # 0=XP, 1=XN, 2=YP, 3=YN
        count0 = -1 if nlist is None else nlist.count(0)
        if count0 < 0 or count0 > 1:
            print "\tSkipped W0", count0
            return [-1, newlow, newhigh, top, bottom, prevtop, prevbottom], profiling, snapshot

    plist, nlist = pnlist[2], pnlist[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    if plist is None:
        # free climbing (PADINI 2012-07-30)
        minP, maxP = firstpos, firstpos
    else:
        minP, maxP = min(plist), max(plist)
        if pntype == "C":
            if minP > firstpos:
                # PADINI 2013-04-18
                minP = firstpos
            if maxP < firstpos:
                maxP = firstpos
    if nlist is None:
        # free falling
        minN, maxN = firstpos, firstpos
    else:
        minN, maxN = min(nlist), max(nlist)
        if pntype == "C":
            if minN > firstpos:
                # PADINI 2013-04-18
                minN = firstpos
            if maxN < firstpos:
                maxN = firstpos
    clist, profiling = profilemapping(pntype, pnlist)
    if lastpos > maxP:
        newhigh = True
        pos = 4
    if len(clist) and clist[-1] == maxP:
        top = True
    elif plist is not None and plist[-1] == maxP:
        prevtop = True

    if lastpos < minN:
        newlow = True
        pos = 0
    if len(clist) and clist[-1] == minN:
        bottom = True
    elif nlist is not None and nlist[-1] == minN:
        prevbottom = True

    if pntype == 'C':
        if not newhigh and not newlow:
            range4 = (maxP - minN) / 4
            if lastpos < minN + range4:
                pos = 1
            elif lastpos >= maxP - range4:
                pos = 3
            else:
                pos = 2
    elif pos != 4:
        if plist is not None and nlist is not None:
            if len(plist) > 1:
                plistsorted = sorted(plist)
                ppoint = plistsorted[-2]
            else:
                ppoint = plist[0]
            if len(nlist) > 1:
                nlistsorted = sorted(nlist)
                npoint = nlistsorted[1]
            else:
                npoint = nlist[0]
            pos = 3 if lastpos > ppoint else 2 if lastpos > npoint else 0 if newlow else 1

        # retrace = True if (top or prevtop) and pos > 1 else False

    snapshot = ".".join(profiling)
    profiling = snapshot
    snapshot = ""
    snapshot = [snapshot + str(i * 1) for i in [pos, newhigh, newlow,
                                                top, bottom, prevtop, prevbottom]]
    snapshot = "".join(snapshot)
    return [pos, newhigh, newlow, top, bottom, prevtop, prevbottom], profiling, snapshot


def collectCompositions(pnlist, lastTrxn):
    def formListCMPV(cmpv, mthlist):
        xp, xn, yp, yn = mthlist[0], mthlist[1], mthlist[2], mthlist[3]  # 0=XP, 1=XN, 2=YP, 3=YN
        # cmpv 0=C, 1=M, 2=P, 3=V
        cmpvlist = []
        cmpvlist.append(xp[cmpv])
        cmpvlist.append(xn[cmpv])
        cmpvlist.append(yp[cmpv])
        cmpvlist.append(yn[cmpv])
        return cmpvlist

    def datesmatching(mm, mp):
        tolerance, matchlevel = 0, 0
        mxpdates, mxndates = mm[0], mm[1]
        pxpdates, pxndates = mp[0], mp[1]
        if mxpdates is not None and pxpdates is not None:
            pdays = abs(getBusDaysBtwnDates(mxpdates[-1], pxpdates[-1]))
        else:
            pdays = -1
        if mxndates is not None and pxndates is not None:
            ndays = abs(getBusDaysBtwnDates(mxndates[-1], pxndates[-1]))
        else:
            ndays = -1
        if pdays == 0 or ndays == 0:
            matchlevel = 5 if pdays == 0 and ndays == 0 else 4
        else:
            if DBGMODE:
                print "pdays, ndays =", pdays, ndays
            pdays1, ndays1 = pdays, ndays
            if pdays > 0:
                if len(mxpdates) > len(pxpdates):
                    pdays = getBusDaysBtwnDates(mxpdates[-2], pxpdates[-1])
                elif len(mxpdates) < len(pxpdates):
                    pdays = getBusDaysBtwnDates(mxpdates[-1], pxpdates[-2])
                elif len(mxpdates) > 1 and len(pxpdates) > 1:
                    pdays = getBusDaysBtwnDates(mxpdates[-2], pxpdates[-2])
                pdays = abs(pdays)
            if ndays > 0:
                if len(mxndates) > len(pxndates):
                    ndays = getBusDaysBtwnDates(mxndates[-2], pxndates[-1])
                elif len(mxndates) < len(pxndates):
                    ndays = getBusDaysBtwnDates(mxndates[-1], pxndates[-2])
                elif len(mxndates) > 1 and len(pxndates) > 1:
                    ndays = getBusDaysBtwnDates(mxndates[-2], pxndates[-2])
                ndays = abs(ndays)
            matchlevel = 3 if pdays == 0 and ndays == 0 else 2 if pdays == 0 or ndays == 0 else 0

            if not matchlevel and pdays != -1 and ndays != -1:
                # match tops and bottoms
                npdays1 = getBusDaysBtwnDates(mxndates[-1], pxpdates[-1])
                pndays1 = getBusDaysBtwnDates(mxpdates[-1], pxndates[-1])
                npdays2, pndays2 = -1, -1
                if len(mxpdates) > 1 and len(mxndates) > 1 and len(pxpdates) > 1 and len(pxndates) > 1:
                    npdays2 = getBusDaysBtwnDates(mxndates[-2], pxpdates[-2])
                    pndays2 = getBusDaysBtwnDates(mxpdates[-2], pxndates[-2])
                matchlevel = 7 if npdays1 == 0 and npdays2 == 0 or pndays1 == 0 and npdays2 == 0 else \
                    6 if (npdays1 == 0 or npdays2 == 0) and (pndays1 == 0 or pndays2 == 0) else 0
                if DBGMODE:
                    print "npdays1,2, pndays1,2 =", npdays1, npdays2, pndays1, pndays2
                if matchlevel:
                    pdays, ndays = 0, 0

            if matchlevel:
                if matchlevel < 6:
                    tolerance = 1
            else:
                if pdays1 != -1 and abs(pdays) < abs(pdays1) and abs(ndays) < abs(ndays1):
                    if pdays < 30 or ndays < 30:
                        tolerance = 2
                        matchlevel = 1
                else:
                    if ndays1 != -1 and pdays1 < 30 or ndays1 < 30:
                        pdays, ndays = pdays1, ndays1
                        tolerance = 0
                        matchlevel = 1
        if DBGMODE:
            print "mdates =", mxpdates, mxndates
            print "pdates =", pxpdates, pxndates
        return [tolerance, pdays, ndays, matchlevel]

    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastC, lastM, lastP, lastV, firstC, firstM, firstP, firstV = \
        lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4], lastTrxn[5], \
        lastTrxn[7], lastTrxn[8], lastTrxn[9], lastTrxn[10]
    if DBGMODE:
        print "first:%.2fC,%.2fc,%.2fm,%.2fp,%.2fv" % (lastprice, firstC, firstM, firstP, firstV)
        print "last:%.2fC,%.2fc,%.2fm,%.2fp,%.2fv" % (lastprice, lastC, lastM, lastP, lastV)

    if len(pnlist) > 1:
        pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
        cmpvWC = formListCMPV(0, pnW)
    else:
        pnM = pnlist[0]
        cmpvWC = []
    cmpvMC = formListCMPV(0, pnM)
    cmpvMM = formListCMPV(1, pnM)
    cmpvMP = formListCMPV(2, pnM)
    cmpvMV = formListCMPV(3, pnM)
    composeC, historyC, strC = checkposition('C', cmpvMC + cmpvWC, firstC, lastC)
    if DBGMODE:
        [posC, newhighC, newlowC, topC, bottomC, prevtopC, prevbottomC] = composeC
        print "C=%d,h=%d,l=%d,t=%d,b=%d,pT=%d,pB=%d, %s" % \
            (posC, newhighC, newlowC, topC, bottomC, prevtopC, prevbottomC, historyC)
    posC = composeC[0]
    if posC < 0:
        return None, None, None, None, None
    composeM, historyM, strM = checkposition('M', cmpvMM, firstM, lastM)
    composeP, historyP, strP = checkposition('P', cmpvMP, firstP, lastP)
    composeV, historyV, strV = checkposition('V', cmpvMV, firstV, lastV)
    matchdate = datesmatching(cmpvMM, cmpvMP)
    if DBGMODE:
        [posM, newhighM, newlowM, topM, bottomM, prevtopM, prevbottomM] = composeM
        print "M=%d,h=%d,l=%d,t=%d,b=%d,pT=%d,pB=%d, %s" % \
            (posM, newhighM, newlowM, topM, bottomM, prevtopM, prevbottomM, historyM)
        [posP, newhighP, newlowP, topP, bottomP, prevtopP, prevbottomP] = composeP
        print "P=%d,h=%d,l=%d,t=%d,b=%d,pT=%d,pB=%d, %s" % \
            (posP, newhighP, newlowP, topP, bottomP, prevtopP, prevbottomP, historyP)
        [posV, newhighV, newlowV, topV, bottomV, prevtopV, prevbottomV] = composeV
        print "V=%d,h=%d,l=%d,t=%d,b=%d,pT=%d,pB=%d, %s" % \
            (posV, newhighV, newlowV, topV, bottomV, prevtopV, prevbottomV, historyV)
        [tolerance, pdays, ndays, matchlevel] = matchdate
        print "tol, pdays, ndays, matchlevel =", tolerance, pdays, ndays, matchlevel

    cmpvlists = []
    cmpvlists.append(cmpvMC)
    cmpvlists.append(cmpvMM)
    cmpvlists.append(cmpvMP)
    cmpvlists.append(cmpvMV)
    composelist = []
    composelist.append(composeC)
    composelist.append(composeM)
    composelist.append(composeP)
    composelist.append(composeV)
    hstlist = []
    hstlist.append(historyC)
    hstlist.append(historyM)
    hstlist.append(historyP)
    hstlist.append(historyV)
    strlist = []
    strlist.append(strC)
    strlist.append(strM)
    strlist.append(strP)
    strlist.append(strV)
    return matchdate, cmpvlists, composelist, hstlist, strlist


if __name__ == '__main__':
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
        if S.DBG_ALL:
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
        if S.DBG_ALL:
            print "Start,Stop,Step =", nums
        return nums.split(',')

    def loadargs():
        klse = "scrapers/i3investor/klse.txt"
        tmpdir = "data"
        if args['--datadir']:
            S.DATA_DIR = args['--datadir']
            if not S.DATA_DIR.endswith("/"):
                S.DATA_DIR += "/"
        dbgmode = "" if args['--debug'] is None else args['--debug']
        # DBG_ALL = True if "a" in dbgmode else False
        dbg = 1 if "s" in dbgmode else 2 if "u" in dbgmode else 3 if "p" in dbgmode else 0
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
        return stocklist, tmpdir, S.MVP_CHART_DAYS, args['--simulation'], dbg

    def plot(scode, showchart):
        lsttxn = sdict['lsttxn']
        plttitle = lsttxn[0] + " (" + str(chartDays) + "d) [" + scode + "]"
        if len(signals):
            title = plttitle + " [" + signals + "]"
        else:
            title = plttitle + " [" + counter + "]"
        if args['--plot']:
            figsize = (10, 6) if showchart else (15, 9)
            fig, axes = plt.subplots(4, 1, figsize=figsize, sharex=False, num=plttitle)
            jsonPlotSynopsis(axes, lsttxn, sdict['pnlist'])
            fsize = 10 if showchart else 15
            fig.canvas.set_window_title(plttitle)
            fig.suptitle(title, fontsize=fsize)
            if dbg and dbg != 2:
                prefix = '\t' if dbg == 1 else ""
                print prefix, title

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            if showchart:
                plt.show()
            else:
                if len(signals):
                    outname = "data/mpv/synopsis/" + counter
                    if simulation is not None:
                        outname = outname + "." + lsttxn[0]
                    plt.savefig(outname + "-synopsis.png")
            plt.close()
        else:
            if len(signals) and dbg != 2:
                print title

    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    stocklist, tmpdir, chartDays, simulation, dbg = loadargs()
    mpvdir = os.path.join(tmpdir, "mpv", '')
    for counter in sorted(stocklist.iterkeys()):
        if counter in S.EXCLUDE_LIST:
            print "INF:Skip: ", counter
            continue
        try:
            if simulation is None:
                dates = jsonLastDate(counter, tmpdir)
                dates = [dates]
            else:
                nums = simulation.split(",") if "," in simulation else numsFromDate(counter, simulation, chartDays)
                if len(nums) <= 0:
                    print "Input not found:", simulation
                    continue
                dates = simulation.split(":")
            end = dates[0]
            if len(dates) > 2:
                step = int(dates[2])
            else:
                step = 1
            while True:
                start = pdDaysOffset(end, chartDays * -1)
                sdict = loadfromjson(tmpdir, counter, end)
                if sdict is None:
                    print "Not a trading day:", end
                else:
                    signals = scanSignals(mpvdir, dbg, counter, sdict)
                    plot(stocklist[counter], args['--showchart'])
                if len(dates) < 2 or end >= dates[1]:
                    break
                else:
                    # end = getDayOffset(end, step)
                    end = pdDaysOffset(end, step)
                    if end > dates[1]:
                        end = dates[1]
        except Exception:
            traceback.print_exc()
