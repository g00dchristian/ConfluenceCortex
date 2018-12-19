import time
from sqlog import logCloseTrade
from sqlog import sqlogger
from bnWebsocket.languageHandled import languageHandler
from tradeModule import TradeClient








def Close_Trades(openTrades, pkg):
	limiter=pkg['Trade_Limiter']
	logReturn=[]
	sql_log = 0
	tradestatus=0 #Has to be outside of the loop as we only need to know if a trade has occured 
	if len(openTrades)>0:
		for trade in openTrades:
			closegatewayresult=0
			closeQuery=0
			if trade['Market']==pkg['Market'] and trade['Strategy']==pkg['Strategy']:
				print('  ! Open Trade Reviewed: %s'%(trade['Market']))
				#LIMITATION: The Trade Check only refers to the same strategy timeperiod... i.e. the 4h confluence cannot affect the 1d trades
				if pkg['CR'] <50 and trade['ClipSize']>0:
					closeOtype='market-sell'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='CR'

				if pkg['CR'] >-50 and trade['ClipSize']<0:
					closeOtype='market-buy'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='CR'

				if pkg['Price'] <= trade['Stop_Level'] and trade['ClipSize']>0:
					closeOtype='market-sell'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='Stop_Loss'

				if pkg['Price'] >= trade['Stop_Level'] and trade['ClipSize']<0:
					closeOtype='market-buy'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='Stop_Loss'

				if pkg['Price'] >= trade['Profit_Level'] and trade['ClipSize']>0:
					closeOtype='market-sell'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='Profit_Take'

				if pkg['Price'] <= trade['Profit_Level'] and trade['ClipSize']<0:
					closeOtype='market-buy'
					closeOtype=closeOtype+pkg['Testing']
					closeQuery=1
					closeMethod='Profit_Take'
				
				if time.time() < limiter:
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
						sql_log=['Close',(trade['UUID'],trade['Open_Time'],TC.tPrice,trade['OrderPrice'],trade['ClipSize'],TC.oid,closeMethod)]

						trade.update({'Market':'Closed'})
						trade.update({'ClipSize':0})
						closegatewayresult = (f"Trade Closed-- {trade['UUID']}")
						tradestatus=1
						limiter = time.time()+pkg['Limiter_Rate']

					except Exception as error_result:
						closegatewayresult = f"FAILED-- attempt to close Trade[{trade['UUID']}]: {error_result}"

				if closegatewayresult!=0:
					logReturn.append(closegatewayresult)


	return {'Log':logReturn,'Trade_Status':tradestatus, 'Trade_Limiter':limiter, 'SQL':sql_log}



def Open_Trade(refracList, openTrades, pkg, tpkg):  
	print('  ! New Trade Reviewed: %s'%(pkg['Market']))
	limiter=pkg['Trade_Limiter']
	logReturn=[]
	eligible=1
	sql_log=0
	tradestatus=0
	if len(refracList)>0:
		for datum in refracList:
			if datum['Market'] == pkg['Market'] and datum['Strategy'] == pkg['Strategy'] and time.time()<datum['Epoch']:
				eligible=0
				gatewayresult = ('FAILED-- %s_%s within refractory period'%(pkg['Market'], pkg['Strategy']))
	if len(openTrades)>0:
		symboltotal=0
		opentotal=0
		for datum in openTrades:
			if datum['Market'] == pkg['Market'] and datum['Strategy'] == pkg['Strategy']:
				symboltotal=symboltotal+datum['USD_Value']
			opentotal=opentotal+datum['USD_Value']
		if symboltotal >= tpkg['MaxPair']:


			
			eligible=0
			gatewayresult = ('FAILED-- Total open %s_%s trades (%.1f) exceeds restriction (%.1f)'%(pkg['Market'], pkg['Strategy'], symboltotal, tpkg['MaxPair']))
		if opentotal >= tpkg['MaxOpen']:
			eligible=0
			gatewayresult = ('FAILED-- Total open trades (%.1f) exceeds restriction (%.1f)'%(opentotal,tpkg['MaxOpen']))
	if pkg['Market'][-4:] != 'USDT' and pkg['Exchange'] == 'Binance':
		eligible=0
		gatewayresult=('FAILED-- Pair not USDT pair and not recognised by clipSize_USD calculator')
	
	if pkg['Market'][-3:] != 'USD' and pkg['Exchange'] == 'Bitmex':
		eligible=0
		gatewayresult=('FAILED-- Pair not USD on Bitmex therefore not supported by clipSize_USD calculator')


	if time.time() < limiter:
		eligible=0
		gatewayresult=('FAILED-- Trade Rate Limiter Exceeded')			 




	if eligible == 1:
		try:
			if pkg['Exchange'] == 'Binance':
				clipSize = (tpkg['usdClipSize']/pkg['Price'])
			elif pkg['Exchange'] == 'Bitmex':
				clipSize = tpkg['usdClipSize']
			if pkg['Side'] == 'buy':
				oType='market-buy'
				oType=oType+pkg['Testing']
			elif pkg['Side'] == 'sell':
				oType='market-sell'
				oType=oType+pkg['Testing']
				clipSize=clipSize*-1


			TC=TradeClient(exchange=pkg['Exchange'].lower(),
				market=languageHandler(output_lang="TradeModule", inputs=[pkg['Market']], input_lang=pkg['Exchange'])[0],
				clipSize=abs(clipSize),
				orderPrice=0.00000001,
				orderType=oType
				)

			
			
			pkg.update({'clipSize':clipSize})
			pkg.update({'Exchange_UUID':TC.oid})
			pkg.update({'tPrice':TC.tPrice})
			if pkg['Exchange']=='Binance':
				pkg.update({'USD':(abs(float(pkg['Price'])*float(clipSize)))}) #TESTING LINE
			elif pkg['Exchange']=='Bitmex':
				pkg.update({'USD':clipSize})
			
			#pkg.update({'USD':(abs(float(TC.tPrice)*float(clipSize)))})
			sql_log=['Open',(pkg,tpkg['CR'],tpkg['CF'])]	
			gatewayresult = ('SUCCESS-- Trade Sent (Trade OID: %s)'%(TC.oid)) 

			limiter = time.time()+pkg['Limiter_Rate']
			tradestatus=1

		except Exception as error_result:
			gatewayresult = ('FAILED attempt to send trade: %s'%(error_result))


	logReturn.append(gatewayresult)
	print('tradestatus',tradestatus)
	return {'Log':logReturn,'Trade_Status':tradestatus, 'Trade_Limiter':limiter, 'SQL':sql_log}
	

