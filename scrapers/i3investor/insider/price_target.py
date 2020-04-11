import settings as S
from common import connect_url, printable
from scrapers.i3investor.insider.format_insiders import format_table_target, \
    format_target
from utils.dateutils import change2KlseDateFmt, getToday

I3_TARGET_URL = S.I3_KLSE_URL + '/jsp/pt.jsp'


def crawl_price_target(trading_date=getToday("%d-%b-%Y"), formatted_output=True):
    price_targets = scrape_target(connect_url(I3_TARGET_URL), trading_date, formatted_output)
    if formatted_output and len(price_targets) > 0:
        new_list = []
        for key in price_targets:
            new_list.append(price_targets[key])
        format_table_target("Price Target", new_list)
        return new_list

    return price_targets


def scrape_target(soup, trading_date, formatted_output):
    if soup is None:
        print ('Insider ERR: no result for <' + I3_TARGET_URL + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + I3_TARGET_URL + '>')
        return None
    targets = {}
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
            announce_date, stock, last_price, target, upside_down, call, source = \
                unpack_listing_td(*insider)
            ann_date = change2KlseDateFmt(announce_date, "%d/%m/%Y")
            trd_date = change2KlseDateFmt(trading_date, "%d-%b-%Y")
            if S.DBG_QR:
                print("DBG:dates:{0}:{1}".format(ann_date, trd_date))
            if ann_date >= trd_date:
                targets[stock] = format_target(
                    formatted_output, announce_date, stock, last_price, target, upside_down, call, source)
            else:
                break
    return targets


def unpack_listing_td(announce_date, stock, last_price, target, updown_side, call, source):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5},{6}".format(
            announce_date, stock, last_price, target, updown_side, call, source)
    return announce_date, stock, last_price, target, updown_side, call, source
