'''
Created on Dec 26, 2016

@author: t.roy
'''

#  Configurations
ABS_START = '2007-01-01'
ABS_END = ''
DATA_DIR = 'data/'
BKUP_DIR = ''
EXCLUDE_LIST = 'CAP,CLIQ,CLOUD,CSL,GDB,GNB,HLCAP,JMEDU,KINSTEL,MSPORTS,NPS,PETONE,QES,RALCO,SONA,TIMWELL,WINTONI,XINQUAN'
MONGODB = 'klsedb'
MONGOEOD = 'klseeod'
MT4_DIR = ''
SHORTLISTED_FILE = ''
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
