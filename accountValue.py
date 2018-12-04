import ccxt
from bnWebsocket import keychain
import time

def Account_Balance(exchange):
	factory = getattr(ccxt,exchange)()
	factory.apiKey=getattr(keychain,exchange).Christian('API')
	factory.secret=getattr(keychain,exchange).Christian('Secret')

	balances = factory.fetch_total_balance()

	usd_Balance=0
	usdt_usd=ccxt.kraken().fetch_ticker('USDT/USD')['last']
	try:
		btc_usd=ccxt.bitmex().fetch_ticker('BTC/USD')['last']
	except:
		btc_usd=ccxt.coinbase().fetch_ticker('BTC/USD')['last']
	print(btc_usd)

	for currency in balances:
		if balances[currency] != 0:
			time.sleep(0.1)
			if currency == 'BTC':
				balance=balances[currency]*btc_usd
			elif currency == 'USDT':
				balance=balances[currency]*usdt_usd 
			else:
				try:
					btc_pair=factory.fetch_ticker(f'{currency}/BTC')['last']
					balance=balances[currency]*btc_pair*btc_usd
				except Exception as e:
					print(e)
			print(currency, balance)
			usd_Balance=usd_Balance+balance
	
	return [usd_Balance,btc_usd]
	
