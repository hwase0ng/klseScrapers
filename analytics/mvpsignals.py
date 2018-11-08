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
    if bbprice < 0 or bbprice > 1:
        return False
    if rvsM > 0 and rvsP > 0:
        outfile = fname + "-signals.csv"
        signals = "\tBBS: %s,%d,%d,%d,%d" % (counter, bbprice, rvsM, rvsP, rvsV)
        print signals
        with open(outfile, "ab") as fh:
            bbsline = lastTrxnData[0] + signals
            fh.write(bbsline + '\n')
        with open(S.DATA_DIR + S.MVP_DIR + "sss-" + lastTrxnData[0] + ".cvs", "ab") as fh:
            bbsline = counter + signals
            fh.write(bbsline + '\n')
        return True
    return False


def bottomBuySignals(pnW, pnF, lastTrxn):
    # lastTrxnData = [lastTrxnDate, lastClosingPrice, lastTrxnM, lastTrxnP, lastTrxnV]
    lastprice, lastvol = lastTrxn[1], lastTrxn[4]
    # 0=XP, 1=XN, 2=YP, 3=YN
    bbprice = checkBottomPrice(pnW[3], lastprice)
    if bbprice < 0 or bbprice > 1:
        return bbprice, 0, 0, 0
    ypF, ynF = pnF[2], pnF[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    mynF, pynF, vypF = ynF[1], ynF[2], ypF[3]    # 0=C, 1=M, 2=P, 3=V
    if len(mynF) < 4 or len(pynF) < 4:
        return bbprice, 0, 0, 0
    rvsM = checkReversal(mynF, 5)
    if rvsM < 0:
        return bbprice, 0, 0, 0
    rvsP = checkReversal(pynF, -0.09)
    if rvsP < 0:
        return bbprice, 0, 0, 0
    rvsV = checkVol(vypF, lastvol)
    return bbprice, rvsM, rvsP, rvsV


def checkVol(yplist, lastvol):
    if yplist is None:
        return 0
    yplist.sort()
    maxY = yplist[-1]
    maxY2 = yplist[-2]
    maxY3 = yplist[-3]
    if lastvol > maxY:
        return 3
    if lastvol > maxY2:
        return 2
    if lastvol > maxY3:
        return 1
    return 0


def checkReversal(ynlist, cond):
    if ynlist is None:
        return 0
    if ynlist.count(0) > 0:
        return -1
    minY = min(ynlist)
    if minY >= cond:
        return -1
    if minY == ynlist[-1]:
        return -1
    if minY == ynlist[-2]:
        return 1
    if ynlist[-1] > cond:
        return 2
    return -1


def checkBottomPrice(pnlist, lastprice):
    if pnlist is None:
        return -1
    ynC, ynM, ynP = pnlist[0], pnlist[1], pnlist[2]  # 0=C, 1=M, 2=P, 3=V
    if ynC is None or ynC.count(0.0) > 2:
        return -1
    if ynM is None or ynM[-1] < 5:
        return -1
    minY = min(ynC)
    if minY == ynC[-1] or lastprice < ynP[-2] or lastprice < min(ynP):
        return -1
    ylist = []
    for j, val in enumerate(reversed(ynC)):
        ylist.append(val)
        if j > 2:  # only interested with last 4 elements
            break
    if len(ylist) < 4 or ylist.count(0.0) > 0:
        return -1
    maxY = max(ynC)
    if maxY == ynC[-1]:
        return 2
    if lastprice > maxY:
        return 1
    if lastprice > ynC[-1]:
        return 0
    return -1
