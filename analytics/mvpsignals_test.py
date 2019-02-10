
'''
Created on Nov 15, 2018

@author: hwase0ng
'''

from mvpsignals import scanSignals
import pytest
import settings as S
from common import loadCfg
from utils.fileutils import loadfromjson


def setup_module():
    loadCfg(S.DATA_DIR)


def loadjson(counter, cdate):
    sdict = loadfromjson('data', counter, cdate)
    return sdict


@pytest.mark.parametrize("counter,tdate,expected", [
    ("AXREIT", "2018-03-09", "AXREIT,BBS,1.6,0.0.0.0,(c0.m0.p0.v2),(3.3.3.0^9.8.7^0.0.4^1.0.0.o.1),(^),1.22"),
    ("DANCO", "2018-03-08", "DANCO,TSS,-1.-2,0.0.0.0,(c0.m2.p2.v2),(3.4.0.0^4.5.7^0.0.9^0.1.0.r.0),(^),0.39"),
    ("DANCO", "2018-03-22", "DANCO,TSS,-11.-2,0.0.0.0,(c0.m2.p2.v2),(3.4.0.0^4.5.7^0.0.9^0.1.0),(0.0.1^0.2.0),0.37"),
    ("DANCO", "2018-06-22", "DANCO,BBS,1.12,0.0.0.0,(c0.m2.p2.v2),(3.0.0.0^0.7.7^0.0.0^0.2.0.r.1),(^),0.37"),
    ("DUFU", "2014-03-07", "DUFU,BBS,10.1,0.0.0.0,(c0.m3.p2.v2),(3.0.0.0^9.7.0^0.0.0^6.0.0),(0.0.0^1.1.1),0.13"),
    ("F&N", "2014-09-18", "F&N,TSS,-14.1,0.0.0.0,(c0.m1.p0.v2),(3.0.3.2^0.6.8^0.0.0^0.0.0),(0.0.0^0.2.0),16.80"),
    ("F&N", "2014-09-26", "F&N,TSS,-13.1,0.0.0.0,(c0.m0.p0.v2),(3.3.3.2^0.6.8^0.0.0^0.2.0),(0.0.0^0.2.0),16.90"),
    ("F&N", "2014-10-02", "F&N,BBS,11.-1,0.0.0.0,(c0.m2.p0.v2),(3.4.3.2^8.6.8^0.0.0^0.3.0),(0.0.0^0.2.0),16.88"),
    ("F&N", "2014-11-03", "F&N,BBS,14.1,0.0.0.0,(c0.m1.p0.v2),(3.0.3.0^6.6.0^0.5.0^0.3.6),(0.0.0^0.2.0),15.98"),
    ("F&N", "2014-11-04", "F&N,BBS,14.1,0.0.0.0,(c0.m2.p0.v2),(3.0.3.0^6.6.0^0.5.0^0.3.6),(0.0.0^0.2.0),15.98"),
    ("KLSE", "2009-03-18", "KLSE,BBS,1.8,0.0.0.0,(c0.m0.p2.v2),(3.3.0.0^0.0.0^0.0.0^0.0.0.l.2),(^),847.96"),
])
@pytest.mark.lowC
def test_lowC_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


@pytest.mark.parametrize("counter,tdate,expected", [
    ("CARLSBG", "2014-08-04", "CARLSBG,TSS,-26.1,0.0.0.0,(c1.m2.p2.v4),(0.0.0.1^0.0.4^0.0.0^0.0.0),(0.2.0^0.0.0),11.94"),
    ("CARLSBG", "2014-11-04", "CARLSBG,BBS,10.2,0.0.0.0,(c0.m2.p2.v2),(3.0.0.0^4.0.7^0.0.0^0.0.0),(0.0.0^0.2.0),10.82"),
    ("CARLSBG", "2014-12-02", "CARLSBG,BBS,21.2,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^4.0.7^1.0.0^0.0.0),(0.0.0^0.2.1),11.44"),
    ("CARLSBG", "2014-12-11", "CARLSBG,BBS,2.3,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^4.0.7^1.0.0^0.0.0.l.6),(^),11.86"),
    ("CARLSBG", "2015-03-03", "CARLSBG,TSS,-2.-3,0.0.0.0,(c2.m4.p3.v4),(4.1.0.1^0.1.0^1.0.0^0.0.0.s.6),(^),13.16"),
    ("CARLSBG", "2015-04-16", "CARLSBG,TSS,-2.3,0.0.0.0,(c2.m4.p2.v2),(4.1.0.2^0.1.1^1.0.0^0.0.0.s.6),(^),14.40"),
    ("CARLSBG", "2009-07-31", "CARLSBG,TSS,-27.1,0.0.0.0,(c2.m2.p2.v4),(0.0.0.1^4.0.0^1.0.0^0.0.0),(0.0.0^0.1.2),4.64"),
    ("CARLSBG", "2009-07-01", "CARLSBG,BBS,28.3,0.0.0.0,(c2.m2.p2.v0),(0.0.0.3^4.0.0^1.0.0^0.0.0),(0.0.0^0.1.2),3.74"),
    ("DANCO", "2018-09-04", "DANCO,TSS,-2.-1,0.0.0.0,(c2.m2.p4.v2),(4.0.1.0^1.7.1^1.0.0^0.1.0.z.4),(^),0.48"),
    ("DUFU", "2011-12-09", "DUFU,TSS,-28.2,0.0.0.0,(c1.m2.p2.v0),(0.0.2.3^0.7.7^1.0.0^0.1.0),(0.0.2^0.1.1),0.23"),
    ("F&N", "2014-07-02", "F&N,TSS,-25.1,0.0.0.0,(c1.m2.p2.v4),(4.0.0.1^0.4.6^1.0.2^0.0.0),(0.0.0^0.1.0),18.18"),
    ("F&N", "2014-07-24", "F&N,TSS,-27.1,0.0.0.0,(c1.m2.p2.v0),(0.0.0.3^0.6.6^1.0.0^0.1.0),(0.0.0^0.2.0),17.86"),
    ("KESM", "2013-05-13", "KESM,BBS,21.-5,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^0.2.0^1.6.0^0.0.0),(0.0.2^0.2.0),1.80"),
    ("KESM", "2013-09-04", "KESM,BBS,22.2,0.0.0.0,(c1.m0.p2.v1),(0.3.0.0^0.2.0^1.7.0^0.1.0),(0.0.2^0.1.1),1.73"),
    ("PADINI", "2014-03-14", "PADINI,TSS,-23.-1,0.0.0.0,(c2.m3.p4.v4),(0.4.1.1^4.0.7^2.0.0^0.2.0),(0.0.0^0.0.1),1.93"),
    ("PADINI", "2015-04-02", "PADINI,BBS,2.-1,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^6.0.0^0.0.1^0.0.0.m.5),(^),1.44"),
    ("PADINI", "2015-08-04", "PADINI,BBS,28.2,0.0.0.0,(c1.m2.p2.v0),(4.0.0.3^0.0.1^0.0.4^0.1.0),(0.0.0^0.2.1),1.34"),
    ("PADINI", "2015-09-17", "PADINI,BBS,21.-2,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^0.0.1^0.0.4^0.1.0),(0.0.0^0.0.2),1.41"),
    ("PADINI", "2015-10-01", "PADINI,BBS,24.1,0.0.0.0,(c1.m2.p2.v2),(4.2.0.0^1.0.1^0.0.4^0.1.0),(0.0.0^0.0.2),1.40"),
])
@pytest.mark.bottomC
def test_bottomC_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


