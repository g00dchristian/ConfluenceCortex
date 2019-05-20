import pandas as pd
import math


def Market_Sentiment(dforig, propertyDic, entry=None):
	df=dforig.copy()

	pHigh = propertyDic['Periods']
	rHigh = propertyDic['Periods']
	pLow = propertyDic['Periods']
	rLow = propertyDic['Periods']


	propertyDic['Last_Level']=""
	minimumPeriod = 2
	rCandleHigh = 0
	rCandleLow = math.inf
	propertyDic['Break']='Nil'
	#df.to_csv('C:\\Users\\Christian\\RedPanda\\DF.csv')

	for index, row in df.iterrows():
		newLow = False
		newHigh = False

		#THE LOWS
		if row['Low'] <= rCandleLow:
			test = True 
			if row['Low'] > df.loc[rLow,'Low']:
				if row['Low']*0.997<df.loc[rLow,'Low'] and rLow-index <= minimumPeriod:
					test=False
					#print('Rejected Low: %i (Rule 1)'%(index))
					#print('False1 Low')
					#print(index)
			if row['Low'] < df.loc[rLow,'Low']:
				if row['Low']*1.003>df.loc[rLow,'Low'] and rLow-index <= minimumPeriod:
					test=False
					#print('Rejected Low: %i (Rule 2)'%(index))
					#print('False2 Low')
					#print(index)
			if row['Low'] > df.loc[rLow,'Low']:
				if row['Low'] < rCandleLow and row['High'] > rCandleHigh:
					test = False
					#print('Rejected Low: %i (Rule 3)'%(index))
					#print('False3 Low')
					#print(index)



			if index>=2 and row['Low']<df.loc[index-1,'Low'] and test is True:
					if rLow-index >= minimumPeriod:
						#the new low needs to be at least the 'minimumPeriod' since the last low
						if propertyDic['Last_Level'] != 'Low':
							#print('New Low: %i | pLow %i --> %i | rLow %i --> %i | Rule: 1'%(index, pLow, rLow, rLow, index))
							pLow=rLow
						rLow = index
						newLow = True
					elif row['Low']*0.997 <= rCandleLow:
						if propertyDic['Last_Level'] != 'Low':
							#print('New Low: %i | pLow %i --> %i | rLow %i --> %i | Rule: 2'%(index, pLow, rLow, rLow, index))
							pLow=rLow
						rLow = index
						newLow = True
					elif row['Low'] < rLow:
						if propertyDic['Last_Level'] != 'Low':
							#print('New Low: %i | pLow %i --> %i | rLow %i --> %i | Rule: 3'%(index, pLow, rLow, rLow, index))
							pLow=rLow
						rLow = index
						newLow = True
			'''
			elif index == 2 and test is True:
				if propertyDic['Last_Level'] != 'Low':
					pLow=rLow
				rLow = index
				newLow is True
			'''


		#THE HIGHS
		if row['High'] >= rCandleHigh:
			test = True
			if row['High'] < df.loc[rHigh,'High'] and rHigh-index <= minimumPeriod:
				if row['High']*1.003>df.loc[rHigh,'High']:
					test=False
					#print('Rejected High: %i (Rule 1)'%(index))
					#print('False1 High')
					#print(index)

			if row['High'] > df.loc[rHigh,'High']:
				if row['High']*0.997<df.loc[rHigh,'High'] and rHigh-index <= minimumPeriod:
					test=False
					#print('Rejected High: %i (Rule 2)'%(index))
					#print('False2 High')
					#print(index)

			if row['High'] < df.loc[rHigh,'High']:
				#engulfing candle
				if row['High'] > rCandleHigh and row['Low'] < rCandleLow:
					test = False
					#print('Rejected High: %i (Rule 3)'%(index))
					#print('False3 High')
					#print(index)


			if index>=2 and row['High']>df.loc[index-1,'High'] and test is True:
					if rHigh-index >= minimumPeriod:
						if propertyDic['Last_Level'] != 'High':
							pHigh=rHigh
						rHigh = index
						newHigh = True
						#print('New High: %i'%(index))
					elif row['High']*1.003 >= rCandleHigh:
						if propertyDic['Last_Level'] != 'High':
							pHigh=rHigh
						rHigh = index
						newHigh = True
						#print('New High: %i'%(index))
					elif row['High'] > rHigh:
						if propertyDic['Last_Level'] != 'High':
							pHigh=rHigh
						rHigh = index
						newHigh = True
						#print('New High: %i'%(index))
			'''
			elif index == 2 and test is True:
				if propertyDic['Last_Level'] != 'High':
					pHigh=rHigh
				rHigh = index
				newHigh is True
			'''

		#Updating the pHigh/pLow
		if newHigh and newLow is True:
			propertyDic['Last_Level']='Both'
		elif newHigh is True and newLow is False:
			propertyDic['Last_Level']='High'
		elif newHigh is False and newLow is True:
			propertyDic['Last_Level']='Low'

		#Sentiment Pattern
		if df.loc[rHigh,'High'] > df.loc[pHigh,'High']:
			HigherHigh=True
		else: HigherHigh=False
		if df.loc[rLow,'Low'] < df.loc[pLow,'Low']:
			LowerLow=True
		else: LowerLow=False

		#Market Sentiment
		if HigherHigh is True and LowerLow is False:
			Sentiment='Bullish'
		elif HigherHigh is True and LowerLow is True:
			Sentiment='Ranging'
		elif HigherHigh is False and LowerLow is True:
			Sentiment='Bearish'
		elif HigherHigh is False and LowerLow is False:
			Sentiment='Equilibrium'

		#Recent Candle Set
		rCandleHigh = row['High']
		rCandleLow = row['Low']
	

	#Append to Dataframe		
	df.loc[pHigh, "pHigh"] = 'pHigh'
	df.loc[rHigh, "rHigh"] = 'rHigh'
	df.loc[pLow, "pLow"] = 'pLow'
	df.loc[rLow, "rLow"] = 'rLow'


	#Print Dataframe & Sentiment 
	#print(df)

	if df.loc[1, 'Low'] < df.loc[rLow, "Low"]:
		propertyDic['Break']='Bearish'
	elif df.loc[1, 'High'] > df.loc[rHigh, "High"]:
		propertyDic['Break']='Bullish'

	results = {
	'Market':propertyDic['Market'],
	'Breaking':propertyDic['Break'],
	'Past High':df.loc[pHigh,'Close'],
	'Past Low':df.loc[pLow,'Close'],
	'Recent High':df.loc[rHigh,'Close'],
	'Recent Low:':df.loc[rLow,'Close'],
	'Sentiment':Sentiment
	}

	if entry != None:
		entry.update({'Levels':results})
	return results
	
	#########################################################################################


	'''
	print('New High')
	print(index)
	print(row['High'])
	print(rHigh)
	print(df.loc[rHigh,'High'])
	'''