import pandas as pd
import os
def RSI_Calculate(df, periods):


	alpha = 1/14

	df['Change'] = df['Close']-df['Open']
	
	for index, row in df.iterrows():
		if row['Change'] >= 0:
			df.loc[index,['Gain']]=row['Change']
		elif row['Change'] < 0:
			df.loc[index,['Loss']]=-row['Change']


	df.loc[14,['Avg']]=-row['Change']


	print(df)



	'''
	x=period
	gain=[]
	loss=[]
	while x>0:
		change = df.loc[x,'Close']-df.loc[x+1,'Close']
		if change >= 0:
			gain.append(change)
		else:
			loss.append(abs(change))
		x=x-1
	avgGain = sum(gain)/14
	avgLoss = sum(loss)/14
	RS = avgGain/avgLoss
	RSI = 100-(100/(1+RS))
	print(df)
	print(gain)
	print(loss)
	return RSI

	'''