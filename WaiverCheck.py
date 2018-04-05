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

class WaiverCheck():
    def __init__(self, api_key):		
        self.options = {"API_key":api_key}
        while(not WA_API.ConnectAPI(self.options["API_key"])):
            time.sleep(5)

    def SetWaiverDate(self, contact_ID, date):
        WA_API.UpdateContactField(contact_ID, 'WaiverDate', date)
    
    def SetDOB(self, contact_ID, date):
            WA_API.UpdateContactField(contact_ID, 'DOB', date)

script_start_time = datetime.now()
#db = Database()
#current_db = db.GetAll()
#for entry in current_db:
#	print (entry)
config = configparser.SafeConfigParser()
config.read('config.ini')

time_format_string = '%B %d, %Y at %I:%M%p'

script = WaiverCheck(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'))
mb.setDisplayName(config.get('email', 'displayName'))
mb.setAdminAddress(config.get('email', 'adminAddress'))

sw = smartwaiver.Smartwaiver(config.get('smartwaiver', 'api_key'))

templates = sw.get_waiver_templates()

for template in templates:
    print(template.template_id + ': ' + template.title)

# Get a list of recent signed waivers for this account
summaries = sw.get_waiver_summaries(100)

# List waiver ID and title for each summary returned
print('List all waivers:\n')
for summary in summaries:
    print("====================================")
    print(summary.waiver_id + ': ' + summary.title)
    # print(summary.tags)
    WA_ID = None
    print(summary.first_name, summary.last_name)

    for tag in summary.tags:
        if tag.split(' ')[0]=='WA_ID':
            WA_ID = int(tag.split(' ')[1])

    if WA_ID:
    	pass

    else:
        waiver = sw.get_waiver(summary.waiver_id, True)
        try:
            #Pull contact's info from WA if it exists
            contact = WA_API.GetContactByEmail(waiver.email)[0]
            #print(contact)

            WA_ID = contact['Id']

        #If query returns no contact
        except IndexError:
            print("Contact does not exist")
            continue

    #If waiver date is not newer than what is currently on the WA profile, don't update
    saved_waiver_date = [field['Value'] for field in contact['FieldValues'] if field['FieldName']=="WaiverDate"][0]
    print("saved waiver date:", saved_waiver_date)
    print("summary created_on date:", summary.created_on)
    if saved_waiver_date:
        if datetime.strptime(saved_waiver_date, "%Y-%m-%d %H:%M:%S") >= datetime.strptime(summary.created_on, "%Y-%m-%d %H:%M:%S"):
            continue

    #update WA account waiver date with the current waiver's date
    print('.' + summary.dob + '.')
    waiver_DOB = datetime.strptime(summary.dob, "%Y-%m-%d")
    WA_DOB = waiver_DOB.strftime("%d %b %Y")
    #print(WA_DOB)
    #print(WA_ID, ":", waiver_date)
    #print(waiver_DOB)
    #print(type(WA_ID))
    #print(type(waiver_date))
    script.SetWaiverDate(WA_ID, summary.created_on)
    script.SetDOB(WA_ID, summary.dob)


    
    #print(waiver.pdf)

#Send waiver email if no waiver
#   -When a new member signs up
#   -When somebody registers for an event
#   -Periodically when a member doesn't have a current waiver (rate limit)
