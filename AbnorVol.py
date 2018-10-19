

def AbnormalVolume(df, vM=1.5, pM=1.1):
	vdf=df[-30:]
	vdf.loc[:,'Weighting'] = 1/(vdf.index**0.5)
	weight_sum = vdf.loc[:,'Weighting'].sum()
	vdf.loc[:,'vSignal'] = (vdf.loc[:,'Volume'] * vdf.loc[:,'Weighting']) /weight_sum
	vdf.loc[:,'pSignal'] = (abs(vdf.loc[:,'Change']) * vdf.loc[:,'Weighting']) /weight_sum
	vol_mv_avg = vdf.loc[:,'vSignal'].sum()
	price_mv_avg = vdf.loc[:,'pSignal'].sum()
	vThreshold = vM*vol_mv_avg
	pThreshold = pM*price_mv_avg

	pThreshDistance = float(pThreshold) - abs(vdf.loc[1,'Change'])
	vThreshDistance = float(vThreshold) - vdf.loc[1,'Volume']
	

	#---- VOL_EYE -------------------------------
	if abs(vdf.loc[1,'Change']) <= pThreshold and abs(vdf.loc[1,'Volume']) >= vThreshold:
		if vdf.loc[1,'Change'] > 0: 
			result='Bullish'
		else: 
			result='Bearish'
	else: result = 'Nil'
	

	#-- PASS RESULTS -------------------------------------------
	AbnorVolResult = {
	'vM':vM,
	'pM':pM,
	'pThreshDistance':pThreshDistance,
	'vThreshDistance':vThreshDistance,
	'vThreshold':vThreshold,
	'pThreshold':pThreshold,
	'Result':result
	}

	return AbnorVolResult


