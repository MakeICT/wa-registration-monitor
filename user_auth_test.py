#!/usr/bin/python3 

import logging, time, traceback, os, sys
from datetime import datetime
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
#import MySQLdb

from WildApricotAPI.WildApricotAPI import WaApiClient
from MailBot.mailer import MailBot
#from Database import Database

#os.chdir(config.get('files', 'installDirectory'))


# tzlocal = tz.gettz('CST')

class CredCheck():
	lastAuthenticatedUser = None

	def __init__(self, client_id, client_secret, username, password):		
		self.options = {"client_id":client_id, "client_secret":client_secret}
		self.WA_API = WaApiClient(client_id, client_secret)
		while(not self.WA_API.ConnectAPI(username=username, password=password)):
			time.sleep(5)

	def AuthenticateUser(self, username, password):
		try:
			try:
				result = self.WA_API.authenticate_contact(username, password)
				self.lastAuthenticatedUser = username
				print("user authenticated!")
				return True
			except urllib.error.HTTPError as e:
				 if e.code == 400:
				 	print("invalid credentials!")
				 	return False
				 else:
				 	raise
		except Exception as e:
			message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
			mb.send([config.get('email', 'adminAddress')], "Registration Monitor Crash", message)
			raise

	def GetUserInfo(self):
		if self.lastAuthenticatedUser:
			return self.WA_API.GetContactByEmail(self.lastAuthenticatedUser)

script_start_time = datetime.now()

config = configparser.SafeConfigParser()
config.read('auth_config.ini')

script = CredCheck(config.get('api','client_id'),
				   config.get('api','client_secret'),
				   config.get('api','admin_username'),
				   config.get('api','admin_password'),)


username = 'testuser@makeict.org'
password = 'password'

script.AuthenticateUser(username, password)
# print(script.GetUserInfo())



