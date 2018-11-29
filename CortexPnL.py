from datetime import datetime, timedelta
from slacker import send_message
import time
import sqlite3
import xlsxwriter 
import pandas as pd

class PnL(object):
	"""docstring for PnL"""
	def __init__(self, report_type):
		day=datetime.today().strftime('%Y-%m-%d')
		dt = datetime.strptime(day, '%Y-%m-%d')
		self.week = datetime(dt.year, dt.month, dt.day-7)
		self.night = datetime(dt.year, dt.month, dt.day-1, 17)
		self.end = self.week + timedelta(days=6)
		self.day = datetime(dt.year, dt.month, dt.day)
		self.all = datetime(2018,11,12)
		self.date=day
		self.fetchTrades(report_type)

	def fetchTrades(self, report_type):
		"""Fetch all trades from database"""
		conn = sqlite3.connect(r'C:\Users\Christian\Google Drive\PyScripts\ConfluenceCortex\tradelog.db')
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
		if report_type == 'Daily':
			self.Scaffolding(trades,self.day, 'Daily')
			print('done day Scaffolding')
			self.Scaffolding(trades,self.week, 'Weekly')
			print('done week Scaffolding')
			self.Scaffolding(trades,self.all, 'All-Time')
			print('done all Scaffolding')
			self.ExcelWriter()
		elif report_type == 'Nightly':
			self.Scaffolding(trades, self.night, 'Nightly')
			self.Slack()

	def Scaffolding(self,trades,since, tf):
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

		weeklyrow=dailylen+6
		alltimerow=weeklyrow+weeklylen+5


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
		worksheet.merge_range('A1:I1', f'Daily - {self.day.strftime("%Y-%m-%d")}', merge_format)
		worksheet.merge_range(f'A{weeklyrow}:I{weeklyrow}', f'Last 7 Days - {self.week.strftime("%Y-%m-%d")}', merge_format)
		worksheet.merge_range(f'A{alltimerow}:I{alltimerow}', 'All-Time', merge_format)

		#### Cell Formatting
		currency_format = workbook.add_format({'num_format':'$#,##0.00'})
		percent_format = workbook.add_format({'num_format':'0.00%'})

		worksheet.set_column('B:C', 8.43, percent_format)
		worksheet.set_column('F:F', 8.43, currency_format)
		worksheet.set_column('H:H', 8.43, percent_format)
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


