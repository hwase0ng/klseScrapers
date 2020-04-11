import settings as S
from common import connect_url, printable
from scrapers.i3investor.insider.format_insiders import format_table_insiders, format_insider, format_company
from utils.dateutils import change2KlseDateFmt, getToday

I3_INSIDER_URL = S.I3_KLSE_URL + '/insider/'
I3_INSIDER_DIRECTOR_URL = I3_INSIDER_URL + "director/latest.jsp"
I3_INSIDER_SHAREHOLDER_URL = I3_INSIDER_URL + "substantialShareholder/latest.jsp"
I3_INSIDER_COMPANY_URL = I3_INSIDER_URL + "company/latest.jsp"


def crawl_latest(trading_date=getToday("%d-%b-%Y"), formatted_output=True):
    url = I3_INSIDER_DIRECTOR_URL
    latest_dir = scrape_latest(connect_url(url), url, trading_date, formatted_output)
    if formatted_output and len(latest_dir) > 0:
        format_table_insiders("Latest Directors Transactions", latest_dir)

    url = I3_INSIDER_SHAREHOLDER_URL
    latest_shd = scrape_latest(connect_url(url), url, trading_date, formatted_output)
    if formatted_output and len(latest_shd) > 0:
        format_table_insiders("Latest Substantial Shareholders Transactions", latest_shd)

    url = I3_INSIDER_COMPANY_URL
    latest_company = scrape_latest(connect_url(url), url, trading_date, formatted_output)
    if formatted_output and len(latest_company) > 0:
        format_table_insiders("Latest Company Transactions", latest_company)
    return latest_dir, latest_shd, latest_company


def scrape_latest(soup, url, trading_date, formatted_output):
    if soup is None:
        print ('Insider ERR: no result for <' + url + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + url + '>')
        return None
    insiders = {}
    director = "director" in url
    # for each row, there are many rows including no table
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        if S.DBG_INSIDER:
            print("DBG:")
            for x in td:
                print repr(x)
        # u'\u2019' is the last char in DATO' which can't be encoded to ascii
        # insider = [x.text.replace(u'\u2019', '').strip().encode("ascii") for x in td]
        insider = [printable(x.text.replace(u'\u2019', '').encode("ascii")).strip() for x in td]
        if len(insider) >= 10:
            name, chg_date, price, view = "", "", "", ""
            from_date, to_date, min_price, max_price = "", "", "", ""
            if len(insider) == 11:
                stock, announce_date, name, chg_date, chg_type, shares, price, direct, indirect, total = \
                    unpack_latest_td(*insider)
                view = S.I3_KLSE_URL + td[10].find('a').get('href').encode("ascii")
                if S.DBG_ALL or S.DBG_INSIDER:
                    print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
                          (stock, announce_date, chg_date, chg_type, shares, price, direct, indirect, total, view))
            else:
                stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total = \
                    unpack_company_td(*insider)
                view = S.I3_KLSE_URL + td[9].find('a').get('href').encode("ascii")
                if S.DBG_ALL or S.DBG_INSIDER:
                    print("%s, %s, %s, %s, %s, %s, %s, %s, %s" %
                          (stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total))
            ann_date = change2KlseDateFmt(announce_date, "%d-%b-%Y")
            trd_date = change2KlseDateFmt(trading_date, "%d-%b-%Y")
            if S.DBG_QR:
                print("DBG:dates:{0}:{1}".format(ann_date, trd_date))
            if ann_date >= trd_date:
                if len(insider) == 11:
                    if stock not in insiders:
                        insiders[stock] = []
                    insiders[stock].append(format_insider(
                        formatted_output,
                        director, stock, announce_date, name, chg_date,
                        chg_type, shares, price, view))
                else:
                    if stock not in insiders:
                        insiders[stock] = []
                    insiders[stock].append(format_company(
                        formatted_output,
                        stock, announce_date,from_date, to_date,
                        chg_type, shares, min_price, max_price, total, view))
            else:
                break
    return insiders


def unpack_latest_td(stock, announce_date, name, chg_date, chg_type, shares, price, direct, indirect, total, view):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(
            stock, announce_date, name, chg_date, chg_type, shares, price, direct, indirect, total)
    return stock, announce_date, name, chg_date, chg_type, shares, price, direct, indirect, total


def unpack_company_td(stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total, view):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8}".format(
            stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total)
    return stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total
