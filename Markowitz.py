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

# Load Flag
# if 1, load data from file
# if not 1, get data from web and save to file
load_flag = 1
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

# Which shift to use, positive or negative?
# shift_returns = price/price.shift(shift) - 1
shift_returns = price/price.shift(-shift) - 1
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
counter = 0
StockList.append('InterestRate')
DISTRIBUTION = DataFrame(index=StockList)
RETURNS = Series(index=INDEX)

# Start Value
TOTAL_VALUE = 1.0
RETURNS[INDEX[DATE_INDEX_iter]] = TOTAL_VALUE

while DATE_INDEX_iter + 20 < END_INDEX:
	DATEiter = INDEX[DATE_INDEX_iter]
	# print counter
	print DATEiter

	# CVXOPT setup taken from:
	# http://cvxopt.org/userguide/coneprog.html#quadratic-programming
	# http://cvxopt.org/userguide/coneprog.html#quadratic-programming

	# Increase by one because taking a possible position gaining only interest
	# Interest is assumed fixed and has zero variance
	n = NumStocks+1
	pbar = matrix(interest_rate,(1,n))
	p2 = shift_returns_mean.ix[DATEiter]
	p2 = matrix(p2)
	pbar[:n-1] = p2
	SIGMA = matrix(0.0,(n,n))

	# Ensure feasability Code
	pbar2 = np.array(pbar)
	if(pbar2.max() < rmin):
		rmin_constraint = interest_rate
	else:
		rmin_constraint = rmin;

	# Generate Sigma Matrix
	# Framework and variable names taken from pg. 155 of Boyd and Vandenberghe
	counter = 0
	for i in np.arange(NumStocks):
		for j in np.arange(i,NumStocks):
			if i == j:
				SIGMA[i,j] = shift_returns_var.ix[DATEiter][i]
			else:
				SIGMA[i,j] = CovSeq.ix[DATEiter][counter]
				SIGMA[j,i] = SIGMA[i,j]
				counter+=1

	# Generate G matrix and h vector for inequality constraints
	G = matrix(0.0,(n+1,n))
	h = matrix(0.0,(n+1,1))
	h[-1] = -rmin_constraint
	for i in np.arange(n):
		G[i,i] = -1
	G[-1,:] = -pbar
	# Generate p matrix and b vector for equality constraints
	p = matrix(1.0,(1,n))
	b = matrix(1.0)
	q = matrix(0.0,(n,1))
	# Run convex optimization program
	solvers.options['show_progress'] = False
	sol=solvers.qp(SIGMA,q,G,h,p,b)
	# Solution
	xsol = np.array(sol['x'])
	dist_sum = xsol.sum()
	DISTRIBUTION[DATEiter.strftime('%Y-%m-%d')] = xsol

	DATEiter2 = INDEX[DATE_INDEX_iter+shift]
	temp1 = price.ix[DATEiter]/price.ix[DATEiter2]
	temp1.ix[StockList[-1]] = interest_rate+1
	temp2 = Series(xsol.ravel(),index=StockList)
	TOTAL_VALUE = np.sum(TOTAL_VALUE*temp2*temp1)
	print TOTAL_VALUE

	# Increase Date
	DATE_INDEX_iter += shift
	print INDEX[DATE_INDEX_iter]
	# RETURNS[INDEX[DATE_INDEX_iter]] = TOTAL_VALUE
	RETURNS[DATE_INDEX_iter] = TOTAL_VALUE
	# print RETURNS[INDEX[DATE_INDEX_iter]]
	print RETURNS[DATE_INDEX_iter]

Figures
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
plt.show()