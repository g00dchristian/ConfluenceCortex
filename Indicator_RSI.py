import numpy as np
import pandas as pd

def Indicator_RSI(dforig, propertyDic, entry=None):
	df=dforig.copy()
	alpha = 1/14
	df['ClsShift'] = df['Close'].shift(1)
	df['Change'] = df['Close'] - df['ClsShift']
	df['Gain'] = np.where(df['Change']>=0, df['Change'], 0)
	df['Loss'] = np.where(df['Change']<0, abs(df['Change']), 0)		
	avGain = np.average(df.iloc[1:15]['Gain'])
	avLoss = np.average(df.iloc[1:15]['Loss'])

	df.loc[propertyDic['Periods']-14,'Avg Gain']=avGain
	df.loc[propertyDic['Periods']-14,'Avg Loss']=avLoss
	
	iterReference=propertyDic['Periods']
	for index, row in df.iterrows():
		if iterReference != propertyDic['Periods'] and iterReference < propertyDic['Periods']-14:
			#lbdafunc = lambda x: (x['Gain']*(1/14))+((1-1/14)*self.lastlbdafunc)
			#df.apply(lbdafunc, axis=1)
			#print(df.loc[index,'Gain'])
			df.loc[index, 'Avg Gain'] = (df.loc[index, 'Gain']*(1/14))+((1-1/14)*recGain)
			df.loc[index, 'Avg Loss'] = (df.loc[index, 'Loss']*(1/14))+((1-1/14)*recLoss)
		recGain = df.loc[iterReference, 'Avg Gain']
		recLoss = df.loc[iterReference, 'Avg Loss']
		#print(self.lastlbdafunc)
		iterReference=iterReference-1
		
	df['RS'] = df['Avg Gain']/df['Avg Loss']
	#df.loc[propertyDic['Periods']-14, 'RS'] = np.nan
	df['RSI'] = np.where(df['Avg Loss']==0,100,(100-(100/(1+df['RS']))))
	

	if entry != None:
		entry.update({'RSI':df.loc[1,'RSI']})
	return df.loc[1,'RSI']