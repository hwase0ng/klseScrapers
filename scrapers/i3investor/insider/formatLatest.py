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
    if "Company" in table_title:
        table_heading = '<table id="t01">'
        table_heading += "<tr>"
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
        table_heading += "</tr>"
        insider_list.insert(0, table_heading)
    else:
        table_heading = '<table id="t01">'
        table_heading += "<tr>"
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
    insider_list.insert(0, "<h2>{}</h2>".format(table_title))
    insider_list.insert(0, "<body>")
    insider_list.insert(0, "<html>")
    insider_list.insert(0, "<!DOCTYPE html>")
    insider_list.append("</table>")
    insider_list.append("</body>")
    insider_list.append("</html>")


def format_ar_qr(htext, item, tracking):
    if htext == "Latest AR":
        htext = '<table id="t01" style=\"width:100%\">'
        htext += "<tr>"
        htext += "<th>Stock</th>"
        htext += "<th>Finance year</th>"
        htext += "<th>Audited Anniverary Date</th>"
        htext += "<th>AR Anniverary Date</th>"
        htext += "<th>Latest Anniverary Date</th>"
        htext += "<th>PDF</th>"
        htext += "</tr>"
        item.insert(0, htext)
    elif htext == "Latest QR":
        htext = '<table id="t01" style=\"width:100%\">'
        htext += "<tr>"
        htext += "<th>Stock</th>"
        htext += "<th>Announcement Date</th>"
        htext += "<th>Quarter</th>"
        htext += "<th>Q#</th>"
        htext += "<th>Revenue</th>"
        htext += "<th>PBT</th>"
        htext += "<th>NP</th>"
        htext += "<th>DIV</th>"
        htext += "<th>ROE</th>"
        htext += "<th>EPS</th>"
        htext += "<th>DPS</th>"
        htext += "<th>QoQ</th>"
        htext += "<th>YoY</th>"
        htext += "<th>PDF</th>"
        htext += "</tr>"
        item.insert(0, htext)
    else:
        htext = '<table id="t01" style=\"width:100%\">'
        htext += "<tr>"
        htext += "<th>Stock</th>"
        htext += "<th>Name</th>"
        htext += "<th>Date</th>"
        htext += "<th>Notice</th>"
        htext += "<th>No. of Shares</th>"
        htext += "<th>Price</th>"
        htext += "<th>View</th>"
        htext += "</tr>"
        item.insert(0, htext)
    item.insert(0, T.t01)
    item.insert(0, "")
    header = "<h2>{}</h2>".format(tracking.upper())
    item.insert(0, header)
    item.append("</table>")
