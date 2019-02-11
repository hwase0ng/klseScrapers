'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to patch

Created on Feb 11, 2019

@author: hwase0ng
'''
import settings as S
from common import loadCfg
from docopt import docopt
from utils.fileutils import mergecsv


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)

    if not args['COUNTER']:
        print "Usage: patchcsv <counter>"
    else:
        counter = args['COUNTER'][0].upper()
        mergecsv(counter, S.DATA_DIR)
