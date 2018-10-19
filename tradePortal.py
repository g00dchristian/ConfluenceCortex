import ccxt
from sqlog import sqlogger






def OpenTrade(pkg, tradepkg, confluenceRating, confluenceFactor):
	factory=getattr(ccxt,pkg['Exchange'].lower())

	#LOG TRADE
	#Prrrrrrrobs need to attach exchange uuid to the trade too.......
	#pkg.update(EXCHANGE trade UUID)
	logreturn=sqlog(pkg, confluenceRating, confluenceFactor)



	output={
	'UUID':logreturn
	}

	return output



def CloseTrade():
	pass