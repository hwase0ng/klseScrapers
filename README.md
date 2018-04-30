# klseScrapers
EOD data scrapings for KLSE

Alternative sites to scrap for KLSE EOD after both google and yahoo finance stops working.

1. investing.com

	```
	# Sample code
	idmap = loadIdMap()
	counter = "PBBANK"
	START_DATE = "2018-01-01"
	END_DATE = "2018-02-26"
	df = InvestingQuote(idmap, counter, START_DATE, END_DATE).to_df()
	if isinstance(df, pd.DataFrame):
	   print df[:5]
	   df.to_csv(counter+".csv", index=False, header=False)
	```
	```
 	# Sample output
	Commodity    Date   Open   High   Low   Close    Volume
	PBBANK 2018-01-02  20.76  20.80  20.62  20.76  1870000.0
	PBBANK 2018-01-03  20.80  20.86  20.74  20.76  3910000.0
	PBBANK 2018-01-04  20.76  20.88  20.70  20.74  4750000.0
	PBBANK 2018-01-05  20.74  20.86  20.74  20.78  3800000.0
	PBBANK 2018-01-08  20.86  20.86  20.76  20.82  7690000.0
	```

   	limitation: cannot download more than 5 months of EOD at any one time due to the code below:
   
	```
	df["Volume"] = pd.eval(df["Vol."].replace(mp.keys(), mp.values(), regex=True).str.replace(r'[^\d\.\*]+', ''))
	```
	
	Any suggestion/improvements are welcome.

2. finance.yahoo.com

	```
	# Sample code
	cookie, crumb = getYahooCookie('https://uk.finance.yahoo.com/quote/AAPL/')
	stock_name = "PBBANK"
	stock_code = "1295"
	START_DATE = "2018-01-01"
	END_DATE = "2018-02-26"
	q = YahooQuote(cookie, crumb, stock_name, stock_code + ".KL",
                           START_DATE, END_DATE)
	if len(q.getCsvErr()) > 0:
		st_code, st_reason = q.getCsvErr().split(":")
		rtn_code = int(st_code)
		print rtn_code, st_reason
	else:
		print q
	```


   - limitation: yahoo finance for KLCI has been broken since February 2018 so is only good for EOD prior to that.
   
 3. i3investor.com
 
 	```
	# Sample code
	START_DATE = "2018-03-28"
    	i3 = scrapeEOD(connectRecentPrices("6998"), START_DATE)
    	if i3 is not None:
        	for key in sorted(i3.iterkeys()):
            	print key + ',' + ','.join(map(str, unpackEOD(*(i3[key]))))
	```
	```
	# Sample output:
	2018-04-02,0.1350,0.1350,0.1350,0.1350,50000
	2018-04-03,0.1350,0.1350,0.1300,0.1300,45500
	2018-04-04,0.1350,0.1350,0.1350,0.1350,500
	2018-04-05,0.1250,0.1300,0.1250,0.1300,80000
	2018-04-09,0.1300,0.1300,0.1300,0.1300,500
	2018-04-10,0.1250,0.1400,0.1250,0.1400,221900
	2018-04-11,0.1400,0.1500,0.1400,0.1450,76800
	2018-04-18,0.1400,0.1400,0.1400,0.1400,35000
	2018-04-25,0.1350,0.1350,0.1350,0.1350,50000
	2018-04-26,0.1350,0.1350,0.1350,0.1350,24600
	```
	
 	limitation: i3 only provides recent prices of up to past 1 month

