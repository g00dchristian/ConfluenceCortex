### Lib Imports
from slackclient import SlackClient
import datetime
import numpy as np
from time import sleep
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
from genVolumeAnalysis import *
from AbnorVol import *
from Indicator_RSI import *
from priceShear import Price_Shear
from insideBar import *
from BinanceSocketTest import *
from mathByChristian import *
from sqlog import openTrades
from sqlog import sqlogger
from sqlog import refracFetch
from sqlog import logCloseTrade
from marketSentiment import Market_Sentiment
from xlog import xlog

### Offline Imports 
from bnWebsocket.klines import bnStream
from bnWebsocket.languageHandled import languageHandler
from bnWebsocket import keychain




### DataFram View Options




pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
#pd.set_option('display.height', None)


class Confluence_Cortex():
	def __init__(self, exchange, logFileName, TimeFrame):
		#-- INTRINSIC --------------------------------------------------------------- 
		localpath = r"C:\Users\Christian\Dropbox\Crypto\Python\ConfluenceCortex\\"

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
		self.tradesoccured=0
		self.closedtradesoccured=0

		#-- EXTRINSIC --------------------------------------------------------------- 
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
		self.openTradeList=openTrades()
		print(self.openTradeList)
		self.refractoryList = refracFetch()
		self.lastPrice = {}
		self.timeUpdate=time.time()


		#-- MARKET MANAGMENT --------------------------------------------------------------- 
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
				pdEntry.update({'Volume' : candle[5]})
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
			
			self.Logic(df=df, market=kline.market)




	def Logic(self, df, market):
		#-- SETTINGS ---------------------------------------------------------------
		CR = 0 #Confluence Rating
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

		confluenceRating={}
		confluenceFactor={}

		#-- MARKET SENTIMENT -------------------------------------------------------
		MS = Market_Sentiment(df, propertyDic)
		confluenceFactor.update({'Sentiment':MS['Sentiment']})
		confluenceRating.update({'Sentiment':self.confSet.loc[MS['Sentiment'],'Market Sentiment']})
		CR = CR + confluenceRating['Sentiment']
		#-- BREAKING ------
		confluenceFactor.update({'Break':MS['Breaking']})
		confluenceRating.update({'Break':self.confSet.loc[MS['Breaking'],'Break']})
		CR = CR + confluenceRating['Break']
		#-- PRICE SHEAR -------------------------------------------------------------
		if self.TimeFrame != '1d':
			PS = Price_Shear(df, propertyDic,[12,26])
			confluenceFactor.update({'PriceShear':PS})
			confluenceRating.update({'PriceShear':self.confSet.loc[PS,'PriceShear']})
		#-- GENERIC VOLUME ----------------------------------------------------------
		VA_Flipper=-1
		VA = genVolumeAnalysis(df, propertyDic)
		if VA['Type'] == 'Bull':
			confluenceRating.update({'GenVolume':self.confSet.loc[VA['Accel/Decel'],'Generic Volume']})
			CR = CR + confluenceRating['GenVolume']
		elif VA['Type'] == 'Bear':
			confluenceRating.update({'GenVolume':self.confSet.loc[VA['Accel/Decel'],'Generic Volume']*VA_Flipper})
			CR = CR + confluenceRating['GenVolume']
		else: 
			confluenceRating.update({'GenVolume':'ERROR'})
			print('Generic Volume Error')
		confluenceFactor.update({'GenVolume':(str(VA['Accel/Decel'])+'_'+str(VA['Type']))})

		#-- RSI --------------------------------------------------------------------
		RSI = Indicator_RSI(df, propertyDic)
		confluenceFactor.update({'RSI':RSI})
		confluenceRating.update({'RSI':self.confSet.loc[round_Down(RSI,10),'RSI']})
		CR = CR + confluenceRating['RSI']

		#-- INSIDE BAR -------------------------------------------------------------
		IB = InsideBar(df, propertyDic)
		confluenceFactor.update({'IB':(str(IB['ConsecIB']))+'_'+str(IB['Status'])})
		confluenceRating.update({'IB':IB['ConsecIB']*self.confSet.loc[IB['Status'],'IB']})	
		CR = CR + confluenceRating['IB']

		#-- ABNORMAL VOLUME --------------------------------------------------------
		AVol = AbnormalVolume(df)
		confluenceFactor.update({'AbnorVol':AVol['Result']})
		confluenceRating.update({'AbnorVol':self.confSet.loc[AVol['Result'],'AbnorVol']})
		CR = CR + confluenceRating['AbnorVol']


		#-- INFO PACKAGE ---------------------------------------------------------------
		pkg = {
		'Market':market,
		'RefracPeriod':60*60,
		'Exchange':self.exchange.capitalize(),
		'CR':CR,
		'Market Sentiment': propertyDic['Sentiment'],
		'RSI':RSI,
		'Price':df.loc[1,'Close'],
		'Strategy':'Confluence'+'_'+str(self.TimeFrame)
		}

		#-- LOCAL PRINTER ---------------------------------------------------------------
		print('')
		print(datetime.datetime.now())
		print(f'Open Trades: {len(self.openTradeList)}')
		print('TimeFrame: %s'%(self.TimeFrame))
		print(pkg)
		print(confluenceRating)

		#-- CLOSE TRADE CHECK -------------------------------------------------- 
		dbModCheck = os.path.getmtime(self.databasepath)
		if self.dbModTime != dbModCheck:
			self.openTradeList = openTrades()
			self.refractoryList = refracFetch()
			self.dbModTime = dbModCheck
			self.log('Database modified... Open_Trades & Refractory_Periods updated')
		if len(self.openTradeList)>0:
			closeQuery=0
			logGateway=0
			for trade in self.openTradeList:
				if trade['Market']==pkg['Market'] and trade['Strategy']==pkg['Strategy']:
					print(trade)
					print('Closable Market: %s'%(trade['Market']))
					#LIMITATION: The Trade Check only refers to the same strategy timeperiod... i.e. the 4h confluence cannot affect the 1d trades
					if CR <50 and trade['ClipSize']>0:
						closeOtype='market-sell'
						closeOtype=closeOtype+self.testSwitch
						closeQuery=1
						logGateway=1
					if CR >-50 and trade['ClipSize']<0:
						closeOtype='market-buy'
						closeOtype=closeOtype+self.testSwitch
						closeQuery=1
						logGateway=1 
					
					if time.time() < self.tradeRateLimiter:
						closeQuery=0
						closegatewayresult=('FAILED-- Trade Rate Limiter Exceeded')

					if closeQuery == 1:
						try:
							TC=TradeClient(exchange=pkg['Exchange'].lower(),
								market=languageHandler(output_lang="TradeModule", inputs=[pkg['Market']], input_lang=pkg['Exchange'])[0],
								clipSize=abs(trade['ClipSize']),
								orderPrice=0.00000001,
								orderType=closeOtype
								)
							self.closedtradesoccured=self.closedtradesoccured+1
							logCloseTrade(trade['UUID'],TC.tPrice,trade['OrderPrice'],trade['ClipSize'],TC.oid)
							trade.update({'Market':'Closed'})
							trade.update({'ClipSize':0})
							closegatewayresult = ('Trade Closed-- %s'%(trade['UUID']))
							self.tradeRateLimiter = time.time()+self.maxTradeRate
							self.refractoryList = refracFetch()
							self.dbModTime = os.path.getmtime(self.databasepath)
							self.openTradeList=openTrades()

						except Exception as error_result:
							closegatewayresult = ('FAILED-- attempt to send trade: %s'%(error_result))
					
					if logGateway==1:
						self.log('CloseTrade Gateway: %s'%(closegatewayresult))

		#-- TRADE SIZE --------------------------------------------------
		tradepkg={
		'usdClipSize':5,
		'MaxPair':50,
		'MaxOpen':100,
		}


		#-- OPEN TRADE-------------------------------------------------- 
		if CR <= -100:
			pkg.update({'Side':'sell'})
			self.TradeGateway(pkg, tradepkg, confluenceRating, confluenceFactor)
		elif CR >= 100:
			pkg.update({'Side':'buy'})
			self.TradeGateway(pkg, tradepkg, confluenceRating, confluenceFactor)



	# - Move Trade Function to Standalone Script
	# - Open Trade LIST
	# 		- Sum Values of Open Trades
	# 		- Max Value of open trades
	# - Set MAX single pair open trades
	# - Set Refractory period for confluence timeframe+pair
	# - refractory period data to be stored in tradelog db
	# - Make Close Trade Function on the same script as the Trade Function
	# - Daily stop/start for Confluence_Cortex scripts



	def TradeGateway(self, pkg, tpkg, confluenceRating, confluenceFactor):
		self.log('OpenTrade Gateway: Trade Received')
		eligible=1
		if len(self.refractoryList)>0:
			for datum in self.refractoryList:
				if datum['Market'] == pkg['Market'] and datum['Strategy'] == pkg['Strategy'] and time.time()<datum['Epoch']:
					eligible=0
					gatewayresult = ('FAILED-- %s_%s within refractory period'%(pkg['Market'], pkg['Strategy']))
		if len(self.openTradeList)>0:
			symboltotal=0
			opentotal=0
			for datum in self.openTradeList:
				if datum['Market'] == pkg['Market'] and datum['Strategy'] == pkg['Strategy']:
					symboltotal=symboltotal+datum['USD_Value']
				opentotal=opentotal+datum['USD_Value']
			if symboltotal >= tpkg['MaxPair']:
				eligible=0
				gatewayresult = ('FAILED-- Total open %s_%s trades (%.1f) exceeds restriction (%.1f)'%(pkg['Market'], pkg['Strategy'], symboltotal, tpkg['MaxPair']))
			if opentotal >= tpkg['MaxOpen']:
				eligible=0
				gatewayresult = ('FAILED-- Total open trades (%.1f) exceeds restriction (%.1f)'%(opentotal,tpkg['MaxOpen']))
		if pkg['Market'][-4:] != 'USDT':
			eligible=0
			gatewayresult=('FAILED-- Pair not USDT pair and not recognised by clipSize_USD calculator')
		if time.time() < self.tradeRateLimiter:
			eligible=0
			gatewayresult=('FAILED-- Trade Rate Limiter Exceeded')			 

		# NON-BITMEX SHORT REJECTION
		# if pkg['Side']=='sell' and pkg['Exchange']!='Bitmex':
		# 	eligible=0
		# 	gatewayresult=('FAILED-- %s does not support leveraged (short) orders\nTrade Details:\n%s'%(pkg['Exchange'],pkg))

		if eligible == 1:
			try:
				clipSize = (tpkg['usdClipSize']/pkg['Price'])
				if pkg['Side'] == 'buy':
					oType='market-buy'
					oType=oType+self.testSwitch
				elif pkg['Side'] == 'sell':
					oType='market-sell'
					oType=oType+self.testSwitch
					clipSize=clipSize*-1

				TC=TradeClient(exchange=pkg['Exchange'].lower(),
					market=languageHandler(output_lang="TradeModule", inputs=[pkg['Market']], input_lang=pkg['Exchange'])[0],
					clipSize=abs(clipSize),
					orderPrice=0.00000001,
					orderType=oType
					)
				self.tradesoccured=self.tradesoccured+1
				
				
				pkg.update({'clipSize':clipSize})
				pkg.update({'Exchange_UUID':TC.oid})
				pkg.update({'tPrice':TC.tPrice})
				pkg.update({'USD':(abs(float(pkg['Price'])*float(clipSize)))}) #TESTING LINE
				
				#pkg.update({'USD':(abs(float(TC.tPrice)*float(clipSize)))})
				logfunction=sqlogger(pkg,confluenceRating,confluenceFactor)
				gatewayresult = ('SUCCESS-- Trade Sent (UUID: %s)'%(logfunction))
				self.tradeRateLimiter = time.time()+self.maxTradeRate
				self.refractoryList = refracFetch()
				self.dbModTime = os.path.getmtime(self.databasepath)
				self.log('Refractory_Periods updated')
				self.openTradeList=openTrades()


			except Exception as error_result:
				gatewayresult = ('FAILED attempt to send trade: %s'%(error_result))

		self.log('OpenTrade Gateway: %s'%(gatewayresult))
		print(self.tradesoccured)
		print(self.closedtradesoccured)








	def log(self,msg):
		print(msg)
		self.logger.info(msg)





Confluence_Cortex(exchange = 'binance', logFileName='Confluence.log', TimeFrame='15m')