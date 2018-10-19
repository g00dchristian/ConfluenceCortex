from __future__ import print_function
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from bittrex_websocket.websocket_client import BittrexSocket as BSocket
from binance.websockets import BinanceSocketManager
from languageHandler import languageHandler
from slackclient import SlackClient
from binance.client import Client
from tradeModule import Trader
from tradingInterface import *
from time import sleep
import pandas as pd
import keychain
import logging
import ccxt
import time
import sys
import os


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
#pd.set_option('display.height', None)


class TradeManagement():
	def __init__(self, exchange, logFileName):
		#-- INTRINSIC --------------------------------------------------------------- 
		self.logger = logging.getLogger(name = "Full")
		#hdlr = logging.FileHandler(str(os.path.dirname(__file__)) +'\\' + logFileName)
		lggrName = "C:\\Users\\Christian\\RedPanda\\"
		hdlr = logging.FileHandler(lggrName + logFileName)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr) 
		self.logger.setLevel('INFO')
		self.log('loaded')
		self.sc=SlackClient(keychain.slack.TradeAlertApp('BotUser'))
		self.sc_read=SlackClient(keychain.slack.TradeAlertApp('OAuth'))

		#-- EXTRINSIC --------------------------------------------------------------- 
		self.trade_file = r'C:\Users\Christian\RedPanda\TradeLog.csv'
		self.startup = 1
		self.TWA = 1 #TradeWatchActive

		#-- WEBSOCKET ---------------------------------------------------------------
		callbacks=[self.WebSocketFunction]
		#ticker_fetch=getattr(ccxt,exchange)().fetch_tickers()
		ticker_fetch = ['BTC/USDT']
		self.market_jar=[]
		for market in ticker_fetch:
			if market[-3:] != 'USD': 
				self.market_jar.append(market)
				toParse = [market]
				parsedMarket = languageHandler(output_lang = exchange.capitalize(),inputs = toParse,input_lang = "TradeModule")
				setattr(self, parsedMarket[0], {})
				#self.data.update({parsedMarket[0]:None})
		if exchange == 'bittrex':
			self.bxSocket= tradingInterface(BittrexSocket(),self.market_jar,callbacks)
			self.bnSocket= tradingInterface(BinanceSocket(),[],callbacks)
		elif exchange == 'binance':
			self.bxSocket= tradingInterface(BittrexSocket(),[],callbacks)
			self.bnSocket= tradingInterface(BinanceSocket(),self.market_jar,callbacks)

		self.TradeWatch(startup=True)


	def TradeWatch(self, startup=False):
		try:
			TST = os.path.getmtime(self.trade_file) #Trade Save Timestamp
			
			if startup:
				self.trade_df = pd.read_csv(self.trade_file)
				self.trade_df = self.trade_df.set_index('OrderTime')
				print(self.trade_df)
				self.TST = TST
				time.sleep(3)
				self.startup = 0
				print('START UP COMPLETE')
			x = 1
			while x == 1: 
				TST = os.path.getmtime(self.trade_file) #Trade Save Timestamp
				if self.TST != TST:
					self.trade_df = pd.read_csv(self.trade_file)
					self.trade_df = self.trade_df.set_index('OrderTime')
					print(self.trade_df)
					self.TST = TST #Trade Save Timestamp
				time.sleep(0.1)
		except:
			self.TWA = 0




	def WebSocketFunction(self,bbo):
		if self.startup == 1:
			pass
		else:
			self.log(bbo)
			if self.TWA == 0:
				self.TradeWatch()
				self.TWA = 1
			trades = self.trade_df[self.trade_df['Status']=='Open']
			for i, row in trades.iterrows():
				if row['Market'] == bbo.market:
					if row['Side'] == 'Buy':
						if bbo.bidPrice >= float(row['ProfitTake']):
							self.trade_df.loc[i, "Status"] = "Closed"
							self.CloseTrade(bbo.bidPrice, 'ProfitTake', i)
							print('TAKE PROFIT')
						elif bbo.bidPrice <= float(row['StopLoss']):
							self.trade_df.loc[i, "Status"] = "Closed"
							self.CloseTrade(bbo.bidPrice, 'StopLoss', i)
					elif row['Side'] == 'Sell':
						if bbo.bidPrice <= float(row['ProfitTake']):
							self.trade_df.loc[i, "Status"] = "Closed"
							self.CloseTrade(bbo.bidPrice, 'ProfitTake', i)
							print('TAKE PROFIT')
						elif bbo.bidPrice >= float(row['StopLoss']):
							self.trade_df.loc[i, "Status"] = "Closed"
							self.CloseTrade(bbo.bidPrice, 'StopLoss', i)
							print('STOP LOSS')
			wins = self.trade_df[self.trade_df.Result=='ProfitTake'].shape[0]
			loss = self.trade_df[self.trade_df.Result=='StopLoss'].shape[0]




	def CloseTrade(self,closePrice, result, index):
		duration = time.time()-float(index)/100000
		self.trade_df.loc[index, 'Order Duration'] = duration
		self.trade_df.loc[index, 'Result'] = result
		self.trade_df.loc[index, 'CloseTime'] = time.time()
		self.trade_df.to_csv(self.trade_file)
		wins = self.trade_df[self.trade_df.Result=='ProfitTake'].shape[0]
		loss = self.trade_df[self.trade_df.Result=='StopLoss'].shape[0]
		self.sc.api_call( "chat.postMessage", channel=keychain.slack.IDs('levelalert'), text=('Wins: %i | Losses: %i'%(wins,loss)))


	def log(self,msg):
		print(msg)	
		self.logger.info(msg)


TradeManagement(exchange = 'binance', logFileName='TM_Testing.log')