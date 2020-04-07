import settings as S
import styles as T


def format_insider(formatted_output, director, counter, announce_date, name, dt, notice, shares, price, view):
    if formatted_output:
        td_str = "<tr>"
        td_str += "<td>{}</td>".format(counter)
        td_str += "<td>{}</td>".format(announce_date)
        td_str += "<td>{}</td>".format(name)
        td_str += "<td>{}</td>".format(dt)
        td_str += "<td>{}</td>".format(notice)
        td_str += "<td>{}</td>".format(shares)
        if director:
            td_str += "<td>{}</td>".format(price)
        link = '<a href="{}">{}</a>'.format(view, "link")
        td_str += ('<td>{}</td>'.format(link))
        td_str += "</tr>"
    else:
        if True:
            if director:
                td_str = [counter, announce_date, name, dt, notice, shares, price, view]
            else:
                td_str = [counter, announce_date, name, dt, notice, shares, view]
        else:
            if director:
                td_str = "{},{},{},{},{},{},{},{}".format(counter, announce_date, name,
                                                          dt, notice, shares, price, view)
            else:
                td_str = "{},{},{},{},{},{},{}".format(counter, announce_date, name,
                                                       dt, notice, shares, view)
    return td_str


def format_company(formatted_output, counter, announce_date, from_date, to_date, chg_type,
                   shares, min_price, max_price, total, view):
    if formatted_output:
        td_str = "<tr>"
        td_str += "<td>{}</td>".format(counter)
        td_str += "<td>{}</td>".format(announce_date)
        td_str += "<td>{}</td>".format(from_date)
        td_str += "<td>{}</td>".format(to_date)
        td_str += "<td>{}</td>".format(chg_type)
        td_str += "<td>{}</td>".format(shares)
        td_str += "<td>{}</td>".format(min_price)
        td_str += "<td>{}</td>".format(max_price)
        td_str += "<td>{}</td>".format(total)
        link = '<a href="{}">{}</a>'.format(view, "link")
        td_str += ('<td>{}</td>'.format(link))
        td_str += "</tr>"
    else:
        if True:
            td_str = [counter, announce_date, from_date, to_date,
                      chg_type, shares, min_price, max_price, total, view]
        else:
            td_str = "{},{},{},{},{},{},{},{},{},{}".format(
                counter, announce_date, from_date, to_date,
                chg_type, shares, min_price, max_price, total, view)
    return td_str


def format_table(table_title, insider_list):
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    if "Company" in table_title:
        table_heading += "<th>Stock</th>"
        table_heading += "<th>Ann.Date</th>"
        table_heading += "<th>From</th>"
        table_heading += "<th>To</th>"
        table_heading += "<th>Type</th>"
        table_heading += "<th>No. of Shares</th>"
        table_heading += "<th>Min Price</th>"
        table_heading += "<th>Max Price</th>"
        table_heading += "<th>Total</th>"
        table_heading += "<th>View</th>"
    else:
        table_heading += "<th>Stock</th>"
        table_heading += "<th>Ann.Date</th>"
        table_heading += "<th>Name</th>"
        table_heading += "<th>Date</th>"
        table_heading += "<th>Notice</th>"
        table_heading += "<th>No. of Shares</th>"
        if "Directors" in table_title:
            table_heading += "<th>Price</th>"
        table_heading += "<th>View</th>"
    table_heading += "</tr>"
    insider_list.insert(0, table_heading)
    insider_list.insert(0, T.browserref)
    insider_list.insert(0, "<h2>{}</h2>".format(table_title))
    insider_list.insert(0, "<body>")
    insider_list.insert(0, "<html>")
    insider_list.insert(0, "<!DOCTYPE html>")
    insider_list.append("</table>")
    insider_list.append("</body>")
    insider_list.append("</html>")


def format_ar_qr_table(title, item):
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    if title == "Annual Results":
        table_heading += "<th>Stock</th>"
        table_heading += "<th>Finance year</th>"
        table_heading += "<th>Audited Anniversary Date</th>"
        table_heading += "<th>AR Anniversary Date</th>"
        table_heading += "<th>Latest Anniversary Date</th>"
        table_heading += "<th>PDF</th>"
    else:
        table_heading += "<th>Stock</th>"
        table_heading += "<th>Announcement Date</th>"
        table_heading += "<th>Quarter</th>"
        table_heading += "<th>Q#</th>"
        table_heading += "<th>Revenue</th>"
        table_heading += "<th>PBT</th>"
        table_heading += "<th>NP</th>"
        table_heading += "<th>DIV</th>"
        table_heading += "<th>ROE</th>"
        table_heading += "<th>EPS</th>"
        table_heading += "<th>DPS</th>"
        table_heading += "<th>QoQ</th>"
        table_heading += "<th>YoY</th>"
        table_heading += "<th>PDF</th>"
    table_heading += "</tr>"
    item.insert(0, table_heading)
    item.insert(0, T.browserref)
    item.insert(0, "<h2>{}</h2>".format(title))
    item.insert(0, "<body>")
    item.insert(0, "<html>")
    item.insert(0, "<!DOCTYPE html>")
    item.append("</table>")
    item.append("</body>")
    item.append("</html>")


def format_latest_ar(counter, fy, anndate, announcementDate, latestann, view):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s" %
              (counter, fy, anndate, announcementDate, latestann))
    tdstr = "<tr>"
    tdstr += "<td>{}</td>".format(counter)
    tdstr += "<td>{}</td>".format(fy)
    tdstr += "<td>{}</td>".format(anndate)
    tdstr += "<td>{}</td>".format(announcementDate)
    tdstr += "<td>{}</td>".format(latestann)
    tdstr += "<td>"
    for link in view:
        pdf_name = view[link].strip()
        link = link.strip()
        pdf_link = '<li><a href="{}">{}</a></li>'.format(link, pdf_name)
        tdstr += ('{}'.format(pdf_link))
        # td_str += '\n\tlink=' + pdf_link
    tdstr += "</td>"
    tdstr += "</tr>"
    return tdstr


def format_latest_qr(counter, announcement_date, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy, jsp_link):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" %
              (counter, announcement_date, qd, qn, rev, pbt, np, div, roe, eps, dps, qoq, yoy))
        for link in jsp_link:
            print('\t' + link)
    td_str = "<tr>"
    td_str += "<td>{}</td>".format(counter)
    td_str += "<td>{}</td>".format(announcement_date)
    td_str += "<td>{}</td>".format(qd)
    td_str += "<td>{}</td>".format(qn)
    td_str += "<td>{}</td>".format(rev)
    td_str += "<td>{}</td>".format(pbt)
    td_str += "<td>{}</td>".format(np)
    td_str += "<td>{}</td>".format(div)
    td_str += "<td>{}</td>".format(roe)
    td_str += "<td>{}</td>".format(eps)
    td_str += "<td>{}</td>".format(dps)
    td_str += "<td>{}</td>".format(qoq)
    td_str += "<td>{}</td>".format(yoy)
    td_str += "<td>"
    for link in jsp_link:
        pdf_name = jsp_link[link].strip()
        link = link.strip()
        pdf_link = '<li><a href="{}">{}</a></li>'.format(link, pdf_name)
        td_str += ('{}'.format(pdf_link))
        # td_str += '\n\tlink=' + pdf_link
    td_str += "</td>"
    td_str += "</tr>"
    return td_str
