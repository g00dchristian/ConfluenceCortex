import os, sys
sys.path.append("C:/Users/Christian/Anaconda3/Lib/site-packages")
import ccxt
import pandas as pd
import numpy
import time
import logging
"""
"""

exchanges = [#"_1btcxe",

"acx",
#"anxpro",
"anybits",
"bibox",
"binance",
"bit2c",
"bitbank",
"bitbay",
#"bitfinex",
#"bitfinex2",
"bitflyer",
"bithumb",
"bitkk",
"bitlish",
"bitmarket",
"bitmex",
"bitsane",
"bitso",
"bitstamp",
"bitstamp1",
"bittrex",
"bl3p",
"bleutrade",
"braziliex",
"btcbox",
"btcmarkets",
"btctradeim",
"btctradeua",
"btcturk",
"btcx",
"bxinth",
"cex",
"chilebit",
"cobinhood",
"coinbase",
"coinbasepro",
"coincheck",
"coinex",
"coinexchange",
"coinfalcon",
"coinfloor",
"coinmarketcap",
"coinmate",

"coinnest",
"coinone",
"coinsecure",
"coinspot",
"cointiger",
"crypton",
"cryptopia",
"deribit",
"dsx",
"ethfinex",
"exmo",
"exx",
"fcoin",
"foxbit",
"fybse",
"fybsg",
"gatecoin",
"gateio",
"gdax",
"gemini",
"getbtc",
"hadax",
"hitbtc",
"hitbtc2",
"huobi",
"huobipro",
"ice3x",
"independentreserve",
"indodax",
"itbit",
"kraken",
"kucoin",
"kuna",
"lakebtc",
"lbank",
"liqui",
"livecoin",
"luno",
"lykke",
"mercado",
"mixcoins",
"negociecoins",
"nova",
"okcoinusd",
"okex",
"paymium",
"poloniex",
"quadrigacx",
"quoinex",
"southxchange",
"surbitcoin",
"therock",
"tidebit",
"tidex",
"urdubit",
"vaultoro",
"vbtc",
"virwox",
"wex",
"yobit",
"zaif",
"zb"
]


class ExchangeSpikeEye():
	"""Crooked Colours"""
	def __init__(self, logFileName):

		self.logger = logging.getLogger(name = "Full")
		#hdlr = logging.FileHandler(str(os.path.dirname(__file__)) +'\\' + logFileName)
		lggrName = "C:\\Users\\Christian\\RedPanda\\"
		hdlr = logging.FileHandler(lggrName + logFileName)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

			
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr) 
		self.logger.setLevel('INFO')
		self.log('loaded')

		self.run()


	def run(self):
		spikeDF = []
		seconds = 86400
		epoch = time.time()
		since = epoch-28*seconds
		since = int(numpy.floor(since)*1000)
		spikes = []
		for exchange in exchanges:
			tickers = getattr(ccxt,exchange)().fetch_markets()
			dicname = exchange+'_tickers'
			setattr(self, dicname, [])
			time.sleep(3)
			try:
				for ticker in tickers:
					klines = getattr(ccxt, exchange)().fetch_ohlcv(symbol=ticker['symbol'], timeframe='1h', since=since, limit=None)
					x = 0.6
					for candle in klines:
						#print(candle)
						if candle[4] > candle[1]:
							if candle[3] <= candle[1]*0.6:
								dic = {}
								dic.update({'market':ticker['symbol']})
								dic.update({'exchange':exchange})
								dic.update({'time':candle[0]})
								dic.update({'open':candle[1]})
								dic.update({'high':candle[2]})
								dic.update({'low':candle[3]})
								dic.update({'close':candle[4]})
								dic.update({'volume':candle[5]})
								if candle[3]*x <= candle[1]:
									dic.update({'spikeType':'Bear'})
								spikes.append(dic)
								self.log(dic)
						if candle[4] < candle[1]:
							if candle[3] <= candle[4]*0.6:
								dic = {}
								dic.update({'market':ticker['symbol']})
								dic.update({'time':candle[0]})
								dic.update({'exchange':exchange})
								dic.update({'open':candle[1]})
								dic.update({'high':candle[2]})
								dic.update({'low':candle[3]})
								dic.update({'close':candle[4]})
								dic.update({'volume':candle[5]})
								if candle[3]*x <= candle[4]:
									dic.update({'spikeType':'Bear'})
								spikes.append(dic)
								self.log(dic)
			except: 
				self.log('Fail: %s'%(exchange))

			
		df = pd.DataFrame(spikes)
		#df = df.set_index('time')
		df.to_csv('SpikeEye101.csv')
		return df
		self.log(df)


	def log(self,msg):
		print(msg)	
		self.logger.info(msg)
ExchangeSpikeEye('ExchangeSpikes01.log')

'''





def spike_eye_func():

	bn = ccxt.binance()
	bx = ccxt.bittrex()
	seconds = 86400
	epoch = time.time()
	since = epoch-4*seconds
	since = int(numpy.floor(since)*1000)

	binanceMarketsGrab = bn.fetch_tickers()
	bittrexMarketsGrab = bx.fetch_tickers()

	binanceMarkets = []
	bittrexMarkets = []

	for market in bittrexMarketsGrab:
		bittrexMarkets.append(market)
	for market in binanceMarketsGrab:
		if market not in bittrexMarkets:
			binanceMarkets.append(market)

	spikes = []
	print('#### BITTREX MARKETS:')
	for market in bittrexMarkets:
		candles = bx.fetch_ohlcv(market, timeframe='1h', since=since, limit=None, params={})
		x = 0.6
		print(market)
		for candle in candles:
			#print(candle)
			if candle[4] > candle[1]:
				if candle[3] <= candle[1]*0.6 or candle[2]*0.6 >= candle[4]:
					dic = {}
					dic.update({'market':market})
					dic.update({'exchange':'bittrex'})
					dic.update({'time':candle[0]})
					dic.update({'open':candle[1]})
					dic.update({'high':candle[2]})
					dic.update({'low':candle[3]})
					dic.update({'close':candle[4]})
					dic.update({'volume':candle[5]})
					if candle[3]*x <= candle[1]:
						dic.update({'spikeType':'Bear'})
					if candle[2]*x >= candle[4]: 
						dic.update({'spikeType':'Bull'})
					spikes.append(dic)
					print(dic)
			if candle[4] < candle[1]:
				if candle[3] <= candle[4]*0.6 or candle[2]*0.6 >= candle[1]:
					dic = {}
					dic.update({'market':market})
					dic.update({'time':candle[0]})
					dic.update({'exchange':'bittrex'})
					dic.update({'open':candle[1]})
					dic.update({'high':candle[2]})
					dic.update({'low':candle[3]})
					dic.update({'close':candle[4]})
					dic.update({'volume':candle[5]})
					if candle[3]*x <= candle[4]:
						dic.update({'spikeType':'Bear'})
					if candle[2]*x >= candle[1]:
						dic.update({'spikeType':'Bull'})
					spikes.append(dic)
					print(dic)


	df = pd.DataFrame(spikes)
	#df = df.set_index('time')
	df.to_csv('SpikeEye.csv')
	return df
	print(df)

a = spike_eye_func()

'''