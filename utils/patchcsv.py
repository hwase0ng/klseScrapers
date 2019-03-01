'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to patch

Created on Feb 11, 2019

@author: hwase0ng
'''
import settings as S
from common import loadCfg, loadKlseCounters
from docopt import docopt
from utils.fileutils import mergecsv


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    klse = "scrapers/i3investor/klse.txt"
    stocklist = {}
    scode = "0000"

    if args['COUNTER']:
        counter = args['COUNTER'][0].upper()
        if len(args['COUNTER']) > 1:
            scode = args['COUNTER'][1]
        stocklist[counter] = scode
    else:
        print "Usage: patchcsv [counter] [scode]"
        stocklist = loadKlseCounters(klse)

    for counter in sorted(stocklist.iterkeys()):
        if counter in S.EXCLUDE_LIST:
            print "INF:Skip: ", counter
            continue
        mergecsv(counter, S.DATA_DIR, scode)
