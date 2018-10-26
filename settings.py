'''
Created on Dec 26, 2016

@author: t.roy
'''

#  Configurations
ABS_START = '2007-01-01'
ABS_END = ''
DATA_DIR = 'data/'
BKUP_DIR = ''
# CHROME_DIR = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
CHROME_DIR = ''
EXCLUDE_LIST = 'CAP,CLIQ,CLOUD,CSL,GDB,GNB,HLCAP,JMEDU,KINSTEL,MSPORTS,NPS,PETONE,QES,RALCO,SONA,TIMWELL,WINTONI,XINQUAN'
KLSE_RELATED = 'USDMYR.2168,FTFBM100.0200,FTFBMKLCI.0201,FTFBMMES.0202,FTFBMSCAP.0203,FTFBM70.0204,FTFBMEMAS.0205,KLSE.0206'
MONGODB = 'klsedb'
MONGOEOD = 'klseeod'
MT4_DAYS = 2500
MT4_DIR = ''
MVP_DAYS = 15
MVP_DIR = 'mpv/'
MVP_CHART_DAYS = 200  # Display last 200 trading days
MVP_PLOT_PEAKS = False
MVP_DIVERGENCE_COUNT = 5
SHORTLISTED_FILE = ''
I3_UID = ''
I3_PWD = ''
I3_KLSE_URL = ''
I3_PORTFOLIO_URL = ''
I3_HOLDINGS = ''
I3_WATCHLIST = ''
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
}

# Features toggle
DBG_ALL = False
DBG_ICOM = False
DBG_YAHOO = False
RESUME_FILE = True  # False = fresh reload from ABS_START date, True = only download from next date of last record
PRICE_WITHOUT_SPLIT = True  # False - Apply adjusted close by default
I3LATEST = True
USEMONGO = False
