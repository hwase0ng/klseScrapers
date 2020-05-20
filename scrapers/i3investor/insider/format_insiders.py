import settings as S
import styles as T


def format_director(formatted_output, counter, announce_date, name, dt, notice, shares, price, view):
    return format_insider(formatted_output, True, counter, announce_date, name, dt, notice, shares, price, view)


def format_shareholder(formatted_output, counter, announce_date, name, dt, notice, shares, view):
    return format_insider(formatted_output, False, counter, announce_date, name, dt, notice, shares, "", view)


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


def format_table_insiders(table_title, insider_list):
    if len(insider_list) <= 0:
        return
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
    format_table(table_title, insider_list, table_heading)


def format_ar_table(title, financial_list):
    if len(financial_list) <= 0:
        return
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    table_heading += "<th>Stock</th>"
    table_heading += "<th>Finance year</th>"
    table_heading += "<th>Audited Anniversary Date</th>"
    table_heading += "<th>AR Anniversary Date</th>"
    table_heading += "<th>Latest Anniversary Date</th>"
    table_heading += "<th>PDF</th>"
    table_heading += "</tr>"
    format_table(title, financial_list, table_heading)


def format_qr_table(title, financial_list):
    if len(financial_list) <= 0:
        return
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
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
    format_table(title, financial_list, table_heading)


def format_latest_ar(counter, fy, ann_date, announce_date, latest_ann, view):
    if S.DBG_ALL or S.DBG_QR:
        print("%s, %s, %s, %s, %s" %
              (counter, fy, ann_date, announce_date, latest_ann))
    td_str = "<tr>"
    td_str += "<td>{}</td>".format(counter)
    td_str += "<td>{}</td>".format(fy)
    td_str += "<td>{}</td>".format(ann_date)
    td_str += "<td>{}</td>".format(announce_date)
    td_str += "<td>{}</td>".format(latest_ann)
    td_str += "<td>"
    for link in view:
        pdf_name = view[link].strip()
        link = link.strip()
        pdf_link = '<li><a href="{}">{}</a></li>'.format(link, pdf_name)
        td_str += ('{}'.format(pdf_link))
        # td_str += '\n\tlink=' + pdf_link
    td_str += "</td>"
    td_str += "</tr>"
    return td_str


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


def format_div(formatted_output, others,
               announce_date, stock, open_price,
               current_price, dividend_ratio, ex_date, view):
    return format_dividend(formatted_output, others,
                           announce_date, stock, "", open_price,
                           current_price,dividend_ratio, ex_date, view)


def format_dividend(formatted_output, others,
                    announce_date, stock, subject, open_price,
                    current_price, dividend_ratio, ex_date, view):
    if formatted_output:
        td_str = "<tr>"
        td_str += "<td>{}</td>".format(announce_date)
        td_str += "<td>{}</td>".format(stock)
        if others:
            td_str += "<td>{}</td>".format(subject)
        td_str += "<td>{}</td>".format(open_price)
        td_str += "<td>{}</td>".format(current_price)
        td_str += "<td>{}</td>".format(dividend_ratio)
        td_str += "<td>{}</td>".format(ex_date)
        link = '<a href="{}">{}</a>'.format(view, "link")
        td_str += ('<td>{}</td>'.format(link))
        td_str += "</tr>"
    else:
        if others:
            td_str = [announce_date, stock, subject, open_price, current_price, dividend_ratio, ex_date, view]
        else:
            td_str = [announce_date, stock, open_price, current_price, dividend_ratio, ex_date, view]
    return td_str


def format_table_entitlement(table_title, entitle_list):
    if len(entitle_list) <= 0:
        return entitle_list
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    table_heading += "<th>Ann.Date</th>"
    table_heading += "<th>Stock</th>"
    if "Dividend" not in table_title:
        table_heading += "<th>Subject</th>"
    table_heading += "<th>Opening Price</th>"
    table_heading += "<th>Current Price</th>"
    if "Dividend" in table_title:
        table_heading += "<th>Dividend</th>"
    else:
        table_heading += "<th>Ratio</th>"
    table_heading += "<th>Ex Date</th>"
    table_heading += "<th>View</th>"
    table_heading += "</tr>"
    format_table(table_title, entitle_list, table_heading)


def format_listing(formatted_output,
                   stock, announce_date, listing_date, list_type, units, price, view):
    if formatted_output:
        td_str = "<tr>"
        td_str += "<td>{}</td>".format(stock)
        td_str += "<td>{}</td>".format(announce_date)
        td_str += "<td>{}</td>".format(listing_date)
        td_str += "<td>{}</td>".format(list_type)
        td_str += "<td>{}</td>".format(units)
        td_str += "<td>{}</td>".format(price)
        link = '<a href="{}">{}</a>'.format(view, "link")
        td_str += ('<td>{}</td>'.format(link))
        td_str += "</tr>"
    else:
        td_str = [stock, announce_date, listing_date, list_type, units, price, view]
    return td_str


def format_table_listing(table_title, listing_list):
    if len(listing_list) <= 0:
        return
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    table_heading += "<th>Stock</th>"
    table_heading += "<th>Ann.Date</th>"
    table_heading += "<th>Date</th>"
    table_heading += "<th>Type</th>"
    table_heading += "<th>Units</th>"
    table_heading += "<th>Price</th>"
    table_heading += "<th>View</th>"
    table_heading += "</tr>"
    format_table(table_title, listing_list, table_heading)


def format_target(formatted_output,
                  announce_date, stock, last_price, target, upside_down, call, source):
    if formatted_output:
        td_str = "<tr>"
        td_str += "<td>{}</td>".format(stock)
        td_str += "<td>{}</td>".format(announce_date)
        td_str += "<td>{}</td>".format(last_price)
        td_str += "<td>{}</td>".format(target)
        td_str += "<td>{}</td>".format(upside_down)
        td_str += "<td>{}</td>".format(call)
        td_str += "<td>{}</td>".format(source)
        td_str += "</tr>"
    else:
        td_str = [announce_date, stock, last_price, target, upside_down, call, source]
    return td_str


def format_table_target(table_title, target_list):
    if len(target_list) <= 0:
        return
    table_heading = '<table id="t01" style=\"width:100%\">'
    table_heading += "<tr>"
    table_heading += "<th>Ann.Date</th>"
    table_heading += "<th>Stock</th>"
    table_heading += "<th>Last Price</th>"
    table_heading += "<th>Target</th>"
    table_heading += "<th>Upside/Downside</th>"
    table_heading += "<th>Price Call</th>"
    table_heading += "<th>Source</th>"
    table_heading += "</tr>"
    format_table(table_title, target_list, table_heading)


def format_table(table_title, table_list, table_head):
    table_list.insert(0, table_head)
    table_list.insert(0, T.browserref)
    table_list.insert(0, "<h2>{}</h2>".format(table_title))
    table_list.insert(0, "<body>")
    table_list.insert(0, "<html>")
    table_list.insert(0, "<!DOCTYPE html>")
    table_list.append("</table>")
    table_list.append("</body>")
    table_list.append("</html>")
