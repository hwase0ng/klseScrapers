'''
Created on Apr 16, 2018

@author: hwase0ng
'''

import settings as S
import pandas as pd
from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
from scrapers.i3investor.scrapeStocksListing import writeStocksListing,\
    writeLatestPrice
from utils.dateutils import getLastDate, getDayBefore, getToday
from scrapers.investingcom.scrapeInvestingCom import loadIdMap, InvestingQuote,\
    scrapeKlseRelated
from common import formStocklist, loadKlseCounters, appendCsv, loadCfg, loadMap
from utils.fileutils import cd, purgeOldFiles
from scrapers.dbKlseEod import dbUpsertCounters, initKlseDB
import os
import subprocess
import tarfile
import glob
import fileinput
import csv


def dbUpdateLatest(eodlist=''):
    eodfile = 'latest.eod'
    if len(eodlist) > 0:
        with open(S.DATA_DIR + eodfile, 'wb') as eodf:
            for eod in eodlist:
                eodf.write(str(eod) + '\n')
        # return and do not perform upsert ops due to speed
        return
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
    eodStock = scrapeEOD(connectRecentPrices(scode), lastdt)
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
        if len(startdt) == 0:
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


def checkLastTradingDay(lastdt):
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


def backupKLse(prefix):
    if len(S.BKUP_DIR) == 0 or not S.BKUP_DIR.endswith('\\'):
        print "Skipped backing up data", S.BKUP_DIR
        return

    with cd(S.DATA_DIR):
        subprocess.call('pwd')
        bkfl = S.BKUP_DIR + prefix + 'klse' + getToday() + '.tgz'
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


def preUpdateProcessing():
    if len(S.BKUP_DIR) == 0:
        print 'Nothing to do.'
        return

    try:
        print "Pre-update Processing ...", S.BKUP_DIR
        with cd(S.BKUP_DIR):
            purgeOldFiles('*.tgz', 10)
        '''
        with cd(S.DATA_DIR):
            backupKLse("pre")
        '''
        print "Pre-update Processing ... Done"
    except Exception, e:
        print e
        pass


def getCsvFiles(eodfile):
    i3map = loadMap("scrapers/i3investor/klse.txt", ",")
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
    backupKLse("pst")

    if len(S.MT4_DIR) == 0:
        return

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
        os.system('mt4.sh')
        print "Post-update Processing ... Done"


def scrapeKlse(stocks=''):
    S.DBG_ALL = False
    S.RESUME_FILE = True

    klse = "scrapers/i3investor/klse.txt"
    if len(stocks) > 0:
        #  download only selected counters
        scrapeI3(formStocklist(stocks, klse))
    else:
        '''
        Determine if can use latest price found in i3 stocks page
        Conditions:
          1. latest eod record in csv file is not today
          2. latest eod record in csv file is 1 trading day behind
             that of investing.com latest eod
        '''
        lastdt = getLastDate(S.DATA_DIR + 'PBBANK.1295.csv')
        dates = checkLastTradingDay(lastdt)
        if dates is None or (len(dates) == 1 and dates[0] == lastdt):
            print "Already latest. Nothing to update."
            postUpdateProcessing()
        else:
            if len(dates) == 2 and dates[1] > lastdt and dates[0] == lastdt:
                useI3latest = True
            else:
                useI3latest = False

            if useI3latest:
                preUpdateProcessing()
                list1 = writeLatestPrice(dates[1], True)
            else:
                # Full download using klse.txt
                # To do: a fix schedule to refresh klse.txt
                writeStkList = False
                if writeStkList:
                    print "Scraping i3 stocks listing ..."
                    writeStocksListing(klse)

                # TODO:
                # I3 only keeps 1 month of EOD, while investing.com cannot do more than 5 months
                # May need to do additional checking to determine if need to use either
                list1 = scrapeI3(loadKlseCounters(klse))

            list2 = scrapeKlseRelated('scrapers/investingcom/klse.idmap')
            eodlist = list2 + list1
            dbUpdateLatest(eodlist)

    print "\nDone."


if __name__ == '__main__':
    cfg = loadCfg(S.DATA_DIR)
    '''
    preUpdateProcessing()
    print scrapeKlseRelated('scrapers/investingcom/klse.idmap', False)
    dbUpdateLatest()

    stocks = 'AASIA,ADVPKG,AEM,AIM,AMTEK,ASIABRN,ATLAN,ATURMJU,AVI,AYER,BCB,BHIC,BIG,BIPORT,BJFOOD,BJMEDIA,BLDPLNT,BOXPAK,BREM,BRIGHT,BTM,CAMRES,CEPCO,CFM,CHUAN,CICB,CNASIA,CYMAO,DEGEM,DIGISTA,DKLS,DOLMITE,EIG,EKSONS,EPMB,EUROSP,FACBIND,FCW,FSBM,GCE,GETS,GOCEAN,GOPENG,GPA,HCK,HHHCORP,HLT,ICAP,INNITY,IPMUDA,ITRONIC,JASKITA,JETSON,JIANKUN,KAMDAR,KANGER,KIALIM,KLCC,KLUANG,KOMARK,KOTRA,KPSCB,KYM,LBICAP,LEBTECH,LIONDIV,LIONFIB,LNGRES,MALPAC,MBG,MELATI,MENTIGA,MERGE,METROD,MGRC,MHCARE,MILUX,MISC,MSNIAGA,NICE,NPC,NSOP,OCB,OFI,OIB,OVERSEA,PENSONI,PESONA,PGLOBE,PJBUMI,PLB,PLS,PTGTIN,RAPID,REX,RSAWIT,SANBUMI,SAPIND,SBAGAN,SCIB,SEALINK,SEB,SERSOL,SHCHAN,SINOTOP,SJC,SMISCOR,SNC,SNTORIA,SRIDGE,STERPRO,STONE,SUNSURIA,SUNZEN,SYCAL,TAFI,TFP,TGL,THRIVEN,TSRCAP,UMS,UMSNGB,WEIDA,WOODLAN,XIANLNG,YFG,ZECON,ZELAN'
    stocks = 'D&O,E&O,F&N,L&G,M&G,P&O,Y&G'
    postUpdateProcessing()
    '''
    scrapeKlse()
    pass
