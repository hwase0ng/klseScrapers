import settings as S
from common import connect_url
from utils.dateutils import change2KlseDateFmt, getToday

I3_LATEST_AR_URL = S.I3_KLSE_URL + '/financial/annual/latest.jsp'


def crawl_latest_ar(trading_date=getToday("%d-%b-%Y")):
    return scrape_latest_ar(connect_url(I3_LATEST_AR_URL), trading_date)


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
            [stock, fy, ann_date, announcementDate, latest_ann] = unpack_latest_ar(*latestAR)
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
                    ar_list[stock] = [fy, ann_date, announcementDate, latest_ann, jsp_link]
                else:
                    print ("INFO: Duplicated announcement: " + stock + ":" + latest_ann + ":" + announcementDate)
            else:
                ann_dt = change2KlseDateFmt(announcementDate, "%d-%b-%Y")
                trd_dt = change2KlseDateFmt(trading_date, "%d-%b-%Y")
                if S.DBG_QR:
                    print("DBG:dates:{0}:{1}".format(ann_dt, trd_dt))
                if ann_dt < trd_dt:
                    break
    return ar_list


def unpack_latest_ar(stock, fy, ann_date, announce_date, latest_ann, view):
    if S.DBG_QR:
        print "DBG:{0},{1},{2},{3},{4}".format(
            stock, fy, ann_date, announce_date, latest_ann)
    return [stock, fy, ann_date, announce_date, latest_ann]


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
                        f_name = link.getText().replace('&nbsp;', '')
                        pdf_links[S.I3_KLSE_URL + pdf_link] = f_name.strip()
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
