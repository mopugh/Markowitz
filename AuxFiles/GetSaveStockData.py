# Get stock names from file
# Download all daily closing prices for all stocks
# Save data to file

import pandas as pd
import pandas.io.data as web
from datetime import datetime
from pandas import Series, DataFrame

# # Text file with list of stocks
# filename = 'stocks.txt'

# temp = pd.read_csv(filename,names=['Stock'])
# STOCKS = temp['Stock']
# del temp

STOCKS = ['GOOG','AAPL','AMZN']
# Dates to gather data from
begin_date = datetime(2014,1,1)
end_date = datetime(2014,1,31)

counter = 0
for stock in STOCKS:
	print 'Getting info for ' + stock
	StockData = web.DataReader(stock,"yahoo",begin_date,end_date)
	StockData['Symbol'] = stock
	# print StockData
	if counter == 0:
		DATA = StockData
	else:
		DATA = pd.concat([DATA,StockData],axis=0)
	counter+=1

# DATA.to_csv('FirstData.csv',sep=',')