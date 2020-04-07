'''
Created on Dec 26, 2016

@author: t.roy
'''

#  Configurations
ABS_START = '2010-01-02'
ABS_END = ''
DATA_DIR = 'data/'
DATA_DIR_W = 'data\\'
BKUP_DIR = ''
# CHROME_DIR = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
CHROME_DIR = ''
EXCLUDE_LIST = 'CAP,CLIQ,CLOUD,CSL,EIG,FOCUSP,JMEDU,HLCAP,KINSTEL,LEBTECT,LYC,MPCORP,NPS,PETONE,RALCO,SONA,TIMWELL,WINTONI,XINHE,XINQUAN,YFG'
KLSE_RELATED = 'KLSE.0206,FTFBM100.0200,FTFBMKLCI.0201,FTFBMMES.0202,FTFBMSCAP.0203,FTFBM70.0204,FTFBMEMAS.0205,USDMYR.2168'
MONGODB = 'klsedb'
MONGOEOD = 'klseeod'
MT4_DAYS = 2500
MT4_DIR = ''
MVP_CHART_DAYS = 300  # for volume play, PADINI 2018-07-04 plenM==1 if 300, ARANK 2017-01-06 plenM==2
MVP_DAYS = 15
MVP_DIR = 'mpv/'
SHORTLISTED_FILE = ''
I3_UID = ''
I3_PWD = ''
I3_KLSE_URL = "https://klse.i3investor.com"
I3_PORTFOLIO_URL = ''
I3_HOLDINGS = ''
I3_DIVIDEND = ''
I3_MOMENTUM = ''
I3_MVP = ''
I3_WATCHLIST = ''
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
}
KLSE_LIST = "scrapers/i3investor/klse.txt"
MAIL_SENDER = "insider4trader@gmail.com"
MAIL_PASSWORD = "vwxaotmoawdfwxzx"

# Features toggle
DBG_ALL = False
DBG_ICOM = False
DBG_YAHOO = False
DBG_INSIDER = False
DBG_QR = False
RESUME_FILE = True  # False = fresh reload from ABS_START date, True = only download from next date of last record
PRICE_WITHOUT_SPLIT = True  # False - Apply adjusted close by default
I3LATEST = True
USEMONGO = False
