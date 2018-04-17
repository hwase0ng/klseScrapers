from scrapers.scrapeI3 import connectRecentPrices, scrapeEOD
import settings as S

S.DBG_ALL = True
scrapeEOD(connectRecentPrices("5010"))
