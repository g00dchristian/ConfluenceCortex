
import pandas as pd
import os
def languageHandler(output_lang="Bittrex",input_lang= "Binance" ,inputs=[""]):
	"""
	#Binance is all uppercase capitals with buy | sell e.g. BTCUSDT
	#Bittrex is hyphenated uppercase capitals with sell | buy e.g. USDT-BTC
	filename = "LanguageFile.csv"
	filepath =  os.path.dirname(os.path.realpath(__file__)) +"\\"
	lang_file = pd.read_csv(filepath+filename,header = 0)
	output = []
	for ins in inputs:
		try:
			output.append(lang_file[lang_file[input_lang]==ins][output_lang].values[0])
			#output.append(ins)
			#print(lang_file[lang_file[input_lang]==ins][output_lang].values[0])
		except IndexError:
			print("WARNING, TRYING TO TRANSLATE INELIGIBLE MARKET, MARKET :" +ins)
			return
	print('Input: %s (InputLang %s) | output: %s (output_lang: %s'%(inputs, input_lang, output, output_lang))
	return output

	#print(languageHandler("Bittrex","Binance",["NEOBTC","INCNTBTC"]))

	"""
	output = []
	if input_lang == 'TradeModule'  and output_lang == 'Bittrex':
		for ins in inputs:
			output.append(ins.split('/')[1]+'-'+ins.split('/')[0])
			#print(ins.split('/')[1]+'-'+ins.split('/')[0])

	elif input_lang == 'TradeModule' and output_lang == 'Binance':
		for ins in inputs:	
			output.append(ins.split('/')[0]+ins.split('/')[1])
			#print(ins.split('/')[0]+ins.split('/')[1])
	elif input_lang == 'Binance' and output_lang == 'TradeModule':
		for ins in inputs:	
			if ins[-3:] == 'BTC':
				output.append(ins[:-3]+'/'+ins[-3:])
			elif ins[-4:] == 'USDT':
				output.append(ins[:-4]+'/'+ins[-4:])
			elif ins[-3:] == 'ETH':
				output.append(ins[:-3]+'/'+ins[-3:])
			elif ins[-3:] == 'BNB':
				output.append(ins[:-3]+'/'+ins[-3:])

	elif input_lang == 'Bittrex' and output_lang == 'TradeModule':
		for ins in inputs:
			output.append(ins.split('-')[1]+'/'+ins.split('-')[0])
	else:
		"ERROR: Change the languageHandler back to Ben's format"
	return output

	