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


def get_labels():
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])

	if not labels:
		print('No labels found')
	else:
		print('Labels:')
		for label in labels:
			print(label['name'])


SCOPES = 'https://mail.google.com'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Python'
authInst=auth.auth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
credentials = authInst.get_credentials()


http= credentials. authorize(httplib2.Http())
service = discovery.build('gmail','v1', http=http)

import send_gmail

sendInst = send_gmail.send_email(service)
message = sendInst.create_message_with_attachment('rp.cryptotrading@gmail.com', 'chrisabh@gmail.com', 'Testing 123', 'Hi there, this is a test from Python', 'cup.jpg')
sendInst.send_message('me', message)