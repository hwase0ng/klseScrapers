import settings as S
from common import connect_url, printable
from scrapers.i3investor.insider.format_insiders import format_listing, format_table_listing
from utils.dateutils import change2KlseDateFmt, getToday

I3_LISTING_URL = S.I3_KLSE_URL + '/additionalListing/latest.jsp'


def crawl_listing(trading_date=getToday("%d-%b-%Y"), formatted_output=True):
    latest_listings = scrape_listing(connect_url(I3_LISTING_URL), trading_date, formatted_output)
    if formatted_output and len(latest_listings) > 0:
        new_list = []
        for key in latest_listings:
            new_list.append(latest_listings[key])
        format_table_listing("Additional Listing", new_list)
        return new_list

    return latest_listings


def scrape_listing(soup, trading_date, formatted_output):
    if soup is None:
        print ('Insider ERR: no result for <' + I3_LISTING_URL + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + I3_LISTING_URL + '>')
        return None
    listings = {}
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
            stock, announce_date, listing_date, type, units, price = \
                unpack_listing_td(*insider)
            view = S.I3_KLSE_URL + td[6].find('a').get('href').encode("ascii")
            if S.DBG_ALL or S.DBG_INSIDER:
                print "view: {}".format(view)
            ann_date = change2KlseDateFmt(announce_date, "%d-%b-%Y")
            trd_date = change2KlseDateFmt(trading_date, "%d-%b-%Y")
            if S.DBG_QR:
                print("DBG:dates:{0}:{1}".format(ann_date, trd_date))
            if ann_date >= trd_date:
                listings[stock] = format_listing(
                    formatted_output, stock, announce_date, listing_date, type, units, price, view)
            else:
                break
    return listings


def unpack_listing_td(stock, announce_date, listing_date, type, units, price, view):
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5}".format(
            stock, announce_date, listing_date, type, units, price)
    return stock, announce_date, listing_date, type, units, price
