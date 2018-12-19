from __future__ import print_function
import ccxt
from binance.websockets import BinanceSocketManager
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from languageHandled import languageHandler
from time import sleep
import time



class BinanceSocket(object):
	def __init__(self, TimeFrame):
		self.client = Client(None,None)
		self.bm = BinanceSocketManager(self.client)
		self.exchange = "Binance"
		self.engine = "Websocket"
		self.observers = []
		self.TimeFrame = TimeFrame

	def start(self,tickers):
		stream = []
		for ticker in tickers:
			streamName = ticker.lower()+'@kline_'+self.TimeFrame
			stream.append(streamName)
		self.bm.start_multiplex_socket(stream, self.process_message)
		#self.bm.start_kline_socket('BTC-USDT', self.process_message)
		self.bm.start()

	def process_message(self,msg):
		self.msg = msg


	@property
	def msg(self):
		return self._msg	

	@msg.setter
	def msg(self,value):
		self._msg = value
		for callback in self.observers:
			callback(self._msg)

	def on_orderbook(self,value):
		self.msg = value

	def bind_to(self,callback):
		self.observers.append(callback)	
	

class tradingInterface(object):
	def __init__(self,interface,tickers=[""],callbacks=[],error_responses=[]):
		self.msgs = {}
		self.engine = ""
		self.interface = interface
		self.exchange = self.interface.exchange
		self.tickers = tickers
		self.tickers = languageHandler(output_lang = self.interface.exchange,inputs = self.tickers,input_lang = "TradeModule")
		self.observers = []
		self._error_observers=[]

		for error_response in error_responses:
			self.bind_to_error(error_response)

		for callback in callbacks:
			self.bind_to(callback)

		for ticker in self.tickers:
			self.msgs[ticker] = kLines()
		
		if self.interface.exchange == "Binance":
			self.engine = self.interface.engine
			self.interface.bind_to(self.updateMsgBinance)
			self.interface.start(self.tickers)

	def __repr__(self):
		return "Interface Details: " + str([(var +": "+ str(getattr(self,var))) for var in dir(self)])

	def __dir__(self):
		return ['exchange','tickers','engine']

		
		# (BINANCE:ETHUSDT - BITTREX:ETHUSDT) / BINANCE:ETHUSDT
	'''def updateMsgBittrex(self,msg):
		
		#Z = buys  S = sells f = trades
			#{'M': 'BTC-OMG', 'N': 7548, 'Z': [{'TY': 0, 'R': 0.00147559, 'Q': 15.25282626}], 'S': [], 'f': [], 'invoke_type': 'SubscribeToExchangeDeltas'}
			#{'M': 'BTC-ADA', 'H': 3.0430000000000002e-05, 'L': 2.886e-05, 'V': 23439919.29879991, 'l': 2.887e-05, 'm': 695.89879699, 'T': 1526964023070, 'B': 2.887e-05, 'A': 2.888e-05, 'G': 2576, 'g': 17687, 'PD': 3e-05, 'x': 1506668518873}			
		marketName = msg['M']

		self.msgs[marketName] = kLines(market =marketName,bidPrice=msg["Z"][0]['R'],bidVolume=msg["Z"][0]['Q'],offerPrice=msg["S"][0]['R'],offerVolume=msg["S"][0]['Q'],exchange = self.exchange)
		for callback in self.observers:
			callback(self.msgs[marketName])

		self.interface.query_exchange_state(self.tickers)'''




	def updateMsgBinance(self,msg):
		#try:
			msg=msg['data']
			marketName = msg['s']
			#print(marketName)#languageHandler(input_lang = "Binance",output_lang = "TradeModule", inputs = [msg['s']])[0]
			self.msgs[marketName] = kLines(market =marketName,kOpen=float(msg['k']['o']),kClose=float(msg['k']['c']),kHigh=float(msg['k']['h']),kLow=float(msg['k']['l']),kVolume=float(msg['k']['v']), openTime=float(msg['k']['t']) ,closeTime=float(msg['k']['T']), interval=msg['k']['i'],exchange = self.exchange)
			#print(self.msgs)

			#print(self.msgs[marketName])
			for callback in self.observers:
				callback(self.msgs[marketName])
		#except Exception as e:
		#	print(e)
		#	print("Error located in message update for binance")
	"""
	def updateMsgBinance(self,msg):
		#try:
			marketName = msg['s']
			#print(marketName)#languageHandler(input_lang = "Binance",output_lang = "TradeModule", inputs = [msg['s']])[0]
			self.msgs[marketName] = kLines(market =marketName,kOpen=float(msg['k']['o']),kClose=float(msg['k']['c']),kHigh=float(msg['k']['h']),kLow=float(msg['k']['l']),kVolume=float(msg['k']['v']),exchange = self.exchange)
			print(msg)
			print(self.msgs[marketName])
			for callback in self.observers:
				callback(self.msgs[marketName])
		#except Exception as e:
		#	print(e)
		#	print("Error located in message update for binance")
	"""


	def bind_to(self,callback):
		self.observers.append(callback)

	def bind_to_error(self,callback):
		self._error_observers.append(callback)


 	








