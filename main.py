'''
Created on Apr 16, 2018

@author: hwase0ng
'''

import settings as S
import pandas as pd
from scrapers.i3investor.scrapeRecentPrices import connectRecentPrices, scrapeEOD, unpackEOD
from scrapers.i3investor.scrapeStocksListing import writeStocksListing,\
    writeLatestPrice
from Utils.dateutils import getLastDate, getDayBefore
from scrapers.investingcom.scrapeInvestingCom import loadIdMap, InvestingQuote
from common import formStocklist, loadKlseCounters
from Utils.fileutils import cd, getSystemIP
import os


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
    for shortname in sorted(stocklist.iterkeys()):
        if shortname in S.EXCLUDE_LIST:
            print "INF:Skip: ", shortname
            continue
        stock_code = stocklist[shortname]
        if len(stock_code) > 0:
            rtn_code = -1
            OUTPUT_FILE = 'data/' + shortname + "." + stock_code + ".csv"
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
                if S.DBG_ALL:
                    print eod
            f.close()
        else:
            print "ERR: Not found: ", shortname
            rtn_code = -1

        if rtn_code == 0:
            f = open(OUTPUT_FILE, "ab")
            ftmp = open(TMP_FILE, "r")
            f.write(ftmp.read())
            f.close()
            ftmp.close()


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


def preUpdateProcessing():
    ip = getSystemIP()
    if ip.endswith(".2") or ip.endswith(".10"):
        os.system('cp *.csv /z/data/')


def postUpdateProcessing(datadir):
    with cd(datadir):
        mt4dir = '/c/Users/hwase/AppData/Roaming/MetaQuotes/Terminal/DFF6411A75BCA6204637971EAA184B85/history/klse'
        os.system('pwd')
        ip = getSystemIP()
        if S.DBG_ALL:
            print ip
        if ip.endswith(".2"):
            os.system('mt4.sh ' + mt4dir)


if __name__ == '__main__':
    '''
    stocks = 'AASIA,ADVPKG,AEM,AIM,AMTEK,ASIABRN,ATLAN,ATURMJU,AVI,AYER,BCB,BHIC,BIG,BIPORT,BJFOOD,BJMEDIA,BLDPLNT,BOXPAK,BREM,BRIGHT,BTM,CAMRES,CEPCO,CFM,CHUAN,CICB,CNASIA,CYMAO,DEGEM,DIGISTA,DKLS,DOLMITE,EIG,EKSONS,EPMB,EUROSP,FACBIND,FCW,FSBM,GCE,GETS,GOCEAN,GOPENG,GPA,HCK,HHHCORP,HLT,ICAP,INNITY,IPMUDA,ITRONIC,JASKITA,JETSON,JIANKUN,KAMDAR,KANGER,KIALIM,KLCC,KLUANG,KOMARK,KOTRA,KPSCB,KYM,LBICAP,LEBTECH,LIONDIV,LIONFIB,LNGRES,MALPAC,MBG,MELATI,MENTIGA,MERGE,METROD,MGRC,MHCARE,MILUX,MISC,MSNIAGA,NICE,NPC,NSOP,OCB,OFI,OIB,OVERSEA,PENSONI,PESONA,PGLOBE,PJBUMI,PLB,PLS,PTGTIN,RAPID,REX,RSAWIT,SANBUMI,SAPIND,SBAGAN,SCIB,SEALINK,SEB,SERSOL,SHCHAN,SINOTOP,SJC,SMISCOR,SNC,SNTORIA,SRIDGE,STERPRO,STONE,SUNSURIA,SUNZEN,SYCAL,TAFI,TFP,TGL,THRIVEN,TSRCAP,UMS,UMSNGB,WEIDA,WOODLAN,XIANLNG,YFG,ZECON,ZELAN'
    '''
    stocks = ''

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
        datadir = './data/'
        lastdt = getLastDate(datadir + 'PBBANK.1295.csv')
        dates = checkLastTradingDay(lastdt)
        if len(dates) == 1 and dates[0] == lastdt:
            print "Already latest. Nothing to update."
            print "Start post update processing"
            postUpdateProcessing(datadir)
        else:
            if len(dates) == 2 and dates[1] > lastdt and dates[0] == lastdt:
                useI3latest = True
            else:
                useI3latest = False

            if useI3latest:
                preUpdateProcessing()
                writeLatestPrice(True, datadir)
            else:
                # Full download using klse.txt
                # To do: a fix schedule to refresh klse.txt
                writeStocksListing = False
                if writeStocksListing:
                    print "Scraping i3 stocks listing ..."
                    writeStocksListing(klse)

                # TODO:
                # I3 only keeps 1 month of EOD, while investing.com cannot do more than 5 months
                # May need to do additional checking to determine if need to use either
                scrapeI3(loadKlseCounters(klse))

    pass
