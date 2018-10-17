'''
Usage: main [-pwh] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -p,--portfolio    Select portfolio from config.json
    -w,--watchlist    Select watchlist from config.json
    -h,--help         This page

Created on Oct 14, 2018

Motion - 12 days up in 15 days
Volume - 25% up in 15 days
Price  - 20% up in 15 days

@author: hwase0ng
'''

from common import getCounters, loadCfg, formStocklist, FifoDict, loadKlseCounters
from docopt import docopt
from pandas import read_csv
from StringIO import StringIO
import csv
import settings as S
import tailer as tl
import traceback


def unpackEOD(counter, dt, price_open, price_high, price_low, price_close, volume):
    return counter, dt, price_open, price_high, price_low, price_close, volume


def generateMPV(counter, stkcode):
    if S.DBG_YAHOO:
        print shortname, stkcode
    totalVol = 0.0
    totalPrice = 0.0
    mvpDaysUp = 0
    eodlist = FifoDict()
    for i in range(S.MVP_DAYS):
        #  names=['Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
        #         'Total Vol', 'Total Price', 'DayB4 Motion', 'MOTION', 'PRICE', 'VOLUME'])
        eodlist.append(['', '1900-01-{:02d}'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0])
    lasteod = ['', '1900-01-14'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0]

    S.DBG_ALL = False
    if S.DBG_ALL:
        for _ in range(S.MVP_DAYS):
            print eodlist.pop()

    fh = open(S.DATA_DIR + 'mpv/mpv-' + counter + '.csv', "w")
    with open(S.DATA_DIR + counter + '.' + stkcode + '.csv', "rb") as fl:
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
                mvpDaysUp = mvpDaysUp + dayUp - int(eodpop[-4])
                totalPrice = totalPrice + float(pclose) - float(eodpop[5])
                totalVol = totalVol + float(volume) - float(eodpop[6])
                aveVol = float(eodpop[7]) / S.MVP_DAYS
                avePrice = float(eodpop[8]) / S.MVP_DAYS
                volDiff = (float(volume) - aveVol) / aveVol
                priceDiff = (float(pclose) - avePrice) / avePrice
                # priceDiff *= 20  # easier to view as value is below 1
                if S.DBG_ALL and dt.startswith('2018-07'):
                    print '\t', dt, aveVol, avePrice, volDiff, priceDiff
                neweod = '{},{},{},{},{},{},{},{},{:.2f},{},{},{:.2f},{:.2f}'.format(
                    stock, dt, popen, phigh, plow, pclose, volume,
                    totalVol, totalPrice, dayUp, mvpDaysUp, priceDiff, volDiff)
                if S.DBG_ALL:
                    print neweod
                fh.write(neweod + '\n')
                eodlist.append(neweod.split(','))
                lasteod = line
        except Exception:
            print eodpop
            traceback.print_exc()
    fh.close()


def updateMPV(counter, eod):
    fname = S.DATA_DIR + "mpv/mpv-" + counter
    csvfl = fname + ".csv"
    fil = open(csvfl)
    lastlines = tl.tail(fil, S.MVP_DAYS)
    print lastlines
    fil.close()

    df = read_csv(StringIO('\n'.join(lastlines)), sep=',',
                  header=None, index_col=False, parse_dates=['date'],
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])

    print df
    eoddata = eod.split(',')
    stock = eoddata[0]
    dt = eoddata[1]
    popen = float(eoddata[2])
    phigh = float(eoddata[3])
    plow = float(eoddata[4])
    pclose = float(eoddata[5])
    volume = float(eoddata[6])
    if pclose >= popen and pclose >= df.iloc[-1]['close']:
        dayUp = 1
    else:
        dayUp = 0
    mvpDaysUp = df[0]['M']
    mvpDaysUp = mvpDaysUp + dayUp - int(df.iloc[0]['dayB4 motion'])
    totalPrice = float(df.iloc[-1]['total price']) + float(pclose) - float(df.iloc[0]['close'])
    totalVol = float(df.iloc[-1]['total vol']) + float(volume) - float(df.iloc[0]['volume'])
    aveVol = float(df.iloc[0]['total vol']) / S.MVP_DAYS
    avePrice = float(df.iloc[0]['total price']) / S.MVP_DAYS
    volDiff = (float(volume) - aveVol) / aveVol
    priceDiff = (float(pclose) - avePrice) / avePrice
    neweod = '{},{},{},{},{},{},{},{},{:.2f},{},{},{:.2f},{:.2f}'.format(
        stock, dt, popen, phigh, plow, pclose, volume,
        totalVol, totalPrice, dayUp, mvpDaysUp, priceDiff, volDiff)
    if S.DBG_ALL:
        print neweod
    fh = open(S.DATA_DIR + 'mpv/mpv-' + counter + '.csv', "a")
    fh.write(neweod + '\n')
    fh.close()

    if mvpDaysUp >= 10 or volDiff > 24:
        trigger = ""
        if mvpDaysUp >= 10:
            trigger += ",M"
        if volDiff >= 24:
            trigger += ",V"
        fh = open(S.DATA_DIR + 'mpv/mpv-' + dt + '.csv', "a")
        fh.write(stock + trigger + '\n')
        fh.close()


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    global klse
    klse = "scrapers/i3investor/klse.txt"
    stocks = getCounters(args['COUNTER'], args['--portfolio'], args['--watchlist'], False)
    if len(stocks):
        stocklist = formStocklist(stocks, klse)
    else:
        S.DBG_YAHOO = True
        stocklist = loadKlseCounters(klse)
    for shortname in sorted(stocklist.iterkeys()):
        generateMPV(shortname, stocklist[shortname])
