### Lib Imports
from slackclient import SlackClient
from queue import Queue
import datetime
from uuid import uuid4
import numpy as np
from time import sleep
import threading
import pandas as pd
import logging
import math
import ccxt
import time
import sys
import os


### Repo Imports
from shifteraverage import calc
from tradeModule import TradeClient
from VolumeAnalysis import *
from Indicator_RSI import *
from priceShear import Price_Shear
from insideBar import *
from BinanceSocketTest import *
from mathByChristian import *
from sqlog import openTrades
from sqlog import sqlogger
from sqlog import refracFetch
from sqlog import logCloseTrade_CR
from marketSentiment import Market_Sentiment
from xlog import xlog
from TradeGateway import Close_Trades
from TradeGateway import Open_Trade

### Offline Imports 
from bnWebsocket.klines import bnStream
from bnWebsocket.languageHandled import languageHandler
from bnWebsocket import keychain


### DataFram View Options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
#pd.set_option('display.height', None)

sql_lock = threading.Lock()

class SQL_Thread(threading.Thread):
    def __init__(self, queue, args=(), kwargs=None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = queue
        self.daemon = False
        # self.receive_messages = args[0]
	
    def run(self):
	    # print(threading.currentThread().getName(), self.receive_messages)
        while True:
	        val = self.queue.get()
	        if val is None:   # If you send `None`, the thread will exit.
	            return
	        self.do_thing_with_message(val)

    def do_thing_with_message(self, data):
    	with sql_lock:
    		if data[0]=='Open':
    			sqlogger(*data[1])
    			self.queue.task_done()

    		if data[0]=='Close':
    			logCloseTrade_CR(*data[1])
    			self.queue.task_done()

    		if data[0]=='refracFetch':
    			setattr(self,data[1],refracFetch())
    			self.queue.task_done()

    		if data[0]=='openTrades':
    			setattr(self,data[1],openTrades())
    			self.queue.task_done()


class Confluence_Cortex():
	def __init__(self, exchange, logFileName, TimeFrame):
		#-- INTRINSIC --------------------------------------------------------------- 
		localpath = os.getcwd()+'//'

		### Logging
		self.logger = logging.getLogger(name = "Full")
		#hdlr = logging.FileHandler(str(os.path.dirname(__file__)) +'\\' + logFileName)
		hdlr = logging.FileHandler(localpath + logFileName)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr) 
		self.logger.setLevel('INFO')

		self.log('loaded')
		#self.TimeFrame=sys.argv[1]
		self.cortex_version=3.11
		self.exchange=exchange
		self.TimeFrame=TimeFrame
		self.sc=SlackClient(keychain.slack.TradeAlertApp('BotUser'))
		self.sc_read=SlackClient(keychain.slack.TradeAlertApp('OAuth'))

		
		#-- TESTING --------------------------------------------------------------- 
		testing = 1
		if testing == 1:
			self.testSwitch='-test'
			self.log('###----------- TESTING MODE -----------###')
		elif testing == 0:
			self.testSwitch=''

		#-- THREAD MANAGEMENT ----------------------------------------------------------------
		self.threads = {}
		q=Queue()
		self.threads.update({'SQLT':SQL_Thread(q)})
		self.threads['SQLT'].start()

		#-- EXTRINSIC --------------------------------------------------------------- 
		self.Profit_Take=0.02
		self.Stop_Loss=0.01

		self.data = {}
		self.startup = 1 
		self.trades = {}
		self.tradeRateLimiter = 0
		self.maxTradeRate = 2 #1 trade every [self.maxTradeRate] seconds
		self.p=131
		self.confSetPath=localpath+'confluenceValues.xlsx' 
		self.confSet=pd.read_excel(self.confSetPath,index_col=0)
		self.databasepath=localpath+'tradelog.db'
		self.confSetMod=os.path.getmtime(self.confSetPath)
		self.dbModTime=os.path.getmtime(self.databasepath)
		temp_uuid=str(uuid4())
		self.threads['SQLT'].queue.put(['openTrades',temp_uuid])
		self.threads['SQLT'].queue.join()
		self.openTradeList=getattr(self.threads['SQLT'],temp_uuid)
		print(self.openTradeList)
		temp_uuid_2=str(uuid4())
		self.threads['SQLT'].queue.put(['refracFetch',temp_uuid_2])
		self.threads['SQLT'].queue.join()
		self.refractoryList=getattr(self.threads['SQLT'],temp_uuid_2)
		print(self.refractoryList)
		self.lastPrice = {}
		self.timeUpdate=time.time()


		#-- MARKET MANAGEMENT --------------------------------------------------------------- 
		#ticker_fetch=getattr(ccxt,exchange)().fetch_tickers()
		ticker_fetch = ['BTC/USDT']
		#ticker_fetch = ['BTC/USDT', 'ETH/USDT', 'NEO/USDT', 'ADA/USDT', 'XRP/USDT']
		self.market_jar=[]
		for market in ticker_fetch:
			if market[-3:] != 'USD':
				self.market_jar.append(market)
				toParse = [market]
				parsedMarket = languageHandler(output_lang = exchange.capitalize(),inputs = toParse,input_lang = "TradeModule")
				setattr(self, parsedMarket[0], {})
				#self.data.update({parsedMarket[0]:None})
				MSname = parsedMarket[0]+'_MS'
				setattr(self, MSname, 'Unknown')
				#print(market)
		


		#-- WEBSOCKET ---------------------------------------------------------------
		callbacks=[self.WebSocketFunction]
		bnStream(self.market_jar, self.TimeFrame, callbacks)
		

		self.FetchPast(exchange)


	def FetchPast(self, exchange):
		for market in self.market_jar:
			self.trades.update({market:[]})
			name = market+'_past'
			setattr(self, name, getattr(ccxt,exchange)().fetch_ohlcv(market, timeframe=self.TimeFrame)[-self.p:])
			dfName = market+'_df'
			setattr(self, dfName, [])
			cf = market+'_cf' #Confluence Factor
			setattr(self, cf, 0)

			x=self.p
			for candle in getattr(self,name):
				pdEntry = {}
				pdEntry.update({'Time': candle[0]})
				pdEntry.update({'Volume':candle[5]})
				pdEntry.update({'High':candle[2]})
				pdEntry.update({'Low':candle[3]})
				pdEntry.update({'Open':candle[1]})
				pdEntry.update({'Close':candle[4]})
				pdEntry.update({'Period':x})
				getattr(self, dfName).append(pdEntry)
				x=x-1
			df = pd.DataFrame(getattr(self,dfName))
			df = df.set_index('Period')
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
			'Low':kline.kLow,
			'High':kline.kHigh,
			'Close':kline.kClose,
			'Open':kline.kOpen,
			'Volume':kline.kVolume,
			'Period':1
			}

			if getattr(self,dfName)[-1:][0]['Time'] == candleData['Time']:
				setattr(self,dfName, getattr(self,dfName)[:-1])
				getattr(self,dfName).append(candleData)
			else:
				getattr(self,dfName).append(candleData)
				setattr(self,dfName, getattr(self,dfName)[1:])
				y=self.p
				for candle in getattr(self,dfName):
					candle.update({'Period':y})
					y=y-1
			df=pd.DataFrame(getattr(self,dfName))
			df = df.set_index('Period')
			
			#-- CONFLUENCE SETTINGS UPDATE ---------------------------------------------------------------
			confSet=os.path.getmtime(self.confSetPath)
			if confSet != self.confSetMod:
				self.confSet=pd.read_excel(self.confSetPath,index_col=0)
				self.confSetMod=os.path.getmtime(self.confSetPath)
				self.log('\nConfluence Settings Updated: \n%s'%(self.confSet))			
			
			self.Conditions(df=df, market=kline.market)


	def Conditions(self, df, market):
		#-- SETTINGS ---------------------------------------------------------------
		propertyDic = {
		'Market':market,
		'Periods':self.p,
		'Last_Level':market+'_lastlevel',
		'RSI':market+'_RSI',
		'PS':market+'_PS',
		'Break':market+'_Break',
		'Sentiment':market+'_MS',
		'VolumeAnalysis':market+'_VA'
		}

		#-- MARKET LEVELS ----------------------------------------------------------
		MS = Market_Sentiment(df, propertyDic)
		#-- PRICE SHEAR ------------------------------------------------------------
		PS = Price_Shear(df, propertyDic,[12,26])
		#-- GENERIC VOLUME ---------------------------------------------------------
		VA = Volume_Analysis(df, propertyDic)
		#-- RSI --------------------------------------------------------------------
		RSI = Indicator_RSI(df, propertyDic)
		#-- INSIDE BAR -------------------------------------------------------------
		IB = Inside_Bar(df, propertyDic)
		#-- ABNORMAL VOLUME --------------------------------------------------------
		AVol = Abnormal_Volume(df)

		Market_Conditions={
		'Levels':MS,
		'Price_Shear':PS,
		'Volume':VA,
		'RSI':RSI,
		'Inside_Bar':IB,
		'Abnormal_Volume':AVol,
		'Last_Price':df.loc[1,'Close']
		}

		self.Cortex(Market_Conditions, market)


	def Cortex(self, MC, market):
		CR = 200 #Confluence Rating
		confluenceRating={}
		confluenceFactor={}
		#-- MARKET SENTIMENT -------------------------------------------------------
		confluenceFactor.update({'Sentiment':MC['Levels']['Sentiment']})
		confluenceRating.update({'Sentiment':self.confSet.loc[MC['Levels']['Sentiment'],'Market Sentiment']})
		CR = CR + confluenceRating['Sentiment']
		#-- BREAKING ------
		confluenceFactor.update({'Break':MC['Levels']['Breaking']})
		confluenceRating.update({'Break':self.confSet.loc[MC['Levels']['Breaking'],'Break']})
		CR = CR + confluenceRating['Break']
		#-- PRICE SHEAR -------------------------------------------------------------
		if self.TimeFrame != '1d':
			confluenceFactor.update({'PriceShear':MC['Price_Shear']})
			confluenceRating.update({'PriceShear':self.confSet.loc[MC['Price_Shear'],'PriceShear']})
		#-- GENERIC VOLUME ----------------------------------------------------------
		VA_Flipper=-1
		if MC['Volume']['Type'] == 'Bull':
			confluenceRating.update({'GenVolume':self.confSet.loc[MC['Volume']['Accel/Decel'],'Generic Volume']})
			CR = CR + confluenceRating['GenVolume']
		elif MC['Volume']['Type'] == 'Bear':
			confluenceRating.update({'GenVolume':self.confSet.loc[MC['Volume']['Accel/Decel'],'Generic Volume']*VA_Flipper})
			CR = CR + confluenceRating['GenVolume']
		else: 
			confluenceRating.update({'GenVolume':'ERROR'})
			print('Generic Volume Error')
		confluenceFactor.update({'GenVolume':(str(MC['Volume']['Accel/Decel'])+'_'+str(MC['Volume']['Type']))})
		confluenceFactor.update({'RSI':MC['RSI']})
		confluenceRating.update({'RSI':self.confSet.loc[round_Down(MC['RSI'],10),'RSI']})
		CR = CR + confluenceRating['RSI']
		#-- INSIDE BAR -------------------------------------------------------------
		confluenceFactor.update({'IB':(str(MC['Inside_Bar']['ConsecIB']))+'_'+str(MC['Inside_Bar']['Status'])})
		confluenceRating.update({'IB':MC['Inside_Bar']['ConsecIB']*self.confSet.loc[MC['Inside_Bar']['Status'],'IB']})	
		CR = CR + confluenceRating['IB']
		#-- ABNORMAL VOLUME --------------------------------------------------------
		confluenceFactor.update({'AbnorVol':MC['Abnormal_Volume']['Result']})
		confluenceRating.update({'AbnorVol':self.confSet.loc[MC['Abnormal_Volume']['Result'],'AbnorVol']})
		CR = CR + confluenceRating['AbnorVol']
		#-- FEAR & GREED -----------------------------------------------------------
		print(market)


		#-- INFO PACKAGE ---------------------------------------------------------------
		pkg = {
		'Market':market,
		'RefracPeriod':60*60,
		'Exchange':self.exchange.capitalize(),
		'CR':CR,
		'Market Sentiment': MC['Levels']['Sentiment'],
		'RSI':MC['RSI'],
		'Price':MC['Last_Price'],
		'Strategy':'Confluence'+'_'+str(self.TimeFrame),
		'Testing':self.testSwitch,
		'Trade_Limiter':self.tradeRateLimiter,
		'Limiter_Rate':self.maxTradeRate,
		'Version':self.cortex_version,
		'Profit_Take':self.Profit_Take,
		'Stop_Loss':self.Stop_Loss
		}

		#-- TRADE SIZE --------------------------------------------------
		tradepkg={
		'usdClipSize':15,
		'MaxPair':50,
		'MaxOpen':100,
		'CR':confluenceRating,
		'CF':confluenceFactor
		}

		#-- LOCAL PRINTER ---------------------------------------------------------------
		print('')
		print(datetime.datetime.now())
		print(f'Open Trades: {len(self.openTradeList)}')
		print('TimeFrame: %s'%(self.TimeFrame))
		print(pkg)
		print(confluenceRating)


		#-- CLOSE TRADE ---------------------------------------------------------------
		CT=Close_Trades(self.openTradeList, pkg)
		if len(CT['Log'])>0:
			for msg in CT['Log']:
				self.log(f'Close Gateway Result: {msg}')

		if CT['SQL']!=0:
			print('Adding open trade to SQL queue')
			self.threads['SQLT'].queue.put(CT['SQL'])

		if CT['Trade_Status'] == 1:
			print(CT)
			### Refractory Periods
			temp_uuid_2=str(uuid4())
			self.threads['SQLT'].queue.put(['refracFetch',temp_uuid_2])
			self.threads['SQLT'].queue.join()
			self.refractoryList=getattr(self.threads['SQLT'],temp_uuid_2)

			self.tradeRateLimiter = CT['Trade_Limiter'] 
			self.dbModTime = os.path.getmtime(self.databasepath)

			### Open Trade List
			temp_uuid=str(uuid4())
			self.threads['SQLT'].queue.put(['openTrades',temp_uuid])
			self.threads['SQLT'].queue.join()
			self.openTradeList=getattr(self.threads['SQLT'],temp_uuid)
			print(self.openTradeList)
		



		#-- OPEN TRADE ---------------------------------------------------------------
		if CR <= -100:
			pkg.update({'Side':'sell'})
			pkg.update({'Profit_Level':(1-self.Profit_Take)*MC['Last_Price']})
			pkg.update({'Stop_Level':(1+self.Stop_Loss)*MC['Last_Price']})

		elif CR >= 100:
			pkg.update({'Side':'buy'})
			pkg.update({'Profit_Level':(1+self.Profit_Take)*MC['Last_Price']})
			pkg.update({'Stop_Level':(1-self.Stop_Loss)*MC['Last_Price']})
			
		if 'Side' in pkg:
			OT=Open_Trade(self.refractoryList, self.openTradeList, pkg, tradepkg)
			if len(OT['Log'])>0:
				for msg in OT['Log']:
					self.log(f'Open Gateway Result: {msg}')

			if OT['SQL']!=0:
				print('Adding open trade to SQL queue')
				self.threads['SQLT'].queue.put(OT['SQL'])

 
			if OT['Trade_Status'] == 1:
				self.tradeRateLimiter = OT['Trade_Limiter']
				### Refractory Periods
				temp_uuid_2=str(uuid4())
				self.threads['SQLT'].queue.put(['refracFetch',temp_uuid_2])
				self.threads['SQLT'].queue.join()
				self.refractoryList=getattr(self.threads['SQLT'],temp_uuid_2)

				self.log('Refractory_Periods updated')

				### Open Trade List
				temp_uuid=str(uuid4())
				self.threads['SQLT'].queue.put(['openTrades',temp_uuid])
				self.threads['SQLT'].queue.join()
				self.openTradeList=getattr(self.threads['SQLT'],temp_uuid)
				print(self.openTradeList)

				self.dbModTime = os.path.getmtime(self.databasepath)





	def log(self,msg):
		print('LOG: '+msg)
		self.logger.info(msg)





Confluence_Cortex(exchange = 'binance', logFileName='Confluence.log', TimeFrame='15m')