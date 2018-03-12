#!/usr/bin/python3

import logging, time, traceback, os, sys
from datetime import datetime, date
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
import smartwaiver
#import MySQLdb

from WildApricotAPI.WildApricotAPI import WaApiClient
from MailBot.mailer import MailBot
#from Database import Database

#os.chdir(config.get('files', 'installDirectory'))

WA_API = WaApiClient()

tzlocal = tz.gettz('CST')

class PayCalc():
	def __init__(self, api_key):		
		self.options = {"API_key":api_key}
		while(not WA_API.ConnectAPI(self.options["API_key"])):
			time.sleep(5)


script_start_time = datetime.now()
#db = Database()
#current_db = db.GetAll()
#for entry in current_db:
#	print (entry)
config = configparser.SafeConfigParser()
config.read('config.ini')

time_format_string = '%B %d, %Y at %I:%M%p'
unpaid_cutoff = timedelta(days=config.getint('thresholds','unpaidCutOff'))
unpaid_buffer = timedelta(hours=config.getint('thresholds', 'unpaidBuffer'))
noshow_drop = timedelta(minutes=config.getint('thresholds','noShowDrop'))
poll_interval = config.getint('api','pollInterval')
nag_buffer = timedelta(minutes=config.getint('thresholds','nagBuffer'))
enforcement_date = datetime.strptime(config.get('thresholds','enforcementDate'),'%m-%d-%y %z')
reminders = len(config.get('thresholds', 'reminderDays').split(','))
reminders_days = []
refund_cutoff = 7
refund_grace_hours = 24
refund_min_days = 1
#for r in config.get('thresholds', 'reminderDays').split(','):
#	reminders_days.append(timedelta(days=int(r)))

script = PayCalc(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'))
mb.setDisplayName(config.get('email', 'displayName'))
mb.setAdminAddress(config.get('email', 'adminAddress'))

sw = smartwaiver.Smartwaiver(config.get('smartwaiver', 'api_key'))

templates = sw.get_waiver_templates()

for template in templates:
    print(template.template_id + ': ' + template.title)

# Get a list of recent signed waivers for this account
summaries = sw.get_waiver_summaries()

# List waiver ID and title for each summary returned
print('List all waivers:\n')
for summary in summaries:
    print(summary.waiver_id + ': ' + summary.title)
    # print(summary.tags)
    WA_ID = None

    for tag in summary.tags:
        if tag.split(' ')[0]=='WA_ID':
            WA_ID = tag.split(' ')[1]

    if WA_ID:
    	pass

    else:
        waiver = sw.get_waiver(summary.waiver_id, True)
        contact = WA_API.GetContactByEmail(waiver.email)[0]
        WA_ID = contact['Id']
    #update WA account waiver version with the current waiver's version number
    waiver_date = summary.created_on
    print(WA_ID, ":", waiver_date)


    
    #print(waiver.pdf)
