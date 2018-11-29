from uuid import uuid4
from datetime import datetime
import time
import sqlite3

def sqlogger(pkg,CR,CF):
	print('LOGGER HAS BEEN SENT DATA')
	tradeID = str(uuid4())
	tradeIDstring = '`'+tradeID+'`'
	conn = sqlite3.connect('tradelog.db')
	c = conn.cursor()
	#-- ENTER TRADE_LIST VALUES -------------------------------------------------------------
	c.execute("INSERT INTO Trade_List(UUID,Time,Symbol,Status,Clip_Size,Strategy,USD_Value,Exchange,Version,Profit_Take,Stop_Loss) VALUES(:UUID,:Time,:Symbol,:Status,:Clip_Size,:Strategy,:USD_Value,:Exchange,:Version,:Profit_Take,:Stop_Loss)",
			{
			'UUID':tradeID,
            'Time':datetime.now(),
            'Symbol':pkg['Market'],
            'Status':'Open',
            'Clip_Size':pkg['clipSize'],
            'Strategy':pkg['Strategy'],
            'USD_Value':pkg['USD'],
            'Exchange':pkg['Exchange'],
            'Version':pkg['Version'],
            'Profit_Take':pkg['Profit_Take'],
            'Stop_Loss':pkg['Stop_Loss']
            })
	conn.commit()

	#-- ENTER TRADE_RESULT VALUES -------------------------------------------------------------
	c.execute("INSERT INTO Trade_Results(UUID,OrderPrice,Profit_Level,Stop_Level) VALUES(:UUID,:OrderPrice,:Profit_Level,:Stop_Level)",
			{
			'UUID':tradeID,
			'OrderPrice':pkg['tPrice'],
			'Profit_Level':pkg['Profit_Level'],
			'Stop_Level':pkg['Stop_Level']
			# 'ClosePrice':,
			# 'Return':,
			# 'PnL':
			})
	conn.commit()

	#-- ENTER CONFLUENCE_RATING VALUES -------------------------------------------------------------
	c.execute("INSERT INTO Confluence_Ratings(UUID,Sentiment,Break,GenVolume,RSI,AbnorVol,InsideBar,Rating) VALUES(:UUID,:Sentiment,:Break,:GenVolume,:RSI,:AbnorVol,:InsideBar,:Rating)",
			{
			'UUID':tradeID, 
			'Sentiment':CR['Sentiment'],
			'Break':CR['Break'],
			'GenVolume':CR['GenVolume'],
			'RSI':CR['RSI'],
			'AbnorVol':CR['AbnorVol'],
			'InsideBar':CR['IB'],
			'Rating':pkg['CR']
			})
	conn.commit()

	#-- ENTER CONFLUENCE_FACTOR -------------------------------------------------------------------
	c.execute("INSERT INTO Confluence_Factors(UUID,Sentiment,Break,GenVolume,RSI,AbnorVol,InsideBar) VALUES(:UUID,:Sentiment,:Break,:GenVolume,:RSI,:AbnorVol,:InsideBar)",
			{
			'UUID':tradeID, 
			'Sentiment':CF['Sentiment'],
			'Break':CF['Break'],
			'GenVolume':CF['GenVolume'],
			'RSI':CF['RSI'],
			'AbnorVol':CF['AbnorVol'],
			'InsideBar':CF['IB'],
			})
	conn.commit()

	#-- ENTER TRADE_ID -------------------------------------------------------------------
	c.execute("INSERT INTO Trade_ID(UUID,Xopen_UUID) VALUES(:UUID,:Xopen_UUID)",
			{
			'UUID':tradeID, 
			'Xopen_UUID':pkg['Exchange_UUID']
			})
	conn.commit()

	#-- ENTER REFRACTORY_PERIOD -------------------------------------------------------------------
	c.execute("INSERT INTO REFRACTORY_PERIODS(UUID, Symbol, Time, Strategy, Epoch) VALUES(:UUID,:Symbol,:Time,:Strategy,:Epoch)",
			{
			'UUID':tradeID, 
			'Symbol':pkg['Market'], 
			'Time':datetime.now(),
			'Strategy':pkg['Strategy'],
			'Epoch':time.time()+pkg['RefracPeriod'],
			})
	conn.commit()
	print('SQLOG: refrac entry')

	return tradeID


