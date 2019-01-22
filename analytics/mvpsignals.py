'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S
from common import loadCfg
from utils.dateutils import getBusDaysBtwnDates
from utils.fileutils import grepN


def scanSignals(mpvdir, dbg, counter, sdict, pid):
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
        with open(outfile, "ab") as fh:
            bbsline = trxndate + "," + signals
            fh.write(bbsline + '\n')
        if 1 == 1:
            # Stop this until system is ready for production use
            sss = workdir + "signals/" + label + "-" + trxndate + ".csv"
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
    sss, sstate, psig, pstate, nsig, nstate, patterns, neglist, poslist = \
        extractSignals(sdict, extractX())
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
    p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    if patterns is not None:
        [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15] = patterns
    lastprice = lastTrxnData[1]
    signaldet = "(c%s.m%s.p%s.v%s),(%d.%d.%d.%d^%d.%d.%d^%d.%d.%d^%d.%d.%d.%s.%d),(%s^%s),%.2f" % \
        (strC[:1], strM[:1], strP[:1], strV[:1],
         p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15,
         neglist, poslist, lastprice)
    # tolerance, pdays, ndays, matchlevel)
    signalsss, label = "NUL,0.0,0.0.0.0", ""
    if sss or psig or nsig:
        label = "TBD" if sss > 900 else \
                "TSS" if sss < 0 else "BBS" if sss > 0 else \
                "TSS" if psig < 0 or nsig < 0 else \
                "BBS" if psig > 0 or nsig > 0 else \
                "NUL"
        signalsss = "%s,%d.%d,%d.%d.%d.%d" % (label, sss, sstate, nsig, nstate, psig, pstate)

    signals = "%s,%s,%s" % (counter, signalsss, signaldet)
    if dbg == 2:
        # print '\n("%s", %s, %s, %s, "%s"),\n' % (counter, pnlist, div, lastTrxnData, signals.replace('\t', ''))
        print '\n("%s", "%s", "%s"),\n' % (counter, lastTrxnData[0], signals.replace('\t', ''))
    printsignal(mpvdir, lastTrxnData[0])
    return signals


