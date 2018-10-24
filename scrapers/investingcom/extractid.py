'''
Usage: main [URL]

Arguments:
    URL           investing.com URL where id is to be extracted

Created on Oct 24, 2018

@author: hwase0ng
'''

import settings as S
import re
import requests
from bs4 import BeautifulSoup
from docopt import docopt


def extractIDs(url):
    r = requests.get(url, headers=S.HEADERS)
    if S.DBG_ALL:
        print r.status_code
        print r.content
    soup = BeautifulSoup(r.content, 'html.parser')
    pairid = findID(soup, "pairId")
    smlid = findID(soup, "smlId")
    return pairid, smlid


def findID(soup, pattern):
    pattern = re.compile(r"{}: (\d+)".format(pattern))
    script = soup.find('script', text=pattern)
    if S.DBG_ALL:
        print type(script), script

    match = pattern.search(script.text)
    if match:
        if S.DBG_ALL:
            print(match.group(1))
        return int(match.group(1))

    return None


if __name__ == '__main__':
    args = docopt(__doc__)
    if args['URL']:
        url = args['URL']
    else:
        url = 'https://www.investing.com/indices/ftse-malaysia-klci-historical-data'
    url2 = url.split("/")
    print url2[-1], extractIDs(url)
