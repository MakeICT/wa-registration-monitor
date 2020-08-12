#!/usr/bin/python3

import logging, time, traceback, os
from datetime import datetime
# from datetime import timedelta
# from dateutil import tz
# import urllib
import configparser
# import MySQLdb

# from WildApricotAPI.WildApricotAPI import WaApiClient
from mailer import MailBot
# from database import Database


class Script(object):
	'''An automation script template '''
	def __init__(self, name):
		self.name = name
		self.start_time = datetime.now()
		self.config = configparser.SafeConfigParser()
		self.config.read('config.ini')
		os.chdir(self.config.get('files','installDirectory'))

		self.mailer = MailBot(self.config.get('email','username'), self.config.get('email','password'), self.config.get('email','server'), self.config.get('email','port'))
		self.mailer.setDisplayName(self.config.get('email', 'displayName'))
		self.mailer.setAdminAddress(self.config.get('email', 'adminAddress'))

		# db = Database(self.config.get('database','name'),self.config.get('database','username'),self.config.get('database','password'))
		# current_db = db.GetAll()

		self.Setup()

	def LogDebug(self, message):
		logging.debug(message)

	def LogInfo(self, message):
		logging.info(message)

	def LogError(self, message):
		logging.error(message)

	def LogWarn(self, message):
		logging.warn(message)

	def RunAndNotify(self):
		try:
			self.Run()

		except Exception as e:
			message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
			# self.mailer.send([self.config.get('email', 'adminAddress')], self.name + " has crashed!", message)
			raise

		else:
			message = "The script '%s' ran successfully" % (self.name)
			# self.mailer.send([self.config.get('email', 'adminAddress')], self.name + " ran successfully", message)

	def Setup(self):
		pass

	def Run(self):
		pass

# class ChildScript(Script):
# 	def Run(self):
# 		assert 1==2, "I'm bad at numbers" 

# s = ChildScript("Test Script")
# s.RunAndNotify()
