from __future__ import print_function
import ccxt
from bittrex_websocket.websocket_client import BittrexSocket as BSocket
from binance.websockets import BinanceSocketManager
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from languageHandler import languageHandler
from time import sleep
import time


#from tradeClasses import BestBidOffer
from bittrex_websocket import OrderBook

class BittrexSocket(OrderBook):
	def __init__(self):
		super().__init__()
		self.exchange = "Bittrex"
		self.engine = "Websocket"
		self.observers = []

	def on_ping(self, msg):
		#book = ws.get_order_book('BTC-ETH')
		for callback in self.observers:
			callback(msg)

	def bind_to(self,callback):
		self.observers.append(callback)

class BinanceSocket(object):
	def __init__(self):
		self.client = Client(None,None)
		self.bm = BinanceSocketManager(self.client)
		self.exchange = "Binance"
		self.engine = "Websocket"
		self.observers = []

	def start(self,tickers):
		self.bm.start_symbol_ticker_socket(tickers, self.process_message)
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
			self.msgs[ticker] = BestBidOffer()
		
		if self.interface.exchange == "Bittrex":
			self.engine = self.interface.engine
			self.interface.bind_to(self.updateMsgBittrex)
			self.interface.subscribe_to_orderbook(self.tickers)
			
		elif self.interface.exchange == "Binance":
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

		self.msgs[marketName] = BestBidOffer(market =marketName,bidPrice=msg["Z"][0]['R'],bidVolume=msg["Z"][0]['Q'],offerPrice=msg["S"][0]['R'],offerVolume=msg["S"][0]['Q'],exchange = self.exchange)
		for callback in self.observers:
			callback(self.msgs[marketName])

		self.interface.query_exchange_state(self.tickers)'''


	def updateMsgBittrex(self,msg):
		#try:
			marketName = msg
			msg = self.interface.get_order_book(msg)
			#Z = buys  S = sells f = trades
				#{'M': 'BTC-OMG', 'N': 7548, 'Z': [{'TY': 0, 'R': 0.00147559, 'Q': 15.25282626}], 'S': [], 'f': [], 'invoke_type': 'SubscribeToExchangeDeltas'}
				#{'M': 'BTC-ADA', 'H': 3.0430000000000002e-05, 'L': 2.886e-05, 'V': 23439919.29879991, 'l': 2.887e-05, 'm': 695.89879699, 'T': 1526964023070, 'B': 2.887e-05, 'A': 2.888e-05, 'G': 2576, 'g': 17687, 'PD': 3e-05, 'x': 1506668518873}			

			self.msgs[marketName] = BestBidOffer(market =marketName,bidPrice=msg["Z"][0]['R'],bidVolume=msg["Z"][0]['Q'],offerPrice=msg["S"][0]['R'],offerVolume=msg["S"][0]['Q'],exchange = self.exchange)
			for callback in self.observers:
				callback(self.msgs[marketName])

			self.interface.query_exchange_state(self.tickers)
		#except Exception as e:
		#	print(e)
		#	print("Error located in message update for Bittrex")


	def updateMsgBinance(self,msg):
		#try:
			marketName = msg['s']
			#print(marketName)#languageHandler(input_lang = "Binance",output_lang = "TradeModule", inputs = [msg['s']])[0]
			self.msgs[marketName] = BestBidOffer(market =marketName,bidPrice=float(msg['b']),bidVolume=float(msg['B']),offerPrice=float(msg['a']),offerVolume=float(msg['A']),exchange = self.exchange)
			for callback in self.observers:
				callback(self.msgs[marketName])
		#except Exception as e:
		#	print(e)
		#	print("Error located in message update for binance")


	def bind_to(self,callback):
		self.observers.append(callback)

	def bind_to_error(self,callback):
		self._error_observers.append(callback)


class BestBidOffer():
	def __init__(self,market ="",bidPrice=None,bidVolume=None,offerPrice=None,offerVolume=None,exchange = ""):
		self.market = market
		self.exchange = exchange
		self.bidPrice = bidPrice
		self.bidVolume = bidVolume
		self.offerVolume = offerVolume
		self.offerPrice = offerPrice

	def __repr__(self):
		return "BBO Details: " + str([(var +": "+ str(getattr(self,var))) for var in dir(self)])

	def __dir__(self):
		return ['bidVolume','bidPrice','offerPrice','offerVolume','market','exchange']

	def __hash__(self):
		return hash((self.bidVolume,self.bidPrice,self.offerPrice,self.offerVolume,self.market,self.exchange))








