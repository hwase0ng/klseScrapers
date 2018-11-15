'''
Usage: main [options] [COUNTER] ...

Arguments:
    COUNTER           Counter to display MVP line chart
Options:
    -c,--chartdays=<cd>     Days to display on chart [default: 200]
    -h,--help               This page

Created on Oct 27, 2018

@author: hwase
'''

from docopt import docopt
import pandas as pd
from matplotlib import pyplot as plt
import settings as S
import timeit
from common import match_approximate, match_approximate2, loadCfg
from statistics import stdev
from fractions import Fraction as fr
from analytics.mvpchart import getSynopsisDFs
from analytics.mvp import load_mvp_args

list1 = [7, 22, 34, 49, 56, 62, 76, 82, 89, 149, 161, 182]
list2 = [7, 14, 49, 57, 66, 76, 135, 142, 161]


def testmatch():
    print "match1"
    print min(timeit.Timer("match_approximate(list1, list2)",
                           setup="from __main__ import match_approximate, list1, list2").repeat(100, 1000))
    result = match_approximate(list1, list2, 3)
    print result[0]
    print result[1]
    print "match2"
    print min(timeit.Timer("match_approximate2(list1, list2)",
                           setup="from __main__ import match_approximate2, list1, list2").repeat(100, 1000))
    result = match_approximate2(list1, list2, 3)
    print result[0]
    print result[1]
    print "match3 invert"
    result = match_approximate2(list1, list2, 1, True)
    print result[0]
    print result[1]


def teststdev():
    sample1 = (0.39, 0.51, 0.37, 0.31)
    sample2 = (0.39, 0.51, 0.37, 0.31, 0.4)
    sample3 = (0.8, 0.9, 1, 0.9)
    sample4 = (0.8, 0.9, 1, 0.9, 0.8)
    print("The Standard Deviation of Sample1 is % s" % (stdev(sample1)))
    print("The Standard Deviation of Sample2 is % s" % (stdev(sample2)))
    print("The Standard Deviation of Sample3 is % s" % (stdev(sample3)))
    print("The Standard Deviation of Sample4 is % s" % (stdev(sample4)))


def teststats(counter):
    load_mvp_args()
    with pd.option_context('display.max_columns', 9, 'display.expand_frame_repr', False):
        dflist, title, fname, lasttrxn = getSynopsisDFs(counter, "", 300)
        dfW, dfF, dfM = dflist[0], dflist[1], dflist[2]
        # dfW = dfW[:13]
        print dfW[:5]
        print dfW.describe()
        fig, ax = plt.subplots(6, 1, figsize=(12, 5))
        ax1 = dfW['close'].plot(ax=ax[5], subplots=False, grid=False)

        '''
        dfW_dateC = dfW.groupby(pd.Grouper(freq='M'))
        dfW_dateC.boxplot()
        '''

        dfW = dfW.reset_index()
        dfWdate = dfW['date']
        dfW['date'] = dfW['date'].astype(str)
        print type(dfW['date'][0]), dfW['date'][0]
        dfW_dateC = dfW[['close', 'date']].groupby(dfW['date'].str[:7])
        dfW_dateM = dfW[['M', 'date']].groupby(dfW['date'].str[:7])
        dfW_dateP = dfW[['P', 'date']].groupby(dfW['date'].str[:7])
        dfW_dateV = dfW[['V', 'date']].groupby(dfW['date'].str[:7])
        # dfwc = dfW_dateC.describe().loc[:, (slice(None), ['mean', 'std', 'min', 'max', '25%', '50%', '75%'])]
        dfwc = dfW_dateC.describe().loc[:, (slice(None), ['mean', 'min', 'max'])]
        dfwm = dfW_dateM.describe().loc[:, (slice(None), ['mean', 'min', 'max'])]
        dfwp = dfW_dateP.describe().loc[:, (slice(None), ['mean', 'min', 'max'])]
        dfwv = dfW_dateV.describe().loc[:, (slice(None), ['mean', 'min', 'max'])]
        dfwstdC = dfW_dateC.describe().loc[:, (slice(None), ['std'])]
        dfwstdM = dfW_dateM.describe().loc[:, (slice(None), ['std'])]
        dfwstdP = dfW_dateP.describe().loc[:, (slice(None), ['std'])]
        dfwstdV = dfW_dateV.describe().loc[:, (slice(None), ['std'])]
        '''
        print dfwc[:3]
        dfwc = dfwc.reset_index()
        dfwm = dfwm.reset_index()
        dfwp = dfwp.reset_index()
        dfwv = dfwv.reset_index()
        # dfwc.boxplot()
        '''
        ax2 = dfwc.plot(ax=ax[0], subplots=False, grid=False)
        ax3 = dfwm.plot(ax=ax[1], subplots=False, grid=False)
        ax4 = dfwp.plot(ax=ax[2], subplots=False, grid=False)
        ax5 = dfwv.plot(ax=ax[3], subplots=False, grid=False)
        ax6 = dfwstdC.plot(ax=ax[4], grid=False)
        dfwstdM.plot(ax=ax6, grid=False)
        dfwstdP.plot(ax=ax6, grid=False)
        dfwstdV.plot(ax=ax6, grid=False)
        # dfW.set_index(dfW['date'], drop=True, inplace=True)
        # fig.tight_layout()
        plt.show()
        plt.close()
        '''
        dfwc['diff'] = dfwc['max'] - dfwc['min']
        df = dfwc[['date', 'diff', 'mean', 'std', '25%', '50%', '70%']]
        print dfwm
        print dfwp
        print dfwv
        '''


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = loadCfg(S.DATA_DIR)
    # testmatch()
    chartDays = int(args['--chartdays']) if args['--chartdays'] else S.MVP_CHART_DAYS
    teststats(args['COUNTER'][0].upper())
