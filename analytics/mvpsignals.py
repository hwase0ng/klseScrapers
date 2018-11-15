'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S
from common import combineList, loadCfg


def scanSignals(dbg, counter, pnlist, lastTrxnData):
    global DBGMODE
    DBGMODE = dbg
    if dbg == 2:
        print pnlist
        print
        print lastTrxnData
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    # lastClosingPrice is not aggregated while the rest are from the weekly aggregation!
    if pnlist is None or not len(pnlist):
        print "Skipped:", counter
        return False
    if len(pnlist) < 3:
        print "Skipped len:", counter, len(pnlist)
        return False
    bbprice, rvsM, rvsP, rvsV, bottomrevs, oversold, divergent = \
        bottomBuySignals(pnlist, lastTrxnData)
    topSell = topSellSignals(bbprice, pnlist)
    if not oversold and not divergent and not bottomrevs and not topSell:
        # if (bbprice < 0 or rvsM < 0 or rvsP < 0):
        if not dbg:
            return ""

    signals = ""
    if topSell:
        signals = "\t%s,TOP,%d,(%dc,%dm,%dp,%dv)" % (counter, topSell,
                                                     bbprice, rvsM, rvsP, rvsV)
    elif oversold or divergent:
        signals = "\t%s,OVS,%d,%d,(%dc,%dm,%dp,%dv)" % (counter, oversold, divergent,
                                                        bbprice, rvsM, rvsP, rvsV)
    elif bottomrevs or dbg:
        label = "BRV" if bottomrevs else "Dbg"
        signals = "\t%s,%s,%d,(%dc,%dm,%dp,%dv)" % (counter, label, bottomrevs,
                                                    bbprice, rvsM, rvsP, rvsV)
    print signals
    outfile = S.DATA_DIR + S.MVP_DIR + "signals/" + counter + "-signals.csv"
    with open(outfile, "ab") as fh:
        bbsline = lastTrxnData[0] + signals
        fh.write(bbsline + '\n')
    if "simulation" in outfile:
        sss = S.DATA_DIR + S.MVP_DIR + "simulation/sss-" + lastTrxnData[0] + ".csv"
    else:
        sss = S.DATA_DIR + S.MVP_DIR + "signals/sss-" + lastTrxnData[0] + ".csv"
        with open(sss, "ab") as fh:
            fh.write(signals + '\n')
    return signals