def extractSignals(sdict, xpn):

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
        if nlistM[-1] >= 5 and nlistM[-1] < 7.5:
            if mvalley and plistM[-1] >= 10:
                retrace = 1
            elif mpeak and plistM[-1] < plistM[-2] and plistM[-2] >= 10:
                retrace = 2
        elif prevbottomM and bottomP:
            if mpeak and plistM[-1] < 10 and tripleM in p3d:
                # 2013-03-13 ORNA
                retrace = 3
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
                        # DUFU 2014-11-21 retrace completed
                        # UCREST 2017-08-02 topM valley divergence
                        # YSPSAH 2013-04-29
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
                            # MUDA 2013-04-30
                            # PADINI 2015-08-04
                            ncount += 1
                            if pnrange[i] <= nrange2:
                                # KLSE 2016-11-14
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
                    # VSTECS 2014-08-29 minmax=0.5653
                    return 0, 0
                if plenC > 1 and plistC[-1] > highbar and plistC[-2] < lowbar:
                    # 2014-06-24 MUDA
                    return 0, 0
                # YSPSAH 2017-02-21: [0.179, 0.035, 0.356, 0.125, 0.0302, 0.031]
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
                        # KESM 2017-01-09
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
                        # KLSE 2013-01-28 <pnrange>: [0.125, 0.125, 0.0586, 0.309, 0.101, 0.684]
                        break
                if vcount2 > 0.5:
                    vcount += 1
                    alt = 1
                return vcount, alt

            if newlowC:
                return 0
            ncount, alt = volatilityCheck()
            narrowc = 0
            if ncount < 4:
                ncount = 0
            elif ncount > 3:
                # GHLSYS 2017-01-06
                if alt:
                    # KLSE 2017-01-09
                    ncount = 1
                if max(nlistC[-3:]) < lowbar:
                    # 2017-01-11 KLSE
                    narrowc = 1
                elif max(nlistC[-3:]) > lowbar and min(nlistC[-3:]) < midbar:
                    # 2017-01-03 GHLSYS
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
                # DUFU 2014-05-12
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
                if ncount and ncount < 2:
                    ncount = 0
                else:
                    narrowc = 1
            return narrowc  # ncount

        def bottomscount():
            tripleBottoms = 0
            if plistC[-1] < plistC[-2] and plistC[-2] < plistC[-3]:
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
                        # 2017-08-28 N2N
                        tripleBottoms = 2
                    elif nlistC[-1] > midbar and max(nlistC[-3:]) > highbar:
                        # 2014-02-05 PADINI newlowC, 2015-10-02
                        tripleBottoms = 3

                    if nlenC > 3 and nlistC[-3] < nlistC[-4]:
                        ''' --- lower peaks and lower valleys extension --- '''
                        if plistC[-4] > highbar and plistC[-3] > midbar and plistC[-1] < lowbar:
                            # 2018-07-23 DANCO
                            tripleBottoms = 1
                        elif nlistC[-1] > midbar and max(nlistC[-3:]) > highbar:
                            # 2018-06-13 DUFU retrace with valley follow by peak divergence
                            tripleBottoms = 3
                        elif nlistC[-4] > midbar and nlistC[-1] < lowbar:
                            # 2014-04-25 PETRONM
                            tripleBottoms = 2
                elif nlenC > 3 and bottomC and \
                        nlistC[-2] < nlistC[-4] and nlistC[-3] < nlistC[-4]:
                    ''' --- lower peaks and lower valleys variant --- '''
                    if plistC[-1] < lowbar and nlistC[0] > highbar:
                        # 2011-10-12 DUFU
                        tripleBottoms = 1
                    elif plistC[-2] < lowbar and nlistC[0] > highbar:
                        # 2012-04-10 DUFU
                        tripleBottoms = 1
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
                if len(nlistM) < 3 or len(nlistP) < 3:
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

    '''
    def evalNarrowM(sval):
        sig, state = 0, 0
        if posC == 2 and narrowM:
            sig, state = sval, 1
            if newlowP or newhighV:
                state = 2
            elif bottomP or newlowV:
                state = 3
        elif not topC and posC == 3 and narrowM:
            # 2012-02-21 MUDA
            sig = -sval
            if tripleM in p3d or tripleP in n3u:
                # 2015-04-30 KLSE
                state = 1
        return sig, state

    def evalM10x3(sval):
        sig, state = 0, 0
        # 3 consecutive M above 10 - powerful break out / bottom reversal signal
        if nlistM[-1] < 0:
            # 2017-10-17 AXREIT
            sig, state = -sval, 1
        elif plistP[-1] > 0 and plistP[-2] > 0 and plistP[-3] > 0:
            # 2013-03-01 MAGNI top retrace with CM and CP valley divergence follow by break out
            sig, state = sval, 2
        # elif posC < 2:
            # --- bottom reversal --- #
            # 2014-05-05, DUFU 2014-06-04 (plistP[-1] < 0) bottom break out
            # 2014-09-10 DUFU (5 plistM vs 4 plistP)
        else:
            if topC or topM:
                if mpeak:
                    # 2014-09-03 DUFU retracing
                    sig, state = sval, 0
                else:
                    # 2014-11-21 DUFU retrace completed
                    # 2017-08-02 UCREST topM valley divergence
                    sig, state = sval, 3
            elif not newlowC:
                if nlistP[-1] > 0 and lastP > plistP[-1]:
                    # 2013-04-29 YSPSAH
                    sig, state = sval, 4
                else:
                    if pvalley and lastP > plistP[-1]:
                        # 2015-02-17 MUDA
                        sig, state = sval, 5
                    else:
                        # 2015-04-14 MUDA
                        sig, state = -sval, 6
            elif mpeak or lastM < 0:
                # 2018-12-21 ABLEGRP
                sig, state = -sval, 5
            else:
                sig, state = sval, 0
            # sstate = 2 if "CM" in ndiv or "CP" in ndiv else 1
        return sig, state
    '''

    def evalRetrace(sval):
        def evalC0():
            if (newlowM and newlowP) or (bottomM or bottomP):
                # 2014-02-05 PADINI newlowC
                # 2012-01-20 YSPSAH bottomP
                sig, state = sval, 1
            elif newhighM or newhighP or topM or topP:
                # 2015-10-02 PADINI
                sig, state = sval, 2
            elif newhighV:
                # 2017-08-28 N2N
                sig, state = sval, 3
            elif cmpdiv in bearpeak:
                sig, state = -sval, 4
                if newlowP:
                    # 2014-12-10 KLSE newlowP
                    # 2018-04-03 GHLSYS newlowP, newlowM
                    sig, state = sval, 4
            elif cmpdiv in bullvalley:
                if nlistP[-1] > 0:
                    # 2009-04-01 KLSE
                    sig, state = sval, 5
                else:
                    sig, state = -sval, -6
            else:
                # 2011-10-12 DUFU
                sig, state = -sval, 7
            return sig, state

        def evalC1(sts=20):
            sig, state = 0, 0
            if cpeak and cmpdiv in bearpeak:
                # 2016-02-03 ORNA
                # 2018-02-06 GHLSYS
                sig, state = -sval, sts + 1
                if newlowP:
                    # 2014-12-10 KLSE newlowP
                    # 2018-04-03 GHLSYS newlowP, newlowM
                    sig, state = sval, sts + 1
            elif cvalley and cmpdiv in bullvalley:
                if plistP[-1] > plistP[-2] and plistP[-1] > plistP[-3]:
                    # 2009-06-10 KLSE
                    # 2018-06-07 DANCO
                    sig, state = sval, 11
                elif plistP[-2] == max(plistP):
                    # 2012-01-20 SCGM bottomC bullish nlistM[-1] > plistM[-2]
                    sig, state = sval, 12
                else:
                    sig, state = sval, 0
            elif newhighC:
                # 2012-10-25 ORNA
                sig, state = -sval, 12
            elif plistM[-1] < 10:
                # 2016-01-21 ORNA
                sig, state = -sval, 13
            return sig, state

        sig, state = 0, 0
        if posC < 3 and newhighV:
            # 2018-07-17 DUFU
            sig, state = sval, 1
        elif cmpdiv in bearpeak:
            # 2018-02-06 GHLSYS
            sig, state = -sval, 2
            if newlowP:
                # 2014-12-10 KLSE newlowP
                # 2018-04-03 GHLSYS newlowP, newlowM
                sig, state = sval, 2
        elif posC < 1:
            sig, state = evalC0()
        else:
            sig, state = evalC1()
        return sig, state

    def eval3Tops(sval):
        def evalHigherTops():
            sig, state = 0, 0
            if tripleM in p3d and tripleP in p3d and tripleV in p3d and \
                    nlenV > 1 and nlistV[-1] > nlistV[-2] and \
                    plistM[-1] > 5 and plistP[-1] > 0:
                # 2013-03-20 KLSE
                sig, state = sval, 1
            elif newlowM:
                # 2017-01-09 MAGNI
                sig, state = sval, 2
            elif bottomM:
                if cpeak:
                    # 2014-07-25 MUDA
                    sig, state = -sval, 4
                else:
                    # 2014-09-29 MUDA
                    sig, state = sval, 4
            elif tripleP in n3u:
                if tripleM in n3d:
                    # 2015-10-27 MUDA
                    sig, state = sval, 6
                else:
                    sig, state = sval, 0
            elif tripleP in p3d:
                sig, state = sval, -8
                if newlowP or newlowM:
                    # 2014-12-10 KLSE
                    # 2018-04-03 GHLSYS
                    sig, state = sval, 8
            return sig, state

        sig, state = evalHigherTops()
        return sig, state

    def evalBottomsC(sval):
        def common_narrows():
            def evalP(sval5):
                sigP, stateP = 0, 0
                if newhighP or topP or prevtopP:
                    if nlistM[-1] > 10:  # tripleM == 9 (M10x3)
                        # 2014-05-09 DUFU
                        sigP, stateP = sval5, 1
                    elif nlistM[-2] > 10:
                        # 2014-06-24 DUFU
                        sigP, stateP = -sval5, -1
                    else:
                        # 2013-12-02 DUFU
                        # 2018-03-06 MUDA
                        sigP, stateP = -sval5, 1
                elif bottomP:
                    # 2013-05-29 PADINI oversold
                    sigP, stateP = sval5, 0
                elif not tripleP:
                    pass
                elif cmpdiv in bullvalley:
                    if narrowP:
                        if narrowP == 9:
                            # 2012-08-16 ORNA
                            # 2016-12-29 ORNA
                            # 2018-06-13 DUFU retrace with valley follow by peak divergence
                            sigP, stateP = sval5, 2
                        elif nlistP[-1] > 0:
                            # 2016-12-27 GHLSYS
                            sigP, stateP = sval5, 3
                        else:
                            # 2017-10-24 MUDA
                            sigP, stateP = -sval5, 3
                    elif tripleP in n3u or tripleP in p3d:
                        if nlistM[-1] < 5 and (nlistP[-2] < 0 or nlistM[-1] > nlistM[-2]):
                            # 2013-03-06 KLSE
                            # 2018-07-11 DANCO
                            sigP, stateP = sval5, 4
                            if bottomC and nlistM[-1] > 10:
                                # 2018-09-03 DANCO
                                sigP, stateP = sval5, 0
                        else:
                            # 2012-01-16 DUFU
                            # 2018-03-02 GHLSYS
                            sigP, stateP = -sval5, 6
                elif tripleP in p3u and nlistP[-1] > 0 and plistM[-1] >= 10 and nlistM[-1] < 5:
                    if plistM[-1] >= 10:
                        # 2013-06-05 SCGM
                        sigP, stateP = sval5, 7
                    else:
                        sigP, stateP = -900 - sval5, 7
                elif narrowP == 9:
                    if nlistP[-2] < 0 and nlistP[-1] >= 0:
                        # 2012-08-02 ORNA with topV
                        sigP = sval5
                        stateP = -8 if posC < 2 else 8
                    else:
                        sigP, stateP = -900 - sval5, 10
                elif narrowP:
                    if tripleM in n3u and tripleP in n3u:
                        # 2017-01-12 ORNA
                        if lastM >= nlistM[-1]:
                            sigP, stateP = sval5, 11
                        else:
                            sigP, stateP = sval5, 0
                return sigP, stateP

            def evalM(sval6):
                sigM, stateM = 0, 0
                if not tripleM:
                    pass
                elif topM and nlistP[-1] > 0:
                    # 2011-11-08 N2N
                    # 2014-02-20 PETRONM
                    sigM, stateM = sval6, 1
                elif newhighM:
                    if not (newhighP or topP) and max(plistP[-3:]) == max(plistP):
                        # 2012-04-02 DUFU with narrowM
                        sigM, stateM = -sval6, 1
                elif bottomM or prevbottomM:
                    # 2014-03-05 PADINI short rebound
                    # 2015-09-17 ORNA
                    if bottomM:
                        sigM, stateM = sval6, 2
                    else:
                        sigM, stateM = -sval6, 2
                elif nlistM[-1] > 10 and nlistP[-1] > 0:
                    # 2013-05-29 PADINI 20% short push before top reversal
                    sigM, stateM = -sval6, -3
                elif tripleM in p3u and nlistP[-1] >= 0:
                    if newhighM and posC < 2:
                        # 2013-03-21 PETRONM
                        sigM, stateM = sval6, 4
                    elif posC > 2:
                        # 2017-02-08 SCGM
                        sigM, stateM = sval6, 5
                    else:
                        sigM, stateM = sval6, 6
                        if topV and plistP[-1] < plistP[-2]:
                            # 2012-08-02 ORNA
                            sigM, stateM = sval6, 7
                elif tripleM in [2, 4, 5, 6, 7]:
                    if nlistM[-1] >= 5:
                        if nlistP[-1] > 0:
                            sigM, stateM = sval6, 8
                        elif lastM > plistM[-1]:
                            # 2016-08-25 MAGNI Strong reversal after short retrace (p=-0.057)
                            # 2013-07-04 ORNA
                            sigM, stateM = sval6, 9
                        else:
                            # 2018-01-04 DANCO newlowM
                            # 2018-03-06 GHLSYS
                            sigM, stateM = -sval6, 10
                            if newlowP:
                                # 2014-12-10 KLSE no longer valid here due to not bottomC
                                # 2018-04-03 GHLSYS newlowP, newlowM - not applicable due to not bottomC
                                sigM, stateM = sval6, 10
                    elif nlistM[-1] > nlistM[-2]:
                        # 2013-03-06 KLSE
                        sigM, stateM = sval6, 11
                    else:
                        sigM, stateM = -sval6, 11
                elif narrowM:
                    sigM = sval6
                    if nlistP[-1] >= 0:
                        # 2013-03-25 KLSE
                        stateM = 15
                        if nlistM[-1] > 5:
                            # 2013-09-06 KESM
                            # 2017-02-03 GHLSYS
                            stateM = 16
                    elif nlistM[-1] > 5:
                        # 2014-03-10 VSTECS
                        # 2017-02-21 YSPSAH
                        # 2018-07-20 DANCO
                        stateM = 17
                    else:
                        sigM, stateM = -900 - sval6, 1
                    if posC < 2 and stateM:
                        stateM = -stateM
                return sigM, stateM

            sig, state = evalP(sval + 1)
            if not sig or sig > 900:
                sig, state = evalM(sval + 2)
                if not sig or sig > 900:
                    if (newhighM or topM) and posC < 2:
                        # 2018-11-11 SUPERLN
                        sig, state = sval, 3
                    elif bottomP or prevbottomP:
                        if nlenM > 3 and min(nlistM[-4:]) > 5:
                            # 2013-04-03 GHLSYS
                            sig, state = sval, 4
                        else:
                            sig, state = sval, 0
                    elif (newhighP or topP) and posC < 2:
                        sig, state = -903, 1
                    elif nlistP[-1] < 0:
                        # 2017-05-16 MUDA
                        # 2018-08-02 MAGNI
                        sig, state = -sval, 4
                    else:
                        # 2019-01-07 GUOCO, HSL
                        sig, state = sval, 5
            return sig, state

        ssig, sstate = 0, 0
        if narrowC > 3 and (bottomP or narrowP or
                            (cmpdiv in [4, 5] and
                             ((nlistP[-1] > nlistP[-2] or nlistP[-1] > nlistP[-3]) or
                              (nlistM[-1] > nlistM[-2] or nlistM[-1] > nlistM[-3])) or
                             (tripleM in p3u or tripleP in p3u))):
            ssig, sstate = common_narrows()
        elif narrowC > 0:
            if topP or prevtopP:
                # 2011-12-01 DUFU m>5, p>0
                ssig, sstate = -sval, 10
            elif nlistM[-1] > 5 and nlistP[-1] > 0:
                if nlenM > 2 and (nlistM[-2] < 5 or nlistM[-3] < 5) and \
                        nlenP > 2 and (nlistP[-2] < 0 or nlistP[-3] < 0):
                    # 2017-01-09 KLSE
                    ssig, sstate = sval, 10
                elif posC < 2 and tripleP in n3u:
                    if nlenP > 2 and nlistP[-3] < 0:
                        ssig, sstate = sval, 11
                    else:
                        # 2013-02-18 DUFU
                        ssig, sstate = -sval, 11
            else:
                ssig, sstate = common_narrows()

        return ssig, sstate

    def evalHighC(sval):
        sig, state = sval, 99
        if newhighP:
            if newhighM:
                # 2007-02-07 KLSE
                sig, state = -sval, 1
                if newhighV:
                    # 2007-02-28 KLSE
                    sig, state = sval, 1
            elif plistM[-1] > plistM[-2] or plistM[-1] > plistM[-3]:
                # 2014-02-04, 2014-02-25 MUDA
                # 2017-03-01 PADINI
                # 2017-05-03 PADINI newlowV
                sig, state = sval, 2
            else:
                # 2014-02-20 ORNA
                # 2014-07-25 VSTECS
                # 2015-02-09 DUFU
                sig, state = -sval, 3
        elif topP or topM:
            # 2012-09-05 KLSE
            sig, state = -sval, 4
            if topP and topM:
                if topV or plistM[-1] < 10:
                    # 2018-09-03 DUFU
                    sig, state = sval, 4
                else:
                    # 2018-08-29 PADINI
                    sig, state = -sval, 4
        elif bottomP or min(nlistM) == nlistM[-1]:
            if newhighM or lastM > 10 or plistM[-1] > 10:
                # 2014-08-05 MUDA
                sig, state = -sval, 5
            elif plistM[-1] > plistM[-2] or plistM[-1] > plistM[-3]:
                # 2017-03-29 PADINI
                sig, state = sval, 5
            else:
                sig, state = -sval, 6
        elif newhighM:
            if min(nlistM[-4:]) == min(nlistM) and min(nlistM) < 5:
                # 2011-07-13 KLSE
                sig, state = -sval, 7
            elif not (newhighP or prevtopP):
                # 2010-09-01 KLSE
                sig, state = sval, 7
            else:
                # 2014-07-17 ORNA
                sig, state = -sval, 7
        elif plistM[-1] > plistM[-2] or plistM[-1] > plistM[-3]:
            if nlistP[-1] < 0:
                # 2017-01-26 MAGNI
                sig, state = sval, 8
                if newhighP or topP:
                    # 2014-02-11 MUDA
                    # 2014-06-04 PADINI
                    pass
                elif max(plistM[-3:]) > 10:
                    # 2015-02-05 ORNA
                    sig, state = -sval, 8
            else:
                if lastM < 5 or lastP < 0:
                    # 2010-10-06 KLSE
                    sig, state = sval, 9
                else:
                    # tripleP in p3d
                    # 2013-08-01 ORNA
                    # 2014-05-05 KLSE
                    sig, state = sval, -9
                if plistP[-1] < plistP[-2] and plistP[-1] < plistP[-3]:
                    # 2016-04-04 VSTECS
                    sig, state = -sval, 9
        else:
            # 2013-07-29 KLSE
            sig, state = -sval, 10
            if tripleP in n3d or nlistM[-1] > nlistM[-2]:
                # 2013-04-03 KLSE
                sig, state = sval, 10
            elif tripleP in p3d:
                # 2012-09-05 KLSE
                sig, state = -sval, 11
                if newhighV or topV or cmpdiv in bearpeak:
                    # 2014-06-02 KLSE
                    # 2011-12-01 ORNA
                    sig, state = -sval, 12
                elif newlowM and newlowP:
                    # 2011-09-28 KLSE
                    sig, state = sval, -13
                elif bottomM and bottomP:
                    # 2011-10-05 KLSE
                    sig, state = sval, 13
                elif bottomM:
                    # 2011-10-05 KLSE
                    sig, state = sval, 14
            elif tripleM in p3d:
                if bottomM:
                    # 2013-01-03 ORNA
                    sig, state = -sval, 15
                elif newlowM:
                    # 2011-08-18 ORNA
                    sig, state = -sval, 15
                else:
                    sig, state = -sval, 0
            elif tripleP in p3u:
                if topV and newlowV:
                    # 2018-11-05 YSPSAH
                    sig, state = -sval, 16
                elif nlistP[-1] < 0:
                    # 2013-12-19 ORNA
                    sig, state = sval, -16
                elif nlistP[-2] < 0:
                    # 2014-01-09 ORNA
                    # 2014-03-13 ORNA
                    sig, state = sval, -17
                else:
                    # 2014-08-29 VSTECS
                    sig, state = sval, -17
            elif cmpdiv in bearpeak:
                if nlistP[-1] < 0:
                    # 2011-11-17 ORNA
                    sig, state = -sval, 18
                else:
                    # 2014-06-24 MUDA
                    # 2019-01-06 DUFU
                    sig, state = sval, 18
            elif plistP[-1] > 0:
                if lastM < 5 and lastP < 0:
                    # 2013-09-02 KLSE
                    sig, state = -sval, -19
                elif nlistM[-1] > 5:
                    # 2010-08-11 KLSE
                    sig, state = sval, 19
                else:
                    # 2014-08-21 ORNA
                    sig, state = -sval, 20
            else:
                # from pEvaluation
                if cvalley and cmpdiv in bullvalley:
                    if nlistP[-1] < 0:
                        if prevtopP:
                            # 2013-01-31 ORNA
                            sig, state = -sval, 21
                        else:
                            # 2013-12-19 ORNA
                            sig, state = sval, 21
                    elif highlowM:
                        # 2011-05-12 ORNA
                        sig = -sval if newhighC or newhighP or topP else sval
                        sig, state = -sval, 22
                    elif newhighC and newhighM:
                        sig, state = -sval, 23
                    else:
                        # 2014-02-20 ORNA
                        sig = -sval if newhighP or topP else sval
                        sig, state = -sval, 24
                elif nlistP[-1] < 0 or cpeak:
                    sig, state = -sval, 0
                    if (newlowM or bottomM) and (newlowP or bottomP):
                        # 2014-12-16 MUDA
                        sig, state = sval, 25
                    elif newlowP and bottomV:
                        # 2014-12-23 MUDA
                        sig, state = sval, 26
                elif plistM[-1] < plistM[-2] and plistM[-1] < plistM[-3] or \
                        tripleM in n3u and lastM < nlistM[-1]:
                    sig, state = sval, 0
                    if lastM < nlistM[-1]:
                        # 2017-12-06 PADINI
                        sig, state = -sval, 27
        return sig, state

    def evalTopC(sval):
        def evalBottomPM(st=0):
            sig, state = 0, 0
            if (prevbottomM or prevbottomP) and not (topM or topP):
                if newlowM or newlowP:
                    if newlowM and newlowP and nlistM[-1] > 5:
                        # 2018-04-04 PADINI
                        sig, state = -sval, st + 1
                    elif newlowM or bottomM:
                        if max(nlistP[-3:]) < 0:
                            # 2018-08-02 N2N
                            sig, state = -sval, st + 1
                        else:
                            # 2011-09-21 KLSE newlowM, prevbottomM, bottomP
                            # 2011-09-28 KLSE newlowM, prevbottomM, newlowP
                            # 2013-02-06 KLSE newlowM, prevbottomM, p3d + p3d
                            # 2014-12-09 MUDA newlowM, prevbottomM, plistP[-1] < 0
                            # 2014-12-29 MUDA newlowM, bottomM, newlowP
                            # 2018-05-02 PADINI newlowM, prevbottomM
                            sig, state = sval, st + 1
                    else:
                        # 2011-08-03 KLSE
                        sig, state = -sval, st + 1
                elif prevbottomM or prevbottomP:
                    # 2011-11-16 KLSE
                    # 2011-12-07 KLSE
                    sig, state = sval, st + 2
                    if plistM[-1] > 10:
                        # 2015-02-24 MUDA final push before collapse
                        sig, state = -sval, -st - 2
                        if bottomM or bottomP:
                            # 2015-02-10 MUDA
                            sig, state = sval, st + 3
                    elif nlistM[-1] > 5:
                        # 2018-05-16 PADINI
                        sig, state = sval, st + 3
                    elif plistM[-1] > plistM[-2] and plistM[-1] > plistM[-3]:
                        # 2011-11-16 KLSE
                        # 2011-12-07 KLSE
                        sig, state = sval, -st - 4
                    else:
                        # 2008-05-07 KLSE
                        sig, state = -sval, st + 4
                else:
                    if cmpdiv in bullvalley:
                        sig, state = sval, st + 5
                    else:
                        sig, state = -sval, st + 5
            elif (newlowM and newlowP) or (bottomM and bottomP) or \
                    (newlowM and bottomP) or (bottomM and newlowP):
                if topM or topP or prevtopM or prevtopP:
                    # 2014-10-14 MUDA topM
                    # 2018-12-05 PADINI
                    sig, state = -sval, st + 7
                    if bottomM or bottomP:
                        if plistP[-1] < 0:
                            # 2015-01-06 MUDA
                            # 2019-01-02 PADINI
                            sig, state = sval, st + 7
                elif newlowP:
                    if newlowM:
                        # 2008-03-12 KLSE === 2011-09-28 KLSE
                        if nlistM[-1] < 5:
                            # 2011-09-28 KLSE
                            sig, state = sval, st + 9
                        else:
                            # 2008-03-12 KLSE
                            sig, state = -sval, -st - 9
                    elif nlistM[-1] > 5:
                        # 2018-04-11 PADINI
                        sig, state = sval, -st - 10
                    else:
                        # 2011-10-05 KLSE bottomM, newlowP
                        sig, state = sval, st + 10
                elif bottomM or bottomP:
                    if newhighM or newhighP:
                        # 2011-11-02 KLSE
                        sig, state = sval, -st - 12
                    elif bottomM and bottomP:
                        # 2008-04-02 KLSE
                        # 2011-10-12 KLSE bottomM, bottomP
                        sig, state = sval, st + 12
            elif newlowP and not newlowM:
                sig, state = -sval, st + 14
                if topP:
                    # 2015-03-02 DUFU
                    sig, state = sval, st + 14
            elif newlowM or bottomM:
                if topM and topP or prevtopM and prevtopP:
                    # 2018-11-21 PADINI
                    sig, state = sval, st + 16
                elif newlowP or bottomP:
                    # 2018-04-04 PADINI
                    # 2018-11-07 PADINI
                    sig, state = -sval, st + 16
                else:
                    if cmpdiv in bullvalley:
                        # 2018-05-16 PADINI
                        sig, state = sval, st + 18
                    else:
                        # 2012-11-28 KLSE
                        # 2018-04-25 PADINI
                        sig, state = sval, -st - 18
            return sig, state

        def evalTopPM(st=20):
            # 2014-10-07 MUDA topM
            # 2016-03-01 MUDA === PADINI 2018-11-21 === 2014-12-29 MUDA
            # 2018-05-07 KLSE
            sig, state = 0, 0
            if topM and topP or prevtopM and prevtopP:
                if plistM[-1] > 10:
                    if nlistM[-1] < nlistM[-2] and nlistM[-1] < nlistM[-3] and \
                            nlistP[-1] < nlistP[-2] and nlistP[-1] < nlistP[-3]:
                        # 2018-09-24 PADINI
                        # 2018-10-03 PADINI
                        sig, state = -sval, st + 1
                    else:
                        # 2014-04-03 KESM
                        # 2017-05-24 GHLSYS
                        sig, state = sval, st + 1
                else:
                    if (nlistM[-1] > nlistM[-2] or nlistM[-1] > nlistM[-3]) and \
                            nlistP[-1] > nlistP[-2] or nlistP[-1] > nlistP[-3]:
                        # 2013-09-02 GHLSYS
                        # 2018-11-02 DUFU
                        sig, state = sval, st + 2
                    else:
                        sig, state = sval, st + 71
            elif topM or prevtopM:
                if prevtopP or max(plistP[-3:]) == max(plistP):
                    # 2012-06-01 VSTECS
                    # 2012-10-01 SCGM
                    # 2014-10-10 MUDA
                    sig, state = -sval, st + 3
                elif plenP > 4 and plistP[-1] < max(plistP[-5:]):
                    if pvalley or mvalley:
                        # 2010-06-30 KLSE
                        # 2014-06-03 VSTECS
                        sig, state = sval, st + 3
                    else:
                        # 2015-09-18 SCGM
                        sig, state = sval, -st - 3
                else:
                    # 2012-09-12 KLSE
                    # 2013-06-04 VSTECS
                    sig, state = -sval, st + 4
            elif topP or prevtopP:
                if not bottomM and min(nlistM[-3:]) == min(nlistM):
                    # 2013-06-26 KLSE
                    # 2018-04-04 KLSE
                    sig, state = -sval, st + 7
                elif plistM[-1] > 10:
                    # 2012-05-03 N2N
                    # 2015-03-19 DUFU
                    sig, state = sval, st + 7
                elif topV or prevtopV:
                    # 2017-11-03 N2N
                    sig, state = -sval, st + 8
                elif newhighC and cmpdiv in bullvalley:
                    if lastM > 10:
                        sig, state = -sval, 0
                        if newhighM:
                            # 2014-07-17 ORNA
                            sig, state = -sval, st + 10
                    else:
                        # 2017-01-26 MAGNI
                        sig, state = sval, st + 10
                else:
                    sig, state = -sval, 0
            elif lastM < nlistM[-2]:
                # 2015-04-13 DUFU prevtopP
                sig, state = -sval, st + 10
            return sig, state

        if (newlowP or newlowM or bottomP or bottomM or
                (prevbottomP or prevbottomM)) and not (topM or topP):
            sig, state = evalBottomPM()
        elif topP or topM or prevtopP or prevtopM:
            sig, state = evalTopPM()
        elif cmpdiv in bearpeak:
            # 2008-02-06 KLSE
            sig, state = -sval, 31
        elif plistM[-1] < plistM[-2] and plistM[-1] < plistM[-3]:
            # 2012-11-07 KLSE
            # 2013-08-07 KLSE
            # 2018-01-24 PADINI
            sig, state = -sval, 33
            if prevbottomM:
                # 2013-02-20 KLSE
                sig, state = sval, 34
            elif tripleM in n3u:
                # 2013-08-28
                sig, state = sval, 35
            elif tripleP in p3u:
                # 2014-02-06 ORNA
                sig, state = sval, 36
            elif nlistM[-1] > 5 and nlistM[-2] < 5 and nlistP[-1] > 0 and nlistP[-2] < 0:
                if mpeak or ppeak:
                    # 2013-08-07 KLSE
                    sig, state = -sval, 37
                    if lastM < 5 or lastP < 0:
                        # 2013-09-04 KLSE
                        sig, state = sval, 37
                elif nlistP[-1] > 0:
                    # 2013-09-25 KLSE
                    sig, state = sval, 38
                else:
                    sig, state = -sval, 38
        elif plistM[-1] > plistM[-2] or plistM[-1] > plistM[-3]:
            # 2014-06-03 MUDA
            sig, state = sval, 40
            if newlowP or newhighP or topP:
                # 2013-09-05 ORNA
                # 2014-02-11 MUDA
                # 2014-06-04 PADINI
                pass
            elif plenM > 3 and max(plistM[-3:]) > 10:
                # 2014-06-24 MUDA
                # 2015-02-05 ORNA
                sig, state = -sval, -40
            elif plistP[-1] < plistP[-2] and plistP[-1] < plistP[-3]:
                # 2016-05-09 VSTECS
                sig, state = -sval, 41
        else:
            sig, state = -sval, 42
        return sig, state

    def evalLowC(sval):
        sig, state = -sval, 1
        if tripleBottoms:
            if newlowM and not newlowP:
                if plistP[-1] > 0 and lastP > 0:
                    # 2009-03-18 KLSE
                    sig, state = sval, 1
                else:
                    sig, state = sval, 0
            elif newlowC and not (newlowM or newlowP):
                if plenM > 2 and plistM[-1] > plistM[-2] and plistM[-1] > plistM[-3]:
                    if plenP > 2 and plistP[-1] > plistP[-2] and plistP[-1] > plistP[-3]:
                        # 2009-03-25 KLSE
                        # 2011-10-12 N2N topM
                        sig, state = sval, 2
        elif bottomM:
            if nlistM[-1] > 5 or nlistP[-1] < 0:
                # 2018-03-22 DANCO
                sig, state = -sval, 3
        elif newlowM and newlowP:
            if plistP[-1] < 0:
                # 2018-03-03 AXREIT
                sig, state = sval, 4
            else:
                sig, state = sval, 0
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
    p1, p2, mpdiv, negstr, posstr = None, None, 0, "", ""
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
    if plistM is None or plistP is None or nlistM is None or nlistP is None:
        nosignal = True
    else:
        nosignal = False
        cmpdiv, mpdiv, mpnow, highlowM, highlowP, lowhighM, lowhighP = divergenceDiscovery()
        p0, p2, cmpvlen = shapesDiscovery()
        matrix = evalMatrix()
        p1 = p0 + [matrix, cmpdiv]
        [c, m, p, v, tripleM, tripleP, tripleV,
         narrowC, narrowM, narrowP, countP, tripleBottoms, tripleTops] = p0
        [firstmp, firstmn, firstpp, firstpn] = p2
        [plenM, nlenM, plenP, nlenP, plenV, nlenV, plenC, nlenC] = cmpvlen

    if nosignal:   # or DBGMODE == 3:
        pass
    else:
        psig, pstate, nsig, nstate, neglist, poslist = evalPNsignals()
        negstr = "".join(neglist)
        posstr = "".join(poslist)
        if newlowC:
            ssig, sstate = evalLowC(1)
        else:
            if not ssig or sstate > 900:
                if narrowC == 1 or (tripleBottoms and tripleBottoms < 3):
                    ssig, sstate = evalBottomsC(1)
            if not ssig or sstate > 900:
                if narrowC > 1 or tripleBottoms > 1 or tripleTops > 5:
                    ssig, sstate = evalRetrace(4)
            if not ssig or sstate > 900:
                if tripleBottoms > 2 or (tripleTops and tripleTops < 6):
                    ssig, sstate = eval3Tops(5)
            if not ssig or sstate > 900:
                if newhighC:
                    if prevtopC and plistC[-1] < highbar:
                        ssig, sstate = evalHighC(6)
            if not ssig or sstate > 900:
                if topC or prevtopC or (newhighC and plistC[-1] == max(plistC)):
                    ssig, sstate = evalTopC(7)
            if not ssig or sstate > 900:
                if posC < 3 and newlowM and newlowP:
                    # --- Oversold signal after retrace from break out --- #
                    if ((plistM[-1] > 10 or plistM[-2] > 10) and not topP) or \
                            (nlistM[-1] < nlistM[-2] and nlistM[-1] < nlistM[-3]):
                        # 2013-05-03 DUFU
                        # 2017-12-05 MAGNI
                        # 2017-12-15 YSPSAH
                        ssig, sstate = -8, 1
                    else:
                        # 2014-09-02 DUFU
                        # 2014-12-16 VSTECS
                        # 2018-04-02 N2N
                        ssig, sstate = 8, 1

    return ssig, sstate, psig, pstate, nsig, nstate, p1, negstr, posstr


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


