import pandas as pd
 
#df= pd.read_csv('C:\\Users\\Christian\\RedPanda\\DF.csv')

propertyDic = {
'Market':'BTC',
'Periods':131,
'Last_Level':'BTC'+'_lastlevel',
'RSI':'BTC'+'_RSI',
'PS':'BTC'+'_PS',
'Break':'BTC'+'_Break',
'Sentiment':'BTC'+'_MS',
'VolumeAnalysis':'BTC'+'_VA'
}

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
	
def Price_Shear(df, propertyDic, EMAs):
	"""EMAs variable must be a list"""
	
	ShearFactor=1.012

	if len(EMAs)==2:
		SMA=min(EMAs) #Simple moving average is calculated based upon the smallest EMA value
		for index, row in df.iterrows(): 
			if index <= propertyDic['Periods']-SMA+1: 
				spSMACP = index+SMA-1 #starting point Simple Moving Average Closing Price
				CPT = 0 #Closing Price Total
				while spSMACP>=index:
					CPT=CPT+df.loc[spSMACP, 'Close']
					spSMACP=spSMACP-1
				df.loc[index,'SMA']=CPT/SMA
		for EMA in EMAs:
			EMAd='EMA_'+str(EMA) #EMA table header
			for index, row in df.iterrows():
				if index == propertyDic['Periods']-EMA+1:
					df.loc[index,EMAd]=df.loc[index,'SMA']
				elif index < propertyDic['Periods']-EMA+1:
					func=lambda x:(2/(x+1))
					EMAv=((df.loc[index,'Close']-df.loc[index+1,EMAd])*func(EMA)+df.loc[index+1,EMAd])
					df.loc[index,EMAd]=EMAv

		pullEMA=lambda x,y: df.loc[y,'EMA_'+str(x)]

		if pullEMA(min(EMAs),2) >= pullEMA(max(EMAs),2):
			senti='bullish'
		else:
			senti='bearish'

		rEMAspread=pullEMA(min(EMAs),2)/pullEMA(max(EMAs),2)
		r2EMAspread=pullEMA(min(EMAs),3)/pullEMA(max(EMAs),3)


		if r2EMAspread <=1.0050 or r2EMAspread >= 0.9950:
			if rEMAspread <=1.0035 or rEMAspread >= 0.9965:
				EMAvalues=[pullEMA(min(EMAs),2),pullEMA(max(EMAs),2)]
				EMAcentre=min(EMAvalues)+((max(EMAvalues)-min(EMAvalues))/2)
				if df.loc[1,'Close']>=EMAcentre*ShearFactor:
					output='Bullish'
				elif df.loc[1,'Close']<=EMAcentre*(2-ShearFactor):
					output='Bearish'
				else: output='Nil'
			else: output='Nil'
		else: output='Nil'


	else:
		output='2 EMA inputs required'
	# print(df)
	# print(EMAcentre)
	return(output)

#Price_Shear(df, propertyDic,[12,26])