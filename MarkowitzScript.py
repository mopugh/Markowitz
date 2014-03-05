''' First Attempt at Markowitz portfolio optimization.
Uses exponential weighting moving average filters to compute
means and covariances over returns over a specified period.
In this code the returns are taken over a 20 business day period.'''

import pandas as pd
import numpy as np
import pandas.io.data as web
import matplotlib.pyplot as plt
import matplotlib.dates as md
from pandas import Series, DataFrame
from cvxopt import matrix, solvers
from datetime import datetime
from pandas.tseries.offsets import BusinessDay
import MarkowitzOpt
reload(MarkowitzOpt)

# Load Flag
# if 1, load data from file
# if not 1, get data from web and save to file
load_flag = 1
# Plot Flag
# if 1, plot results
# if not 1, do not plot results
plot_flag = 1

# File name with Stock Prices
filename = 'StockPrices.csv'

StockList = ['AAPL','IBM','MSFT','GOOG','QCOM']
NumStocks = len(StockList)
# For simplicity, assume fixed interest rate
interest_rate = 0.03/12.
# Minimum desired return
rmin = 0.02

# Get data from web if not loading from file
if load_flag != 1:

	all_data = {}
	for ticker in StockList:
		all_data[ticker] = web.get_data_yahoo(ticker,'1/1/2000','1/1/2014')

	price = DataFrame({tic: data['Adj Close'] for tic, data in all_data.iteritems()})
	volume = DataFrame({tic: data['Volume'] for tic, data in all_data.iteritems()})

	price.to_csv(filename)
# Get data from file if loading from file
else:
	price = pd.read_csv(filename)
	price.index = [datetime.strptime(x,'%Y-%m-%d') for x in price['Date']]
	price = price.drop('Date',1)


# Specify number of days to shift
shift = 20
# Specify filter "length"
filter_len = shift

# Compute returns over the time period specified by shift
shift_returns = price/price.shift(shift) - 1
shift_returns_mean = pd.ewma(shift_returns,span=filter_len)
shift_returns_var = pd.ewmvar(shift_returns,span=filter_len)

# Compute covariances
CovSeq = pd.DataFrame()
for FirstStock in np.arange(NumStocks-1):
	for SecondStock in np.arange(FirstStock+1,NumStocks):
		ColumnTitle = StockList[FirstStock] + '-' + StockList[SecondStock]
		CovSeq[ColumnTitle] = pd.ewmcov(shift_returns[StockList[FirstStock]],shift_returns[StockList[SecondStock]],span=filter_len)

START_DATE = '2006-01-03'
INDEX = shift_returns.index
START_INDEX = INDEX.get_loc(START_DATE)
END_DATE = INDEX[-1]
END_INDEX = INDEX.get_loc(END_DATE)
DATE_INDEX_iter = START_INDEX
StockList.append('InterestRate')
DISTRIBUTION = DataFrame(index=StockList)
RETURNS = Series(index=INDEX)

# Start Value
TOTAL_VALUE = 1.0
RETURNS[INDEX[DATE_INDEX_iter]] = TOTAL_VALUE

while DATE_INDEX_iter + 20 < END_INDEX:
	DATEiter = INDEX[DATE_INDEX_iter]
	# print DATEiter

	xsol = MarkowitzOpt.MarkowitzOpt(shift_returns_mean.ix[DATEiter],shift_returns_var.ix[DATEiter],CovSeq.ix[DATEiter],interest_rate,rmin)

	dist_sum = xsol.sum()
	DISTRIBUTION[DATEiter.strftime('%Y-%m-%d')] = xsol

	DATEiter2 = INDEX[DATE_INDEX_iter+shift]
	temp1 = price.ix[DATEiter2]/price.ix[DATEiter]
	temp1.ix[StockList[-1]] = interest_rate+1
	temp2 = Series(xsol.ravel(),index=StockList)
	TOTAL_VALUE = np.sum(TOTAL_VALUE*temp2*temp1)
	# print TOTAL_VALUE

	# Increase Date
	DATE_INDEX_iter += shift
	print 'Date:' + str(INDEX[DATE_INDEX_iter])
	RETURNS[INDEX[DATE_INDEX_iter]] = TOTAL_VALUE

# Remove dates that there are no trades from returns
RETURNS = RETURNS[np.isfinite(RETURNS)]

# Figures
if plot_flag == 1:
	DISTRIBUTION.T.plot(kind='bar',stacked=True)
	plt.ylim([0,1])
	plt.xlabel('Date')
	plt.ylabel('Distribution')
	plt.title('Distribution vs. Time')

	fig, axes = plt.subplots(nrows=2,ncols=1)
	price.plot(ax=axes[0])
	shift_returns.plot(ax=axes[1])
	axes[0].set_title('Stock Prices')
	axes[0].set_xlabel('Date')
	axes[0].set_ylabel('Price')
	axes[1].set_title(str(shift)+ ' Day Shift Returns')
	axes[1].set_xlabel('Date')
	axes[1].set_ylabel('Returns ' + str(shift) + ' Days Apart')

	plt.figure()
	RETURNS.plot()
	plt.xlabel('Date')
	plt.ylabel('Returns')
	plt.title('Returns vs. Time')

	plt.show()