def bottomBuySignals(lastTrxn, matchdate, cmpvlists, composelist, pdiv, ndiv, odiv):
    bottomBuySignal, bbs_stage, bottomrevs = 0, 0, 0
    lastprice, lastC, lastM, lastP, lastV = \
        lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4], lastTrxn[5]
    cmpvMC, cmpvMM, cmpvMP, cmpvMV = cmpvlists[0], cmpvlists[1], cmpvlists[2], cmpvlists[3]
    plistC, nlistC, plistM, nlistM, nlistP, plistV = \
        cmpvMC[2], cmpvMC[3], cmpvMM[2], cmpvMM[3], cmpvMP[3], cmpvMV[2]  # 0=XP, 1=XN, 2=YP, 3=YN
    composeC, composeM, composeP, composeV = \
        composelist[0], composelist[1], composelist[2], composelist[3]
    [posC, newhighC, newlowC, topC, bottomC, prevtopC, prevbottomC] = composeC
    [posM, newhighM, newlowM, topM, bottomM, prevtopM, prevbottomM] = composeM
    [posP, newhighP, newlowP, topP, bottomP, prevtopP, prevbottomP] = composeP
    [posV, newhighV, newlowV, topV, bottomV, prevtopV, prevbottomV] = composeV
    [tolerance, pdays, ndays, matchlevel] = matchdate
    '''
     1 - PADINI 2014-03-03 BBS,1,1 (LowC + LowM with higher P divergent) - short rebound
       - PADINI 2014-03-14 BBS,1,2
     2 - PADINI 2011-10-12 (LowC + LowP with higher M divergent) - weak oversold
     3 - PETRONM 2013-04-24: extension of 1 after retrace - short rebound
     4 - Pre-cursor of 12 powerful break out
       - EDGENTA 2018-08-16 with 30% rebound (LowC + highP)
       - FLBHD 2018-07-02
       - DUFU 2016-04-14 bottomM, prevTop C,M,V & P
     5 - DUFU 2015-08-26 (BottomM + BottomP + BottomV) - strong reversal
     6 - Recovery from retrace before long term reversal - pre-cursor of 4?
       - DUFU 2016-02-10 BBS,6,1 topC + topP + lowM + pbV
       - DUFU 2016-03-15 BBS,6,2
     7 - bottomC + (LowV / HighV) - powerful bottom reversal
       - PADINI 2015-08-17
       - DUFU 2018-07
     8 - Extension of 9 - short term rebound during volatility period
       - DUFU 2014-11-21 BottomM + BottomP
       - PADINI 2017-02-06 BottomP + HighV and higherM
       - KLSE 2017-12-12 BottomM + HighV and higerP
         # below nlistC condition not applicable due to one short retrace in KLSE example
         # else 8 if not newlowC and posV > 0 and lastC > nlistC[-1] and \
     9 - DUFU 2014-11-14 topC + bottomM + bottomP - short term rebound
    10 - KLSE 2017-01-03 - precursor of 4 (bottomC, lowerM with higherP, newlowV)
    11 - KLSE 2018-07-12 - Oversold from top, bottomC + bottomP + bottom V (Variant of 2 with M < 5 or P < 0)
    12 - DUFU 2016-11-01 topC with newlowV - final retrace before powerful break out
    '''
    if nlistM is None or nlistP is None or len(nlistM) < 2 or len(nlistP) < 2:
        return bottomrevs, bottomBuySignal, bbs_stage

    retrace = True if (topC or prevtopC) and posC > 2 else False

    if bottomC and newhighM and newhighP and newhighV and \
            len(plistC) > 2 and len(nlistC) > 2 and \
            plistC[-1] < plistC[-2] and plistC[-2] < plistC[-3] and \
            nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3] and \
            nlistM[-1] > nlistM[-2] and nlistP[-1] > nlistP[-2]:
        # very strong breakout
        bottomBuySignal = 13
    elif matchlevel > 0 and bottomC and posC < 2 and len(plistM) > 2 and len(nlistP) > 2 and \
            plistM[-1] > plistM[-2] and plistM[-2] > plistM[-3] and plistM[-3] > 10 and \
            nlistP[-1] > nlistP[-2] and nlistP[-2] > nlistP[-3] and nlistP[-1] < 0:
        # ----- bottom break out ----- #
        # ----- Higher M peaks and higher P valleys ----- #
        # DUFU 2014-05-02
        bottomBuySignal = 14
    '''
    elif topC or prevtopC:
        if newlowC:
            if (prevtopM or prevtopP) and newlowV and topV \
                and ((bottomP and nlistM[-1] < 5 and nlistM[-2] == min(nlistM)) or
                     (bottomM and nlistP[-1] < 0 and nlistP[-2] == min(nlistP))):
                bottomBuySignal = 11
        elif not newlowC and posV > 0 and \
            ((topM and min(nlistM) > 5 and lastM > nlistM[-1] or
              bottomP and lastP > nlistP[-1]) or
             (bottomM and nlistM[-1] < 5 and nlistP[-1] > min(nlistP))):
            bottomBuySignal = 8
        elif bottomM and bottomP:
            if not (newlowC or bottomC) and prevtopP and bottomV:
                bottomBuySignal = 5
            elif prevbottomC and prevtopP and lastM > 10 and lastP < 0:
                bottomBuySignal = 9
        elif topP and newlowM and (lastM < 5 and lastP > 0):
            bottomBuySignal = 6
        elif prevtopM and lastM > 5 and lastP < 0 and newlowV:
            bottomBuySignal = 12
    elif newlowC or bottomC:
        if (newlowM or bottomM):
            if min(nlistM) < 5 and not (newlowP or bottomP) and not prevtopP and not newlowV \
                    and nlistP[-1] > nlistP[-2]:
                bottomBuySignal = 1
        elif not (newlowM or bottomM):
            if newlowP or bottomP:
                if min(nlistM) < 5 and nlistM[-1] > 5 \
                    and not prevtopP and not newlowV \
                        and nlistP[-1] < nlistP[-2]:
                    bottomBuySignal = 2
            else:
                if (newhighP or topP or newhighM or topM) and not (prevtopM or prevtopP):
                    bottomBuySignal = 4
                elif bottomC:
                    if (newlowV or newhighV) and not (topP or topV or prevtopP or
                                                      prevbottomM or prevbottomV):
                        bottomBuySignal = 7
                    elif (prevbottomM and nlistM[-1] < 5) and \
                            (nlistP[-2] == min(nlistP) and nlistP[-1] > nlistP[-2]) and newlowV:
                        bottomBuySignal = 10
    elif not (newlowC or bottomC):
        if not (newlowP or bottomP) and (newhighM or topM) and \
                min(nlistM) < 5 and nlistM[-1] > 5 and posC == 1:
            bottomBuySignal = 3
    '''
    '''
    else:
        bottomBuySignal = 0 if nlistM is None or nlistP is None or len(nlistM) < 2 or len(nlistP) < 2 \
            else 1 if (newlowC or bottomC) and (newlowM or bottomM) and min(nlistM) < 5 \
            and not (newlowP or bottomP) and not prevtopP and not newlowV \
            and nlistP[-1] > nlistP[-2] \
            else 2 if (newlowC or bottomC) and not (newlowM or bottomM) and min(nlistM) < 5 and nlistM[-1] > 5 \
            and (newlowP or bottomP) and not prevtopP and not newlowV \
            and nlistP[-1] < nlistP[-2] \
            else 3 if not (newlowC or bottomC) and not (newlowP or bottomP) and (newhighM or topM) \
            and min(nlistM) < 5 and nlistM[-1] > 5 and posC == 1 \
            else 4 if (newlowC or bottomC) and not (newlowM or bottomM) and not (newlowP or bottomP) \
            and (newhighP or topP or newhighM or topM) and not (prevtopM or prevtopP) \
            else 5 if topC and not (newlowC or bottomC) and bottomM and prevtopP and bottomP and bottomV \
            else 6 if topC and topP and newlowM and (lastM < 5 and lastP > 0) \
            else 7 if bottomC and (newlowV or newhighV) and not (topP or topV or prevtopP or
                                                                 prevbottomM or prevbottomV) \
            else 8 if not newlowC and posV > 0 and \
                ((topM and min(nlistM) > 5 and lastM > nlistM[-1] or bottomP and lastP > nlistP[-1]) or
                 (bottomM and nlistM[-1] < 5 and nlistP[-1] > min(nlistP))) \
            else 9 if topC and bottomM and bottomP and prevbottomC and prevtopP and lastM > 10 and lastP < 0 \
            else 10 if bottomC and (prevbottomM and
                                    nlistM[-1] < 5) and (nlistP[-2] == min(nlistP) and
                                                         nlistP[-1] > nlistP[-2]) and newlowV \
            else 11 if topC and newlowC and (prevtopM or prevtopP) and newlowV and topV \
            and ((bottomP and nlistM[-1] < 5 and nlistM[-2] == min(nlistM)) or
                 (bottomM and nlistP[-1] < 0 and nlistP[-2] == min(nlistP))) \
            else 12 if topC and prevtopM and lastM > 5 and lastP < 0 and newlowV \
            else 0
    '''
    if bottomBuySignal:
        if bottomBuySignal in [5, 7, 12, 13]:
            bottomrevs = bottomBuySignal
        if bottomBuySignal == 7:
            bbs_stage = 0 if lastP < 0 else 1
        # elif bottomBuySignal == 4:
        #     bbs_stage = 2 if bottomC else 1
        elif bottomBuySignal == 10:
            bbs_stage = 0 if lastV > -0.5 else 1
        elif bottomBuySignal == 12:
            bbs_stage = 0 if lastV < 0 else 1
        elif posV > 0 or (bottomBuySignal == 4 and posC > 1) \
                or (bottomBuySignal == 6 and (bottomM or bottomP)):
            bbs_stage = 1
        elif (newhighP or newhighM) or (bottomP and not bottomM and nlistM[-1] > 5):
            bbs_stage = 2 if posC > 1 else 1 if posV > 0 else 0
    elif not retrace:
        '''
        # bottomrevs 1 = reversal with P remains in negative zone (early signal of reversal)
        # bottomrevs 2 = reversal with P crossing to positive (confirmed reversal)
        # bottomrevs 9 = Now OVS2, end of long term retrace from top with new low M and P,
        #                divergent on month's M and P
        '''
        if nlistC is not None and plistC is not None and nlistM is not None:
            bottom_divider = min(nlistC) + (max(plistC) - min(nlistC)) / 3
            if DBGMODE:
                print "min,max of C=%.2f, %.2f" % (min(nlistC), max(nlistC))
            if posC < 3 and plistC[-1] < bottom_divider and bottomC \
                    and len(nlistM) > 1 and min(nlistM) < 5 and nlistM[-1] > nlistM[-2] \
                    and not topP and not prevtopP and not newlowP and lastM > 5 and not topV:
                # Volume should near or exceeds new low
                # PADINI 2015-08-17, DUFU 2018-07
                bottomrevs = 1 if lastP < 0 else 2
            elif bottomC and newlowP and not newlowM:
                if nlistC is not None and lastC > nlistC[-1]:
                    # PADINI 2011-10-12 - now reclassified under OVS2
                    bottomrevs = 9
                # else failed example: PETRONM 2013-12-06
    else:
        '''
        bottomrevs 3 = end of short term retrace from top with volume (PADINI 2017-02-06)
        maxPV = max(plistV)
        if DBGMODE:
            print "min(nlist)=", min(nlistM), min(nlistP), maxPV, lastV
        bottomrevs = 3 if retrace and not newlowC and \
            (newhighV and (lastV > maxPV * 2 or lastC > nlistC[-1])) and \
            (topM and min(nlistM) > 5 and lastM > nlistM[-1] or
             bottomP and lastP > nlistP[-1]) \
            else 0
        '''
        if not newlowC and posV > 0 and nlistC is not None and lastC > nlistC[-1] and \
            (topM and min(nlistM) > 5 and lastM > nlistM[-1] or
             bottomP and lastP > nlistP[-1]):
            bottomrevs = 3
            maxPV = max(plistV)
            if DBGMODE:
                print "min(nlist)=%.2f,%.2f,%.2f,%.2f" % (min(nlistM), min(nlistP), maxPV, lastV)

    return bottomrevs, bottomBuySignal, bbs_stage


