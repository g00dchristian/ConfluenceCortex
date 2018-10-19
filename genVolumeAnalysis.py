
def genVolumeAnalysis(df, propertyDic):
	consecVolMin = 3

	for index, row in df.iterrows():
		#Volume Type - Bull/Bea
		if row['Close']>=row['Open']:
			df.loc[index, 'VolType'] = 'Bull'
			volType = 'Bull'
		if row['Close']<row['Open']:
			df.loc[index, 'VolType'] = 'Bear'
			volType = 'Bear'


	if df.loc[1, 'VolType'] == df.loc[2, 'VolType'] == df.loc[3, 'VolType']:
		if df.loc[1, 'Volume'] <= df.loc[1, 'Volume'] <= df.loc[1, 'Volume']:
			propertyDic['VolumeAnalysis']='Decelerating'
		elif df.loc[1, 'Volume'] >= df.loc[1, 'Volume'] >= df.loc[1, 'Volume']:
			propertyDic['VolumeAnalysis']='Accelerating'
		else:
			propertyDic['VolumeAnalysis']='Nil'
	else:
		propertyDic['VolumeAnalysis']='Nil'


	results = {
	'Accel/Decel':propertyDic['VolumeAnalysis'],
	'Type':volType
	}
	return results