@pytest.mark.parametrize("counter,tdate,expected", [
    ("CARLSBG", "2011-08-02", "CARLSBG,TSS,-38.1,0.0.0.0,(c3.m2.p2.v0),(0.0.0.3^4.6.8^0.0.0^0.0.0),(0.0.0^0.2.0),7.45"),
    ("CARLSBG", "2011-08-12", "CARLSBG,TSS,-35.3,0.0.0.0,(c3.m2.p0.v3),(0.0.3.0^4.6.0^0.0.0^0.0.0),(0.0.0^0.2.1),6.88"),
    ("CARLSBG", "2011-10-03", "CARLSBG,BBS,35.3,0.0.0.0,(c2.m2.p0.v1),(0.0.3.0^4.6.0^0.0.0^1.0.0),(0.1.0^0.0.1),6.38"),
    ("CARLSBG", "2013-09-04", "CARLSBG,TSS,-33.4,0.0.0.0,(c2.m0.p0.v4),(2.3.3.1^0.4.0^0.0.0^1.0.0),(0.1.0^0.2.0),12.62"),
    ("CARLSBG", "2016-03-02", "CARLSBG,BBS,34.1,0.0.0.0,(c2.m3.p4.v2),(0.0.1.0^4.7.0^2.6.9^0.0.0),(0.0.0^0.2.2),12.62"),
    ("CARLSBG", "2016-04-04", "CARLSBG,BBS,3.-16,0.0.0.0,(c3.m2.p3.v0),(0.0.2.3^0.2.7^2.0.0^0.0.0.s.4),(^),13.94"),
    ("CARLSBG", "2016-05-06", "CARLSBG,BBS,3.3,0.0.0.0,(c2.m1.p0.v2),(0.0.2.0^0.2.7^0.0.0^0.0.0.s.1),(^),12.64"),
    ("CARLSBG", "2016-05-16", "CARLSBG,BBS,3.16,0.0.0.0,(c2.m1.p2.v2),(0.0.2.0^0.2.7^0.0.0^0.0.0.s.1),(^),12.94"),
    ("CARLSBG", "2016-07-05", "CARLSBG,BBS,32.2,0.0.0.0,(c3.m4.p2.v2),(0.1.0.0^8.0.0^0.0.0^0.0.0),(0.0.0^0.0.0),13.72"),
    ("CARLSBG", "2016-12-28", "CARLSBG,BBS,3.9,0.0.0.0,(c3.m2.p2.v2),(0.4.0.0^3.4.1^0.0.0^0.0.6.z.2),(^),13.96"),
    ("CARLSBG", "2018-10-17", "CARLSBG,BBS,3.4,0.0.0.0,(c3.m2.p0.v2),(0.0.3.0^6.4.0^0.0.0^0.0.6.l.1),(^),17.76"),
    ("DUFU", "2013-12-24", "DUFU,TSS,-32.1,0.0.0.0,(c1.m4.p2.v2),(0.1.2.2^7.0.0^1.0.1^5.0.0),(0.0.0^0.1.2),0.13"),
    ("DUFU", "2015-08-06", "DUFU,BBS,31.2,0.0.0.0,(c2.m2.p2.v0),(2.4.4.3^8.8.6^0.0.0^0.0.3),(0.0.1^0.2.2),0.20"),
    ("DUFU", "2015-08-18", "DUFU,BBS,30.3,0.0.0.0,(c2.m2.p2.v2),(2.0.0.0^8.6.6^0.0.0^0.0.3),(0.0.1^0.2.0),0.18"),
    ("DUFU", "2017-11-01", "DUFU,TSS,-36.2,0.0.0.0,(c3.m2.p2.v2),(0.4.0.0^3.4.7^0.0.0^0.0.0),(0.0.1^0.0.0),0.95"),
    ("DUFU", "2017-12-05", "DUFU,TSS,-33.-2,0.0.0.0,(c2.m0.p0.v4),(0.3.3.1^8.4.7^0.0.0^1.0.0),(0.1.1^0.0.0),0.71"),
    ("DUFU", "2018-07-17", "DUFU,BBS,38.2,0.0.0.0,(c2.m2.p2.v4),(0.0.0.1^7.0.0^0.0.0^0.3.0),(0.0.1^0.0.0),0.71"),
    ("DUFU", "2018-08-02", "DUFU,BBS,30.1,0.0.0.0,(c3.m4.p4.v4),(0.1.1.1^7.7.0^2.0.9^0.0.0),(0.0.1^0.0.0),0.91"),
    ("F&N", "2015-12-02", "F&N,BBS,33.3,0.0.0.0,(c3.m1.p2.v2),(0.0.0.0^3.1.8^0.0.1^3.0.0),(0.0.0^0.1.0),18.06"),
    ("F&N", "2015-11-02", "F&N,BBS,3.18,0.0.0.0,(c3.m2.p2.v4),(0.0.0.1^3.1.3^0.0.1^3.0.0.z.1),(^),18.06"),
    ("F&N", "2017-11-01", "F&N,BBS,3.10,0.0.0.0,(c3.m4.p2.v2),(0.1.0.0^7.6.0^0.0.0^0.0.0.r.5),(^),25.34"),
    ("KESM", "2013-12-03", "KESM,BBS,33.2,0.0.0.0,(c3.m0.p2.v2),(0.3.2.0^0.2.0^0.8.0^0.0.0),(0.0.2^0.1.2),2.00"),
    ("KESM", "2015-01-19", "KESM,BBS,31.1,0.0.0.0,(c2.m1.p1.v2),(2.4.4.0^6.6.0^0.0.0^1.0.3),(0.1.1^0.2.0),2.41"),
    ("KESM", "2016-03-16", "KESM,BBS,31.-2,0.0.0.0,(c2.m1.p1.v2),(2.0.4.4^0.4.3^0.0.0^0.0.0),(0.0.0^0.2.0),4.52"),
    ("KESM", "2016-04-25", "KESM,BBS,3.7,0.0.0.0,(c2.m2.p2.v0),(2.0.4.3^8.4.8^0.5.0^0.0.0.r.1),(^),4.36"),
    ("KESM", "2018-08-07", "KESM,TSS,-32.2,0.0.0.0,(c3.m4.p2.v2),(0.1.0.0^4.0.0^0.0.0^0.0.0),(0.0.0^0.2.0),17.86"),
    ("KESM", "2018-10-02", "KESM,TSS,-38.1,0.0.0.0,(c2.m2.p1.v4),(0.0.0.1^0.1.0^0.0.0^0.0.0),(0.0.0^0.2.0),15.02"),
    ("PADINI", "2011-06-10", "PADINI,TSS,-30.2,0.0.0.0,(c3.m1.p2.v2),(0.0.0.0^8.8.0^0.0.0^0.0.0),(0.0.0^0.2.2),1.09"),
    ("PADINI", "2011-08-19", "PADINI,TSS,-35.4,0.0.0.0,(c2.m2.p0.v2),(0.0.3.0^0.4.0^0.0.0^0.0.0),(0.0.0^0.1.0),0.94"),
    ("PADINI", "2011-10-04", "PADINI,BBS,31.5,0.0.0.0,(c2.m2.p1.v0),(0.0.4.3^0.4.4^0.0.0^0.0.0),(0.0.0^0.2.0),0.85"),
    ("PADINI", "2011-11-01", "PADINI,BBS,31.3,0.0.0.0,(c2.m2.p4.v2),(0.0.1.0^4.4.4^0.0.0^0.0.0),(0.0.0^0.2.0),1.02"),
    ("PADINI", "2014-10-02", "PADINI,TSS,-38.5,0.0.0.0,(c2.m2.p2.v0),(0.0.0.3^0.0.6^0.0.0^0.0.0),(0.0.1^0.0.0),1.88"),
    ("PADINI", "2017-02-02", "PADINI,BBS,38.1,0.0.0.0,(c2.m2.p1.v4),(2.0.0.1^4.6.0^0.6.0^2.0.3),(0.1.0^0.0.1),2.38"),
    ("PADINI", "2018-12-04", "PADINI,TSS,-33.1,0.0.0.0,(c2.m0.p0.v4),(2.2.3.1^0.0.5^0.0.0^1.0.0),(0.1.1^0.0.0),4.30"),
])
@pytest.mark.retrace
def test_retrace_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


