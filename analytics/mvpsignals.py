'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S


def scanSignals(dbg, counter, fname, hllist, pnlist, lastTrxnData):
    global DBGMODE
    DBGMODE = dbg
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
    # lastClosingPrice is not aggregated while the rest are from the weekly aggregation!
    if pnlist is None or not len(pnlist):
        print "Skipped:", counter
        return False
    if len(pnlist) < 3:
        print "Skipped len:", counter, len(pnlist)
        return False
    bbprice, rvsM, rvsP, rvsV, bottomrevs, oversold, divergent = \
        bottomBuySignals(pnlist, lastTrxnData)
    if not oversold and not divergent and not bottomrevs:
        # if (bbprice < 0 or rvsM < 0 or rvsP < 0):
        if not dbg:
            return ""

    signals = ""
    if oversold or divergent:
        signals = "\tOVS: %s,(%d,%d)" % (counter, oversold, divergent)
    elif bottomrevs or dbg:
        label = "Dbg" if dbg else "BRV"
        signals = "\t%s: %s,(%d,%d,%d,%d,%d)" % (label, counter, bottomrevs,
                                                 bbprice, rvsM, rvsP, rvsV)
    print signals
    outfile = fname + "-signals.csv"
    with open(outfile, "ab") as fh:
        bbsline = lastTrxnData[0] + signals
        fh.write(bbsline + '\n')
    if "simulation" in outfile:
        sss = S.DATA_DIR + S.MVP_DIR + "simulation/sss-" + lastTrxnData[0] + ".csv"
    else:
        sss = S.DATA_DIR + S.MVP_DIR + "sss-" + lastTrxnData[0] + ".csv"
    with open(sss, "ab") as fh:
        bbsline = counter + signals
        fh.write(bbsline + '\n')
    return signals


