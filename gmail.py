from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools 
from oauth2client.file import Storage
import auth

try:
	import argparse
	flags= argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

import send_gmail
from datetime import datetime

def get_labels():
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])

	if not labels:
		print('No labels found')
	else:
		print('Labels:')
		for label in labels:
			print(label['name'])


from CortexPnL import PnL

PnL('Daily') 


SCOPES = 'https://mail.google.com'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Python'
authInst=auth.auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
credentials = authInst.get_credentials()


http= credentials. authorize(httplib2.Http())
service = discovery.build('gmail','v1', http=http)


recipients='blight@atlantictrading.co.uk; ren@atlantictrading.co.uk; sutton@atlantictrading.co.uk; abhayaratna@atlantictrading.co.uk'
# recipients='abhayaratna@atlantictrading.co.uk'
sendInst = send_gmail.send_email(service)
message = sendInst.create_message_with_excel_attachment('rp.cryptotrading@gmail.com', recipients, f'Cortex Report: {datetime.today().strftime("%Y-%m-%d")}', 'Cortex Report attached', f'{datetime.today().strftime("%Y-%m-%d")} Cortex PnL.xlsx')
sendInst.send_message('me', message)