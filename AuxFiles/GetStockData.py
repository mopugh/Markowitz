#!/usr/bin/env python
import pandas as pd
import pandas.io.data as web
from datetime import datetime
  
STOCKS = ['GOOG','AAPL','AMZN']
# Dates to gather data from
begin_date = datetime(2014,1,1)
end_date = datetime(2014,1,31)
                    
data = pd.DataFrame()

for stock in STOCKS:
    print 'Getting info for ' + stock
    StockData = web.DataReader(stock,"yahoo",begin_date,end_date)
    StockData['Symbol'] = stock
    data[stock] = StockData['Adj Close']