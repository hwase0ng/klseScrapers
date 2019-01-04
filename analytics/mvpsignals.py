'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S
from common import loadCfg
from utils.dateutils import getBusDaysBtwnDates
from utils.fileutils import grepN


def scanSignals(mpvdir, dbg, counter, fname, pnlist, div, lastTrxnData, pid):
    def extractX():
        pnM = pnlist[2] if len(pnlist) > 1 else pnlist[0]
        xp, xn, = pnM[0], pnM[1]  # 0=XP, 1=XN, 2=YP, 3=YN
        return [xp, xn]

    def printsignal(trxndate):
        # prefix = "" if DBGMODE == 2 else '\t'
        # print prefix + signal
        postfix = "csv." + str(pid) if pid else "csv"
        if "simulation" in fname:
            outfile = mpvdir + "simulation/signals/" + counter + "-signals." + postfix
        else:
            outfile = mpvdir + "signals/" + counter + "-signals." + postfix
        linenum = grepN(outfile, trxndate)  # e.g. 2012-01-01
        if linenum > 0:
            # Already registered
            return
        with open(outfile, "ab") as fh:
            bbsline = trxndate + "," + signals
            fh.write(bbsline + '\n')
        if "simulation" in fname:
            sss = mpvdir + "simulation/" + label + "-" + trxndate + ".csv"
            # skip writing for simulation
        else:
            sss = mpvdir + "signals/" + label + "-" + trxndate + ".csv"
            with open(sss, "ab") as fh:
                fh.write(signals + '\n')

    global DBGMODE
    DBGMODE = dbg
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    # lastClosingPrice is not aggregated while the rest are from the weekly aggregation!
    if pnlist is None or not len(pnlist):
        print "Skipped:", counter
        return ""
    if len(pnlist) < 1:
        print "Skipped len:", counter, len(pnlist)
        return ""

    matchdate, cmpvlists, composelist, hstlist, strlist = \
        collectCompositions(pnlist, lastTrxnData)
    if cmpvlists is None:
        return ""
    composeC, composeM, composeP, composeV = \
        composelist[0], composelist[1], composelist[2], composelist[3]
    # posC, posM, posP, posV = composeC[0], composeM[0], composeP[0], composeV[0]
    bottomrevs, bbs, bbs_stage = 0, 0, 0
    sss, sstate, psig, pstate, nsig, nstate, patterns, neglist, poslist = \
        extractSignals(lastTrxnData, matchdate,
                       cmpvlists, composelist, hstlist, div,
                       extractX())
    '''
    bottomrevs, bbs, bbs_stage = \
        bottomBuySignals(lastTrxnData, matchdate, cmpvlists, composelist, div)
    '''
    if not (sss or bbs or bbs_stage):
        if not dbg:
            return ""

    strC, strM, strP, strV = strlist[0], strlist[1], strlist[2], strlist[3]
    # [tolerance, pdays, ndays, matchlevel] = matchdate
    p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    if patterns is not None:
        [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15] = patterns
    lastprice = lastTrxnData[1]
    signaldet = "(c%s.m%s.p%s.v%s),(%d.%d.%d.%d.%d^%d.%d.%d^%d.%d.%d^%d.%d.%d.%d),(%s^%s),%.2f" % \
        (strC[:1], strM[:1], strP[:1], strV[:1],
         p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15,
         neglist, poslist, lastprice)
    # tolerance, pdays, ndays, matchlevel)
    signalsss, label = "NUL,0.0,0.0.0.0", ""
    if sss or psig or nsig:
        label = "TBD" if sss > 900 else "TSS" if sss > 0 else "RTR" if sstate > 0 else "BRV" if sss < 0 else "NUL"
        signalsss = "%s,%d.%d,%d.%d.%d.%d" % (label, sss, sstate, nsig, nstate, psig, pstate)

    signals = "%s,%s,%s" % (counter, signalsss, signaldet)
    if dbg == 2:
        print '\n("%s", %s, %s, %s, "%s"),\n' % (counter, pnlist, div, lastTrxnData, signals.replace('\t', ''))
    printsignal(lastTrxnData[0])
    return signals


