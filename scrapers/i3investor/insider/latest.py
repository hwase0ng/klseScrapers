import settings as S
from common import connect_url, printable
from utils.dateutils import change2KlseDateFmt, getToday

I3_INSIDER_URL = S.I3_KLSE_URL + '/insider'
I3_INSIDER_DIRECTOR_URL = I3_INSIDER_URL + "/director/latest.jsp"
I3_INSIDER_SHAREHOLDER_URL = I3_INSIDER_URL + "/director/latest.jsp"
I3_INSIDER_COMPANY_URL = I3_INSIDER_URL + "/director/latest.jsp"


def crawl_latest(trading_date=getToday("%d-%b-%Y")):
    url = I3_INSIDER_DIRECTOR_URL
    latest_dir = scrape_latest(connect_url(url), url, trading_date)
    if S.DBG_INSIDER:
        for i in latest_dir:
            print i
    format_table("Latest Director Transactions", latest_dir)
    url = I3_INSIDER_SHAREHOLDER_URL
    latest_shd = scrape_latest(connect_url(url), url, trading_date)
    format_table("Latest Substantial Shareholders Transactions", latest_shd)
    url = I3_INSIDER_COMPANY_URL
    latest_company = scrape_latest(connect_url(url), url, trading_date)
    format_table("Latest Company Transactions", latest_company)
    return latest_dir, latest_shd, latest_company


def scrape_latest(soup, url, trading_date):
    if soup is None:
        print ('Insider ERR: no result for <' + url + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + url + '>')
        return None
    insiders = []
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
                if S.DBG_ALL or S.DBG_INSIDER:
                    print("%s, %s, %s, %s, %s, %s, %s, %s, %s" %
                          (stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total))
            ann_date = change2KlseDateFmt(announce_date, "%d-%b-%Y")
            trd_date = change2KlseDateFmt(trading_date, "%d-%b-%Y")
            if S.DBG_QR:
                print("DBG:dates:{0}:{1}".format(ann_date, trd_date))
            if ann_date >= trd_date:
                if len(insider) == 11:
                    insiders.append(format_insider(stock, announce_date, name, chg_date, chg_type, shares, price, view))
                else:
                    insiders.append(format_company(stock, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total, view))
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


def format_insider(counter, announce_date, name, dt, notice, shares, price, view):
    td_str = "<tr>"
    td_str += "<td>{}</td>\n".format(counter)
    td_str += "<td>{}</td>\n".format(announce_date)
    td_str += "<td>{}</td>\n".format(name)
    td_str += "<td>{}</td>\n".format(dt)
    td_str += "<td>{}</td>\n".format(notice)
    td_str += "<td>{}</td>\n".format(shares)
    td_str += "<td>{}</td>\n".format(price)
    link = '<a href="{}">{}</a>'.format(view, "link")
    td_str += ('<td>{}</td>\n'.format(link))
    td_str += "</tr>"
    return td_str


def format_company(counter, announce_date, from_date, to_date, chg_type, shares, min_price, max_price, total, view):
    td_str = "<tr>"
    td_str += "<td>{}</td>\n".format(counter)
    td_str += "<td>{}</td>\n".format(announce_date)
    td_str += "<td>{}</td>\n".format(from_date)
    td_str += "<td>{}</td>\n".format(to_date)
    td_str += "<td>{}</td>\n".format(chg_type)
    td_str += "<td>{}</td>\n".format(shares)
    td_str += "<td>{}</td>\n".format(min_price)
    td_str += "<td>{}</td>\n".format(max_price)
    link = '<a href="{}">{}</a>'.format(view, "link")
    td_str += ('<td>{}</td>\n'.format(link))
    td_str += "</tr>"
    return td_str


def format_table(table_title, insider_list):
    if "Company" in table_title:
        table_heading = '<table class="browserref notranslate" style=\"width:100%\">\n'
        table_heading += "<tr>\n"
        table_heading += "<th>Stock</th>\n"
        table_heading += "<th>Ann.Date</th>\n"
        table_heading += "<th>From</th>\n"
        table_heading += "<th>To</th>\n"
        table_heading += "<th>Type</th>\n"
        table_heading += "<th>No. of Shares</th>\n"
        table_heading += "<th>Min Price</th>\n"
        table_heading += "<th>Max Price</th>\n"
        table_heading += "<th>Total</th>\n"
        table_heading += "<th>View</th>\n"
        table_heading += "</tr>\n"
        insider_list.insert(0, table_heading)
    else:
        table_heading = '<table \"browserref notranslate\" style=\"width:100%\">\n'
        table_heading += "<tr>\n"
        table_heading += "<th>Stock</th>\n"
        table_heading += "<th>Ann.Date</th>\n"
        table_heading += "<th>Name</th>\n"
        table_heading += "<th>Date</th>\n"
        table_heading += "<th>Notice</th>\n"
        table_heading += "<th>No. of Shares</th>\n"
        table_heading += "<th>Price</th>\n"
        table_heading += "<th>View</th>\n"
        table_heading += "</tr>\n"
        insider_list.insert(0, table_heading)
    insider_list.insert(0, "<h2>{}</h2>".format(table_title))
    insider_list.append("</table>\n")
