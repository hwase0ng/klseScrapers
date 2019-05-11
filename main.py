'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Optional counters
Options:
    -c,--check            Check processing mode
    -f,--force            Force update when investing.com data is delayed (obsoleted as now using i3)
    -i,--i3=<date>        Use i3 on Saturday to download Friday's EOD, enhanced to accept any dates
    -l,--list=<clist>     List of counters (dhkmwM) to retrieve from config.json
    -k,--klse             Update KLSE stock listing
    -K,--KLSE             Update KLSE related stocks
    -m,--mt4=<mt4date>    Write and update metatrader4
    -r,--resume           Resume after crash [default: False]
    -p,--price=<n1,n2>    Update price after stock split/consolidation/warrant exercise
                            e.g. 1 bonus share for every 2 shares: n1=2,n2=3
                          Output: COUNTER.csv.new
    -h,--help             This page

This app downloads EOD from KLSE, either for all counters or selectively

Created on Apr 16, 2018
@author: hwase0ng
'''

import settings as S
import pandas as pd
from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, \
    scrapeRecentEOD, unpackEOD
from scrapers.i3investor.scrapeStocksListing import writeStocksListing,\
    writeLatestPrice, scrapeLatestPrice, connectStocksListing, mt4eod
from utils.dateutils import getLastDate, getDayBefore, getToday, getNextDay
from scrapers.investingcom.scrapeInvestingCom import loadIdMap, InvestingQuote,\
    scrapeKlseRelated
from common import formStocklist, loadKlseCounters, appendCsv, loadCfg, loadMap,\
    retrieveCounters
from utils.fileutils import cd, purgeOldFiles
from scrapers.dbKlseEod import dbUpsertCounters, initKlseDB
from docopt import docopt
from datetime import datetime
import os
import subprocess
import tarfile
import glob
import fileinput
import csv


def pricesplit(sname, scode, ratio):
    # infile = S.DATA_DIR + sname + "." + scode + ".csv"
    infile = os.path.join(S.DATA_DIR, sname + "." + scode + ".csv")
    outfile = infile + ".new"
    df = pd.read_csv(infile, sep=',', header=None,
                     names=['name', 'date', 'open', 'high', 'low', 'close', 'volume'])
    df['open'] = df['open'] * ratio
    df['high'] = df['high'] * ratio
    df['low'] = df['low'] * ratio
    df['close'] = df['close'] * ratio
    df['volume'] = pd.to_numeric(df['volume'])
    df['volume'].astype(int)
    df.to_csv(outfile, sep=',', header=False, index=False, float_format='%.4f')


def dbUpdateLatest(eodlist=''):
    eodfile = 'latest.eod'
    if len(eodlist) > 0:
        with open(S.DATA_DIR + eodfile, 'wb') as eodf:
            for eod in eodlist:
                eodf.write(str(eod) + '\n')
    elif os.path.isfile(eodfile):
        print "Processing from last EOD file ... "
        return
    else:
        print "ERR: Missing EOD file!"
        return

    db = initKlseDB()
    if db is None:
        print "Missing DB connection ... Skipped"
        return
    dbUpsertCounters(db, eodfile)


def scrapeI3eod(sname, scode, lastdt):
    eodStock = scrapeRecentEOD(connectRecentPrices(scode), lastdt)
    if eodStock is None or not eodStock:
        print "ERR:No Result for ", sname, scode
        return None
    i3eod = []
    for key in sorted(eodStock.iterkeys()):
        if key <= lastdt:
            print "Skip downloaded: ", key, lastdt
            continue
        i3eod += [sname + ',' + key + ',' +
                  ','.join(map(str, unpackEOD(*(eodStock[key]))))]
    return i3eod


def getStartDate(OUTPUT_FILE):
    if S.RESUME_FILE:
        startdt = getLastDate(OUTPUT_FILE)
        if startdt is None or len(startdt) == 0:
            # File is likely to be empty, hence scrape from beginning
            startdt = S.ABS_START
    else:
        startdt = S.ABS_START
    return startdt


def scrapeI3(stocklist):
    eodlist = []
    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "INF:Skip: ", shortname
            continue
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            rtn_code = -1
            OUTPUT_FILE = S.DATA_DIR + shortname + "." + stock_code + ".csv"
            TMP_FILE = OUTPUT_FILE + 'tmp'
            startdt = getStartDate(OUTPUT_FILE)
            print 'Scraping {0},{1}: lastdt={2}'.format(
                shortname, stock_code, startdt)
            i3eod = scrapeI3eod(shortname, stock_code, startdt)
            if i3eod is None or not i3eod:
                continue
            rtn_code = 0
            f = open(TMP_FILE, "wb")
            for eod in i3eod:
                f.write(eod + '\n')
                eodlist.append(eod)
                if S.DBG_ALL:
                    print eod
            f.close()
        else:
            print "ERR: Not found: ", shortname
            rtn_code = -1

        appendCsv(rtn_code, OUTPUT_FILE)

    return eodlist


def checkI3LastTradingDay(lastdt, i3onSat=""):
    dt, popen, pclose, vol = scrapeRecentEOD(connectRecentPrices("1295"), lastdt, True)
    popen2, pclose2, vol2 = scrapeLatestPrice(connectStocksListing("P"), "1295")
    if S.DBG_ALL:
        print dt, popen, pclose, vol, popen2, pclose2, vol2
    if dt == lastdt or i3onSat:
        dates = [dt]
        if popen == popen2 and pclose == pclose2 and vol == vol2:
            # Post processing mode on the following day
            if i3onSat:
                dates = [lastdt]
                # dates.append(getYesterday('%Y-%m-%d'))
                dates.append(i3onSat)
        else:
            if i3onSat:
                dates = [lastdt]
                dates.append(i3onSat)
            now = datetime.now()
            # Use i3 latest price
            if now.hour >= 17:
                # only download today's EOD if it is after 6pm local time
                dates.append(getToday('%Y-%m-%d'))
        return dates
    elif dt > lastdt and dt == getToday('%Y-%m-%d'):
        # sometimes i3 updates latest price on the same day
        dates = [lastdt, dt]
        return dates
    else:
        if lastdt > dt:
            # post processing mode on the same day
            return [lastdt]

    # lastdt < dt, Need to update multiple dates, even for yesterday's EOD alone
    return ['1', getNextDay(lastdt), '3']


def checkInvComLastTradingDay(lastdt):
    idmap = loadIdMap('scrapers/investingcom/klse.idmap')
    eod = InvestingQuote(idmap, 'PBBANK', getDayBefore(lastdt))
    if isinstance(eod.response, unicode):
        dfEod = eod.to_df()
        if isinstance(dfEod, pd.DataFrame):
            dates = pd.to_datetime(dfEod["Date"], format='%Y%m%d')
            dates = dates.dt.strftime('%Y-%m-%d').tolist()
            if S.DBG_ALL:
                print dates
            return dates
    return None


def preUpdateProcessing():
    print "Pre-update Processing ... Done"


def housekeeping(tgtdir, purgedays=10):
    print "Housekeeping ...", tgtdir
    if len(tgtdir) == 0:
        print '\tNothing to do.'
        return

    try:
        with cd(tgtdir):
            purgeOldFiles('*.tgz', purgedays)
        '''
        with cd(tgtdir):
            backupKLse("pre")
        '''
    except Exception, e:
        print e
        pass

    print "Housekeeping ... Done"


def getCsvFiles(eodfile):
    # i3map = loadMap("scrapers/i3investor/klse.txt", ",")
    i3map = loadMap(klse, ",")
    csvfiles = []
    if os.path.isfile(eodfile):
        with open(eodfile, 'r') as f:
            reader = csv.reader(f)
            csvlist = list(reader)
            for item in csvlist:
                shortname = item[0]
                try:
                    scode = i3map[shortname]
                except KeyError:
                    print "INFO:Unmatched stock:", shortname
                    continue
                csvname = shortname + '.' + scode + '.csv'
                csvfiles.append(csvname)
    else:
        csvfiles = glob.glob("*.csv")

    return csvfiles


def postUpdateProcessing():
    def backupKLse(srcdir, tgtdir, prefix):
        if len(tgtdir) == 0 or not tgtdir.endswith('\\'):
            print "Skipped backing up data", tgtdir
            return

        with cd(srcdir):
            subprocess.call('pwd')
            bkfl = tgtdir + prefix + 'klse' + getToday() + '.tgz'
            print "Backing up", bkfl
            with tarfile.open(bkfl, "w:gz") as tar:
                for csvfile in glob.glob("*.csv"):
                    tar.add(csvfile)
            '''
            os.system('backup.sh ' + bkfl + ' ' + S.DATA_DIR)
            cmd = 'tar czvf ' + bkfl + ' -C ' + S.DATA_DIR + ' *.csv'
            print cmd
            os.system(cmd)
            '''

    def backupjson(datadir):
        jsondir = os.path.join(datadir, "json", '')
        tgtdir = os.path.join(S.DATA_DIR, "json", '')
        jfiles = "*." + getToday("%Y-%m-%d") + ".json"
        with cd(jsondir):
            subprocess.call('pwd')
            print jfiles
            for jfile in glob.glob(jfiles):
                jname = jfile.split(".")
                bkfl = tgtdir + jname[0] + ".tgz"
                print "backing up", bkfl
                with tarfile.open(bkfl, "a:gz") as tar:
                    tar.add(jfile)

    housekeeping(S.BKUP_DIR)
    # backupjson("data")
    backupKLse(S.DATA_DIR, S.BKUP_DIR, "pst")
    backupKLse(S.DATA_DIR + S.MVP_DIR, S.BKUP_DIR, "mvp")
    mt4update()


def mt4update(lastTradingDate=getToday('%Y-%m-%d')):
    def latesteod(eodlist):
        if len(eodlist) > 0:
            with open(S.DATA_DIR + eodfile, 'wb') as eodf:
                for eod in eodlist:
                    eodf.write(str(eod) + '\n')
        elif os.path.isfile(eodfile):
            print "Processing from last EOD file ... "
            return
        else:
            print "ERR: Missing EOD file!"
            return

    if len(S.MT4_DIR) == 0 or not mt4date:
        return

    eodfile = 'latest.eod'
    latesteod(mt4eod(lastTradingDate))
    csvfiles = getCsvFiles(S.DATA_DIR + 'latest.eod')

    with cd(S.DATA_DIR):
        quotes = S.MT4_DIR + "quotes.csv"
        print os.getcwd()
        print "Writing to MT4 ... " + quotes
        with open(quotes, 'w') as qcsv:
            input_lines = fileinput.input(csvfiles)
            qcsv.writelines(input_lines)
        print "Writing to MT4 ... Done"

    with cd(S.MT4_DIR):
        cmd = "mt4.sh " + S.MT4_DIR
        os.system(cmd)
        print "Post-update Processing ... Done"


def scrapeKlse(procmode, force_update, resume, i3onSat):
    '''
    Determine if can use latest price found in i3 stocks page
    Conditions:
      1. latest eod record in csv file is not today
      2. latest eod record in csv file is 1 trading day behind
         that of investing.com latest eod
    '''
    lastdt = getLastDate(S.DATA_DIR + 'YTL.4677.csv')
    if force_update or resume:
        dates = []
        dates.append(lastdt)
        dates.append(getToday('%Y-%m-%d'))
    else:
        if 1 == 1:
            # use i3 instead of investing.com due to delayed updating of EOD since 4Q 2018
            dates = checkI3LastTradingDay(lastdt, i3onSat)
        else:
            dates = checkInvComLastTradingDay(lastdt)
    if dates is None or (len(dates) == 1 and dates[0] == lastdt):
        if procmode:
            print "Post updating mode ON"
            print lastdt, dates
            return

        print "Already latest. Post-updating now."
        postUpdateProcessing()
    else:
        if procmode:
            print "Post updating mode OFF"

        if len(dates) == 2 and dates[1] > lastdt and dates[0] == lastdt:
            useI3latest = True
        else:
            useI3latest = False

        if useI3latest:
            print "Scraping from i3 latest ..."
            preUpdateProcessing()
            list1 = writeLatestPrice(dates[1], True, resume)
        else:
            print "Scraping from i3 recent ..."
            # I3 only keeps 1 month of EOD, while investing.com cannot do more than 5 months
            # Have enhanced investing.com code to break down downloads by every 3 months
            if 1 == 0:
                list1 = scrapeI3(loadKlseCounters(klse))
            else:
                list1 = writeLatestPrice(dates[1], True, resume, dates[1])

        list2 = scrapeKlseRelated('scrapers/investingcom/klse.idmap')
        if len(list2):
            pypath = os.environ['PYTHONPATH'].split(os.pathsep)
            if any("klsemvp" in s for s in pypath):
                from analytics.mvp import mpvUpdateKlseRelated
                mpvUpdateKlseRelated()

        if S.USEMONGO:
            # do not perform upsert ops due to speed
            eodlist = list2 + list1
            dbUpdateLatest(eodlist)


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    '''
    preUpdateProcessing()
    print scrapeKlseRelated('scrapers/investingcom/klse.idmap', False)
    dbUpdateLatest()

    stocks = 'AASIA,ADVPKG,AEM,AIM,AMTEK,ASIABRN,ATLAN,ATURMJU,AVI,AYER,BCB,BHIC,BIG,BIPORT,BJFOOD,BJMEDIA,BLDPLNT,BOXPAK,BREM,BRIGHT,BTM,CAMRES,CEPCO,CFM,CHUAN,CICB,CNASIA,CYMAO,DEGEM,DIGISTA,DKLS,DOLMITE,EIG,EKSONS,EPMB,EUROSP,FACBIND,FCW,FSBM,GCE,GETS,GOCEAN,GOPENG,GPA,HCK,HHHCORP,HLT,ICAP,INNITY,IPMUDA,ITRONIC,JASKITA,JETSON,JIANKUN,KAMDAR,KANGER,KIALIM,KLCC,KLUANG,KOMARK,KOTRA,KPSCB,KYM,LBICAP,LEBTECH,LIONDIV,LIONFIB,LNGRES,MALPAC,MBG,MELATI,MENTIGA,MERGE,METROD,MGRC,MHCARE,MILUX,MISC,MSNIAGA,NICE,NPC,NSOP,OCB,OFI,OIB,OVERSEA,PENSONI,PESONA,PGLOBE,PJBUMI,PLB,PLS,PTGTIN,RAPID,REX,RSAWIT,SANBUMI,SAPIND,SBAGAN,SCIB,SEALINK,SEB,SERSOL,SHCHAN,SINOTOP,SJC,SMISCOR,SNC,SNTORIA,SRIDGE,STERPRO,STONE,SUNSURIA,SUNZEN,SYCAL,TAFI,TFP,TGL,THRIVEN,TSRCAP,UMS,UMSNGB,WEIDA,WOODLAN,XIANLNG,YFG,ZECON,ZELAN'
    stocks = 'D&O,E&O,F&N,L&G,M&G,P&O,Y&G'
    postUpdateProcessing()
    stocks = getCounters(args['COUNTER'], args['--klse'],
                         args['--portfolio'], args['--watchlist'], False)
    '''
    global klse, mt4date
    klse = "scrapers/i3investor/klse.txt"
    mt4date = args['--mt4']
    if args['--klse']:
        # Full download using klse.txt
        # To do: a fix schedule to refresh klse.txt
        print "Scraping i3 stocks listing ..."
        writeStocksListing(klse)

    if args['--price']:
        sname = args['COUNTER'][0].upper()
        slist = formStocklist(sname, klse)
        nums = args['--price'].split(",")
        ratio = float(nums[0]) / float(nums[1])
        pricesplit(sname, slist[sname], float("{:.5f}".format((ratio))))
    elif args['--KLSE']:
        scrapeKlseRelated('scrapers/investingcom/klse.idmap')
    elif mt4date is not None:
        mt4update(mt4date)
    else:
        if args['COUNTER']:
            stocks = args['COUNTER'][0].upper()
        else:
            stocks = retrieveCounters(args['--list'])
        S.DBG_ALL = False
        S.RESUME_FILE = True

        if len(stocks) > 0:
            #  download only selected counters
            scrapeI3(formStocklist(stocks, klse))
        else:
            scrapeKlse(args['--check'], args['--force'], args['--resume'], args['--i3'])

    print "\nDone."
