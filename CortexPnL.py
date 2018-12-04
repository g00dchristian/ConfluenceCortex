from datetime import datetime, timedelta
from slacker import send_message
import time
import sqlite3
import xlsxwriter 
import ccxt
import pandas as pd
from languageHandled import languageHandler
from accountValue import Account_Balance

class PnL(object):
	"""docstring for PnL"""
	def __init__(self, report_type):
		day=datetime.today().strftime('%Y-%m-%d')
		dt = datetime.strptime(day, '%Y-%m-%d')
		dst=time.localtime().tm_isdst
		"""
		#Daylight savings 
		if dst==1: 
			UTC_TD=11*3600 #UTC time difference w Daylight savings in seconds
		else:
			UTC_TD=10*3600 #UTC time difference w/o Daylight savings in seconds
		"""

		week_epoch = ((int(time.time()/86400)-7)*86400)+21600 #7 days ago at 4pm (5pm during DST)
		self.week = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(week_epoch))
		print(self.week)

		# self.night = datetime(dt.year, dt.month, dt.day-1, 17)
		day_epoch = ((int(time.time()/86400)-1)*86400)+21600 #1 day ago at 4pm (5pm during DST)
		self.day = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(day_epoch))
		print(self.day)

		self.all = "2018-11-12 17:00:00"
		self.date=day
		self.fetchBalance()
		self.fetchTrades(report_type)

	def fetchBalance(self):
		AB=Account_Balance('binance')
		self.btcusd=AB[1]
		self.b_dates=[]
		self.b_values=[]

		print(AB[0])
		conn = sqlite3.connect(r'C:\Users\Christian\Google Drive\PyScripts\ConfluenceCortex\account_balance.db')
		c = conn.cursor()
		#############
		c.execute("INSERT INTO BINANCE(Date,Balance) VALUES(:Date,:Balance)",
				{
				'Balance':AB[0],
				'Date':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				})
		conn.commit()		
		#############
		balances = []
		SQL='''SELECT BN.DATE, BN.BALANCE
			FROM BINANCE AS BN'''
		c.execute(SQL)
		for entry in c.fetchall():
			balance={'Date':entry[0],'Balance':entry[1]}
			balances.append(balance)
			self.b_dates.append(entry[0])
			self.b_values.append(entry[1])
		conn.commit()
		conn.close()




	def fetchTrades(self, report_type):
		"""Fetch all trades from database"""
		conn = sqlite3.connect(r'C:\Users\Christian\Google Drive\PyScripts\ConfluenceCortex\tradelog.db')
		# conn = sqlite3.connect(r'C:\Users\Christian\Dropbox\Crypto\Python\ConfluenceCortex\tradelog.db')
		c = conn.cursor()
		trades = []
		SQL='''SELECT TL.UUID, TL.Time, TL.Close_Time, TL.Status, TL.Strategy, TL.Symbol, TR.Return, TL.USD_Value, TL.Clip_Size, TR.Profit_Level, TR.Stop_Level, TR.OrderPrice
		FROM Confluence_Ratings as CR
		left join Trade_List as TL
			ON CR.UUID = TL.UUID
		left join Trade_Results as TR
			on CR.UUID = TR.UUID'''
		c.execute(SQL)
		for entry in c.fetchall():
			trade={}
			trade.update({'UUID':entry[0]})
			trade.update({'Time':datetime.strptime(entry[1],'%Y-%m-%d %H:%M:%S.%f')})
			trade.update({'Close_Time':datetime.strptime(entry[2],'%Y-%m-%d %H:%M:%S.%f')})  
			trade.update({'Status':entry[3]})
			trade.update({'Strategy':entry[4]})
			trade.update({'Symbol':entry[5]})
			trade.update({'Return':entry[6]})
			trade.update({'USD':entry[7]})
			trade.update({'Clip_Size':entry[8]})
			trade.update({'Profit_Take':entry[9]})
			trade.update({'Stop_Loss':entry[10]})
			trade.update({'Order_Price':entry[11]})
			trades.append(trade)
		conn.commit()
		conn.close()

		# return trades 
		if report_type == 'Daily':
			self.Scaffolding(trades,self.day, 'Daily')
			print('done day Scaffolding')
			self.Scaffolding(trades,self.week, 'Weekly')
			print('done week Scaffolding')
			self.Scaffolding(trades,self.all, 'All-Time')
			print('done all Scaffolding')
			self.ListOpenTrades(trades)
			self.ExcelWriter()
		elif report_type == 'Nightly':
			self.Scaffolding(trades, self.night, 'Nightly')
			self.Slack()



	def ListOpenTrades(self,trades):
		openTrades=[]
		for trade in trades:
			if trade['Status']=='Open':
				openTrades.append(trade)
			for trade in openTrades:
				trade.pop('UUID',None)
				trade.pop('Time',None)
				trade.pop('Close_Time',None)
				trade.pop('Status',None)
				trade.pop('Strategy',None)
				trade.pop('Return',None)
				trade.update({'Price':ccxt.binance().fetch_ticker(languageHandler(output_lang="TradeModule", inputs=[trade['Symbol']], input_lang='Binance')[0])['last']})
				if trade['Clip_Size']<0:
					trade.update({'R_Return':1-(trade['Price']/(trade['Order_Price']))})
					trade.update({'R_PnL':trade['R_Return']*trade['USD']})
					trade.update({'USD':-trade['USD']})
				else:
					trade.update({'R_Return':(trade['Price']/trade['Order_Price'])})
					trade.update({'R_PnL':trade['R_Return']*trade['USD']})

		# self.Open_Trades= pd.DataFrame(openTrades).set_index('Symbol')
		self.Open_Trades=openTrades
		for trade in self.Open_Trades:
			print(trade)
		print(self.Open_Trades)




	def Scaffolding(self,trades,since, tf):
		relTrades=[]
		for trade in trades:
			if trade['Close_Time']>datetime.strptime(since,'%Y-%m-%d %H:%M:%S'):
				relTrades.append(trade)

		self.pairs={}


		for trade in relTrades:
			dic={
			'Trades':0,
			'Open':0,
			'Profit':0,
			'Loss':0,
			'Gross':0,
			'Fees':0,
			'Return':0,
			'PnL':0
			}
			self.pairs.update({trade['Symbol']:dic})

		####### Compile trades into pairs
		for trade in relTrades:
			self.pairs[trade['Symbol']].update({'Trades':self.pairs[trade['Symbol']]['Trades']+1}) #Number of Trades
			if trade['Status'] == 'Open':
				self.pairs[trade['Symbol']].update({'Open':self.pairs[trade['Symbol']]['Open']+1}) #Open Trades
			elif trade['Status'] == 'Profit':
				self.pairs[trade['Symbol']].update({'Profit':self.pairs[trade['Symbol']]['Profit']+1}) #Profit Trades
			elif trade['Status'] == 'Loss':
				self.pairs[trade['Symbol']].update({'Loss':self.pairs[trade['Symbol']]['Loss']+1}) #Loss Trades
			if trade['Status'] != 'Open':
				self.pairs[trade['Symbol']].update({'Gross':self.pairs[trade['Symbol']]['Gross']+trade['Return']}) #Gross
				self.pairs[trade['Symbol']].update({'Fees':self.pairs[trade['Symbol']]['Fees']-(0.00075*2)}) #Fees
				self.pairs[trade['Symbol']].update({'Return':self.pairs[trade['Symbol']]['Return']+trade['Return']-(0.00075*2)})		
			self.pairs[trade['Symbol']].update({'PnL':self.pairs[trade['Symbol']]['PnL']+trade['USD']*self.pairs[trade['Symbol']]['Return']}) #PnL


		######## Total Dic
		self.pairs.update({'Total':{
			'Trades':0,
			'Open':0,
			'Profit':0,
			'Loss':0,
			'Gross':0,
			'Fees':0,
			'Return':0,
			'PnL':0
			}})


		####### Compile trades into pairs
		for pair in self.pairs:
			if pair != 'Total':
				self.pairs['Total'].update({'Trades':self.pairs['Total']['Trades']+self.pairs[pair]['Trades']})
				self.pairs['Total'].update({'Open':self.pairs['Total']['Open']+self.pairs[pair]['Open']})
				self.pairs['Total'].update({'Profit':self.pairs['Total']['Profit']+self.pairs[pair]['Profit']})
				self.pairs['Total'].update({'Loss':self.pairs['Total']['Loss']+self.pairs[pair]['Loss']})
				self.pairs['Total'].update({'Gross':self.pairs['Total']['Gross']+self.pairs[pair]['Gross']})
				self.pairs['Total'].update({'Fees':self.pairs['Total']['Fees']+self.pairs[pair]['Fees']})
				self.pairs['Total'].update({'Return':self.pairs['Total']['Return']+self.pairs[pair]['Return']})
				self.pairs['Total'].update({'PnL':self.pairs['Total']['PnL']+self.pairs[pair]['PnL']})

		print(self.pairs['Total'])
		setattr(self,tf,pd.DataFrame(self.pairs).transpose())



	def ExcelWriter(self):
		writer = pd.ExcelWriter(f'{self.date} Cortex PnL.xlsx', engine='xlsxwriter')
		workbook  = writer.book
		merge_format = workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color':'black',
			'font_color':'white'
			})

		noTrade_format = workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			})
	
		dailylen=len(getattr(self,'Daily'))
		weeklylen=len(getattr(self,'Weekly'))
		alltimelen=len(getattr(self,'All-Time'))
		opentradelen=len(self.Open_Trades)

		weeklyrow=dailylen+6
		alltimerow=weeklyrow+weeklylen+5
		opentraderow=alltimerow+alltimelen+4


		total_format=workbook.add_format({'bg_color':'#C0C0C0','bold':True})
		negative_format = workbook.add_format({'bg_color': '#FFC7CE',
		                               'font_color': '#9C0006'})
		positive_format = workbook.add_format({'bg_color': '#C6EFCE',
                               'font_color': '#006100'})

		getattr(self,'Daily').to_excel(writer, sheet_name='Sheet1', startrow=1)
		worksheet = writer.sheets['Sheet1']
		if len(getattr(self,'Daily')) == 1:
			worksheet.merge_range('B3:I3', 'NO TRADES', noTrade_format)
		else:
			worksheet.conditional_format(f'H3:H{3+dailylen-2}',{'type': 'cell',
                                         'criteria': '>',
                                         'value': 0,
                                         'format': positive_format}) 
			worksheet.conditional_format(f'H3:H{3+dailylen-2}',{'type': 'cell',
                                         'criteria': '<',
                                         'value': 0,
                                         'format': negative_format})
			worksheet.conditional_format(f'A{3+dailylen-1}:I{3+dailylen-1}', {'type': 'no_errors','format':total_format})
			

		getattr(self,'Weekly').to_excel(writer, sheet_name='Sheet1', startrow=weeklyrow)
		if len(getattr(self,'Weekly')) == 1:
			worksheet.merge_range(f'B{weeklyrow+1}:I{weeklyrow+1}', 'NO TRADES', noTrade_format)		
		else:
			worksheet.conditional_format(f'H{weeklyrow+2}:H{weeklyrow+1+weeklylen-1}',{'type': 'cell',
                                         'criteria': '>',
                                         'value': 0,
                                         'format': positive_format})
			worksheet.conditional_format(f'H{weeklyrow+2}:H{weeklyrow+1+weeklylen-1}',{'type': 'cell',
                                         'criteria': '<',
                                         'value': 0,
                                         'format': negative_format})
			worksheet.conditional_format(f'A{weeklyrow+1+weeklylen}:I{weeklyrow+1+weeklylen}', {'type': 'no_errors','format':total_format})


		getattr(self,'All-Time').to_excel(writer, sheet_name='Sheet1', startrow=alltimerow)
		if len(getattr(self,'All-Time')) == 1:
			worksheet.merge_range(f'B{alltimerow+1}:I{alltimerow+1}', 'NO TRADES', noTrade_format)		
		else:
			worksheet.conditional_format(f'H{alltimerow+2}:H{alltimerow+1+alltimelen-1}',{'type': 'cell',
                                         'criteria': '>',
                                         'value': 0,
                                         'format': positive_format})
			worksheet.conditional_format(f'H{alltimerow+2}:H{alltimerow+1+alltimelen-1}',{'type': 'cell',
                                         'criteria': '<',
                                         'value': 0,
                                         'format': negative_format})			
			worksheet.conditional_format(f'A{alltimerow+1+alltimelen}:I{alltimerow+1+alltimelen}', {'type': 'no_errors','format':total_format})

		

		#### Table Headers
		worksheet.merge_range('A1:I1', f'Daily - {self.day}', merge_format)
		worksheet.merge_range(f'A{weeklyrow}:I{weeklyrow}', f'Last 7 Days - {self.week}', merge_format)
		worksheet.merge_range(f'A{alltimerow}:I{alltimerow}', 'All-Time', merge_format)
		worksheet.merge_range(f'A{opentraderow}:I{opentraderow}', 'Open Trades', merge_format)

		#### Cell Formatting
		currency_format = workbook.add_format({'num_format':'$#,##0.00'})
		percent_format = workbook.add_format({'num_format':'0.00%'})
		number_format = workbook.add_format({'num_format':'0.000'})

		worksheet.set_column('B:C', 8.43, percent_format)
		worksheet.set_column('F:F', 8.43, currency_format)
		worksheet.set_column('H:H', 8.43, percent_format)
		


		opencellformat=workbook.add_format({'bold': True, 'border':True, 'center_across':True})
		if len(self.Open_Trades) == 0:
			worksheet.merge_range(f'A{opentraderow+1}:I{opentraderow+1}', 'NO OPEN TRADES', noTrade_format)		
		else:
			__row=opentraderow+1	
			worksheet.write(f'A{__row}','Symbol',opencellformat)
			worksheet.write(f'B{__row}','USD',opencellformat)
			worksheet.write(f'C{__row}','Clip_Size',opencellformat)
			worksheet.write(f'D{__row}','Return',opencellformat)
			worksheet.write(f'E{__row}','R_PnL',opencellformat)
			worksheet.write(f'F{__row}','OrderP',opencellformat)
			worksheet.write(f'G{__row}','Price',opencellformat)
			worksheet.write(f'H{__row}','P/Take',opencellformat)
			worksheet.write(f'I{__row}','S/Loss',opencellformat)
			__row=__row+1
			for trade in self.Open_Trades:
				worksheet.write(f'A{__row}',trade['Symbol'],opencellformat)
				worksheet.write(f'B{__row}',trade['USD'], currency_format)
				worksheet.write(f'C{__row}',trade['Clip_Size'], number_format)
				worksheet.write(f'D{__row}',trade['R_Return'], percent_format)
				worksheet.write(f'E{__row}',trade['R_PnL'], currency_format)
				worksheet.write(f'F{__row}',trade['Order_Price'], number_format)
				worksheet.write(f'G{__row}',trade['Price'], number_format)
				worksheet.write(f'H{__row}',trade['Profit_Take'], number_format)
				worksheet.write(f'I{__row}',trade['Stop_Loss'], number_format)
				__row=__row+1








		worksheet.write_column(f'A{opentraderow+1+opentradelen+4}', self.b_dates)
		worksheet.write_column(f'F{opentraderow+1+opentradelen+4}', self.b_values)

		_row=opentraderow+opentradelen+4
		row_end=_row+len(self.b_values)-1

		chart = workbook.add_chart({'type': 'line'})
		chart.add_series({
		    'categories': ['Sheet1', _row, 0, row_end, 0],
		    'values':     ['Sheet1', _row, 5, row_end, 5],
		    'line':       {'color': 'blue'},
		})

		chart.set_y_axis({
		    'name': 'USD ($)',
		    'name_font': {'size': 12, 'bold': True},
		})
		chart.set_size({'width': 720, 'height': 400})
		chart.set_title({'name': 'Account Balance'})
		worksheet.insert_chart(f'A{opentraderow+1+opentradelen+3}', chart, {'x_offset': 0, 'y_offset': 10})

		writer.save()



	def Slack(self):
		print(self.pairs['Total'])
		if len(self.pairs) == 1:
			msg = 'CORTEX UPDATE-- No trades overnight'
		else:
			t=self.pairs['Total']
			opTrades = f'{t["Open"]} Trade(s) still Open\n'
			none_open = 'All Trades Closed\n'
			msg = f'{t["Trades"]} Overnight Cortex Trades\n{opTrades if t["Open"]>0 else none_open}Closed Trades Net Return: {(t["Return"]*100):.2f}%'
			print(msg)
		send_message(msg)


