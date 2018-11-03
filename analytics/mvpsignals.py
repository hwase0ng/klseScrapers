'''
Created on Nov 2, 2018

@author: hwase0ng
'''

import settings as S


def scanSignals(counter, fname, hllist, pnlist, lastTrxnDate, lastprice):
    if pnlist is None or not len(pnlist):
        return False
    pnW, pnF, pnM = pnlist[0], pnlist[1], pnlist[2]
    if bottomBuySignals(pnW, pnF, lastprice):
        outfile = fname + "-synopsis-signals.csv"
        with open(outfile, "wb") as fh:
            bbsline = lastTrxnDate + ",BBS"
            fh.write(bbsline + '\n')
        with open(S.DATA_DIR + S.MVP_DIR + "sss-" + lastTrxnDate + ".cvs", "ab") as fh:
            bbsline = counter + ",BBS"
            fh.write(bbsline + '\n')
        return True
    return False


def bottomBuySignals(pnW, pnF, lastprice):
    priceAtBottom = checkBottomPrice(pnW, lastprice)
    if not priceAtBottom:
        return False
    M, P = pnF[1], pnF[2]  # 0=C, 1=M, 2=P, 3=V
    mYN, pYN = M[3], P[3]  # 0=xp, 1=xn, 2=yp, 3=yn
    if len(mYN) < 4 or len(pYN) < 4:
        return False
    if checkReversal(mYN, 5) and checkReversal(pYN, -0.09):
        return True
    return False


def checkReversal(ynlist, cond):
    ylist = []
    for j, val in enumerate(reversed(ynlist)):
        ylist.append(val)
        if j > 3:  # only interested with last 5 elements
            break
    ylist = reversed(ylist)
    minY = min(ylist)
    maxY = max(ylist)
    if maxY == ylist[-1] or maxY == ylist[-2]:
        pos = ylist.index(minY)
        if pos == 1 or pos == 2:
            if maxY > cond:
                return True
    return False


def checkBottomPrice(pnlist, lastprice):
    C = pnlist[0]  # 0=C, 1=M, 2=P, 3=V
    ynegative = C[3]  # 0=xp, 1=xn, 2=yp, 3=yn
    ylist = []
    for j, val in enumerate(reversed(ynegative)):
        ylist.append(val)
        if j > 1:  # only interested with last 3 elements
            break
    minY = min(ylist)
    if minY == ylist[0] or \
       (len(ylist) > 2 and minY == ylist[1]):
        if lastprice >= minY:
            # Higher lows and reversal pattern
            return True
    return False


def scanSignals_X(counter, fname, hllist, pnlist, lastTrxnDate, lastprice):
    if pnlist is None or not len(pnlist):
        return False
    hlsScorelist, revsScorelist = [], []
    totalHLs, totalRevs = 0, 0
    for i in range(3):
        try:
            hlows, revs = bottomBuySignals_Y(i, pnlist[i], lastprice)
        except Exception as e:
            print i, counter
            print e
            continue
        hlsScorelist.append(hlows)
        revsScorelist.append(revs)
        totalHLs += hlows
        totalRevs += revs
    if totalHLs + totalRevs > 5:
        outfile = fname + "-synopsis-BBS.csv"
        with open(outfile, "wb") as fh:
            bbsline = lastTrxnDate + "," + str(totalHLs + totalRevs)
            fh.write(bbsline + '\n')
            bbsline = "HLs"
            for hls in hlsScorelist:
                bbsline += "," + str(hls)
            fh.write(bbsline + '\n')
            bbsline = "Rvs"
            for revs in revsScorelist:
                bbsline += "," + str(revs)
            fh.write(bbsline + '\n')
        with open(S.DATA_DIR + S.MVP_DIR + "BBS-" + lastTrxnDate + ".cvs", "ab") as fh:
            bbsline = counter + "," + str(totalHLs + totalRevs)
            fh.write(bbsline + '\n')
        return True
    return False


def bottomBuySignals_Y(index, pnlist, lastprice):
    bbsHigherLows, bbsReversal = 0, 0
    for i in range(3):  # 0=C, 1=M, 2=P, 3=V (skip V for now)
        '''
        xp = pnlist[0][i]
        xn = pnlist[1][i]
        yp = pnlist[2][i]
        '''
        yn = pnlist[3][i]
        if yn is None or len(yn) < 2:
            continue
        ylist = []
        for j, val in enumerate(reversed(yn)):
            ylist.append(val)
            if j > 2:  # only interested with last 4 elements
                break
        if i == 0:
            minY = min(ylist)
            if minY == ylist[0] or \
               (len(ylist) > 2 and minY == ylist[1]):
                if lastprice >= minY:
                    # Higher lows and reversal pattern
                    bbsHigherLows += 1
                else:
                    break
        else:
            minY = min(ylist)
            maxY = max(ylist)
            if maxY == ylist[0] or maxY == ylist[1]:
                if i == 1 and maxY > 5 or \
                   i == 2 and maxY > -0.09:
                    bbsHigherLows += 1
            if len(ylist) > 1 and min(ylist) == ylist[1]:
                bbsReversal += 1
    return bbsHigherLows, bbsReversal


def bottomBuySignals_X(fname, hllist, pnlist, lastTrxnDate, lastClosingPrice):
    outfile = fname + "-synopsis-BBS.csv"
    with open(outfile, "wb") as fh:
        '''
        cHigh, cLow, mHigh, mLow, pHigh, pLow, vHigh, vLow = hllist
        cxp, mxp, pxp, vxp = pnlist[0]
        cxn, mxn, pxn, vxn = pnlist[1]
        cyp, myp, pyp, vyp = pnlist[2]
        cyn, myn, pyn, vyn = pnlist[3]
        '''
        for i in range(4):
            xp = pnlist[0][i], xn = pnlist[1][i]
            yp = pnlist[2][i], yn = pnlist[3][i]
            yn.append(lastClosingPrice)
            cmpvhigh, cmpvlow, lineitem = yp[0], yn[0], []
            for j in range(len(yn) - 1):
                if xp[j] > xn[j]:
                    if yp[j] > cmpvhigh[j]:
                        cmpvhigh = yp[j]
                if yn[j] < cmpvlow:
                    cmpvlow = yn[j]
                synopsisdate = xn[j]
                nextyn = yn[j + 1]
                HdivL = cmpvhigh / cmpvlow
                HdivNext = cmpvhigh / nextyn
                lineitem.append(synopsisdate)
                lineitem.append(cmpvhigh)
                lineitem.append(cmpvlow)
                lineitem.append(nextyn)
                lineitem.append(HdivL)
                lineitem.append(HdivNext)
                lineitem.append(HdivNext - HdivL)
            fh.write(",".join(lineitem + '\n'))

    return True


if __name__ == '__main__':
    pass
