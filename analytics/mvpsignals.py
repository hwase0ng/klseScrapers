'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S


def scanSignals(counter, fname, hllist, pnlist, lastTrxnData):
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
    if pnlist is None or not len(pnlist):
        print "Skipped:", counter
        return False
    if len(pnlist) < 3:
        print "Skipped len:", counter, len(pnlist)
        return False
    pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
    bbprice, rvsM, rvsP, rvsV = bottomBuySignals(pnW, pnF, lastTrxnData)
    if bbprice > 0 and rvsM >= 0 and rvsP >= 0:
        outfile = fname + "-signals.csv"
        signals = "\tBBS: %s,%d,%d,%d,%d" % (counter, bbprice, rvsM, rvsP, rvsV)
        print signals
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
        return True
    return False


def bottomBuySignals(pnW, pnF, lastTrxn):
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastvol = lastTrxn[1], lastTrxn[4]
    # 0=XP, 1=XN, 2=YP, 3=YN
    bbprice, retrace = checkBottomPrice(pnW[2], pnF[2], lastprice)
    if bbprice < 0:
        return bbprice, 0, 0, 0
    ypF, ynF = pnF[2], pnF[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    mynF, pynF, vypF = ynF[1], ynF[2], ypF[3]    # 0=C, 1=M, 2=P, 3=V
    if len(mynF) < 4 or len(pynF) < 4:
        return bbprice, 0, 0, 0
    rvsM = checkReversalM(retrace, mynF, 5)
    if rvsM < 0:
        return bbprice, 0, 0, 0
    rvsP = checkReversalP(retrace, pynF, -0.09)
    if rvsP < 0:
        return bbprice, 0, 0, 0
    rvsV = checkVol(retrace, vypF, lastvol)
    return bbprice, rvsM, rvsP, rvsV


def checkVol(retrace, plist, lastvol):
    if plist is None:
        return 0
    yplen = len(plist)
    yplist = sorted(plist)
    maxY = yplist[-1]
    if retrace and maxY == plist[-1]:
        return 4
    if lastvol > maxY:
        return 3
    if yplen < 2:
        return 0
    maxY2 = yplist[-2]
    if lastvol > maxY2:
        return 2
    if yplen < 3:
        return 0
    maxY3 = yplist[-3]
    if lastvol > maxY3:
        return 1
    return 0


def checkReversalM(retrace, ynlist, cond):
    if ynlist is None:
        return -1
    if ynlist.count(0) > 0:
        return -1
    minY = min(ynlist)
    if minY >= cond:
        # Have not dropped low enough
        # May be required for retrace scenario
        return -1
    if minY == ynlist[-1]:
        return 0
    if minY == ynlist[-2] or minY == ynlist[-3]:
        if ynlist[-1] > cond:
            # Stage 2 reversal: first/second higher low above 5
            return 2
        else:
            # Stage 1 reversal: first higher low, still need to wait for M to cross 5
            return 1
    if ynlist[-1] > cond:
        print "Off chart minY for investigation:", minY, ynlist.index(minY)
        return 2  # Stage 2 reversal
    return -1


def checkReversalP(retrace, ynlist, cond):
    if ynlist is None:
        return -1
    if ynlist.count(0) > 0:
        return -1
    minY = min(ynlist)
    if minY >= cond:
        # Have not dropped low enough
        # May be required for retrace scenario
        return -1
    if minY == ynlist[-1]:
        if not retrace:
            return 0
        return 4
    # if minY == ynlist[-2] or minY == ynlist[-3]:
    if ynlist[-1] < cond:
        # Stage 1 reversal: first higher low from the lowest M or P
        return 1
    else:
        if minY == ynlist[-2]:
            # Stage 2 reversal: first higher low which shot over the cond mark
            # - short term rebound play, unlikely to sustain
            return 2
    # Stage 3, P has crossed to positive zone
    return 3


def checkBottomPrice(ypW, ypF, lastprice):
    retrace = False
    if ypF is None:
        return -1, retrace
    ypFC = ypF[0]  # 0=C, 1=M, 2=P, 3=V
    if ypFC is None:
        # No peak/trough, price is still free falling?
        return -1, retrace
    minY = min(ypFC)
    if lastprice < minY:
        # Price is still going lower
        return 0, retrace
    minF, maxF = min(ypFC), max(ypFC)
    if lastprice > maxF:
        return 4, retrace  # Stage 4 above last top
    if maxF == ypFC[-1] or maxF == ypFC[-2]:
        retrace = True
    if lastprice > (maxF + minF) / 2:
        # Price above 1/2 from the high
        return 3, retrace  # Stage 3 reversal
    if lastprice > (maxF + minF) / 3:
        # Price above 1/3 from the high
        return 2, retrace  # Stage 2 reversal
    # Stage 1 reversal: Price is just above minY
    return 1, retrace
