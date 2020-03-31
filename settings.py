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
I3_KLSE_URL = ''
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

responseTable = " \
@import \"compass/css3\"; \
 \
/* \
 \
RESPONSTABLE 2.0 by jordyvanraaij \
  Designed mobile first! \
 \
If you like this solution, you might also want to check out the 1.0 version: \
  https://gist.github.com/jordyvanraaij/9069194 \
 \
*/ \
 \
// Default options for table style \
$table-breakpoint: 480px; \
$table-background-color: #FFF; \
$table-text-color: #024457; \
$table-outer-border: 1px solid #167F92; \
$table-cell-border: 1px solid #D9E4E6; \
 \
// Extra options for table style (parse these arguments when including your mixin) \
$table-border-radius: 10px; \
$table-highlight-color: #EAF3F3; \
$table-header-background-color: #167F92; \
$table-header-text-color: #FFF; \
$table-header-border: 1px solid #FFF; \
 \
// The Responstable mixin \
 \
@mixin responstable( \
  $breakpoint: $table-breakpoint, \
  $background-color: $table-background-color, \
  $text-color: $table-text-color, \
  $outer-border: $table-outer-border, \
  $cell-border: $table-cell-border, \
  $border-radius: none, \
  $highlight-color: none, \
  $header-background-color: $table-background-color, \
  $header-text-color: $table-text-color, \
  $header-border: $table-cell-border) { \
   \
  .responstable { \
    margin: 1em 0; \
    width: 100%; \
    overflow: hidden;   \
    background: $background-color; \
    color: $text-color; \
    border-radius: $border-radius; \
    border: $outer-border; \
   \
    tr { \
      border: $cell-border;  \
      &:nth-child(odd) { // highlight the odd rows with a color \
        background-color: $highlight-color; \
      }   \
    } \
   \
    th { \
      display: none; // hide all the table header for mobile \
      border: $header-border; \
      background-color: $header-background-color; \
      color: $header-text-color; \
      padding: 1em;   \
      &:first-child { // show the first table header for mobile \
        display: table-cell; \
        text-align: center; \
      } \
      &:nth-child(2) { // show the second table header but replace the content with the data-th from the markup for mobile \
        display: table-cell; \
        span {display:none;} \
        &:after {content:attr(data-th);} \
      } \
      @media (min-width: $breakpoint) { \
        &:nth-child(2) { // hide the data-th and show the normal header for tablet and desktop \
          span {display: block;} \
          &:after {display: none;} \
        } \
      } \
    } \
   \
    td { \
      display: block; // display the table data as one block for mobile \
      word-wrap: break-word; \
      max-width: 7em; \
      &:first-child {  \
        display: table-cell; // display the first one as a table cell (radio button) for mobile \
        text-align: center; \
        border-right: $cell-border; \
      } \
      @media (min-width: $breakpoint) { \
        border: $cell-border; \
      } \
    } \
   \
    th, td { \
      text-align: left; \
      margin: .5em 1em;   \
      @media (min-width: $breakpoint) { \
        display: table-cell; // show the table as a normal table for tablet and desktop \
        padding: 1em; \
      } \
    }   \
  }     \
} \
 \
// Include the mixin (with extra options as overrides) \
 \
@include responstable( \
  $border-radius: $table-border-radius, \
  $highlight-color: $table-highlight-color, \
  $header-background-color: $table-header-background-color, \
  $header-text-color: $table-header-text-color, \
  $header-border: $table-header-border); \
 \
// General styles \
 \
body { \
  padding: 0 2em; \
  font-family: Arial, sans-serif; \
  color: #024457; \
  background: #f2f2f2; \
} \
 \
h1 { \
  font-family: Verdana; \
  font-weight: normal; \
  color: #024457; \
  span {color: #167F92;} \
}"

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