@pytest.mark.parametrize("counter,tdate,expected", [
    ("CARLSBG", "2009-08-04", "CARLSBG,BBS,42.-1,0.0.0.0,(c3.m3.p4.v3),(0.0.1.2^5.7.0^1.9.9^0.0.0),(0.0.0^0.1.2),4.50"),
    ("CARLSBG", "2010-04-13", "CARLSBG,TSS,-40.-6,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^8.0.7^0.0.0^5.0.4),(0.0.0^0.1.0),5.13"),
    ("CARLSBG", "2011-03-01", "CARLSBG,BBS,40.1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^7.0.0^0.0.0^0.0.0),(0.0.0^0.1.0),6.75"),
    ("CARLSBG", "2011-04-04", "CARLSBG,TSS,-41.-3,0.0.0.0,(c4.m4.p2.v0),(1.1.0.3^7.0.0^0.0.0^0.0.0),(0.0.0^0.1.0),7.43"),
    ("CARLSBG", "2011-04-20", "CARLSBG,TSS,-40.2,0.0.0.0,(c4.m3.p3.v2),(1.0.0.0^7.0.0^0.0.0^0.0.0),(0.0.0^0.1.0),7.81"),
    ("CARLSBG", "2012-03-05", "CARLSBG,BBS,42.-1,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^0.0.8^0.0.0^0.0.0),(0.0.0^0.1.0),10.46"),
    ("CARLSBG", "2012-03-23", "CARLSBG,BBS,47.1,0.0.0.0,(c4.m2.p3.v0),(1.0.0.3^0.0.8^0.0.0^0.0.0),(0.0.0^0.1.0),10.46"),
    ("CARLSBG", "2013-05-09", "CARLSBG,BBS,40.4,0.0.0.0,(c4.m2.p2.v2),(1.4.0.0^0.8.0^0.0.0^0.0.4),(0.0.0^0.0.0),15.36"),
    ("CARLSBG", "2013-06-04", "CARLSBG,TSS,-40.5,0.0.0.0,(c4.m2.p3.v2),(1.0.0.0^0.0.0^2.0.0^0.0.0),(0.0.0^0.1.0),16.82"),
    ("CARLSBG", "2016-08-02", "CARLSBG,BBS,4.-3,0.0.0.0,(c4.m2.p2.v2),(1.2.0.0^3.0.0^0.0.0^0.0.0.z.4),(^),14.50"),
    ("CARLSBG", "2017-04-03", "CARLSBG,BBS,4.-2,0.0.0.0,(c4.m4.p2.v0),(1.1.0.3^3.4.2^0.0.0^0.0.0.z.6),(^),15.08"),
    ("CARLSBG", "2018-03-01", "CARLSBG,TSS,-4.-2,0.0.0.0,(c4.m4.p4.v2),(1.1.1.0^0.7.0^0.0.9^3.0.0.s.1),(^),18.78"),
    ("DUFU", "2015-01-12", "DUFU,BBS,40.1,0.0.0.0,(c4.m2.p2.v1),(1.0.0.0^9.0.8^0.0.0^6.0.0),(0.0.0^0.1.2),0.19"),
    ("DUFU", "2015-02-05", "DUFU,TSS,-42.2,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^9.0.0^0.0.0^6.0.0),(0.0.0^0.1.1),0.27"),
    ("DUFU", "2015-12-28", "DUFU,BBS,42.2,0.0.0.0,(c4.m2.p4.v3),(1.0.1.0^2.7.4^0.0.9^0.0.0),(0.0.1^0.1.2),0.35"),
    ("DUFU", "2016-01-05", "DUFU,TSS,-40.-4,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^7.2.0^0.0.0^0.0.0),(0.0.2^0.1.0),0.34"),
    ("DUFU", "2017-04-13", "DUFU,BBS,47.1,0.0.0.0,(c4.m2.p2.v0),(1.0.0.3^5.2.0^0.9.0^3.0.0),(0.0.0^0.1.0),0.75"),
    ("DUFU", "2017-05-03", "DUFU,TSS,-49.-1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.4^7.1.8^0.0.0^4.0.0),(0.0.0^0.1.0),0.87"),
    ("DUFU", "2018-10-01", "DUFU,BBS,40.-1,0.0.0.0,(c4.m2.p2.v1),(1.0.2.2^2.7.0^0.0.3^0.1.0),(0.0.2^0.0.0),1.75"),
    ("DUFU", "2018-11-16", "DUFU,TSS,-40.1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^2.7.7^0.0.0^0.1.0),(0.0.2^0.1.0),2.63"),
    ("F&N", "2016-03-11", "F&N,BBS,4.4,0.0.0.0,(c4.m0.p3.v2),(1.3.0.0^8.1.0^0.0.0^0.0.0.s.4),(^),19.90"),
    ("F&N", "2016-03-23", "F&N,BBS,4.3,0.0.0.0,(c4.m0.p2.v2),(1.3.0.0^8.1.0^0.0.0^0.0.0.s.4),(^),19.76"),
    ("F&N", "2016-08-03", "F&N,TSS,-4.7,0.0.0.0,(c4.m1.p2.v2),(1.0.2.0^4.1.7^0.0.0^5.0.0.m.8),(^),26.10"),
    ("KESM", "2015-05-15", "KESM,BBS,42.2,0.0.0.0,(c4.m2.p4.v3),(1.0.1.0^1.0.0^0.0.0^0.0.0),(0.2.2^0.1.0),3.48"),
    ("KESM", "2015-08-03", "KESM,BBS,41.-3,0.0.0.0,(c4.m4.p3.v2),(1.1.0.0^1.2.2^0.0.0^0.0.0),(0.2.2^0.1.0),4.25"),
    ("KESM", "2016-01-05", "KESM,TSS,-40.1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.0.8^0.0.0^0.0.0),(0.2.0^0.2.0),5.32"),
    ("KESM", "2016-07-04", "KESM,BBS,42.1,0.0.0.0,(c4.m2.p4.v2),(1.0.1.2^4.4.0^0.6.1^0.0.0),(0.0.2^0.1.0),5.54"),
    ("KESM", "2016-07-08", "KESM,BBS,41.3,0.0.0.0,(c4.m4.p4.v2),(1.1.1.2^4.4.0^0.6.1^0.0.0),(0.0.2^0.1.0),5.72"),
    ("KESM", "2016-09-30", "KESM,BBS,44.2,0.0.0.0,(c4.m2.p2.v2),(1.2.2.2^0.0.0^0.6.1^0.0.0),(0.0.2^0.1.0),7.90"),
    ("KESM", "2016-10-07", "KESM,BBS,4.1,0.0.0.0,(c4.m4.p2.v2),(1.1.2.0^7.0.7^0.7.0^0.0.0.r.6),(^),7.92"),
    ("KESM", "2016-11-10", "KESM,BBS,4.3,0.0.0.0,(c4.m2.p2.v2),(1.2.0.0^2.0.7^0.0.0^0.0.0.z.6),(^),9.15"),
    ("KESM", "2018-01-02", "KESM,TSS,-40.3,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.4.0^0.0.0^0.0.0),(0.0.0^0.2.0),19.62"),
    ("PADINI", "2012-02-03", "PADINI,BBS,42.4,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^4.0.1^0.0.0^0.0.0),(0.0.0^0.1.0),1.28"),
    ("PADINI", "2012-03-12", "PADINI,BBS,42.-4,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^5.0.1^0.9.0^0.0.0),(0.0.0^0.1.0),1.58"),
    ("PADINI", "2012-05-03", "PADINI,BBS,42.-5,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^0.1.2^0.0.0^0.0.0),(0.0.0^0.1.0),1.67"),
    ("PADINI", "2012-05-17", "PADINI,BBS,42.5,0.0.0.0,(c4.m2.p4.v2),(1.0.1.0^0.1.2^0.0.0^0.0.0),(0.0.0^0.1.0),1.66"),
    ("PADINI", "2013-05-02", "PADINI,TSS,-30.-3,0.0.0.0,(c2.m0.p1.v2),(0.2.0.0^8.1.0^0.0.1^0.0.0),(0.0.0^0.1.0),1.78"),
    ("PADINI", "2013-06-03", "PADINI,TSS,-34.1,0.0.0.0,(c3.m2.p4.v0),(0.0.1.3^0.2.0^0.0.3^0.0.1),(0.0.0^0.1.0),2.11"),
    ("PADINI", "2013-12-10", "PADINI,TSS,-38.1,0.0.0.0,(c2.m2.p2.v4),(0.0.0.1^7.0.0^2.0.0^0.0.0),(0.0.0^0.0.0),1.81"),
    ("PADINI", "2014-02-04", "PADINI,BBS,33.2,0.0.0.0,(c1.m0.p0.v2),(0.3.3.0^5.0.7^2.9.0^0.0.0),(0.0.0^0.0.1),1.59"),
    ("PADINI", "2014-08-05", "PADINI,TSS,-47.3,0.0.0.0,(c2.m2.p2.v0),(0.0.0.3^7.0.0^0.0.0^0.0.0),(0.0.0^0.0.2),1.98"),
    ("PADINI", "2016-02-04", "PADINI,BBS,40.-1,0.0.0.0,(c4.m2.p3.v3),(1.0.0.0^2.7.1^0.0.0^0.1.0),(0.0.0^0.1.1),2.10"),
    ("PADINI", "2017-04-03", "PADINI,BBS,47.1,0.0.0.0,(c4.m2.p2.v0),(1.0.0.2^0.8.1^0.6.0^0.0.0),(0.2.0^0.0.1),3.02"),
    ("PADINI", "2017-10-02", "PADINI,BBS,47.4,0.0.0.0,(c4.m2.p2.v0),(1.0.0.3^7.4.0^0.6.0^0.0.0),(0.0.0^0.1.0),4.50"),
    ("PADINI", "2017-12-05", "PADINI,TSS,-43.-1,0.0.0.0,(c4.m0.p2.v2),(1.3.0.0^7.4.0^0.5.0^3.0.0),(0.0.0^0.1.0),5.12"),
])
@pytest.mark.highC
def test_highC_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


