import pandas.io.data as web
from pandas import Series, DataFrame

all_data = {}
for ticker in ['AAPL','IBM','MSFT','GOOG']:
	all_data[ticker] = web.get_data_yahoo(ticker,'1/1/2000','1/1/2010')

price = DataFrame({tic: data['Adj Close'] for tic, data in all_data.iteritems()})
volume = DataFrame({tic: data['Volume'] for tic, data in all_data.iteritems()})