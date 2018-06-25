'''
Created on Dec 17, 2016

@author: hwase0ng
'''
import settings as S
from matplotlib.dates import date2num
from datetime import date, datetime, timedelta
from utils.fileutils import tail
from time import time, ctime


def get_now_epoch():
    '''
    @see https://www.linuxquestions.org/questions/programming-9/python-datetime-to-epoch-4175520007/#post5244109
    '''
    return int(time.mktime(datetime.datetime.now().timetuple()))


def datestr2float(myd, fmt='%Y-%m-%d'):
    td = datetime.strptime(myd, fmt)
    return date2num(td)


def generate_dates(start_date, end_date):
    td = timedelta(hours=24)
    # input in string format -> change to datetime format
    year, month, day = (int(x) for x in start_date.split('-'))
    current_date = date(year, month, day)
    year, month, day = (int(x) for x in end_date.split('-'))
    end_date = date(year, month, day)
    dtRange = []
    while current_date <= end_date:
        if S.DBG_ALL:
            print current_date, type(current_date)
        dow = getDayOfWeek(str(current_date))
        if dow > 0 and dow < 6:  # only from monday to friday
            dtRange.append(str(current_date))
        current_date += td
    return dtRange


def getDayOfWeek(pdate):
    year, month, day = (int(x) for x in pdate.split('-'))
    return datetime(year, month, day, 0, 0, 0, 0).isoweekday()
    if S.DBG_ALL:
        ans = date(year, month, day)
        print ans.strftime("%A")


def getNextDay(pdate):
    return getDayOffset(pdate, 1)


def getDayBefore(pdate):
    return getDayOffset(pdate, -1)


def getDayOffset(pdate, offset):
    # Expecting input: YYYY-MM-DD
    if S.DBG_ALL:
        print pdate, len(pdate)
    if len(pdate) != 10:
        return pdate
    pyyyy = int(pdate[:4])
    pmm = int(pdate[5:7])
    pdd = int(pdate[8:10])
    try:
        result = date(pyyyy, pmm, pdd) + timedelta(days=offset)
    except Exception, e:
        return str(e)
    if S.DBG_ALL:
        print result
    result = str(result)
#   result = result.replace("-","")
    return result


def getLastDate(fn):
    try:
        t = tail(fn)
    except Exception, e:
        print 'getLastDate', e
        lastdt = S.ABS_START
        return lastdt

    if len(t[0]) == 0:
        return ''
    else:
        if isinstance(t, basestring):
            # using tail
            t2 = t.split(',')
        else:
            # using tail2
            t2 = t[0].split(",")
        lastdt = t2[1]
        return lastdt
        '''
        nextdt = getNextDay(lastdt)
        return nextdt
        '''


def getToday(fm="%Y%m%d"):
    return datetime.today().strftime(fm)


def getTomorrow(fm="%Y%m%d"):
    tmr = datetime.today() + timedelta(days=1)
    return tmr.strftime(fm)


def getYesterday(fm="%Y%m%d"):
    yesterday = datetime.today() + timedelta(days=-1)
    return yesterday.strftime(fm)


def change2KlseDateFmt(dt, fmt):
    if len(dt) == 0:
        print 'change2KlseDateFmt: Empty date'
        return ''
    newdt = datetime.strptime(dt, fmt).strftime('%Y-%m-%d')
    return newdt


def change2IcomDateFmt(dt, fmt="%Y-%m-%d"):
    if len(dt) == 0:
        print 'change2IcomDateFmt: Empty date'
        return ''
    newdt = datetime.strptime(dt, fmt).strftime('%m/%d/%Y')
    return newdt


def getDaysBtwnDates(d1, d2):
    if len(d1) != 10 or len(d2) != 10:
        return ''
    year, month, day = (int(x) for x in d1.split('-'))
    f_date = date(year, month, day)
    year, month, day = (int(x) for x in d2.split('-'))
    l_date = date(year, month, day)
    delta = l_date - f_date
    return delta.days


def getTime():
    tm = ctime().split()
    return tm[3]


if __name__ == '__main__':
    print getDayBefore('2018-01-01')
    print getNextDay('2017-12-31')
    print getDaysBtwnDates('2016-02-01', '2016-03-01')
    today = getToday('%Y-%m-%d')
    mt4start = getDayOffset(today, S.MT4_DAYS * -1)
    mt4start = mt4start[:4] + '-01-01'
    print mt4start
    pass
