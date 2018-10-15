'''
Created on Oct 14, 2018

Motion - 12 days up in 15 days
Volume - 25% up in 15 days
Price  - 20% up in 15 days

@author: hwase0ng
'''

from common import loadCfg, formStocklist, FifoDict
import csv
import settings as S
import traceback


def unpackEOD(counter, dt, price_open, price_high, price_low, price_close, volume):
    return counter, dt, price_open, price_high, price_low, price_close, volume


def readCSV(counter):
    totalVol = 0.0
    totalPrice = 0.0
    daysUp = 0
    eodlist = FifoDict()
    for i in range(S.MVP_DAYS):
        # counter, date, open, high, low, close, volume, total vol, total price,
        #   up/down from previous day, days up, vol diff, price diff
        eodlist.append(['', '1900-01-{:02d}'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0])
    lasteod = ['', '1900-01-14'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0]

    S.DBG_ALL = False
    if S.DBG_ALL:
        for _ in range(S.MVP_DAYS):
            print eodlist.pop()

    with open(counter, "rb") as fl:
        try:
            reader = csv.reader(fl, delimiter=',')
            for i, line in enumerate(reader):
                stock, dt, popen, phigh, plow, pclose, volume = unpackEOD(*line)
                if S.DBG_ALL:
                    print '{}: {},{},{},{},{},{},{}'.format(
                        i, stock, dt, popen, phigh, plow, pclose, volume)
                if pclose >= popen and pclose >= lasteod[5]:
                    dayUp = 1
                else:
                    dayUp = 0
                eodpop = eodlist.pop()
                daysUp = daysUp + dayUp - int(eodpop[-4])
                totalVol = totalVol + float(volume) - float(eodpop[6])
                totalPrice = totalPrice + float(pclose) - float(eodpop[5])
                aveVol = float(eodpop[7]) / S.MVP_DAYS
                avePrice = float(eodpop[8]) / S.MVP_DAYS
                volDiff = (float(volume) - aveVol) / aveVol
                priceDiff = (float(pclose) - avePrice) / avePrice
                if S.DBG_ALL and dt.startswith('2018-07'):
                    print '\t', dt, aveVol, avePrice, volDiff, priceDiff
                neweod = '{},{},{},{},{},{},{},{},{:.2f},{},{},{:.2f},{:.2f}'.format(
                    stock, dt, popen, phigh, plow, pclose, volume,
                    totalVol, totalPrice, dayUp, daysUp, volDiff, priceDiff)
                print neweod
                eodlist.append(neweod.split(','))
                lasteod = line
        except Exception:
            print eodpop
            traceback.print_exc()


if __name__ == '__main__':
    cfg = loadCfg(S.DATA_DIR)
    global klse
    klse = "scrapers/i3investor/klse.txt"
    stocks = 'DUFU'
    stocklist = formStocklist(stocks, klse)
    for shortname in sorted(stocklist.iterkeys()):
        readCSV(S.DATA_DIR + shortname + '.' + stocklist[shortname] + '.csv')
