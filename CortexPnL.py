from datetime import datetime, timedelta
import time
import sqlite3
import xlsxwriter 
import pandas as pd

class PnL(object):
	"""docstring for PnL"""
	def __init__(self):
		day=datetime.today().strftime('%Y-%m-%d')
		dt = datetime.strptime(day, '%Y-%m-%d')
		self.week = dt - timedelta(days=dt.weekday())
		self.end = self.week + timedelta(days=6)
		self.day = datetime(dt.year, dt.month, dt.day)
		self.all = datetime(2018,1,1)
		self.date=day
		self.fetchTrades()

	def fetchTrades(self):
		"""Fetch all trades from database"""
		conn = sqlite3.connect('tradelog.db')
		c = conn.cursor()
		trades = []
		SQL='''SELECT TL.UUID, TL.Time ,TL.Status, TL.Strategy, TL.Symbol, TR.Return, TL.USD_Value
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
			trade.update({'Status':entry[2]})
			trade.update({'Strategy':entry[3]})
			trade.update({'Symbol':entry[4]})
			trade.update({'Return':entry[5]})
			trade.update({'USD':entry[6]})
			trades.append(trade)
		conn.commit()
		conn.close()
		# return trades 
		self.Scaffolding(trades,self.day)
		self.Scaffolding(trades,self.week)
		self.Scaffolding(trades,self.all)
		self.ExcelWriter()


	def Scaffolding(self,trades,since):
		relTrades=[]
		for trade in trades:
			if trade['Time']>since:
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
			self.pairs[trade['Symbol']].update({'Gross':self.pairs[trade['Symbol']]['Gross']+trade['Return']*100}) #Gross
			if trade['Status'] != 'Open':
				self.pairs[trade['Symbol']].update({'Fees':self.pairs[trade['Symbol']]['Fees']+(0.075*2)}) #Fees
			self.pairs[trade['Symbol']].update({'Return':self.pairs[trade['Symbol']]['Return']+trade['Return']*100-(0.075*2)})		
			self.pairs[trade['Symbol']].update({'PnL':self.pairs[trade['Symbol']]['PnL']+trade['USD']*self.pairs[trade['Symbol']]['Return']/100}) #PnL

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
				print(pair, self.pairs[pair]['Trades'])
				self.pairs['Total'].update({'Trades':self.pairs['Total']['Trades']+self.pairs[pair]['Trades']})
				self.pairs['Total'].update({'Open':self.pairs['Total']['Open']+self.pairs[pair]['Open']})
				self.pairs['Total'].update({'Profit':self.pairs['Total']['Profit']+self.pairs[pair]['Profit']})
				self.pairs['Total'].update({'Loss':self.pairs['Total']['Loss']+self.pairs[pair]['Loss']})
				self.pairs['Total'].update({'Gross':self.pairs['Total']['Gross']+self.pairs[pair]['Gross']})
				self.pairs['Total'].update({'Fees':self.pairs['Total']['Fees']+self.pairs[pair]['Fees']})
				self.pairs['Total'].update({'Return':self.pairs['Total']['Return']+self.pairs[pair]['Return']})
				self.pairs['Total'].update({'PnL':self.pairs['Total']['PnL']+self.pairs[pair]['PnL']})

		print(self.pairs['Total'])

		if since==self.day:
			xlname='Daily'
		elif since==self.week:
			xlname='Weekly'
		elif since==self.all:
			xlname='All-Time'
		setattr(self,xlname,pd.DataFrame(self.pairs).transpose())



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

		weeklyrow=dailylen+6
		alltimerow=weeklyrow+weeklylen+5

		getattr(self,'Daily').to_excel(writer, sheet_name='Sheet1', startrow=1)
		worksheet = writer.sheets['Sheet1']
		if len(getattr(self,'Daily')) == 1:
			worksheet.merge_range('B3:I3', 'NO TRADES', noTrade_format)
		else:
			worksheet.conditional_format(f'H3:H{3+dailylen}', {'type': '3_color_scale'})
			

		getattr(self,'Weekly').to_excel(writer, sheet_name='Sheet1', startrow=weeklyrow)
		if len(getattr(self,'Weekly')) == 1:
			worksheet.merge_range(f'B{weeklyrow+1}:I{weeklyrow+1}', 'NO TRADES', noTrade_format)		
		else:
			worksheet.conditional_format(f'H{weeklyrow+1}:H{weeklyrow+1+weeklylen-1}', {'type': '3_color_scale'})

		getattr(self,'All-Time').to_excel(writer, sheet_name='Sheet1', startrow=alltimerow)
		if len(getattr(self,'All-Time')) == 1:
			worksheet.merge_range(f'B{alltimerow+1}:I{alltimerow+1}', 'NO TRADES', noTrade_format)		
		else:
			worksheet.conditional_format(f'H{alltimerow+1}:H{alltimerow+1+alltimelen-1}', {'type': '3_color_scale'})


			
		worksheet.merge_range('A1:I1', 'Daily', merge_format)

		worksheet.merge_range(f'A{weeklyrow}:I{weeklyrow}', 'Weekly', merge_format)

		worksheet.merge_range(f'A{alltimerow}:I{alltimerow}', 'All-Time', merge_format)


		writer.save()
PnL()