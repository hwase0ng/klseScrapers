'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S


def scanSignals(counter, fname, hllist, pnlist, lastTrxnDate, lastprice):
    if pnlist is None or not len(pnlist):
        return False
    pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
    pabC, pablistC, rvsM, rvslistM, rvsP, rvslistP = bottomBuySignals(pnW, pnF, lastprice)
    if pabC > 0 and rvsM > 0 and rvsP > 0:
        outfile = fname + "-signals.csv"
        print outfile
        signals = ",BBS," + \
                  str(pabC) + " pabC=(" + ",".join("{:.2f}".format(v) for v in pablistC) + ") " + \
                  str(rvsM) + " rvsM=(" + ",".join("{:.2f}".format(v) for v in rvslistM) + ") " + \
                  str(rvsP) + " rvsP=(" + ",".join("{:.2f}".format(v) for v in rvslistP) + ")"
        with open(outfile, "ab") as fh:
            bbsline = lastTrxnDate + signals
            fh.write(bbsline + '\n')
        with open(S.DATA_DIR + S.MVP_DIR + "sss-" + lastTrxnDate + ".cvs", "ab") as fh:
            bbsline = counter + signals
            fh.write(bbsline + '\n')
        return True
    return False


def bottomBuySignals(pnW, pnF, lastprice):
    # 0=XP, 1=XN, 2=YP, 3=YN
    priceAtBottom, pablist = checkBottomPrice(pnW[3], lastprice)
    if priceAtBottom <= 0:
        return 0, pablist, 0, 0, 0, 0
    ynF = pnF[3]  # 0=XP, 1=XN, 2=YP, 3=YN
    mynF, pynF = ynF[1], ynF[2]    # 0=C, 1=M, 2=P, 3=V
    if len(mynF) < 4 or len(pynF) < 4:
        return 0, pablist, 0, 0, 0, 0
    rvsM, rvslistM = checkReversal(mynF, 5)
    rvsP, rvslistP = checkReversal(pynF, -0.09)
    return priceAtBottom, pablist, rvsM, rvslistM, rvsP, rvslistP


def checkReversal(ynlist, cond):
    ylist = []
    for j, val in enumerate(reversed(ynlist)):
        ylist.append(val)
        if j > 2:  # only interested with last 4 elements
            break
    ylist = ylist[::-1]
    minY = min(ylist)
    if minY == ylist[1] and ylist[2] < ylist[3] and ylist[3] > cond:
        return 2, ylist
    minY = min(ylist[1:])
    if minY == ylist[2] and ylist[3] > cond:
        return 1, ylist
    return 0, ylist


def checkBottomPrice(pnlist, lastprice):
    ynegative = pnlist[0]  # 0=C, 1=M, 2=P, 3=V
    ylist = []
    for j, val in enumerate(reversed(ynegative)):
        ylist.append(val)
        if j > 2:  # only interested with last 4 elements
            break
    if len(ylist) < 4:
        return 0, ylist
    ylist = ylist[::-1]
    minY = min(ylist)
    if minY == ylist[-1]:
        if lastprice >= minY:
            # stage 1 lower lows
            return 1, ylist
    elif minY == ylist[-2] and lastprice >= minY:
        return 2, ylist  # stage 2 after first higher low
    return 0, ylist


if __name__ == '__main__':
    pass
