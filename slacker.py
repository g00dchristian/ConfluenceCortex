from slackclient import SlackClient
from bnWebsocket import keychain


def send_message(msg):
	sc=SlackClient(keychain.slack.TradeAlertApp('BotUser'))
	sc_read=SlackClient(keychain.slack.TradeAlertApp('OAuth'))
	sc.api_call('chat.postMessage', channel=keychain.slack.IDs('levelalert'), text=msg)	
	print('Sent')