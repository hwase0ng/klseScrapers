'''
Created on Oct 24, 2018

@author: hwase
'''

from analytics.mvpchart import dfLoadMPV, getMpvDate
from common import loadCfg, FifoDict
import numpy as np
import operator
import peakutils.peak
import settings as S


def match_approximate(a, b):
    c, d = [], []
    bEnd = False
    bfifo = FifoDict()
    for i in b:
        bfifo.append(i)
    y = 0
    for x in a:
        if bEnd:
            continue
        while True:
            if y == 0 or x - y > 3:
                try:
                    y = bfifo.pop()
                except KeyError:
                    bEnd = True
                    break
            if abs(x - y) <= 3:
                c.append(x)
                d.append(y)
                break
            if y > x:
                break
    return c, d


vector = [0, 6, 25, 20, 15, 8, 15, 6, 0, 6, 0, -5, -15, -3, 4,
          10, 8, 13, 8, 10, 3, 1, 20, 7, 3, 0]
print('Detect peaks with minimum height and distance filters.')

cfg = loadCfg(S.DATA_DIR)
df, _, _ = dfLoadMPV("KLSE")
cvector = df['close']
cindexes = peakutils.peak.indexes(np.array(cvector), thres=7.0 / max(cvector), min_dist=5)
print('C Peaks are: %s' % (cindexes))
mvector = df['M']
mindexes = peakutils.peak.indexes(np.array(mvector), thres=7.0 / max(mvector), min_dist=5)
print('M Peaks are: %s' % (mindexes))
for i in mindexes[:3]:
    print i, mvector[i], df['M'][i], getMpvDate(df['date'][i])
ppeak = df.iloc[df['P'].idxmax()]['P']
print ppeak
pvector = df['P']
pindexes = peakutils.peak.indexes(np.array(pvector), thres=(ppeak / 2) / max(pvector), min_dist=5)
print('P Peaks are: %s' % (pindexes))
vvector = df['V']
vindexes = peakutils.peak.indexes(np.array(vvector), thres=5.0 / max(vvector), min_dist=5)
print('V Peaks are: %s' % (vindexes))

clen, mlen, plen, vlen = len(cindexes), len(mindexes), len(pindexes), len(vindexes)
cmpvindexes = {'C': cindexes, 'M': mindexes, 'P': pindexes, 'V': vindexes}
cmpvcount = {'C': clen, 'M': mlen, 'P': plen, 'V': vlen}
cmpvlist = sorted(cmpvcount.items(), key=operator.itemgetter(1), reverse=True)
print cmpvlist
cmpvlines = {}
for i in range(len(cmpvlist) - 1):
    for j in range(i + 1, len(cmpvlist) - 1):
        print i, j, cmpvlist[i][0], cmpvlist[j][0]
        a, b = cmpvindexes[cmpvlist[i][0]], cmpvindexes[cmpvlist[j][0]]
        # test = [x for x in a if (abs(x - b) < 3) in b]
        c, d = match_approximate(a, b)
        print "***"
        print a
        print b
        print c
        print d
        print "***"
        cmpvlines[cmpvlist[i][0] + cmpvlist[j][0]] = \
            np.in1d(cmpvindexes[cmpvlist[i][0]], cmpvindexes[cmpvlist[j][0]])
print len(cmpvlines)
print cmpvlines
'''
for k, v in cmpvlines.iteritems():
    print sum(val for val in v)
    print v
    items = np.nonzero(v)[0]
    for i, j in enumerate(items):
        if k[0] == 'C':
            print i, j, cindexes[i]
        if k[0] == 'P':
            print i, j, pindexes[i]
        if k[0] == 'M':
            print i, j, pindexes[i]
cm = np.in1d(cindexes, mindexes) if clen >= mlen else np.in1d(mindexes, cindexes)
print cm
cp = np.in1d(cindexes, pindexes) if clen >= plen else np.in1d(pindexes, cindexes)
print cp
'''
