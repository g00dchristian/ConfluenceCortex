import numpy as np
import pandas as pd

def Inside_Bar(dforig, propertyDic, entry=None):
	df=dforig.copy()
	numCandles=15
	consecIB=0
	df=df[-int(numCandles):]
	for index, row in df.iterrows():
		if index < numCandles-1:
			if row['Low']>df.loc[index+1,'Low'] and row['High']<df.loc[index+1,'High']:
				consecIB=consecIB+1
				df.loc[index,'IBs']=consecIB
			else:
				consecIB=0
				df.loc[index,'IBs']=consecIB
	if df.loc[2,'IBs']>0 and df.loc[1,'IBs']==0:
		if df.loc[1,'Low']<df.loc[2,'Low'] and  df.loc[1,'High']>df.loc[2,'High']:
			current='Nil'
		elif df.loc[1,'Low']<df.loc[2,'Low'] and df.loc[1,'High']<=df.loc[2,'High']:
			current='Bearish'
		elif df.loc[1,'Low']>=df.loc[2,'Low'] and df.loc[1,'High']>df.loc[2,'High']:
			current='Bullish'
		else:
			current='Error: Revise inside bar break analysis'
	else:
		current='Nil'


	result={'Status':current,'ConsecIB':df.loc[2,'IBs']}

	if entry != None:
		entry.update({'Inside_Bar':result})
	return result
