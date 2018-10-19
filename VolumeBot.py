from __future__ import print_function
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from bittrex_websocket.websocket_client import BittrexSocket as BSocket
from binance.websockets import BinanceSocketManager
from languageHandled import languageHandler
from slackclient import SlackClient
from binance.client import Client
from tradeModule import Trader
from KlinesWebsocket import *
from time import sleep
import pandas as pd
import keychain
import logging
import ccxt
import time
import sys
import os

"""
TO-DO LIST:
- pM minimum to stop trades on doji candles
- log pM/vM values
"""

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
#pd.set_option('display.height', None)


class VolumeBot():
	def __init__(self, exchange, logFileName):
		#-- INTRINSIC --------------------------------------------------------------- 
		self.logger = logging.getLogger(name = "Full")
		hdlr = logging.FileHandler(str(os.path.dirname(__file__)) +'\\' + logFileName)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr) 
		self.logger.setLevel('INFO')
		self.log('loaded')
		self.sc=SlackClient(keychain.slack.TradeAlertApp('BotUser'))
		self.sc_read=SlackClient(keychain.slack.TradeAlertApp('OAuth'))

		#-- EXTRINSIC --------------------------------------------------------------- 
		self.data = {}
		self.startup = 1
		self.vM = 1.5
		self.pM = 1.1
		self.refractory = {}
		self.trades = {}
		self.score = {'ProfitTaken':0, 'StoppedOut':0}

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
		self.FetchPast(exchange)



	def FetchPast(self, exchange):
		for market in self.market_jar:
			self.refractory.update({market:0})
			self.trades.update({market:[]})
			name = market+'_past'
			setattr(self, name, getattr(ccxt,exchange)().fetch_ohlcv(market, timeframe='15m')[-20:])
			dfName = market+'_df'
			setattr(self, dfName, [])
			x=20
			for candle in getattr(self,name):
				pdEntry = {}
				pdEntry.update({'Time': candle[0]})
				pdEntry.update({'Volume' : candle[5]})
				move = abs(candle[4]-candle[1])
				pdEntry.update({'pChange':move})
				pdEntry.update({'Period':x})
				getattr(self, dfName).append(pdEntry)
				x=x-1
			df = pd.DataFrame(getattr(self,dfName))
			df = df.set_index('Time')
			##print(getattr(self,name))
		#print('-------------- STARTED --------------')
		self.startup=0



	def WebSocketFunction(self,kline):
		if self.startup == 1:
			time.sleep(4)
		else:
			dfName = languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]+'_df'
			candleData = {
			'Time':int(kline.openTime),
			'pChange':abs(kline.kClose-kline.kOpen),
			'Volume':kline.kVolume,
			'Period':1
			}
			##print(getattr(self,dfName)[-1:][0]['Time'])
			##print(candleData['Time'])
			if getattr(self,dfName)[-1:][0]['Time'] == candleData['Time']:
				setattr(self,dfName, getattr(self,dfName)[:-1])
				getattr(self,dfName).append(candleData)
			else:
				getattr(self,dfName).append(candleData)
				setattr(self,dfName, getattr(self,dfName)[1:])
				y=20
				for candle in getattr(self,dfName):
					candle.update({'Period':y})
					y=y-1
			df=pd.DataFrame(getattr(self,dfName))
			df = df.set_index('Time')


			#---- CALCULATIONS -------------------------------
			df['Weighting'] = 1/(df['Period']**0.5)
			weight_sum = df['Weighting'].sum()
			df['vSignal'] = (df['Volume'] * df['Weighting']) /weight_sum
			df['pSignal'] = (df['pChange'] * df['Weighting']) /weight_sum
			vol_mv_avg = df['vSignal'].sum()
			price_mv_avg = df['pSignal'].sum()
			vThreshold = self.vM*vol_mv_avg
			pThreshold = self.pM*price_mv_avg

			if kline.market == 'BTCUSDT':
				pThreshDistance = float(pThreshold) - abs(kline.kClose-kline.kOpen)
				vThreshDistance = float(vThreshold) - kline.kVolume
				print(df)
				print('\npThreshDistance: %f\nvThreshDistance: %f\n'%(pThreshDistance,vThreshDistance))

			#---- VOL_EYE -------------------------------
			if abs(kline.kClose-kline.kOpen) <= pThreshold and abs(kline.kVolume) >= vThreshold:
				if time.time() >= self.refractory[languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]]:
					file_location = r'C:\Users\Christian\RedPanda\TradeLog.csv'
					trade_df = pd.read_csv(file_location)
					trade_df = trade_df.set_index('OrderTime')
					temp_df = []
					Market = languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]
					Status = 'Open'
					Result = ""
					if kline.kClose-kline.kOpen > 0: 
						Side = 'Buy'
						ProfitTake = kline.kClose*1.015
						StopLoss = kline.kClose*0.99
					else: 
						Side = 'Sell'
						ProfitTake = kline.kClose*0.99
						StopLoss = kline.kClose*1.015
					tradeDetails = {}
					tradeDetails.update({'Side':Side})  
					tradeDetails.update({'Status':Status})
					tradeDetails.update({'Result':Result})
					tradeDetails.update({'ProfitTake':ProfitTake})
					tradeDetails.update({'Exchange':kline.exchange})
					tradeDetails.update({'Market':kline.market})
					tradeDetails.update({'OrderTime':time.time()*100000})
					tradeDetails.update({'OrderPrice':kline.kClose})
					tradeDetails.update({'StopLoss':StopLoss})
					tradeDetails.update({'Strategy':('VolBot_vM: %.2f_pM: %.2f'%(self.vM,self.pM))})
					#print([tradeDetails])
					self.trades[Market].append(tradeDetails)
					temp_df.append(tradeDetails)
					temp_df = pd.DataFrame(temp_df)
					temp_df = temp_df.set_index('OrderTime')
					frames = [trade_df, temp_df]
					result = pd.concat(frames, sort=True)
					print(result)
					
					tradelogged = 0
					try:
						result.to_csv(file_location)
						tradelogged = 1
					except:
						print('Trade Failed to Log')
					if tradelogged == 1:
						print('ACTION: Send Trade')


					#print('')
					#print(self.trades)
					#print('')

					refrac = time.time()+60*60
					self.refractory.update({languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]:refrac})
					self.log('/////   TRADE   ////////////////////////////////////////\nMarket: %s\nSide: %s\nOrderPrice: %f\nProfitTake: %f\nStopLoss: %f\n'%(Market, Side, kline.kClose, ProfitTake, StopLoss))
					self.log(df)
				#else:
				'''
					Market = languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]
					Status = 'Open'
					Result = ""
					if kline.kClose-kline.kOpen > 0: 
						Side = 'Buy'
						ProfitTake = kline.kClose*1.01
						StopLoss = kline.kClose*0.99
					else: 
						Side = 'Sell'
						ProfitTake = kline.kClose*0.99
						StopLoss = kline.kClose*1.01					
					tradeDetails = {}
					tradeDetails.update({'Side':Side})
					tradeDetails.update({'Status':Status})
					tradeDetails.update({'Result':Result})
					tradeDetails.update({'ProfitTake':ProfitTake})
					tradeDetails.update({'Market':kline.market})
					tradeDetails.update({'OrderTime':time.time()})
					tradeDetails.update({'OrderPrice':kline.kClose})
					tradeDetails.update({'StopLoss':StopLoss})
					#print([tradeDetails])
					#self.trades[Market].append(tradeDetails)
					#print('')
					#print(self.trades)
					#print('')
					self.log('/////   TRADE REJECTED: Refractory Period  /////////////////////////////\nMarket: %s\nSide: %s\nOrderPrice: %f\nProfitTake: %f\nStopLoss: %f\n'%(Market, Side, kline.kClose, ProfitTake, StopLoss))

			#---- VOL_EYE -------------------------------
			goodScore = self.score['ProfitTaken']+1
			badScore = self.score['StoppedOut']+1
			for trade in self.trades[languageHandler(output_lang="TradeModule", inputs=[kline.market], input_lang=kline.exchange)[0]]:
				#print(trade)
				if trade['Status'] == 'Open':
					if trade['Side'] == 'Buy':
						if kline.kClose >= trade['ProfitTake']:
							self.score.update({'ProfitTaken':goodScore})
							trade.update({'Status':'Closed'})
							trade.update({'Result':'ProfitTaken'})
							trade.update({'OrderDuration':time.time()-trade['OrderTime']})
							self.log('----- PROFIT TAKEN -----\nTrade Summary: %s\nScoreboard: %s\n'%(trade,self.score))
							self.sc.api_call( "chat.postMessage", channel=keychain.slack.IDs('levelalert'), text=('Trade Summary: %s\nScoreboard: %s\n'%(trade,self.score)))
						elif kline.kClose <= trade['StopLoss']:
							self.score.update({'StoppedOut':badScore})
							trade.update({'Status':'Closed'})
							trade.update({'Result':'Trade StoppedOut'})
							trade.update({'OrderDuration':time.time()-trade['OrderTime']})
							self.log('----- TRADE STOPPED OUT -----\nTrade Summary: %s\nScoreboard: %s\n'%(trade,self.score))
					elif trade['Side'] == 'Sell':
						if kline.kClose <= trade['ProfitTake']:
							self.score.update({'ProfitTaken':goodScore})
							trade.update({'Status':'Closed'})
							trade.update({'Result':'ProfitTaken'})
							trade.update({'OrderDuration':time.time()-trade['OrderTime']})
							self.log('----- PROFIT TAKEN -----\nTrade Summary: %s\nScoreboard: %s\n'%(trade,self.score))
							self.sc.api_call( "chat.postMessage", channel=keychain.slack.IDs('levelalert'), text=('Trade Summary: %s\nScoreboard: %s\n'%(trade,self.score)))
						elif kline.kClose >= trade['StopLoss']:
							self.score.update({'StoppedOut':badScore})
							trade.update({'Status':'Closed'})
							trade.update({'Result':'Trade StoppedOut'})
							trade.update({'OrderDuration':time.time()-trade['OrderTime']})
							self.log('----- TRADE STOPPED OUT -----\nTrade Summary: %s\nScoreboard: %s\n'%(trade,self.score))

				'''

			print(kline)





	def log(self,msg):
		print(msg)	
		self.logger.info(msg)



VolumeBot(exchange = 'binance', logFileName='VB_20180820.log')