def bottomBuySignals(pnlist, lastTrxn):
    pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastM, lastP, lastvol = lastTrxn[1], lastTrxn[2], lastTrxn[3], lastTrxn[4]
    oversold, divergent, bottomrevs = 0, 0, 0
    # 0=XP, 1=XN, 2=YPositive, 3=YNegative
    bbprice, retrace, newlowC = checkBottomPrice(pnW[3], pnF[2], lastprice)
    if bbprice < 0:
        return bbprice, 0, 0, 0, bottomrevs, oversold, divergent
    ypF, ynF, ynM = pnF[2], pnF[3], pnM[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    pypF, vypF = ypF[2], ypF[3]  # 0=C, 1=M, 2=P, 3=V
    mynF, pynF, vynF, mynM = ynF[1], ynF[2], ynF[3], ynM[1]   # 0=C, 1=M, 2=P, 3=V
    if len(mynF) < 4 or len(pynF) < 4:
        return bbprice, 0, 0, 0, bottomrevs, oversold, divergent
    rvsM, newlowM = checkReversalM(retrace, mynF, 5, lastM)
    rvsP, newlowP, newhighP = checkReversalP(retrace, pypF, pynF, -0.09, lastP)
    rvsV, newlowV, newhighV = checkVol(retrace, vypF, vynF, lastvol)

    oversold = 1 if newlowC and newlowM and not newlowP and not newlowV else \
        2 if newlowC and not newlowM and newlowP and not newlowV else 0
    if oversold and newhighP:
        divergent = 2 if newhighV else 1

    # bottomrevs 1 = reversal with month M below 5 (early reversal with higher risk)
    # bottomrevs 2 = reversal with month M above 5
    # bottomrevs 3 = end of short term retrace from top with volume
    # bottomrevs 4 = end of long term retrace from top with new low M and P,
    #                also to check divergent on month's M and P
    if not retrace and bbprice < 3 and \
            newlowC and not newlowM and not newlowP \
            and lastM > 5 and lastP > 0:
        if mynM is None:
            bottomrevs = 0
        else:
            minMM = min(mynM) if len(mynM) > 1 else -1
            if minMM < 0:
                bottomrevs = 0
            else:
                bottomrevs = 2 if minMM < 5 and mynM[-1] >= 5 else 1
    else:
        bottomrevs = 3 if retrace == 1 and not newlowC and (newlowM or newlowP) and newhighV \
            else 4 if retrace > 1 and not newlowC and newlowM and newlowP else 0

    return bbprice, rvsM, rvsP, rvsV, bottomrevs, oversold, divergent


def checkVol(retrace, plist, nlist, lastvol):
    newlow, newhigh = False, False
    if plist is None:
        return 0, newlow, newhigh
    yplen = len(plist)
    yplist = sorted(plist)
    maxYP = yplist[-1]
    if nlist is not None and len(nlist) > 0:
        minYN = min(nlist)
        if lastvol < minYN:
            newlow = True
    if lastvol > maxYP:
        newhigh = True
    if retrace and maxYP == plist[-1]:
        return 4, newlow, newhigh
    if lastvol > maxYP:
        return 3, newlow, newhigh
    if yplen < 2:
        return 0, newlow, newhigh
    maxY2 = yplist[-2]
    if lastvol > maxY2:
        return 2, newlow, newhigh
    if yplen < 3:
        return 0, newlow, newhigh
    maxY3 = yplist[-3]
    if lastvol > maxY3:
        return 1, newlow, newhigh
    return 0, newlow, newhigh


def checkReversalM(retrace, ynlist, cond, lastM):
    newlow = False
    if ynlist is None:
        return -1, newlow
    if ynlist.count(0) > 0:
        return -1, newlow
    minY = min(ynlist)
    if lastM < minY or minY == ynlist[-1]:
        newlow = True
    if minY >= cond:
        # Have not dropped low enough
        # May be required for retrace scenario
        return -1, newlow
    if minY == ynlist[-1]:
        if not retrace:
            return 0, newlow
        # Stage 3 reversal new low
        return 3, newlow
    if minY == ynlist[-2] or minY == ynlist[-3]:
        if ynlist[-1] > cond:
            # Stage 2 reversal: first/second higher low above 5
            return 2, newlow
        else:
            # Stage 1 reversal: first higher low, still need to wait for M to cross 5
            return 1, newlow
    if ynlist[-1] > cond:
        if DBGMODE:
            print "Off chart minY for investigation:", minY, ynlist.index(minY)
        return 2, newlow  # Stage 2 reversal
    return -1, newlow


def checkReversalP(retrace, yplist, ynlist, cond, lastP):
    newlow, newhigh = False, False
    if yplist is None or ynlist is None:
        return -1, newlow, newhigh
    if yplist.count(0) > 0 or ynlist.count(0) > 0:
        return -1, newlow, newhigh
    minYN, maxYP = min(ynlist), max(yplist)
    if lastP > maxYP:
        newhigh = True
    if minYN == ynlist[-1]:
        newlow = True
    if minYN >= cond:
        # Have not dropped low enough
        # May be required for retrace scenario
        return -1, newlow, newhigh
    if minYN == ynlist[-1]:
        if not retrace:
            return 0, newlow, newhigh
        # stage 4 reversal hits new low
        return 4, newlow, newhigh
    # if minYN == ynlist[-2] or minYN == ynlist[-3]:
    if ynlist[-1] < cond:
        # Stage 1 reversal: first/second higher low from the lowest P
        return 1, newlow, newhigh
    else:
        if minYN == ynlist[-2]:
            # Stage 2 reversal: first higher low which shot over the cond mark
            # - short term rebound play, unlikely to sustain
            return 2, newlow, newhigh
    # Stage 3, P has crossed to positive zone
    return 3, newlow, newhigh


def checkBottomPrice(ynW, ypF, lastprice):
    retrace, newlow = 0, False
    if ypF is None:
        return -1, retrace, newlow
    ynWC, ypFC = ynW[0], ypF[0]  # 0=C, 1=M, 2=P, 3=V
    if ynWC is None or ypFC is None:
        # No peak/trough, price is still free falling?
        return -1, retrace, newlow
    if ynWC.count(0) > 1:
        # Transaction gaps
        return -1, retrace, newlow
    minY = min(ynWC)
    if lastprice < minY or minY == ynWC[-1]:
        newlow = True
    if lastprice < minY:
        # Price is still going lower
        return 0, retrace, newlow
    minF, maxF = min(ypFC), max(ypFC)
    if maxF == ypFC[-1] or maxF == ypFC[-2]:
        # short and early stage retrace (padini 2017-02-06)
        retrace = 1
    elif maxF > ypFC[0]:
        # Long and substantial retrace (padini 2011-10-12)
        retrace = 2
    if lastprice > maxF or (maxF == ypFC[-1] and
                            lastprice > (maxF - minF) * 2 / 3):
        return 4, retrace, newlow  # Stage 4 above last top
    if lastprice > (maxF + minF) / 2:
        # Price above 1/2 from the high
        return 3, retrace, newlow  # Stage 3 reversal
    if lastprice > (maxF + minF) / 3:
        # Price above 1/3 from the high
        return 2, retrace, newlow  # Stage 2 reversal
    # Stage 1 reversal: Price is just above minY
    return 1, retrace, newlow
