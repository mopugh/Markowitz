from cvxopt import matrix, solvers
from pandas import Series, DataFrame
import numpy as np

def MarkowitzOpt(meanvec,varvec,covvec,irate,rmin):
	'''Framework and variable names taken from pg. 155 of Boyd and Vandenberghe
	CVXOPT setup taken from:
	http://cvxopt.org/userguide/coneprog.html#quadratic-programming
	http://cvxopt.org/userguide/coneprog.html#quadratic-programming'''

	# Number of positions
	# Additional position for interest rate
	numPOS = meanvec.size+1
	# Number of stocks
	NumStocks = meanvec.size
	# mean return vector
	pbar = matrix(irate,(1,numPOS))
	pbar[:numPOS-1]=matrix(meanvec)

	# Ensure feasability Code
	pbar2 = np.array(pbar)
	if(pbar2.max() < rmin):
		rmin_constraint = irate
	else:
		rmin_constraint = rmin;

	counter = 0
	SIGMA = matrix(0.0,(numPOS,numPOS))
	for i in np.arange(NumStocks):
		for j in np.arange(i,NumStocks):
			if i == j:
				# SIGMA[i,j] = shift_returns_var.ix[DATEiter][i]
				SIGMA[i,j] = varvec[i]
			else:
				# SIGMA[i,j] = CovSeq.ix[DATEiter][counter]
				SIGMA[i,j] = covvec[counter]
				SIGMA[j,i] = SIGMA[i,j]
				counter+=1

	# Generate G matrix and h vector for inequality constraints
	G = matrix(0.0,(numPOS+1,numPOS))
	h = matrix(0.0,(numPOS+1,1))
	h[-1] = -rmin_constraint
	for i in np.arange(numPOS):
		G[i,i] = -1
	G[-1,:] = -pbar
	# Generate p matrix and b vector for equality constraints
	p = matrix(1.0,(1,numPOS))
	b = matrix(1.0)
	q = matrix(0.0,(numPOS,1))
	# Run convex optimization program
	solvers.options['show_progress'] = False
	sol=solvers.qp(SIGMA,q,G,h,p,b)
	# Solution
	xsol = np.array(sol['x'])
	dist_sum = xsol.sum()

	return xsol