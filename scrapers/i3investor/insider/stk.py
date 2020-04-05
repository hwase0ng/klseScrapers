import settings as S
from common import printable, connect_url, formStocklist

I3_INSIDER_DIRECTOR_URL = S.I3_KLSE_URL + '/servlets/stk/annchdr/'
I3_INSIDER_SHAREHOLDER_URL = S.I3_KLSE_URL + '/servlets/stk/annchsh/'


def crawl_insider(counter, trading_date):
    stk_list = formStocklist(counter, S.KLSE_LIST)
    dirUrl = I3_INSIDER_DIRECTOR_URL + stk_list[counter] + ".jsp"
    shdUrl = I3_INSIDER_SHAREHOLDER_URL + stk_list[counter] + ".jsp"
    if S.DBG_ALL or S.DBG_INSIDER:
        print ("\tInsider: " + counter + " " + stk_list[counter] + " " + dirUrl)
    dirList = scrape_insider(counter, stk_list[counter], connect_url(dirUrl), trading_date)
    if S.DBG_ALL or S.DBG_INSIDER:
        print ("\tInsider: " + counter + " " + stk_list[counter] + " " + shdUrl)
    shdList = scrape_insider(counter, stk_list[counter], connect_url(shdUrl), trading_date)
    return dirList, shdList


def unpack_insider_td(anndt, name, dt, notice, shares, price, direct, indirect, total, view):
    """
    Sample table:
    <tr role="row" class="odd">
        <td class="center sorting_2" nowrap="nowrap">24-May-2019</td>
        <td class="left sorting_3">  YAYASAN GURU TUN HUSSEIN ONN  </td>
        <td class="center sorting_1" nowrap="nowrap">16-May-2019</td>
        <td class="center sorting_3" width="80px"> <span class="up">Notice of Interest</span> </td>
        <td class="right" nowrap="nowrap"> <span class="up">6,000,000</span> </td>
        <td class="center" nowrap="nowrap">0.000</td>
        <td class="right" nowrap="nowrap">5.92</td>
        <td class="right" nowrap="nowrap">0.00</td>
        <td class="right" nowrap="nowrap">5.92</td>
        <td class="center" nowrap="nowrap"> <a href="/insider/substantialShareholderNoticeOfInterest/5276/24-May-2019/13035_1229846127.jsp" title="View Detail" target="_blank"> <img class="sp view16" src="//cdn1.i3investor.com/cm/icon/trans16.gif" alt="View Detail"> </a> </td>
    </tr>
    return anndt, name, dt, notice, int(shares.replace(',', '')), float(price), \
    """
    if S.DBG_INSIDER:
        print "DBG:{0},{1},{2},{3},{4},{5},{6},{7},{8}".format(
            anndt, name, dt, notice, shares, price, direct, indirect, total)
    return anndt, name, dt, notice, shares, price, direct, indirect, total


def scrape_insider(counter, stk_code, soup, last_date, show_latest=False):
    if soup is None or len(soup) <= 0:
        print ('Insider ERR: no result for <' + counter + '>')
        return None
    table = soup.find('table', {'class': 'nc'})
    if table is None:
        if S.DBG_ALL:
            print ('INFO: No insider data is available for <' + counter + "." + stk_code + '>')
        return None
    insiders = []
    count = 0
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
        if len(insider) == 10:
            anndt, name, dt, notice, shares, price, direct, indirect, total = unpack_insider_td(*insider)
            view = S.I3_KLSE_URL + td[9].find('a').get('href').encode("ascii")
            if S.DBG_ALL or S.DBG_INSIDER:
                # print("%s, %s, %s, %s, %s, %s, %.2f, %.2f, %.2f, %.2f, %s" %
                print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
                      (counter, anndt, name, dt, notice, shares, price, direct, indirect, total, view))
            # tdstr = counter + ", " + name + ", " + dt + ", " + notice + ", " + shares + ", " + price + ", " + view
            if dt != last_date:
                if show_latest:
                    if S.DBG_ALL or S.DBG_INSIDER:
                        print("%s, %s, %s, %s, %s, %s, %f, %f, %f, %f, %s" %
                              (counter, anndt, name, dt, notice, shares, price, direct, indirect, total, view))
                    # insiders.append(tdstr)
                    insiders.append(format_insider(counter, name, dt, notice, shares, price, view))
                count += 1
                if count > 9:
                    break
                continue
            else:
                insiders.append(format_insider(counter, name, dt, notice, shares, price, view))
    return insiders


def format_insider(counter, name, dt, notice, shares, price, view):
    tdstr = "<tr>"
    tdstr += "<td>{}</td>\n".format(counter)
    tdstr += "<td>{}</td>\n".format(name)
    tdstr += "<td>{}</td>\n".format(dt)
    tdstr += "<td>{}</td>\n".format(notice)
    tdstr += "<td>{}</td>\n".format(shares)
    tdstr += "<td>{}</td>\n".format(price)
    link = '<a href="{}">{}</a>'.format(view, "link")
    tdstr += ('<td>{}</td>\n'.format(link))
    tdstr += "</tr>"
    return tdstr
