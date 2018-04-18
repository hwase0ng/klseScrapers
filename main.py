from scrapers.scrapeI3 import connectRecentPrices, scrapeEOD
import settings as S

S.DBG_ALL = False
START_DATE = '2018-03-23'
i3 = scrapeEOD(connectRecentPrices("5010"), START_DATE)
print i3.items()
