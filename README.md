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
