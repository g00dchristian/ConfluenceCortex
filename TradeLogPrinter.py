import pandas as pd
import time
import datetime
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
#pd.set_option('display.height', None)
def tradelistprinter():
	file_location = r'C:\Users\Christian\RedPanda\TradeLog.csv'
	x = 1
	modTime=os.path.getmtime(file_location)
	trade_df = pd.read_csv(file_location)
	print(trade_df)
	while x == 1:
		modTimeCheck=os.path.getmtime(file_location)
		if modTimeCheck != modTime:
			trade_df = pd.read_csv(file_location)
			modTime = modTimeCheck
			print('')
			print(datetime.datetime.now())
			print(trade_df)
			time.sleep(2)
		else:
			time.sleep(5)


tradelistprinter()