#!/usr/bin/python3

import logging, time, traceback, os, sys
from datetime import datetime
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
#import MySQLdb

from mcp_api import McpApiClient
from WildApricotAPI.WildApricotAPI import WaApiClient
from MailBot.mailer import MailBot
#from Database import Database

#os.chdir(config.get('files', 'installDirectory'))

class AuthConv():
    def __init__(self, api_key):        
        self.options = {"API_key":api_key}
        while(not WA_API.ConnectAPI(self.options["API_key"])):
            time.sleep(5)
        self.working_file_name = 'unprocessed_id_list.txt'

    def SendEmail(self, to_address, template, replacements):
        template.seek(0)
        t = template.read().format(**replacements)
        subject = t.split('----')[0]
        message = t.split('----')[1]
        mb.send(to_address, subject , message)
        # db.AddLogEntry(event['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
        #              action="Send email with subject `%s`" %(subject.strip()))

    def WriteUnprocessedIDs(self, id_list):
        with open(self.working_file_name, 'w') as f:
            for _id in id_list:
                f.write(str(_id) + '\n')


    def ReadUnprocessedIDs(self):
        with open(self.working_file_name, 'r') as f:
            id_list = [int(line.rstrip('\n')) for line in f]
        return id_list

script_start_time = datetime.now()
#db = Database()
#current_db = db.GetAll()
#for entry in current_db:
#   print (entry)
config = configparser.SafeConfigParser()
config.read('config.ini')
print(config.items('api'))
print(config.items('thresholds'))

MCP_API = McpApiClient()
MCP_API.authenticate_with_contact_credentials(config.get('mcp_api', 'username'), config.get('mcp_api','password'))

WA_API = WaApiClient()

tzlocal = tz.gettz('CST')

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
#   reminders_days.append(timedelta(days=int(r)))

converter = AuthConv(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'))
mb.setDisplayName(config.get('email', 'displayName'))
mb.setAdminAddress(config.get('email', 'adminAddress'))

if False:
    pass
else:
    try:
        try:
            contactIDs = converter.ReadUnprocessedIDs()
            print('Continuing previous id list')
            if not contactIDs:
                contactIDs = WA_API.GetAllContactIDs()
        except:
            contactIDs = WA_API.GetAllContactIDs()
        #contactIDs = [42705673,38657966,38043528,32777335,42819834]




        while contactIDs:
            converter.WriteUnprocessedIDs(contactIDs)
            contactID = contactIDs.pop()
            contactIDs.append(contactID)
            #contactID = 24937088
            try:
                has_key=False
                while(1):
                    contact = WA_API.GetContactById(contactID)
                    if contact:
                        break
                    time.sleep(5)
                print('\n\n',contact["FirstName"], contact["LastName"])
                #if contact["FirstName"] != "Testy":
                #   continue
                MCP_user = MCP_API.GetUserByEmail(contact["Email"])
                if not MCP_user:
                    print("Not found in MCP")
                else:
                    print(MCP_user['firstName'],MCP_user['lastName'], 'is in the MCP')
                    if(MCP_user['nfcID']):
                        has_key=True
                    is_member = True
                    try:
                        contact["MembershipEnabled"]
                    except KeyError:
                        is_member = False
                    if is_member:
                        if contact['Status'] == "Lapsed":
                            print('changing lapsed member to Non-Member')
                            while(1):
                                if WA_API.SetContactMembership(contact['Id'],'813239'):
                                    break
                                time.sleep(5)
                        #print("Member:True")
                    else:
                        pass
                        #print("Member:False")
                    #check if contact has authorizations
                    #if contact has authorizations
                    if not has_key:
                        contactIDs.pop()
                        continue
                    if has_key:
                        print("Has key")
                        #if contact is not member
                        if not is_member:
                            #add contact to Non-Member membership level
                            while(1):
                                if WA_API.SetContactMembership(contact['Id'],'813239'):
                                    break
                                time.sleep(5)
                            #TODO:approve membership
                        while(1):
                            if WA_API.SetMemberGroups(contact['Id'], [435189]):
                                print('added to door auth group')
                                break
                            time.sleep(5)
                contactIDs.pop()
                time.sleep(1)

            except KeyboardInterrupt:
                raise
            except:
                raise
                print('CAUGHT EXCEPTION; CONTINUING')
        print(contactIDs)
        converter.WriteUnprocessedIDs(contactIDs)
        #result = WA_API.GetContactById(test_user_id)
        #print(result)
        #WA_API.SetContactMembership(test_user_id)
        #WA_API.SetEventAccessControl(test_event_id, restricted=True, any_group=False, group_ids=[130906])
        #WA_API.SetContactGroups(test_user_id)
    #   WA_API.ProcessUnpaidRegistrants(upcoming_events)
    #   WA_API.SendEventReminders(upcoming_events)
    #   print(config.get('email', 'adminAddress'))
    #   message = "Registration Monitor completed successfully"
    #   mb.send([config.get('email', 'adminAddress')], "Registration Monitor Success", message)

    except Exception as e:
        message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
        mb.send([config.get('email', 'adminAddress')], "Authorization Converter Crash", message)
        raise

# if datetime.now() - script_start_time > timedelta(minutes=60):
#   exit()