@pytest.mark.parametrize("counter,tdate,expected", [
    ("CARLSBG", "2009-10-01", "CARLSBG,BBS,51.1,0.0.0.0,(c3.m0.p2.v2),(0.3.2.0^4.7.8^0.0.0^0.0.0),(0.0.0^0.1.0),4.19"),
    ("CARLSBG", "2009-10-19", "CARLSBG,BBS,53.3,0.0.0.0,(c3.m1.p2.v2),(0.0.2.0^4.7.8^0.0.0^0.0.0),(0.0.0^0.1.0),4.24"),
    ("CARLSBG", "2010-02-02", "CARLSBG,BBS,58.5,0.0.0.0,(c3.m2.p2.v0),(2.0.0.3^4.4.0^0.0.0^4.0.0),(0.0.0^0.1.0),4.52"),
    ("CARLSBG", "2010-05-03", "CARLSBG,TSS,-50.8,0.0.0.0,(c3.m2.p2.v2),(2.0.0.0^0.0.7^0.0.0^5.0.3),(0.0.0^0.1.0),5.12"),
    ("CARLSBG", "2010-06-02", "CARLSBG,BBS,51.4,0.0.0.0,(c3.m0.p1.v1),(2.3.0.0^8.0.7^0.0.0^5.0.3),(0.0.0^0.1.0),4.80"),
    ("CARLSBG", "2010-11-03", "CARLSBG,BBS,59.2,0.0.0.0,(c4.m4.p2.v2),(1.1.0.0^0.0.4^0.0.0^0.0.4),(0.0.0^0.1.0),5.55"),
    ("CARLSBG", "2012-06-01", "CARLSBG,BBS,55.3,0.0.0.0,(c3.m2.p0.v0),(2.0.3.3^6.0.0^0.0.0^0.0.0),(0.0.0^0.1.0),10.30"),
    ("CARLSBG", "2012-08-06", "CARLSBG,BBS,57.-3,0.0.0.0,(c4.m2.p2.v4),(1.0.0.1^4.4.0^0.0.0^0.0.0),(0.0.0^0.2.0),12.50"),
    ("CARLSBG", "2012-09-03", "CARLSBG,BBS,51.-4,0.0.0.0,(c3.m0.p2.v0),(2.3.0.3^4.4.0^0.0.0^0.0.0),(0.0.0^0.2.0),12.20"),
    ("CARLSBG", "2012-09-27", "CARLSBG,BBS,51.4,0.0.0.0,(c3.m0.p1.v2),(2.3.0.0^4.4.0^0.0.0^0.0.0),(0.0.0^0.2.0),11.24"),
    ("CARLSBG", "2012-12-14", "CARLSBG,BBS,58.-4,0.0.0.0,(c4.m2.p2.v0),(1.0.0.3^0.6.0^0.5.0^0.0.4),(0.0.0^0.0.0),12.82"),
    ("CARLSBG", "2013-01-03", "CARLSBG,BBS,51.-3,0.0.0.0,(c3.m0.p2.v0),(2.3.0.3^0.6.0^0.6.0^0.0.3),(0.0.0^0.0.0),12.58"),
    ("CARLSBG", "2013-01-21", "CARLSBG,BBS,51.3,0.0.0.0,(c3.m0.p2.v2),(2.3.0.0^0.6.0^0.6.0^0.0.3),(0.0.0^0.0.0),12.10"),
    ("CARLSBG", "2013-02-18", "CARLSBG,BBS,52.4,0.0.0.0,(c3.m1.p1.v4),(2.4.0.1^0.6.0^0.0.0^0.0.3),(0.0.0^0.0.0),12.34"),
    ("CARLSBG", "2013-04-01", "CARLSBG,BBS,50.3,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.8.0^0.0.0^0.0.4),(0.0.0^0.0.0),14.12"),
    ("CARLSBG", "2013-08-01", "CARLSBG,TSS,-56.2,0.0.0.0,(c3.m2.p2.v0),(0.0.4.3^0.0.0^0.0.0^0.0.0),(0.0.0^0.2.0),14.86"),
    ("CARLSBG", "2015-07-22", "CARLSBG,TSS,-50.2,0.0.0.0,(c2.m2.p2.v2),(0.0.0.0^1.1.3^0.0.0^0.0.0),(0.0.0^0.2.0),12.66"),
    ("CARLSBG", "2017-11-01", "CARLSBG,BBS,58.-3,0.0.0.0,(c4.m2.p2.v0),(1.0.0.2^0.7.0^0.0.0^0.0.1),(0.0.2^0.1.0),15.94"),
    ("CARLSBG", "2018-01-05", "CARLSBG,BBS,57.2,0.0.0.0,(c3.m2.p2.v4),(2.0.0.1^0.5.8^0.0.9^0.0.1),(0.0.2^0.1.0),15.40"),
    ("DUFU", "2015-04-02", "DUFU,BBS,-51.-2,0.0.0.0,(c4.m0.p2.v2),(1.3.0.0^9.0.0^0.0.0^7.0.0),(0.0.0^0.1.2),0.25"),
    ("DUFU", "2015-05-22", "DUFU,TSS,-52.2,0.0.0.0,(c3.m2.p0.v1),(2.4.3.0^9.0.4^0.0.0^7.0.3),(0.0.0^0.1.2),0.24"),
    ("DUFU", "2015-07-01", "DUFU,BBS,52.2,0.0.0.0,(c2.m1.p0.v2),(2.4.3.0^8.0.6^0.0.0^7.0.3),(0.0.1^0.1.2),0.19"),
    ("DUFU", "2016-02-22", "DUFU,BBS,-51.3,0.0.0.0,(c3.m0.p2.v2),(2.3.0.0^7.2.0^0.0.0^0.0.0),(0.0.2^0.1.2),0.36"),
    ("DUFU", "2016-03-01", "DUFU,TSS,-52.3,0.0.0.0,(c3.m2.p2.v2),(0.4.0.0^0.2.0^0.0.0^0.0.3),(0.0.2^0.1.2),0.36"),
    ("DUFU", "2016-05-06", "DUFU,BBS,50.2,0.0.0.0,(c3.m2.p2.v2),(2.0.0.0^4.1.0^0.0.0^0.0.0),(0.0.2^0.2.0),0.32"),
    ("DUFU", "2016-11-04", "DUFU,BBS,58.2,0.0.0.0,(c3.m2.p1.v0),(2.0.0.3^0.4.4^0.0.0^0.0.0),(0.0.1^0.1.0),0.38"),
    ("DUFU", "2016-12-02", "DUFU,BBS,50.1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.5.0^0.0.9^0.0.4),(0.0.2^0.1.0),0.45"),
    ("DUFU", "2016-12-14", "DUFU,BBS,50.1,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.5.0^0.0.9^0.0.4),(0.0.2^0.1.0),0.46"),
    ("DUFU", "2017-01-03", "DUFU,BBS,58.3,0.0.0.0,(c3.m2.p2.v0),(2.0.0.3^0.7.0^0.0.2^0.0.3),(0.0.2^0.1.0),0.46"),
    ("DUFU", "2017-09-06", "DUFU,TSS,-56.1,0.0.0.0,(c4.m2.p2.v2),(1.0.4.0^1.8.0^0.5.0^0.0.0),(0.0.0^0.2.0),0.99"),
    ("DUFU", "2017-10-06", "DUFU,TSS,-33.-1,0.0.0.0,(c3.m0.p0.v2),(0.3.3.0^1.6.0^0.5.0^0.0.0),(0.0.0^0.2.0),0.93"),
    ("DUFU", "2017-10-20", "DUFU,TSS,-35.1,0.0.0.0,(c3.m1.p0.v2),(0.4.3.0^3.6.0^0.0.0^0.0.0),(0.0.0^0.2.0),0.96"),
    ("F&N", "2011-07-06", "F&N,TSS,-50.2,0.0.0.0,(c3.m2.p2.v2),(2.0.0.0^2.0.0^0.0.0^5.0.0),(0.0.0^0.1.0),19.18"),
    ("F&N", "2011-08-03", "F&N,TSS,-5.7,0.0.0.0,(c3.m2.p2.v2),(0.0.0.0^2.8.0^0.0.0^6.0.4.z.4),(^),19.38"),
    ("F&N", "2011-08-09", "F&N,TSS,-55.2,0.0.0.0,(c3.m2.p0.v2),(2.0.3.0^2.0.0^0.0.0^5.0.0),(0.0.0^0.1.1),18.00"),
    ("KESM", "2013-12-31", "KESM,BBS,51.2,0.0.0.0,(c3.m0.p2.v2),(0.3.2.0^0.2.0^0.8.0^0.0.0),(0.0.0^0.1.2),1.98"),
    ("KESM", "2014-01-02", "KESM,BBS,52.1,0.0.0.0,(c3.m2.p2.v2),(0.4.2.0^8.2.0^0.8.0^0.0.0),(0.0.2^0.1.2),1.99"),
    ("KESM", "2014-06-23", "KESM,BBS,53.-2,0.0.0.0,(c3.m2.p2.v1),(2.0.2.2^0.2.1^0.0.0^0.0.0),(0.0.0^0.1.2),2.45"),
    ("KESM", "2014-07-08", "KESM,TSS,-50.-1,0.0.0.0,(c3.m2.p2.v2),(0.0.0.0^0.1.2^0.0.0^3.0.4),(0.0.0^0.1.2),2.50"),
    ("KESM", "2014-07-17", "KESM,TSS,-57.-1,0.0.0.0,(c3.m2.p2.v4),(0.0.0.1^0.1.2^0.0.0^3.0.4),(0.0.0^0.1.2),2.83"),
    ("KESM", "2014-08-04", "KESM,TSS,-54.1,0.0.0.0,(c4.m2.p4.v2),(1.0.1.2^4.1.2^0.0.0^3.0.0),(0.0.0^0.1.2),2.96"),
    ("KESM", "2014-12-15", "KESM,BBS,51.-2,0.0.0.0,(c2.m0.p0.v2),(2.3.3.0^6.6.7^0.0.0^1.0.3),(0.1.1^0.2.0),2.47"),
    ("KESM", "2015-01-13", "KESM,BBS,51.3,0.0.0.0,(c2.m0.p0.v2),(2.3.3.0^6.6.0^0.0.0^1.0.3),(0.1.1^0.2.0),2.36"),
    ("KESM", "2015-05-06", "KESM,BBS,5.9,0.0.0.0,(c3.m2.p2.v2),(0.0.0.0^1.0.1^0.0.0^0.0.0.s.4),(^),2.91"),
    ("KESM", "2015-09-01", "KESM,BBS,5.3,0.0.0.0,(c3.m2.p0.v0),(2.0.2.3^0.1.0^0.0.0^0.0.0.s.3),(^),3.50"),
    ("KESM", "2017-03-01", "KESM,BBS,58.1,0.0.0.0,(c3.m3.p1.v0),(2.0.0.3^7.7.4^0.0.0^0.0.2),(0.0.1^0.1.0),9.82"),
    ("KESM", "2017-04-06", "KESM,BBS,59.1,0.0.0.0,(c4.m4.p3.v2),(1.1.0.0^7.0.0^0.0.0^0.0.0),(0.0.2^0.2.0),12.70"),
    ("KESM", "2017-09-06", "KESM,BBS,52.3,0.0.0.0,(c3.m2.p2.v2),(2.4.0.0^1.4.1^0.0.0^0.0.2),(0.0.2^0.2.0),14.86"),
    ("KESM", "2018-01-02", "KESM,TSS,-5.9,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^0.4.0^0.0.0^0.0.0.l.4),(^),19.62"),
    ("KESM", "2018-02-14", "KESM,TSS,-55.3,0.0.0.0,(c3.m2.p0.v2),(2.0.3.0^4.4.0^0.0.0^0.0.0),(0.0.0^0.1.0),19.18"),
    ("KESM", "2018-02-26", "KESM,TSS,-50.5,0.0.0.0,(c3.m2.p1.v2),(2.0.0.0^0.4.4^0.0.0^0.0.0),(0.0.0^0.1.0),20.50"),
    ("KESM", "2018-06-18", "KESM,TSS,-50.3,0.0.0.0,(c3.m2.p2.v2),(0.0.4.4^4.6.0^0.0.0^0.0.0),(0.0.0^0.2.0),17.52"),
    ("PADINI", "2012-04-03", "PADINI,BBS,58.6,0.0.0.0,(c3.m2.p2.v0),(2.0.0.3^7.1.1^0.0.0^0.0.0),(0.0.0^0.1.0),1.41"),
    ("PADINI", "2016-04-04", "PADINI,BBS,58.5,0.0.0.0,(c3.m2.p2.v0),(0.0.0.3^7.7.0^0.0.0^0.0.0),(0.0.0^0.1.1),2.06"),
    ("PADINI", "2016-07-11", "PADINI,BBS,58.5,0.0.0.0,(c4.m2.p2.v0),(1.0.0.3^0.0.0^0.0.0^3.0.0),(0.0.0^0.1.2),2.37"),
    ("PADINI", "2016-08-04", "PADINI,TSS,-59.-1,0.0.0.0,(c4.m4.p3.v2),(1.1.0.0^0.0.0^0.0.0^3.0.0),(0.0.0^0.1.0),2.70"),
    ("PADINI", "2016-11-02", "PADINI,TSS,-56.4,0.0.0.0,(c3.m2.p2.v2),(0.0.4.0^4.0.4^0.5.0^0.0.4),(0.0.0^0.2.0),2.87"),
    ("PADINI", "2018-01-02", "PADINI,TSS,-58.8,0.0.0.0,(c3.m2.p2.v0),(2.0.0.3^7.4.0^0.5.0^3.0.0),(0.0.0^0.1.0),5.20"),
    ("PADINI", "2018-05-04", "PADINI,BBS,51.4,0.0.0.0,(c2.m0.p2.v2),(2.3.0.4^4.4.8^0.5.0^0.0.0),(0.0.0^0.2.0),4.50"),
    ("PADINI", "2018-09-07", "PADINI,TSS,-53.2,0.0.0.0,(c3.m1.p2.v2),(2.2.2.0^0.0.0^0.0.0^0.0.0),(0.0.0^0.2.0),5.82"),
    ("PADINI", "2018-11-02", "PADINI,TSS,-51.3,0.0.0.0,(c3.m0.p1.v2),(2.2.0.0^0.0.7^0.0.0^1.0.0),(0.1.0^0.0.0),5.52"),
])
@pytest.mark.topC
def test_topC_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


