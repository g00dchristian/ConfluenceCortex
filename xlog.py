import pandas as pd
import time
import datetime
from uuid import uuid4

def xlog(pkg):
	file_location = r'C:\Users\Christian\RedPanda\TradeLog.csv'
	trade_df = pd.read_csv(file_location)
	trade_df = trade_df.set_index('OrderTime')
	temp_df = []
	Status = 'Open'
	Result = ""
	tradeDetails = {}
	tradeDetails.update({'Side':pkg['Side']})  
	tradeDetails.update({'Status':Status})
	tradeDetails.update({'Result':Result})
	tradeDetails.update({'Exchange':pkg['Exchange']})
	tradeDetails.update({'Market':pkg['Market']})
	tradeDetails.update({'OrderTime':datetime.datetime.now()})
	tradeDetails.update({'OrderPrice':pkg['Price']})
	tradeDetails.update({'StopLoss':'Nil'})
	tradeDetails.update({'Strategy':pkg['Strategy']})
	tradeDetails.update({'UUID':uuid4()})
	print([tradeDetails])

	temp_df.append(tradeDetails)
	temp_df = pd.DataFrame(temp_df)
	temp_df = temp_df.set_index('OrderTime')
	frames = [trade_df, temp_df]
	result = pd.concat(frames, sort=True)

	a = result.to_csv(file_location)