def extractSignals(lastTrxn, matchdate, cmpvlists, composelist, hstlist, div, xpn):

    def ispeak(cmpv):
        xpc, xnc = xpn[0][cmpv], xpn[1][cmpv]  # 0=C, 1=M, 2=P, 3=V
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

            c = 1 if newhighC else 2 if newlowC else 3 if topC else 4 if bottomC else 0
            m = 1 if newhighM else 2 if newlowM else 3 if topM else 4 if bottomM else 0
            p = 1 if newhighP else 2 if newlowP else 3 if topP else 4 if bottomP else 0
            v = 1 if newhighV else 2 if newlowV else 3 if topV else 4 if bottomV else 0

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
            if ncount < 4:
                ncount = 0
            elif ncount > 3:
                # GHLSYS 2017-01-06
                if alt:
                    # KLSE 2017-01-09
                    ncount = 1
            if ncount:
                pass
            elif (newhighC or topC) and (prevbottomC or firstC == minC):
                # PADINI 2012-09-28 beginning of tops reversal
                ncount = 2
                startc = plenC * -1
                for i in range(startc, -1):
                    if plistC[i] > lowbar:
                        ncount = 0
                        break
            elif (firstC == maxC or plistC[0] == maxC) and plistC[-1] < lowbar:
                # KAWAN 2013-05-14
                # DUFU 2014-05-12
                ncount = 4
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
            return ncount

        def bottomscount():
            tripleBottoms = 0
            if plistC[-1] < plistC[-2] and plistC[-2] < plistC[-3]:
                if nlistC[-1] > nlistC[-3] and nlistC[-2] > nlistC[-3]:
                    ''' --- lower peaks and higher valleys --- '''
                    # KESM 2013-09-09
                    # N2N 2014-01-30
                    tripleBottoms = 1
                elif nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3]:
                    ''' --- lower peaks and lower valleys --- '''
                    tripleBottoms = 2
                    # PADINI 2014-02-05 newlowC, 2015-10-02
                    # N2N 2017-08-28
                    # DUFU 2011-10-12, 2012-04-10
                    if nlenC > 3 and nlistC[-3] < nlistC[-4]:
                        ''' --- lower peaks and lower valleys extension --- '''
                        # DUFU 2018-06-13 retrace with valley follow by peak divergence
                        # DANCO 2018-07-23
                        # PETRONM 2014-04-25
                        tripleBottoms = 3
                elif nlenC > 3 and bottomC and \
                        nlistC[-2] < nlistC[-4] and nlistC[-3] < nlistC[-4]:
                    ''' --- lower peaks and lower valleys variant --- '''
                    # DUFU 2011-10-12, 2012-04-10
                    tripleBottoms = 4
                elif nlenC > 3 and \
                        nlistC[-1] < nlistC[-3] and nlistC[-1] < nlistC[-4] and \
                        nlistC[-2] < nlistC[-4] and nlistC[-3] < nlistC[-4]:
                    ''' --- lower peaks and lower valleys variant 2 --- '''
                    # N2N 2017-08-30
                    tripleBottoms = 5
            return tripleBottoms

        def topscount():
            def alternateTops():
                tops = 0
                for i in range(-1, -5, -1):
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
            if plistC[-1] > plistC[-2] and plistC[-2] > plistC[-3] and \
                    nlistC[-1] < nlistC[-2] and nlistC[-2] < nlistC[-3] and \
                    nlistC[-1] > maxC - range4 and posC > 2:
                # KLSE 2013-03-06
                tripleTops = 1

            if not tripleTops and plistC[-1] > plistC[-2] and plistC[-2] > plistC[-3] and \
                    nlistC[-1] > nlistC[-2] and nlistC[-2] > nlistC[-3] and \
                    lastC > nlistC[-1] and nlistC[-1] > plistC[-2] and nlistC[-2] > plistC[-3] and \
                    (firstC < (maxC + minC) / 2 or
                     (nlistC[0] == minC and plistC[0] < minC + (2 * range4))) and \
                    plistC[-1] > maxC - range4 and \
                    nlistC[0] < minC + range4:
                # DUFU 2016-12-23
                # KESM 2016-06-15 only works with chartdays > 500
                tripleTops = 2

            if not tripleTops and plenC > 5:
                if alternateTops() > 3 and \
                        (nlistC[-1] > nlistC[-2] or nlistC[-1] > nlistC[-3]):
                    # VSTECS 2014-01-29
                    tripleTops = 3

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
                cdate = pdateC if cpeak else ndateC
                mpdate = pdateMP if mpeak else ndateMP
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
            def highlowM():
                if len(plistM) < 4 or len(plistP) < 4:
                    return False
                if plistM[-2] > plistM[-1] and plistM[-2] > plistM[-3] and \
                    (plistP[-1] > plistP[-2] and (plistP[-2] < plistP[-3] or
                                                  plistP[-2] < plistP[-4])):
                    # 2011-05-12 ORNA
                    return True
                return False

            def highlowP():
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
                if len(nlistM) < 3 or len(nlistP) < 3:
                    return False
                if nlistM[-2] < nlistM[-1] and nlistM[-2] < nlistM[-3] and \
                    nlistP[-2] > nlistP[-1] and (nlistP[-2] > nlistP[-3] or
                                                 nlistP[-2] > nlistP[-4]):
                    return True
                return False

            def lowHighP():
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

    def evalsignals():
        def nCompilation():
            nsignals = []
            sig = "1" if newlowC or (bottomC and cpeak and plistC[-1] < lowbar) else "0"
            nsignals.append(sig)
            sig = "1" if cmpdiv in peakbear else "0"
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
            sig = "1" if newhighC or (topC and cvalley and nlistC[-1] > highbar) else "0"
            psignals.append(sig)
            sig = "1" if cmpdiv in valleybull else "0"
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
                # DUFU 2013-04-05 bearish
                # VSTECTS 2013-03-04 bullish
                # SCGM 2012-01-20 bottomC bullish nlistM[-1] > plistM[-2]
                nsig = -2 if plistM[-1] < 10 and nlistP[-1] < 0 else 2
                nstate = -1 if posC < 2 else 1
            elif int(nsignals[hlM]):
                nsig = 3
                nstate = 1 if topP or newhighC or topC else 0
            elif mvalley or pvalley:
                nval = 4
                nsig = nval
                if plistM[-1] > 10:
                    if lastM < 7:
                        if lastC > plistC[-1] and lastC > plistC[-2]:
                            # KAWAN 2015-05-13
                            # DANCO 2018-10-31
                            nsig, nstate = -nval, 0
                        else:
                            nsig, nstate = nval, 0
                elif plenM > 1 and nlenM > 1 and plistM[-2] > 10:
                    if nlistM[-1] > 5 and nlistM[-1] < 7:
                        if nlistM[-2] > 5 and nlistM[-2] < 7:
                            # MUDA 2013-07-30
                            nsig, nstate = nval, 1
                        else:
                            nsig, nstate = -nval, 2
                elif nlenP > 1 and nlistP[-1] > nlistP[-2]:
                    nstate = 0
                elif nlenM > 1 and nlistM[-1] > nlistM[-2]:
                    nstate = 0
            elif not mpnow and cpeak and "1" not in psignals:
                nsig, nstate = 1, 1

            if nsig > 0 and nstate > 0 and not (mpeak or ppeak):
                if nlenP > 1 and nlistP[-1] > nlistP[-2]:
                    nstate = 0
                elif nlenM > 1 and nlistM[-1] > nlistM[-2]:
                    nstate = 0
            elif nsig < 0 and nstate and (cpeak or mpeak or ppeak):
                nstate = 0

            return nsig, nstate

        def pEvaluation():
            if "1" not in psignals:
                return 0, 0
            psig, pstate = 0, 0

            if int(psignals[lowhighC]):
                if cvalley and int(psignals[divC]):
                    if nlistP[-1] < 0:
                        # 2013-12-19 ORNA
                        psig, pstate = -2, 1
                    elif highlowM:
                        # 2011-05-12 ORNA
                        psig = 2 if newhighP or topP else -2
                        pstate = 2
                    else:
                        # 2014-02-20 ORNA
                        psig = 2 if newhighP or topP else -2
                        pstate = 3
                elif nlistP[-1] < 0 or cpeak:
                    psig, pstate = 2, 0
                else:
                    # 2013-03-12 MUDA
                    psig, pstate = -2, 4
            elif psignals[pcnt] == "1":
                if countP < 3:
                    if plistM[-1] < 10 and plistM[-2] < 10:
                        psig, pstate = 3, 1
                    else:
                        psig, pstate = -3, 1
                else:
                    psig, pstate = -3, 2
            elif mvalley and plistM[-1] > 10:
                if nlistM[-1] > 5:
                    if nlistM[-1] < 7:
                        psig, pstate = -4, 0
                    else:
                        psig, pstate = 4, 1
            elif psignals[n3uP] == "1":
                if pvalley and lastP < plistP[-1]:
                    psig, pstate = -5, 0
                elif lastP > plistP[-1] and lastC < plistC[-1]:
                    psig, pstate = 5, 1
                else:
                    psig, pstate = -5, 2
            elif psignals[divC] == "1" and nsignals[divMP] == "1":
                psig, pstate = 6, 0
            elif mvalley and psignals[divMP] == "1":
                if cpeak and nsignals[divC] == "1":
                    # MUDA 2012-05-15
                    psig, pstate = 7, 1
                else:
                    psig, pstate = -7, 0
            elif topC and prevbottomC:
                psig, pstate = 8, 0
            elif int(psignals[lhP]):
                psig = -9 if nlistP[-1] >= 0 else 9
                # ORNA 2018-10-30 short rebound due to nlistP[-1] < 0
                pstate = -1
            elif int(psignals[lhM]):
                psig = 10 if nlistP[-1] > 0 else -10
                pstate = 1
            elif mpnow and cvalley and "1" not in nsignals:
                psig, pstate = -1, -1
            '''
            elif int(psignals[higherM]):
                # 2012-01-20 SCGM
                # 2018-08-02 MAGNI
                psig = -9
                pstate = -1 if posC < 2 else 1
            '''

            if psig == 1 or psig == -2 and pstate == 1:
                pass
            elif psig > 0 and pstate > 0 and not (mpeak or ppeak):
                if nlenP > 1 and nlistP[-1] > nlistP[-2]:
                    pstate = 0
                elif nlenM > 1 and nlistM[-1] > nlistM[-2]:
                    pstate = 0
            elif psig < 0 and pstate and (cpeak or mpeak or ppeak):
                pstate = 0

            return psig, pstate

        lowhighC, divC, divMP, n3uM, n3uP, pcnt = 0, 1, 2, 3, 4, 5
        hlP, hlM, lhP, lhM = 6, 7, 6, 7
        nsignals = nCompilation()
        psignals = pCompilation()
        nsig, nstate = nEvaluation()
        psig, pstate = pEvaluation()

        if not psig and "1" in psignals and "1" not in nsignals:
            psig = 99 if cpeak else -99
            if int(psignals[divC]):
                # 2013-03-13 ORNA lowerV and bottomV
                pstate = -2
            else:
                pstate = 0 if mpeak or ppeak else -1 if posC < 2 else 1
        elif not nsig and "1" in nsignals and "1" not in psignals:
            nsig = 99 if cpeak else -99
            if int(nsignals[divC]):
                nstate = 2
            else:
                nstate = 0 if cpeak or mpeak or ppeak else 1

        return psig, pstate, nsig, nstate, nsignals, psignals

    # ------------------------- START ------------------------- #

    def eval3Bottoms(sval):
        sig, state = 0, 0
        if posC > 1:
            # Works mostly in retrace position
            sig = -sval
        elif (newlowM and newlowP) or (bottomM or bottomP):
            # 2014-02-05 PADINI newlowC
            # 2012-01-20 YSPSAH bottomP
            sig = -sval
        elif newhighM or newhighP or topM or topP:
            # 2015-10-02 PADINI
            sig = -sval
        elif newhighV:
            # 2017-08-28 N2N
            sig = -sval
        else:
            # 2011-10-12 DUFU
            sig = sval

        if tripleBottoms == 1:
            state = 1
        elif posC > 1:
            if cpeak and "MP" in ndiv:
                # 2018-06-13 DUFU retrace with valley follow by peak divergence
                state = -2
            elif not newlowC:
                # 2018-07-23 DANCO
                state = -3
            else:
                # 2014-04-25 PETRONM
                state = 4
        return sig, state

    def eval3Tops(sval):
        sig, state = 0, 0
        if tripleM in p3d and tripleP in p3d and tripleV in p3d and \
                nlenV > 1 and nlistV[-1] > nlistV[-2] and \
                plistM[-1] > 5 and plistP[-1] > 0:
            # 2013-03-20 KLSE
            sig, state = -sval, 1
        elif posV > 3:
            sig, state = sval, 2
            if newhighV:
                # 2018-05-07 KLSE
                sig, state = sval, 3
        elif ((bottomM and newhighM) or
              (topM and prevbottomM)) and not newhighP:
            # 2014-08-05, 2014-08-12 MUDA
            sig, state = sval, 4
        else:
            sig, state = sval, 5
        return sig, state

    def evalM10x3(sval):
        sig, state = 0, 0
        # 3 consecutive M above 10 - powerful break out / bottom reversal signal
        sig = -sval
        if nlistM[-1] < 0:
            # 2017-10-17 AXREIT
            sig, state = sval, 1
        elif plistP[-1] > 0 and plistP[-2] > 0 and plistP[-3] > 0:
            # 2013-03-01 MAGNI top retrace with CM and CP valley divergence follow by break out
            state = 2
        # elif posC < 2:
            # --- bottom reversal --- #
            # 2014-05-05, DUFU 2014-06-04 (plistP[-1] < 0) bottom break out
            # 2014-09-10 DUFU (5 plistM vs 4 plistP)
        else:
            if topC or topM:
                if mpeak:
                    # 2014-09-03 DUFU retracing
                    state = 0
                else:
                    # 2014-11-21 DUFU retrace completed
                    # 2017-08-02 UCREST topM valley divergence
                    state = 3
            elif not newlowC:
                # 2013-04-29 YSPSAH
                state = 4
            elif mpeak or lastM < 0:
                # 2018-12-21 ABLEGRP
                sig = sval
                state = 5
            else:
                state = 0
            # sstate = 2 if "CM" in ndiv or "CP" in ndiv else 1
        return sig, state

    def evalNarrowC(sval):
        def common_narrows():
            def evalP(sval2):
                sigP, stateP = 0, 0
                if narrowP == 9:
                    if nlistP[-2] < 0 and nlistP[-2] >= 0:
                        # 2012-08-02 ORNA with topV
                        sigP = -sval2
                        stateP = -1 if posC < 2 else 1
                    else:
                        sigP, stateP = 900 + sval2, 1
                elif tripleP in n3u and cmpdiv in valleybull:
                    if nlistM[-1] > nlistM[-2]:
                        # 2018-07-11 DANCO
                        sigP, stateP = -sval2, 2
                    else:
                        # 2012-01-16 DUFU
                        sigP, stateP = sval2, 3
                elif bottomP:
                    # 2013-05-29 PADINI oversold (could not reach here due to cmpdiv == 1
                    sigP, stateP = -sval2, 0
                elif tripleP in p3u and nlistP[-1] > 0 and plistM[-1] >= 10 and nlistM[-1] < 5:
                    if plistM[-1] >= 10:
                        # 2013-06-05 SCGM
                        sigP, stateP = -sval2, 4
                    else:
                        sigP, stateP = 900 + sval2, 2
                return sigP, stateP

            def evalM(sval3):
                sigM, stateM = 0, 0
                if topM and nlistP[-1] > 0:
                    # 2011-11-08 N2N
                    # 2014-02-20 PETRONM
                    sigM, stateM = -sval3, 1
                elif newhighM and tripleM in p3d:
                    # 2012-04-02 DUFU with narrowM
                    sigM, stateM = sval3, 0
                elif bottomM:
                    # PADINI 2014-03-05 short rebound
                    sigM, stateM = -sval3, 0
                elif nlistM[-1] > 10 and nlistP[-1] > 0:
                    # 2013-05-29 PADINI 20% short push before top reversal
                    sigM, stateM = sval3, -2
                elif tripleM in p3u and nlistP[-1] >= 0:
                    if newhighM and posC < 2:
                        # 2013-03-21 PETRONM
                        sigM, stateM = -sval3, 3
                    elif posC > 2:
                        # 2017-02-08 SCGM
                        sigM, stateM = -sval3, 4
                    else:
                        sigM, stateM = -sval3, 5
                        if topV and plistP[-1] < plistP[-2]:
                            # 2012-08-02 ORNA
                            sigM, stateM = -sval3, 6
                elif tripleM in [2, 4, 5, 6, 7] and nlistM[-1] >= 5:
                    if nlistP[-1] > 0:
                        # 2016-12-27 GHLSYS
                        sigM, stateM = -sval3, 7
                    elif lastM > plistM[-1]:
                        # 2016-08-25 MAGNI Strong reversal after short retrace (p=-0.057)
                        # 2013-07-04 ORNA
                        sigM, stateM = -sval3, 8
                    else:
                        # 2018-03-06 GHLSYS
                        sigM, stateM = sval3, 9
                elif narrowM:
                    sigM = -sval3
                    if nlistP[-1] >= 0:
                        # 2013-03-25 KLSE
                        stateM = 10
                        if nlistM[-1] > 5:
                            # 2013-09-06 KESM
                            # 2017-02-03 GHLSYS
                            stateM = 11
                    elif nlistM[-1] > 5:
                        # 2014-03-10 VSTECS
                        # 2017-02-21 YSPSAH
                        # 2018-07-20 DANCO
                        stateM = 12
                    else:
                        sigM, stateM = 900 + sval3, 1
                    if posC < 2 and stateM:
                        stateM = -stateM
                return sigM, stateM

            sig, state = 0, 0
            if newhighC and cmpdiv in valleybull:
                # 2017-01-26 MAGNI
                sig, state = -sval, 1
            else:
                sig, state = evalP(2)
                if not sig or sig > 900:
                    sig, state = evalM(3)
                    if not sig or sig > 900:
                        sig = sval
                        if (newhighM or topM) and posC < 2:
                            # 2018-11-11 SUPERLN
                            state = 2
                        if (newhighP or topP) and posC < 2:
                            sig, state = 903, 1
                        else:
                            # 2018-08-02 MAGNI
                            state = 3
            return sig, state

        ssig, sstate = 0, 0
        if narrowC > 3 and (bottomP or
                            (cmpdiv in [4, 5] and
                             ((nlistP[-1] > nlistP[-2] or nlistP[-1] > nlistP[-3]) or
                              (nlistM[-1] > nlistM[-2] or nlistM[-1] > nlistM[-3])) or
                             (tripleM in p3u or tripleP in p3u))):
            ssig, sstate = common_narrows()
        elif narrowC > 0:
            if nlistM[-1] > 5 and nlistP[-1] > 0:
                if nlenM > 2 and (nlistM[-2] < 5 or nlistM[-3] < 5) and \
                        nlenP > 2 and (nlistP[-2] < 0 or nlistP[-3] < 0):
                    # 2017-01-09 KLSE
                    ssig, sstate = -sval, 4
                else:
                    # 2013-02-18 DUFU
                    ssig, sstate = sval, 5
            else:
                ssig, sstate = common_narrows()

        return ssig, sstate

    def evalNarrowM(sval):
        sig, state = 0, 0
        if posC == 2 and narrowM:
            sig, state = -sval, 1
            if newlowP or newhighV:
                state = 2
            elif bottomP or newlowV:
                state = 3
        elif not topC and posC == 3 and narrowM:
            sig = sval
            if tripleM in p3d or tripleP in n3u:
                # 2015-04-30 KLSE
                state = 1
        return sig, state

    def evalHighC(sval):
        sig, state = sval, 0
        if countP == 3:
            # 2014-02-04 MUDA
            sig, state = -sval, 1
        elif tripleP in p3d:
            # 2014-05-05 KLSE
            state = 1
            if newhighV or topV or cmpdiv in peakbear:
                # 2014-06-02 KLSE
                # 2011-12-01 ORNA
                state = 2
        elif tripleP in p3u:
            if topV and newlowV:
                # 2018-11-05 YSPSAH
                state = 3
            elif nlistP[-1] < 0:
                # 2013-12-19 ORNA
                sig, state = -sval, -1
        else:
            if newhighM or newhighP or topM or topP:
                # 2013-07-29 KLSE
                # 2014-08-29 VSTECS
                state = 4
            elif cmpdiv in peakbear:
                # 2011-11-17 ORNA
                state = 2
            if plistP[-1] > 0 and lastP < 0:
                # KLSE 2013-09-02
                state = -3
        return sig, state

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
        lastTrxn[6], lastTrxn[7], lastTrxn[8], lastTrxn[9]
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
    peakbear, valleybull = [1, 2, 3], [4, 5, 6]
    cpeak, pdateC, ndateC = ispeak(0)
    mpeak, pdateM, ndateM = ispeak(1)
    ppeak, pdateP, ndateP = ispeak(2)
    vpeak, pdateV, ndateV = ispeak(3)
    cvalley = not cpeak
    mvalley = not mpeak
    pvalley = not ppeak
    vvalley = not vpeak
    cmpInSync = False
    if (cpeak and mpeak and ppeak and
        pdateC == pdateM and pdateM == pdateP) or (cvalley and mvalley and pvalley and
                                                   ndateC == ndateM and ndateM == ndateP):
        cmpInSync = True
    if plistM is None or plistP is None or nlistM is None or nlistP is None:
        nosignal = True
    else:
        nosignal = False
        cmpdiv, mpdiv, mpnow, highlowM, highlowP, lowhighM, lowhighP = divergenceDiscovery()
        p0, p2, cmpvlen = shapesDiscovery()
        p1 = [cmpdiv] + p0 + [cmpInSync]
        [c, m, p, v, tripleM, tripleP, tripleV,
         narrowC, narrowM, narrowP, countP, tripleBottoms, tripleTops] = p0
        [firstmp, firstmn, firstpp, firstpn] = p2
        [plenM, nlenM, plenP, nlenP, plenV, nlenV, plenC, nlenC] = cmpvlen

    if nosignal:   # or DBGMODE == 3:
        pass
    else:
        psig, pstate, nsig, nstate, neglist, poslist = evalsignals()
        negstr = "".join(neglist)
        posstr = "".join(poslist)
        if newlowC:
            ssig, sstate = 9, 9
        elif narrowC:
            ssig, sstate = evalNarrowC(1)
        if not ssig or sstate > 900:
            if plistP is not None and plenP > 3 and tripleM == 9:
                ssig, sstate = evalM10x3(4)
        if not ssig or sstate > 900:
            if tripleTops:
                ssig, sstate = eval3Tops(5)
        if not ssig or sstate > 900:
            if tripleBottoms:
                ssig, sstate = eval3Bottoms(6)
        if not ssig or sstate > 900:
            if narrowM:
                ssig, sstate = evalNarrowM(7)
        if not ssig or sstate > 900:
            if newhighC or topC:
                ssig, sstate = evalHighC(8)

    return ssig, sstate, psig, pstate, nsig, nstate, p1, negstr, posstr


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


def checkposition(pntype, pnlist, firstpos, lastpos):
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


def collectCompositions(pnlist, lastTrxn):
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastC, lastM, lastP, lastV, firstC, firstM, firstP, firstV = \
        lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4], lastTrxn[5], \
        lastTrxn[6], lastTrxn[7], lastTrxn[8], lastTrxn[9]
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
