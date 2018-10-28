'''
Created on Oct 27, 2018

@author: hwase
'''

import timeit
from common import match_approximate, match_approximate2

list1 = [7, 22, 34, 49, 56, 62, 76, 82, 89, 149, 161, 182]
list2 = [7, 14, 49, 57, 66, 76, 135, 142, 161]


if __name__ == '__main__':
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
