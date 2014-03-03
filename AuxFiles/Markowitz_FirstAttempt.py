'''First attempt at computing Markowitz portfolio optimization.
Mean and covariance is computing using exponential weighting moving average
over returns computed over a shift which is specified'''

import pandas as pd
import numpy as np
import pandas.io.data as web
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
from cvxopt import matrix, solvers
from datetime import datetime

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
rmin = 0.03

if load_flag != 1:

	all_data = {}
	for ticker in StockList:
		all_data[ticker] = web.get_data_yahoo(ticker,'1/1/2000','1/1/2014')

	price = DataFrame({tic: data['Adj Close'] for tic, data in all_data.iteritems()})
	volume = DataFrame({tic: data['Volume'] for tic, data in all_data.iteritems()})

	price.to_csv(filename)

else:
	price = pd.read_csv(filename)
	price.index = [datetime.strptime(x,'%Y-%m-%d') for x in price['Date']]
	price = price.drop('Date',1)


# Specify number of days to shift
shift = 20
# Specify filter "length"
filter_len = shift

shift_returns = price/price.shift(shift) - 1
shift_returns_mean = pd.ewma(shift_returns,span=filter_len)
shift_returns_var = pd.ewmvar(shift_returns,span=filter_len)

CovSeq = pd.DataFrame()
for FirstStock in np.arange(NumStocks-1):
	for SecondStock in np.arange(FirstStock+1,NumStocks):
		ColumnTitle = StockList[FirstStock] + '-' + StockList[SecondStock]
		CovSeq[ColumnTitle] = pd.ewmcov(shift_returns[StockList[FirstStock]],shift_returns[StockList[SecondStock]],span=filter_len)

# Test CVXOPT code for a single day
date = '2013-10-31'
n = NumStocks+1
pbar = matrix(interest_rate,(1,n))
p2 = shift_returns_mean.ix[date]
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
counter = 0
for i in np.arange(NumStocks):
	for j in np.arange(i,NumStocks):
		if i == j:
			SIGMA[i,j] = shift_returns_var.ix[date][i]
		else:
			SIGMA[i,j] = CovSeq.ix[date][counter]
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

# Figure
fig, axes = plt.subplots(nrows=2,ncols=1)
price.plot(ax=axes[0])
shift_returns.plot(ax=axes[1])
axes[0].set_title('Stock Prices')
axes[1].set_title(str(shift)+ ' Day Shift Returns')
plt.show()