@pytest.mark.parametrize("counter,tdate,expected", [
    ("CARLSBG", "2014-02-05", "CARLSBG,BBS,90.8,0.0.0.0,(c1.m1.p1.v4),(0.0.0.1^4.1.0^0.0.1^0.0.0),(0.2.0^0.0.0),11.10"),
    ("CARLSBG", "2014-02-25", "CARLSBG,BBS,90.-8,0.0.0.0,(c2.m2.p2.v2),(0.0.0.0^4.2.0^0.0.3^0.0.0),(0.2.0^0.0.0),13.18"),
    ("CARLSBG", "2014-04-24", "CARLSBG,TSS,-90.8,0.0.0.0,(c2.m4.p2.v2),(0.1.0.0^4.2.0^0.0.3^0.0.0),(0.0.0^0.0.0),13.46"),
    ("DUFU", "2014-03-06", "DUFU,BBS,90.5,0.0.0.0,(c0.m3.p2.v2),(3.0.0.0^9.7.0^0.0.0^6.0.0),(0.0.0^1.1.1),0.13"),
    ("DUFU", "2018-08-02", "DUFU,BBS,90.1,0.0.0.0,(c3.m4.p4.v4),(0.1.1.1^7.7.0^2.0.9^0.0.0),(0.0.1^0.0.0),0.91"),
    ("KESM", "2013-05-13", "KESM,BBS,90.-1,0.0.0.0,(c1.m4.p2.v2),(4.1.0.0^0.2.0^1.6.0^0.0.0),(0.0.2^0.0.0),1.80"),
    ("KESM", "2015-01-19", "KESM,BBS,90.7,0.0.0.0,(c2.m1.p1.v2),(2.4.4.0^6.6.0^0.0.0^1.0.3),(0.1.1^0.0.0),2.41"),
    ("KESM", "2018-03-16", "KESM,TSS,-90.1,0.0.0.0,(c3.m2.p2.v2),(0.0.0.0^4.4.4^0.0.0^0.0.0),(0.0.0^0.2.0),19.88"),
    ("PADINI", "2011-11-01", "PADINI,BBS,90.2,0.0.0.0,(c2.m2.p4.v2),(0.0.1.0^4.4.4^0.0.0^0.0.0),(0.0.0^0.2.0),1.02"),
    ("PADINI", "2011-11-09", "PADINI,BBS,90.2,0.0.0.0,(c2.m2.p3.v3),(0.0.4.0^4.4.4^0.0.0^0.0.0),(0.0.0^0.2.0),1.00"),
    ("PADINI", "2012-08-09", "PADINI,TSS,-90.-9,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^4.0.0^0.6.0^3.0.0),(0.0.0^0.1.0),2.10"),
    ("PADINI", "2012-08-23", "PADINI,TSS,-90.9,0.0.0.0,(c4.m2.p2.v2),(1.0.0.0^4.0.4^0.6.0^3.0.0),(0.0.0^0.1.0),2.36"),
    ("PADINI", "2014-02-04", "PADINI,BBS,90.10,0.0.0.0,(c1.m0.p0.v2),(0.3.3.0^5.0.7^2.9.0^0.0.0),(0.0.0^0.0.1),1.59"),
])
@pytest.mark.extremes
def test_extremes_success(counter, tdate, expected):
    result = scanSignals("", 0, counter, loadjson(counter, tdate), 0)
    result, expected = matchpartial(result, expected, 2)
    assert result == expected, "*** Input = " + counter + "," + tdate


def matchpartial(res, exp, partialmatch=2):
    newexp = []
    newres = res.replace('\t', '')
    # endpos = partialmatch + 1
    if partialmatch:
        tmpres = newres.split(",")
        tmpexp = exp.split(",")
        newres = []
        val1 = tmpres[2].split(".")
        val2 = tmpexp[2].split(".")
        for i in range(len(val1)):
            if int(val1[i]) > 0:
                newres.append(1)
            elif int(val1[i]) < 0:
                newres.append(-1)
            else:
                newres.append(0)
            if int(val2[i]) > 0:
                newexp.append(1)
            elif int(val2[i]) < 0:
                newexp.append(-1)
            else:
                newexp.append(0)
        # newres = ",".join(tmpres[:endpos])
        # newexp = ",".join(tmpexp[:endpos])
    else:
        newexp = exp
    return newres, newexp
