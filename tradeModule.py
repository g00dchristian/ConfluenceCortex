### Trade Module ###
import ccxt
from bnWebsocket import keychain

"""
Inputs:
- Exchange
- Market
- ClipSize
- OrderPrice

Functions:
- Log Order Number
- Check if order placed
- Send Slack Message
"""

#bn=ccxt.binance()

class TradeClient():
	"""Required Inputs:
	exchange 	= 'Binance'
	market 		= 'BTC/USDT'
	clipSize 	= 1
	orderPrice 	= 5000
	orderType 	= 'limit-buy' / 'limit-sell' / 'market-buy' / 'market-sell'
	TradeSafe	= TradeSafe csv file required. clipSize limits 

	In-built safety measures:
	Limit Orders: 	If the price of a limit or is such that it would execute as a market order, the trade will be rejected
	TradeSafe:	Trader will not run without being provided a TradeSafe csv file 

		"""
	def __init__(self, exchange, market, clipSize, orderPrice, orderType):
		self.exchange=exchange
		self.market=market
		self.clipSize=clipSize
		self.orderPrice=orderPrice
		self.oid = "OrderID Undefined"
		self.factory = getattr(ccxt,exchange)()
		self.factory.apiKey=getattr(keychain,exchange).Christian('API')
		self.factory.secret=getattr(keychain,exchange).Christian('Secret')
		#self.factory.verbose=True
		if orderType == 'limit-buy': self.limitBuy()
		elif orderType == 'limit-sell': self.limitSell()
		elif orderType == 'market-buy': self.marketBuy()
		elif orderType == 'market-sell': self.marketSell()
		elif orderType == 'market-buy-test': self.marketBuyTest()
		elif orderType == 'market-sell-test': self.marketSellTest()
		else: print('-- ERROR: Invalid orderType --\n// Accepted Formats:\n"limit-buy"\n"limit-sell"\n"market-buy"\n"market-sell"')

	def limitBuy(self):
		ticker = self.factory.fetch_ticker(self.market)['last']
		if float(self.orderPrice) < ticker:
			order=self.factory.create_limit_buy_order(self.market, self.clipSize, self.orderPrice)
			self.oid = order['id']
			self.tPrice = order['price']
		else: 
			print('ERROR: Invalid orderPrice for orderType')

	def limitSell(self):
		ticker = self.factory.fetch_ticker(self.market)['last']
		if float(self.orderPrice) > ticker:
			order=self.factory.create_limit_sell_order(self.market, self.clipSize, self.orderPrice)
			self.oid = order['id']
			self.tPrice = order['price']
		else: print('ERROR: Invalid orderPrice for orderType')

	def marketBuy(self):
		order=self.factory.create_market_buy_order(self.market, self.clipSize)
		self.oid = order['id']
		self.tPrice = order['price']


	def marketSell(self):
		order=self.factory.create_market_sell_order(self.market, self.clipSize)
		self.oid = order['id']
		self.tPrice = order['price']


	def marketBuyTest(self):
		self.tPrice=self.factory.fetch_ticker(self.market)['last']
		self.oid='test'
		print('trade occured')

	def marketSellTest(self):
		self.tPrice=self.factory.fetch_ticker(self.market)['last']
		self.oid='test'
		print('trade occured')
