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


tzlocal = tz.gettz('CST')

class CredCheck():
	def __init__(self, client_id, client_secret, username, password):		
		self.options = {"client_id":client_id, "client_secret":client_secret}
		self.WA_API = WaApiClient(client_id, client_secret)
		while(not self.WA_API.ConnectAPI(username=username, password=password)):
			time.sleep(5)

	def AuthenticateUser(self, username, password):
		try:
			try:
				result = self.WA_API.authenticate_contact(username, password)
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

	def PrintUserInfo(self):
		print(self.WA_API.GetMe())
		print(self.WA_API.GetContactById(38657966))

script_start_time = datetime.now()
#db = Database()
#current_db = db.GetAll()
#for entry in current_db:
#	print (entry)
config = configparser.SafeConfigParser()
config.read('config.ini')
print(config.items('api'))
print(config.items('thresholds'))

time_format_string = '%B %d, %Y at %I:%M%p'
unpaid_cutoff = timedelta(days=config.getint('thresholds','unpaidCutOff'))
unpaid_buffer = timedelta(hours=config.getint('thresholds', 'unpaidBuffer'))
noshow_drop = timedelta(minutes=config.getint('thresholds','noShowDrop'))
poll_interval = config.getint('api','pollInterval')
nag_buffer = timedelta(minutes=config.getint('thresholds','nagBuffer'))
enforcement_date = datetime.strptime(config.get('thresholds','enforcementDate'),'%m-%d-%y %z')
reminders = len(config.get('thresholds', 'reminderDays').split(','))
reminders_days = []
#for r in config.get('thresholds', 'reminderDays').split(','):
#	reminders_days.append(timedelta(days=int(r)))

#script = CredCheck('tzh619hfyw','1mt5qzws075bfywcwk5jt7bw2oikml','iceman81292@gmail.com', 'TJLr9Ffg')
script = CredCheck('tzh619hfyw','1mt5qzws075bfywcwk5jt7bw2oikml','testuser@makeict.org', 'password')

mb = MailBot(config.get('email','username'), config.get('email','password'))
mb.setDisplayName(config.get('email', 'displayName'))
mb.setAdminAddress(config.get('email', 'adminAddress'))

#script.AuthenticateUser('testuser@makeict.org', 'password')
script.PrintUserInfo()
#script.AuthenticateUser('iceman81292@gmail.com', 'TJLr9Ffg')



