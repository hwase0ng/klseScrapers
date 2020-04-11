import settings as S
from common import connect_url, printable
from scrapers.i3investor.insider.format_insiders import format_table_entitlement, format_dividend
from utils.dateutils import change2KlseDateFmt, getToday

I3_ENTITLEMENT_URL = S.I3_KLSE_URL + '/entitlement/'
I3_DIVIDEND_URL = I3_ENTITLEMENT_URL + "dividend/latest.jsp"
I3_ENTITLEMENT_OTHERS_URL = I3_ENTITLEMENT_URL + "others/latest.jsp"


def crawl_entitlement(trading_date=getToday("%d-%b-%Y"), formatted_output=False):
    url = I3_DIVIDEND_URL
    latest_dividends = scrape_entitlement(connect_url(url), url, trading_date, formatted_output)
    if formatted_output and len(latest_dividends) > 0:
        format_table_entitlement("Latest Dividends", latest_dividends)

    url = I3_ENTITLEMENT_OTHERS_URL
    latest_others = scrape_entitlement(connect_url(url), url, trading_date, formatted_output)
    if formatted_output and len(latest_others) > 0:
        format_table_entitlement("Latest Bonus, Share Split & Consolidation", latest_others)

    return latest_dividends, latest_others


def scrape_entitlement(soup, url, trading_date, formatted_output):
    if soup is None:
        print ('Insider ERR: no result for <' + url + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + url + '>')
        return None
    entitlements = {}
    others = "others" in url
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
        if len(insider) >= 7:
            if len(insider) == 7:
                announce_date, stock, open_price, current_price, dividend, ex_date = \
                    unpack_dividend_td(*insider)
                view = S.I3_KLSE_URL + td[6].find('a').get('href').encode("ascii")
            else:
                announce_date, stock, subject, open_price, current_price, ratio, ex_date = \
                    unpack_others_td(*insider)
                view = S.I3_KLSE_URL + td[7].find('a').get('href').encode("ascii")
            if S.DBG_ALL or S.DBG_INSIDER:
                    print "view: {}".format(view)
            ann_date = change2KlseDateFmt(announce_date, "%d-%b-%Y")
            trd_date = change2KlseDateFmt(trading_date, "%d-%b-%Y")
            if S.DBG_QR:
                print("DBG:dates:{0}:{1}".format(ann_date, trd_date))
            if ann_date >= trd_date:
                if len(insider) == 7:
                    entitlements[stock] = format_dividend(formatted_output, others,
                                                          announce_date, stock, "", open_price,
                                                          current_price, dividend, ex_date, view)
                else:
                    entitlements[stock] = format_dividend(formatted_output, others,
                                                          announce_date, stock, subject, open_price,
                                                          current_price, ratio, ex_date, view)
            else:
                break
    return entitlements


def unpack_dividend_td(announce_date, stock, open_price, current_price, dividend, ex_date, view):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5}".format(
                announce_date, stock, open_price, current_price, dividend, ex_date)
    return announce_date, stock, open_price, current_price, dividend, ex_date


def unpack_others_td(announce_date, stock, subject, open_price, current_price, ratio, ex_date, view):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5},{6}".format(
            announce_date, stock, subject, open_price, current_price, ratio, ex_date)
    return announce_date, stock, subject, open_price, current_price, ratio, ex_date
