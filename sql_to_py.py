import sqlite3 as sql
import pandas as pd
import time
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
#pd.set_option("display.precision", 8)



def vol_information(table="BTCUSDT_1m", fed=0):
	conn = sql.connect(database = r'/Users/neptune/Documents/PyOffline/tickerlog.db')
	cur = conn.cursor()
	cur.execute("PRAGMA table_info({tn})".format(tn = table))
	columns = [entry[1] for    entry in cur.fetchall()]
	cur.execute("SELECT {field} FROM  {tn}".format(field = "*",tn = table))

	data = [list(row) for row in cur.fetchall()] # Gets it out of tuple format
	conn.close()
	df = pd.DataFrame(data = data, columns =columns)

	if fed=='topy':
		return df
	elif fed=='feeder':
		return data

def format_data(input_df = pd.DataFrame(),columns = "All", format_time = "Keep", interval = 1, precision = 0):
	'''Basic Level Clean and Filter Data Function to Ensure Uniform Data Formats '''

	#Remove Excess Data in Columns and Rows Before Manipulation 
	### Column Filter
	if columns in ["All","A"]:
		columns = input_df.columns
	input_df = input_df[columns]
	### Interval Filter
	r = range(0,len(input_df),interval)
	input_df = input_df.loc[r,:]

	#Tidy Data to Create Uniform Entries 
	### Human Readable Time Option
	if format_time in ["Keep","K","R","Replace"]:

		if format_time in ["Keep","K"]:
			col_name = "FHour"
		else:
			col_name = "Hour"
		input_df[col_name] = input_df['Hour'].apply(lambda x : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x/1000)))
	### Precision of price
	r_cols = [x for x in columns if x in ["Open", "Low", "High", "Close"]]
	input_df[r_cols] = input_df[r_cols].round(precision)
	return input_df

def gradient( column =pd.Series() ):
	output = column.diff() / column.index.to_series().diff() #Finds Derivative
	return output

def ema( column =pd.Series(), span = 20,**kwargs ):
	if not kwargs:
		kwargs = { "span":span,"min_periods":0,"adjust":False,"ignore_na":False}
	else:
		kwargs.update({"span":span})
	output = column.ewm(**kwargs).mean()
	return output

def sma(column = pd.Series(), window = 60, **kwargs):
	if not kwargs:
		"""https://docs.scipy.org/doc/scipy/reference/signal.html#window-functions"""
		kwargs = { "window":window,"win_type":"boxcar"}
	else:
		kwargs.update({"window":window})
	output = column.rolling(**kwargs).mean()
	return output

def rsi(column = pd.Series(),ma_type = sma,window = 20):
	delta = column.diff()
	up, down = delta.copy(), delta.copy()
	up[up < 0] = 0
	down[down > 0] = 0
	roll_up , roll_down = ma_type(up, window) ,ma_type(down.abs(), window)
	RSI = 100.0 - (100.0 / (1.0 + roll_up / roll_down))
	return RSI

def sqlpy(table):
	df = vol_information(table, 'topy')
	df = format_data(df,interval = 1,columns = ['Hour','Close'], format_time = "Replace")
	df['ema'] = ema(df['Close'])
	df['sma'] = sma(df['Close'])
	df['rsi'] = rsi(df['Close'])
	# print(df[:130])
	return df

def sqlfeeder(table, periods):
	df = vol_information(table, 'feeder')
	time.sleep(3)
	return {'fetchpast':df[:periods], 'feed':df[periods:]}

# sqlpy('BTCUSDT_1m')
# run=sqlfeeder('BTCUSDT_1m', 130)
# print(run['fetchpast'])