def topSellSignals(pricepos, pnlist):
    topSellSignal = 0
    if pricepos < 4:
        return topSellSignal
    pnM = pnlist[2]
    xpM, xnM, ypM, ynM = pnM[0], pnM[1], pnM[2], pnM[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    ynmC, ypmC, ypmM, ypmV = ynM[0], ypM[0], ypM[1], ypM[3]  # 0=C, 1=M, 2=P, 3=V
    if ynmC is None or ypmC is None:
        if len(ypmM) > 1 and ypmM[-1] < ypmM[-2]:
            topSellSignal = 1
        return topSellSignal
    xnmC, xpmC, xpmM, xpmV = xnM[0], xpM[0], xpM[1], xpM[3]  # 0=C, 1=M, 2=P, 3=V
    minYN, maxYP = min(ynmC), max(ypmC)
    xpmCdate = xpmC[ypmC.index(maxYP)]
    xnmCdate = xnmC[ynmC.index(minYN)]
    if ypmM is not None and len(ypmM) > 1 and ypmM[-1] < ypmM[-2]:
        topSellSignal = 1
        if xpmCdate > xnmCdate:
            topSellSignal = 2
    return topSellSignal


def formListCMPV(cmpv, pnlist):
    xp, xn, yp, yn = pnlist[0], pnlist[1], pnlist[2], pnlist[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    # cmpv 0=C, 1=M, 2=P, 3=V
    cmpvlist = []
    cmpvlist.append(xp[cmpv])
    cmpvlist.append(xn[cmpv])
    cmpvlist.append(yp[cmpv])
    cmpvlist.append(yn[cmpv])
    return cmpvlist


def bottomBuySignals(pnlist, lastTrxn):
    oversold, divergent, bottomrevs = 0, 0, 0
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnC, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastC, lastM, lastP, lastV = \
        lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4], lastTrxn[5]

    pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
    cmpvWC = formListCMPV(0, pnW)
    cmpvMC = formListCMPV(0, pnM)
    cmpvMM = formListCMPV(1, pnM)
    cmpvMP = formListCMPV(2, pnM)
    cmpvMV = formListCMPV(3, pnM)
    posC, newlowC, newhighC, retrace, topC, bottomC, prevtopC, prevbottomC = \
        checkposition('C', cmpvMC + cmpvWC, lastC)
    if DBGMODE:
        print "lastPrice vs lastC:", lastprice, lastC
        print "C=", posC, newlowC, newhighC, retrace, topC, bottomC, prevtopC, prevbottomC
    if posC < 0:
        return posC, -1, -1, -1, bottomrevs, oversold, divergent
    posM, newlowM, newhighM, _, topM, bottomM, prevtopM, prevbottomM = \
        checkposition('M', cmpvMM, lastM)
    posP, newlowP, newhighP, _, topP, bottomP, prevtopP, prevbottomP = \
        checkposition('P', cmpvMP, lastP)
    posV, newlowV, newhighV, _, topV, bottomV, prevtopV, prevbottomV = \
        checkposition('V', cmpvMV, lastV)
    if DBGMODE:
        print "M=", posM, newlowM, newhighM, topM, bottomM, prevtopM, prevbottomM
        print "P=", posP, newlowP, newhighP, topP, bottomP, prevtopP, prevbottomP
        print "V=", posV, newlowV, newhighV, topV, bottomV, prevtopV, prevbottomV

    plistC, nlistC, nlistM, nlistP, plistV = \
        cmpvMC[2], cmpvMC[3], cmpvMM[3], cmpvMP[3], cmpvMV[2]  # 0=XP, 1=XN, 2=YP, 3=YN
    # 1 - PADINI 2014-03 (LowC + LowM), 2 - PADINI 2011-10 (LowC + LowP)
    # 3 - extension of 1 after retrace: PETRONM 2013-04-24
    # and plistC is not None and plistC[-1] < min(nlistC) + ((max(plistC) - min(nlistC)) / 3) \
    oversold = 0 if nlistM is None or nlistP is None or len(nlistM) < 2 or len(nlistP) < 2 \
        else 1 if (newlowC or bottomC) and (newlowM or bottomM) and min(nlistM) < 5 \
        and not (newlowP or bottomP) and not newlowV \
        else 2 if (newlowC or bottomC) and not (newlowM or bottomM) and min(nlistM) < 5 and nlistM[-1] > 5 \
        and (newlowP or bottomP) and not newlowV \
        else 3 if not (newlowC or bottomC) and not (newlowP or bottomP) and (newhighM or topM) \
        and min(nlistM) < 5 and nlistM[-1] > 5 and posC == 1 \
        else 0
    if oversold and ((newhighP or newhighM) or (bottomP and not bottomM and nlistM[-1] > 5)):
        oversold = 8
        if posC > 1:
            # Oversold confirmed
            oversold = 9
        divergent = 1 if newhighV else 0

    # bottomrevs 1 = reversal with P remains in negative zone (early signal of reversal)
    # bottomrevs 2 = reversal with P crossing to positive (confirmed reversal)
    # bottomrevs 3 = end of short term retrace from top with volume
    # bottomrevs 4 = end of long term retrace from top with new low M and P,
    #                also to check divergent on month's M and P
    elif not retrace:
        if nlistC is not None and plistC is not None and nlistM is not None:
            bottom_divider = min(nlistC) + (max(plistC) - min(nlistC)) / 3
            if DBGMODE:
                print "min,max of C=", min(nlistC), max(nlistC)
            if posC < 3 and plistC[-1] < bottom_divider and bottomC \
                    and len(nlistM) > 1 and min(nlistM) < 5 and nlistM[-1] > nlistM[-2] \
                    and not newlowP and lastM > 5:
                # Volume should near or exceeds new low
                # PADINI 2015-08-17, DUFU 2018-07
                bottomrevs = 1 if lastP < 0 else 2
            elif bottomC and newlowP and not newlowM:
                if nlistC is not None and lastC > nlistC[-1]:
                    # PADINI 2011-10-12
                    bottomrevs = 4
                # else failed example: PETRONM 2013-12-06
    else:
        # 3 - PADINI 2017-02-06
        maxPV = max(plistV)
        if DBGMODE:
            print "min(nlist)=", min(nlistM), min(nlistP), maxPV, lastV
        bottomrevs = 3 if retrace == 1 and \
            not newlowC and (newhighV and (lastV > maxPV * 2 or lastC > nlistC[-1])) and \
            (topM and min(nlistM) > 5 and lastM > nlistM[-1] or
             bottomP and lastP > nlistP[-1]) \
            else 0

    return posC, posM, posP, posV, bottomrevs, oversold, divergent


def checkposition(pntype, pnlist, lastpos):
    pos, retrace, newlow, newhigh, bottom, top, prevbottom, prevtop = \
        0, 0, False, False, False, False, False, False
    if pntype == 'C':
        nlist = pnlist[7]  # 0=XP, 1=XN, 2=YP, 3=YN
        count0 = -1 if nlist is None else nlist.count(0)
        if count0 < 0 or count0 > 1:
            print "\tSkipped W0", count0
            return -1, newlow, newhigh, retrace, top, bottom, prevtop, prevbottom

    plist, nlist = pnlist[2], pnlist[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    if plist is None or nlist is None:
        if plist is None:
            # free climbing (PADINI 2012-07-30)
            newhigh = True
            pos = 4
        if nlist is None:
            # free falling
            newlow = True
            pos = 0
    else:
        clist = combineList(pnlist)
        minP, maxP = min(plist), max(plist)
        minN, maxN = min(nlist), max(nlist)
        if lastpos > maxP:
            newhigh = True
            pos = 4
        elif clist[-1] == maxP:
            top = True
        elif plist[-1] == maxP:
            prevtop = True

        if lastpos < minN:
            newlow = True
            pos = 0
        elif clist[-1] == minN:
            bottom = True
        elif nlist[-1] == minN:
            prevbottom = True

        if pntype == 'C':
            if not bottom:
                range3 = (maxP - minN) / 3
                if lastpos <= minN + range3:
                    pos = 1
                elif lastpos <= maxP - range3:
                    pos = 3
                else:
                    pos = 2
        else:
            # 1 = climbing from new low
            # 2 = dropping from new high
            # 3 = in between
            pos = 1 if bottom else 2 if top else 3

        retrace = True if (top or prevtop) and pos > 1 else False

    return pos, newlow, newhigh, retrace, top, bottom, prevtop, prevbottom


if __name__ == '__main__':
    cfg = loadCfg(S.DATA_DIR)
    counter = "PADINI"
    pnlist = [[[['2015-12-27', '2016-03-06', '2016-05-29', '2016-09-11', '2016-10-30', '2016-12-18', '2017-01-29'], ['2015-12-27', '2016-03-06', '2016-05-15', '2016-06-26', '2016-08-14', '2016-10-23', '2017-01-01'], ['2015-12-27', '2016-02-07', '2016-03-27', '2016-05-15', '2016-08-14', '2016-10-30', '2017-01-08'], ['2015-12-06', '2016-01-24', '2016-03-13', '2016-05-08', '2016-07-17', '2016-08-28', '2016-10-23', '2016-12-04', '2017-01-22']], [['2015-11-22', '2016-01-10', '2016-04-17', '2016-06-26', '2016-08-28', '2016-10-16', '2016-12-11', '2017-01-22'], ['2016-01-03', '2016-03-20', '2016-05-22', '2016-07-10', '2016-09-04', '2016-11-20', '2017-01-22'], ['2015-11-29', '2016-01-24', '2016-03-20', '2016-06-26', '2016-08-28', '2016-10-16', '2016-12-04', '2017-01-22'], ['2016-01-03', '2016-02-21', '2016-04-03', '2016-05-29', '2016-07-10', '2016-10-02', '2016-11-20', '2017-01-01']], [[1.97, 2.16, 2.3840000000000003, 3.008, 2.922, 2.605, 2.4520000000000004], [8.666666666666666, 10.4, 8.0, 5.5, 11.0, 9.0, 7.25], [0.20666666666666667, 0.1025, -0.0275, 0.156, 0.186, 0.02, -0.037500000000000006], [1.008, 1.0379999999999998, -0.22799999999999998, 2.0775, 0.48, 0.738, 0.9339999999999999, 2.962, 2.302]], [[1.598, 1.8559999999999999, 1.964, 2.2675, 2.7340000000000004, 2.7640000000000002, 2.58, 2.396], [7.75, 6.8, 6.6, 3.6666666666666665, 5.5, 6.4, 5.0], [0.062, 0.017999999999999995, -0.052000000000000005, -0.035, 0.044, -0.06000000000000001, -0.096, -0.074], [-0.5825, -0.33399999999999996, -0.7939999999999999, -0.29, -0.8700000000000001, -0.636, -0.404, -0.865]]], [[['2015-12-27', '2016-03-06', '2016-05-29', '2016-09-18'], ['2016-03-06', '2016-05-15', '2016-08-07', '2016-10-30', '2017-01-08'], ['2015-12-27', '2016-05-15', '2016-08-21', '2016-11-13'], ['2016-02-07', '2016-05-01', '2016-09-04', '2016-12-11']], [['2015-11-29', '2016-04-17', '2016-06-26', '2016-10-16'], ['2016-01-10', '2016-04-03', '2016-07-10', '2016-10-16', '2017-01-22'], ['2016-01-24', '2016-04-17', '2016-06-26', '2016-09-04', '2016-12-11'], ['2016-01-10', '2016-04-03', '2016-07-10', '2016-10-02', '2017-01-08']], [[1.91875, 2.15, 2.3419999999999996, 2.9825000000000004], [10.0, 7.888888888888889, 10.4, 8.9, 7.0], [0.18, 0.12666666666666662, 0.14900000000000002, 0.016], [0.7325, 1.4360000000000002, 0.5855555555555555, 2.402]], [[1.6, 1.9989999999999999, 2.281111111111111, 2.7655555555555558], [8.0, 7.111111111111111, 3.8333333333333335, 7.0, 5.7], [0.036000000000000004, -0.03599999999999999, -0.023333333333333334, 0.06444444444444444, -0.096], [-0.12444444444444443, -0.7311111111111112, -0.5933333333333333, -0.583, -0.73625]]], [[['2016-05-31', '2016-09-30'], ['2016-01-31', '2016-08-31'], ['2015-12-31', '2016-05-31', '2016-11-30'], ['2016-01-31', '2016-05-31']], [['2016-03-31'], ['2015-12-31', '2016-06-30', '2017-01-31'], ['2016-03-31', '2016-12-31'], ['2016-03-31', '2016-09-30']], [[2.3199999999999994, 2.9225000000000008], [8.947368421052632, 8.909090909090908], [0.15857142857142859, 0.1219047619047619, -0.013636363636363636], [0.58, 0.6052380952380952]], [[2.0572727272727276], [8.19047619047619, 5.7368421052631575, 6.3], [-0.01090909090909091, -0.08000000000000002], [-0.5322727272727272, -0.4334999999999999]]]]
    lasttxn = ['2017-02-06', 2.42, 2.393333333333333, 8.0, -0.06333333333333334, 2.9266666666666663]
    expected = "PADINI,Dbg,0,(0c,3m,1p,3v)"
    signals = scanSignals(True, counter, pnlist, lasttxn)
    print signals
