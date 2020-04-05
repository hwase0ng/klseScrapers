import settings as S
from common import connect_url
from utils.dateutils import change2KlseDateFmt, getToday

I3_LATEST_AR_URL = S.I3_KLSE_URL + '/financial/annual/latest.jsp'


def crawl_latest_ar(trading_date=getToday("%d-%b-%Y")):
    latestAR = scrape_latest_ar(connect_url(I3_LATEST_AR_URL), trading_date)
    return latestAR


def scrape_latest_ar(soup, trading_date):
    if soup is None or len(soup) <= 0:
        print ('LatestAR ERR: no result')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No Latest AR data is available')
        return None
    ar_list = {}
    for tr in table.findAll('tr'):
        td = tr.findAll('td')
        latestAR = [x.text.strip().replace('&nbsp; ', '').encode("ascii") for x in td]
        # latestAR = [printable(x.text.encode("ascii").replace('&nbsp;', '')).strip() for x in td]
        if S.DBG_QR:
            print("DBG:")
            for x in latestAR:
                print repr(x)
        if len(latestAR) > 0:
            [stock, fy, anndate, announcementDate, latestann] = unpack_latest_ar(*latestAR)
            if announcementDate == trading_date:
                if stock not in ar_list:
                    links = tr.findAll('a')
                    jsp_link = ""
                    for link in links:
                        jsp_link = link.get('href')
                        if "annual" in jsp_link:
                            jsp_link = get_yoy_links(jsp_link)
                            if len(jsp_link) > 0:
                                break
                    ar_list[stock] = [fy, anndate, announcementDate, latestann, jsp_link]
                else:
                    print ("INFO: Duplicated announcement: " + stock + ":" + latestann + ":" + announcementDate)
            else:
                anndt = change2KlseDateFmt(announcementDate, "%d-%b-%Y")
                trddt = change2KlseDateFmt(trading_date, "%d-%b-%Y")
                if S.DBG_QR:
                    print("DBG:dates:{0}:{1}".format(anndt, trddt))
                if anndt < trddt:
                    break
    return ar_list


def unpack_latest_ar(stock, fy, anndate, announce_date, latestann, view):
    if S.DBG_QR:
        print "DBG:{0},{1},{2},{3},{4}".format(
            stock, fy, anndate, announce_date, latestann)
    return [stock, fy, anndate, announce_date, latestann]


def get_yoy_links(jsp_link):
    soupQR = connect_url(S.I3_KLSE_URL + jsp_link)
    if soupQR is None or len(soupQR) <= 0:
        print ('getYoYLinks ERR: no result')
        return None
    divs = soupQR.find("div", {"id": "container"})
    div = divs.find("div", {"id": "content"})
    tables = div.findAll('table')
    pdf_links = {}
    found = False
    for table in tables:
        for tr in table.findAll('tr'):
            for td in tr.findAll('td'):
                links = td.findAll('a')
                for link in links:
                    pdf_link = link.get('href')
                    if pdf_link is None:
                        continue
                    if "staticfile" in pdf_link:
                        found = True
                        fname = link.getText().replace('&nbsp;', '')
                        pdf_links[S.I3_KLSE_URL + pdf_link] = fname.strip()
                    else:
                        if found:
                            break
                if found:
                    break
            if found:
                break
        if found:
            break
    return pdf_links


def format_latest_ar(counter, fy, anndate, announcementDate, latestann, view):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s" %
              (counter, fy, anndate, announcementDate, latestann))
    tdstr = "<tr>"
    tdstr += "<td>{}</td>\n".format(counter)
    tdstr += "<td>{}</td>\n".format(fy)
    tdstr += "<td>{}</td>\n".format(anndate)
    tdstr += "<td>{}</td>\n".format(announcementDate)
    tdstr += "<td>{}</td>\n".format(latestann)
    tdstr += "<td>"
    for link in view:
        pdf_name = view[link].strip()
        link = link.strip()
        pdf_link = '<li><a href="{}">{}</a></li>'.format(link, pdf_name)
        tdstr += ('{}\n'.format(pdf_link))
        # td_str += '\n\tlink=' + pdf_link
    tdstr += "</td>"
    tdstr += "</tr>"
    return tdstr
