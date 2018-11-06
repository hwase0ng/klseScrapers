'''
Created on Oct 27, 2018

@author: hwase
'''

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


def teststats():
    load_mvp_args()
    dflist, title, fname, lastTrxnDate, lastClosingPrice = \
        getSynopsisDFs("DUFU", "", 300)
    dflist[1].describe()


if __name__ == '__main__':
    cfg = loadCfg(S.DATA_DIR)
    # testmatch()
    teststdev()