def logCloseTrade(uuid, opentime, closeprice, openprice, clipSize, oid, closeMethod):
	conn = sqlite3.connect('tradelog.db')
	open_time=datetime.strptime(opentime,'%Y-%m-%d %H:%M:%S.%f').timestamp()
	print
	c = conn.cursor()
	stringuuid=('"'+str(uuid)+'"')
	#Side
	if clipSize>0:
		returnValue=(closeprice/openprice)-1
		pnl=(closeprice-openprice)*abs(clipSize)
	elif clipSize<0:
		returnValue=(openprice/closeprice)-1
		pnl=(openprice-closeprice)*abs(clipSize)

	if returnValue>0:
		status='Profit'
	elif returnValue<=0:
		status='Loss'
	else:
		status='ERROR'

	now = datetime.now()

	#Update Trade_List Status
	c.execute("UPDATE Trade_Results set ClosePrice=?, Return=?, PnL=?, Trade_Duration=?, Close_Method=? WHERE UUID=?",(closeprice,returnValue,pnl,open_time-now.timestamp(),closeMethod,uuid))
	conn.commit()


	#Retrive and Update Trade_Results
	c.execute("UPDATE TRADE_LIST set Status=?, Close_Time=? WHERE UUID=?",(status,now,uuid))
	conn.commit()

	#Update Exchange Close OID
	c.execute("UPDATE Trade_ID set Xclose_UUID=? WHERE UUID=?",(oid,uuid))
	conn.commit()

	#Refractory Erase
	c.execute("DELETE FROM REFRACTORY_PERIODS WHERE UUID=?",(uuid,))
	conn.commit()

	
	conn.close()




	#conn = sqlite3.connect(':memory') - RAM memory
def openTrades():
	conn = sqlite3.connect('tradelog.db')
	c = conn.cursor()
	trades = []
	SQL='''SELECT Trade_List.UUID, Trade_List.SYMBOL, Trade_List.STRATEGY, Trade_Results.OrderPrice, Trade_List.USD_VALUE, Trade_List.Clip_Size, Trade_List.Time, Trade_Results.Stop_Level, Trade_Results.Profit_Level FROM Trade_List
		INNER JOIN Trade_Results
		ON Trade_List.UUID=Trade_Results.UUID
		WHERE Trade_List.Status = "Open"'''
	c.execute(SQL)
	for entry in c.fetchall():
		trade={}
		trade.update({'UUID':entry[0]})
		trade.update({'Market':entry[1]})  
		trade.update({'Strategy':entry[2]})
		trade.update({'OrderPrice':entry[3]})
		trade.update({'USD_Value':entry[4]})
		trade.update({'ClipSize':entry[5]})
		trade.update({'Open_Time':entry[6]})
		trade.update({'Stop_Level':entry[7]})
		trade.update({'Profit_Level':entry[8]})
		trades.append(trade)
	conn.commit()
	conn.close()
	return trades 



def refracFetch():
	conn = sqlite3.connect('tradelog.db')
	c = conn.cursor()
	refracPeriods = []
	SQL='''SELECT  SYMBOL, TIME, STRATEGY, EPOCH FROM Refractory_Periods'''
	c.execute(SQL)
	for entry in c.fetchall():
		refrac={}
		refrac.update({'Market':entry[0]})
		refrac.update({'Time':entry[1]})
		refrac.update({'Strategy':entry[2]})
		refrac.update({'Epoch':entry[3]})
		refracPeriods.append(refrac)
	conn.close()
	#print(refracPeriods)
	return refracPeriods 



  