if __name__ == '__main__':
    cfg = loadCfg(S.DATA_DIR)
    counter = ""
    if len(counter):
        pnlist = [[[['2015-12-27', '2016-03-06', '2016-05-29', '2016-09-11', '2016-10-30', '2016-12-18', '2017-01-29'], ['2015-12-27', '2016-03-06', '2016-05-15', '2016-06-26', '2016-08-14', '2016-10-23', '2017-01-01'], ['2015-12-27', '2016-02-07', '2016-03-27', '2016-05-15', '2016-08-14', '2016-10-30', '2017-01-08'], ['2015-12-06', '2016-01-24', '2016-03-13', '2016-05-08', '2016-07-17', '2016-08-28', '2016-10-23', '2016-12-04', '2017-01-22']], [['2015-11-22', '2016-01-10', '2016-04-17', '2016-06-26', '2016-08-28', '2016-10-16', '2016-12-11', '2017-01-22'], ['2016-01-03', '2016-03-20', '2016-05-22', '2016-07-10', '2016-09-04', '2016-11-20', '2017-01-22'], ['2015-11-29', '2016-01-24', '2016-03-20', '2016-06-26', '2016-08-28', '2016-10-16', '2016-12-04', '2017-01-22'], ['2016-01-03', '2016-02-21', '2016-04-03', '2016-05-29', '2016-07-10', '2016-10-02', '2016-11-20', '2017-01-01']], [[1.97, 2.16, 2.3840000000000003, 3.008, 2.922, 2.605, 2.4520000000000004], [8.666666666666666, 10.4, 8.0, 5.5, 11.0, 9.0, 7.25], [0.20666666666666667, 0.1025, -0.0275, 0.156, 0.186, 0.02, -0.037500000000000006], [1.008, 1.0379999999999998, -0.22799999999999998, 2.0775, 0.48, 0.738, 0.9339999999999999, 2.962, 2.302]], [[1.598, 1.8559999999999999, 1.964, 2.2675, 2.7340000000000004, 2.7640000000000002, 2.58, 2.396], [7.75, 6.8, 6.6, 3.6666666666666665, 5.5, 6.4, 5.0], [0.062, 0.017999999999999995, -0.052000000000000005, -0.035, 0.044, -0.06000000000000001, -0.096, -0.074], [-0.5825, -0.33399999999999996, -0.7939999999999999, -0.29, -0.8700000000000001, -0.636, -0.404, -0.865]]], [[['2015-12-27', '2016-03-06', '2016-05-29', '2016-09-18'], ['2016-03-06', '2016-05-15', '2016-08-07', '2016-10-30', '2017-01-08'], ['2015-12-27', '2016-05-15', '2016-08-21', '2016-11-13'], ['2016-02-07', '2016-05-01', '2016-09-04', '2016-12-11']], [['2015-11-29', '2016-04-17', '2016-06-26', '2016-10-16'], ['2016-01-10', '2016-04-03', '2016-07-10', '2016-10-16', '2017-01-22'], ['2016-01-24', '2016-04-17', '2016-06-26', '2016-09-04', '2016-12-11'], ['2016-01-10', '2016-04-03', '2016-07-10', '2016-10-02', '2017-01-08']], [[1.91875, 2.15, 2.3419999999999996, 2.9825000000000004], [10.0, 7.888888888888889, 10.4, 8.9, 7.0], [0.18, 0.12666666666666662, 0.14900000000000002, 0.016], [0.7325, 1.4360000000000002, 0.5855555555555555, 2.402]], [[1.6, 1.9989999999999999, 2.281111111111111, 2.7655555555555558], [8.0, 7.111111111111111, 3.8333333333333335, 7.0, 5.7], [0.036000000000000004, -0.03599999999999999, -0.023333333333333334, 0.06444444444444444, -0.096], [-0.12444444444444443, -0.7311111111111112, -0.5933333333333333, -0.583, -0.73625]]], [[['2016-05-31', '2016-09-30'], ['2016-01-31', '2016-08-31'], ['2015-12-31', '2016-05-31', '2016-11-30'], ['2016-01-31', '2016-05-31']], [['2016-03-31'], ['2015-12-31', '2016-06-30', '2017-01-31'], ['2016-03-31', '2016-12-31'], ['2016-03-31', '2016-09-30']], [[2.3199999999999994, 2.9225000000000008], [8.947368421052632, 8.909090909090908], [0.15857142857142859, 0.1219047619047619, -0.013636363636363636], [0.58, 0.6052380952380952]], [[2.0572727272727276], [8.19047619047619, 5.7368421052631575, 6.3], [-0.01090909090909091, -0.08000000000000002], [-0.5322727272727272, -0.4334999999999999]]]]
        lasttxn = ['2017-02-06', 2.42, 2.393333333333333, 8.0, -0.06333333333333334, 2.9266666666666663]
        expected = "PADINI,Dbg,0,(0c,3m,1p,3v)"
        mpvdir = S.DATA_DIR + S.MVP_DIR
        prefix = S.DATA_DIR + S.MVP_DIR + "simulation/"
        signals = scanSignals(mpvdir, True, counter, prefix + counter, pnlist, lasttxn)
    else:
        signals = ""
        signals = [signals + str(i * 1) for i in [1, True, False]]
        signals = "".join(signals)
    print "signal=", signals
