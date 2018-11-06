'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -d,--debug            Enable debug mode [default: False]
    -l,--list=<clist>     List of counters (dhkmwM) to retrieve from config.json
    -g,--generate         Generate MVP from scratch [default: False]
    -h,--help             This page

Created on Oct 14, 2018

Motion - 12 days up in 15 days
Volume - 25% up in 15 days
Price  - 20% up in 15 days

@author: hwase0ng
'''

from common import retrieveCounters, loadCfg, formStocklist, FifoDict, \
    loadKlseCounters, getSkipRows
from docopt import docopt
from mvpchart import mvpChart, mvpSynopsis, globals_from_args
from utils.dateutils import getToday, getLastDate, getBusDaysBtwnDates
from utils.fileutils import wc_line_count, tail2
from pandas import read_csv
import csv
import settings as S
import traceback

DBG_ALL = False
KLSE = "scrapers/i3investor/klse.txt"


def unpackEOD(counter, dt, price_open, price_high, price_low, price_close, volume):
    if volume == "-":
        volume = 0
    return counter, dt, price_open, price_high, price_low, price_close, volume


def generateMPV(counter, stkcode, today=getToday('%Y-%m-%d')):
    if DBG_ALL:
        print shortname, stkcode
    totalVol = 0.0
    totalPrice = 0.0
    mvpDaysUp = 0
    eodlist = FifoDict()
    for i in range(S.MVP_DAYS):
        # Starts with 15 days of dummy record as base
        #  names=['Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
        #         'Total Vol', 'Total Price', 'DayB4 Motion', 'MOTION', 'PRICE', 'VOLUME'])
        eodlist.append(['', '1900-01-{:02d}'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0])
    lasteod = ['', '1900-01-14'.format(i), 0, 0, 0, 0, 1.0, 1.0, 0.0001, 0, 0, 0.0, 0.0]

    if DBG_ALL:
        for _ in range(S.MVP_DAYS):
            print eodlist.pop()

    try:
        fh = open(S.DATA_DIR + S.MVP_DIR + counter + '.csv', "wb")
        inputfl = S.DATA_DIR + counter + '.' + stkcode + '.csv'
        row_count = wc_line_count(inputfl)
        if row_count < S.MVP_DAYS * 2:
            print "Skipped: ", counter, row_count
            return
        with open(inputfl, "rb") as fl:
            try:
                reader = csv.reader(fl, delimiter=',')
                for i, line in enumerate(reader):
                    stock, dt, popen, phigh, plow, pclose, volume = unpackEOD(*line)
                    if DBG_ALL:
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
                    if DBG_ALL and dt.startswith('2018-07'):
                        print '\t', dt, aveVol, avePrice, volDiff, priceDiff
                    neweod = '{},{},{:.4f},{:.4f},{:.4f},{:.4f},{},{},{:.2f},{},{},{:.2f},{:.2f}\n'.format(
                        stock, dt, float(popen), float(phigh), float(plow), float(pclose), volume,
                        totalVol, totalPrice, dayUp, mvpDaysUp, priceDiff, volDiff)
                    if DBG_ALL:
                        print neweod
                    if i > S.MVP_DAYS:  # skip first 15 dummy records
                        fh.write(neweod)
                        if getBusDaysBtwnDates(dt, today) < S.MVP_DAYS:
                            updateMpvSignals(stock, dt, mvpDaysUp, volDiff, priceDiff, avePrice)
                    eodlist.append(neweod.split(','))
                    lasteod = line
            except Exception:
                print line
                print eodpop
                traceback.print_exc()
    except Exception:
        traceback.print_exc()
        print inputfl
    finally:
        fh.close()


def dfLoadMPV(counter, stkcode, genMPV=False):
    fname = S.DATA_DIR + S.MVP_DIR + counter
    csvfl = fname + ".csv"
    skiprow, row_count = getSkipRows(csvfl)
    if row_count <= 0:
        if genMPV and row_count == 0:
            try:
                generateMPV(counter, stkcode)
            except Exception:
                print counter
                traceback.print_exc()
        return None

    df = read_csv(csvfl, sep=',', skiprows=skiprow, header=None, index_col=False,
                  names=['name', 'date', 'open', 'high', 'low', 'close', 'volume',
                         'total vol', 'total price', 'dayB4 motion', 'M', 'P', 'V'])
    if DBG_ALL:
        print df.iloc[0]['date'], df.iloc[-1]['date']
    return df


def updateMPV(counter, stkcode, eod):
    df = dfLoadMPV(counter, stkcode, True)
    if df is None:
        return False
    eoddata = eod.split(',')
    stock = eoddata[0]
    dt = eoddata[1]
    if dt <= df.iloc[-1]['date']:
        print "Skipped processed date: *", dt, "*", \
            " last processed date: ***", df.iloc[-1]['date'], "***"
        return False
    popen = float(eoddata[2])
    phigh = float(eoddata[3])
    plow = float(eoddata[4])
    pclose = float(eoddata[5])
    if "-" in eoddata[6]:
        eoddata[6] = 0.0
    volume = float(eoddata[6])
    if pclose >= popen and pclose >= df.iloc[-1]['close']:
        dayUp = 1
    else:
        dayUp = 0
    mvpDaysUp = df.iloc[-1]['M']
    mvpDaysUp = mvpDaysUp + dayUp - int(df.iloc[0]['dayB4 motion'])
    totalPrice = float(df.iloc[-1]['total price']) + float(pclose) - float(df.iloc[0]['close'])
    totalVol = float(df.iloc[-1]['total vol']) + float(volume) - float(df.iloc[0]['volume'])
    aveVol = float(df.iloc[0]['total vol']) / S.MVP_DAYS
    avePrice = float(df.iloc[0]['total price']) / S.MVP_DAYS
    volDiff = (float(volume) - aveVol) / aveVol
    priceDiff = (float(pclose) - avePrice) / avePrice
    neweod = '{},{},{:.4f},{:.4f},{:.4f},{:.4f},{},{},{:.2f},{},{},{:.2f},{:.2f}'.format(
        stock, dt, popen, phigh, plow, pclose, int(volume),
        totalVol, totalPrice, dayUp, mvpDaysUp, priceDiff, volDiff)
    if DBG_ALL:
        print neweod
    fh = open(S.DATA_DIR + S.MVP_DIR + counter + '.csv', "ab")
    fh.write(neweod + '\n')
    fh.close()

    # return updateMpvSignals(stock, dt, mvpDaysUp, volDiff, priceDiff, avePrice)
    return True


def updateMpvSignals(stock, dt, mvpDaysUp, volDiff, priceDiff, avePrice):
    trigger = ""
    if mvpDaysUp > 9 and priceDiff > -0.05 and avePrice < -0.05:
        trigger += ",M"
    if volDiff > 24 and priceDiff > -0.05 and avePrice < -0.05:
        trigger += ",V"
    if len(trigger) == 0:
        return False
    fh = open(S.DATA_DIR + S.MVP_DIR + 'signal-' + stock + '.csv', "ab")
    fh.write(dt + trigger + '\n')
    fh.close()
    fh = open(S.DATA_DIR + S.MVP_DIR + 'signal-' + dt + '.csv', "ab")
    fh.write(stock + trigger + '\n')
    fh.close()
    return True


def load_mvp_args(synopsis=False):
    params = {}
    params['--debug'] = False
    params['--plotpeaks'] = True
    params['--peaksdist'] = -1
    params['--threshold'] = -1
    params['--filter'] = False
    params['--blocking'] = 1
    params['--tolerance'] = 3
    params['--synopsis'] = synopsis
    params['--chartdays'] = S.MVP_CHART_DAYS
    params['--list'] = ""
    params['--simulation'] = ""
    params['COUNTER'] = ""
    _, chartDays = globals_from_args(params)
    return chartDays


def mvpUpdateMPV(counter, scode):
    inputfl = S.DATA_DIR + counter + "." + scode + ".csv"
    lastdt = getLastDate(inputfl)
    fname = S.DATA_DIR + S.MVP_DIR + counter
    csvfl = fname + ".csv"
    mvpdt = getLastDate(csvfl)
    if mvpdt is None:
        print "Skip empty file:", counter
        return False
    days = getBusDaysBtwnDates(mvpdt, lastdt)
    if days <= 0:
        print "Already latest: ", counter, lastdt
        return False
    lines = tail2(inputfl, days)
    for eod in lines:
        if updateMPV(counter, scode, eod):
            chartdays = load_mvp_args()
            mvpChart(counter, scode, chartdays)
            chartdays = load_mvp_args(True)
            mvpSynopsis(counter, scode, chartdays)


def mpvUpdateKlseRelated():
    stocks = retrieveCounters("k")
    print "Updating KLSE related:", stocks
    stocklist = formStocklist(stocks, KLSE)
    for shortname in sorted(stocklist.iterkeys()):
        mvpUpdateMPV(shortname, stocklist[shortname])


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    DBG_ALL = True if args['--debug'] else False
    if args['COUNTER']:
        stocks = args['COUNTER'][0].upper()
    else:
        stocks = retrieveCounters(args['--list'])
    if len(stocks):
        stocklist = formStocklist(stocks, KLSE)
    else:
        stocklist = loadKlseCounters(KLSE)
    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "INF:Skip: ", shortname
            continue
        if args['--generate']:
            generateMPV(shortname, stocklist[shortname])
        else:
            mvpUpdateMPV(shortname, stocklist[shortname])
