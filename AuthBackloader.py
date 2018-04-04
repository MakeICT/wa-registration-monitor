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

WA_API = WaApiClient()

tzlocal = tz.gettz('CST')

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
		# test_user_id=38043528
		# test_user_id=38657966
		# test_user_id=42705673
		# test_event_id=2567080
		# test_group_id = 280209
		#result = WA_API.GetEventByID(test_event_id)
		#result = WA_API.GetRegistrationTypesByEventID(test_event_id)
		#result = WA_API.SetMemberGroups(test_user_id, [test_group_id])
		#print(result)
		#result = WA_API.GetMemberGroups()
		#for group in result:
		#   print(group['Name'], group['Id'])
		#print(result)
				#Get all contact IDs
		#
		valid_authorizations = ['Woodshop','Metalshop','Forge','LaserCutter',\
								'Mig welding', 'Tig welding', 'Stick welding', 'Manual mill',\
								'Plasma', 'Metal lathes', 'CNC Plasma', 'Intro Tormach', 'Full Tormach']
		
		auth_groups = [group['Name'] for group in WA_API.GetMemberGroups() if group['Name'].strip().split('_')[0] == 'auth']
		print(auth_groups)

		total_class_auths = 0
		unauthorized_attendees = 0

		#WA_API.SetAuthorizations(38657966,['Forge'],['2018-01-01'])
		
		events = WA_API.GetPastEvents()
		# contacts = WA_API.GetAllContacts()

		# for contact in contacts:
		# 	print(contact['FieldValues'])

		authorization = 'CNC Plasma'
		# authorization = 'LaserCutter'

		assert authorization in valid_authorizations, "Not a valid authorization"

		laser_search_strings = ['laser cutter certification', 'laser cutter authorization class', 'laser cutting basics', 'laser cutting quick authorization']
		cncplasma_search_strings = ['cnc plasma cutting basics', 'cnc plasma with jeremiah burian']
		if authorization == 'LaserCutter':
			search_strings = laser_search_strings
		elif authorization == 'CNC Plasma':
			search_strings = cncplasma_search_strings

		for event in events:
			match = False
			for string in search_strings:
				if event['Name'].lower().find(string) == 0:
					match = True
					break

			if match:
				print(event['Name'], event['StartDate'])
				registrants = WA_API.GetRegistrantsByEventID(event['Id'])
				for registrant in registrants:
					if registrant['IsCheckedIn']:
						total_class_auths += 1
						current_authorizations = WA_API.GetAuthorizations(registrant['Contact']['Id'])
						already_authorized = True if current_authorizations.find(authorization)>=0 else False
						if not already_authorized:
							unauthorized_attendees += 1
							# WA_API.SetAuthorizations(registrant['Contact']['Id'],['LaserCutter'],[event["StartDate"].split('T')[0]])
						print(registrant["DisplayName"], event["StartDate"].split('T')[0], already_authorized)
				time.sleep(5)

				print("\n\n")
			else:
				pass
				#print(event['Name'], event['StartDate'])
		print(str(unauthorized_attendees)+'/'+str(total_class_auths))
		sys.exit()






























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
			try:
				has_authorizations=False
				user_authorizations=[]
				while(1):
					contact = WA_API.GetContactById(contactID)
					if contact:
						break
					time.sleep(5)
				print('\n\n',contact["FirstName"], contact["LastName"])
				#if contact["FirstName"] != "Testy":
				#   continue


				for field in contact["FieldValues"]:
					if field["FieldName"] == "authorizations":
						if field["Value"] == '' or field["Value"] == None:
							print("No authorizations")
						else:
							for authorization in field["Value"].split('\n'):
								authorization_name = authorization[0:-11].strip()
								if authorization_name != '':
									if authorization_name in valid_authorizations:
										has_authorizations=True
										user_authorizations.append(authorization_name)
									else:
										#print(contact["FirstName"], contact["LastName"],'>')
										print("ANOMALY FOUND:")
										print(authorization_name)
										print(authorization)


				is_member = True
				try:
					contact["MembershipEnabled"]
				except KeyError:
					is_member = False
				if is_member:
					if contact['Status'] == "Lapsed":
						print('changing lapsed member Non-Member')
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
				if not has_authorizations:
					contactIDs.pop()
					continue
				if has_authorizations:
					print("Has authorizations:", user_authorizations)
					#if contact is not member
					if not is_member:
						#add contact to Non-Member membership level
						while(1):
							if WA_API.SetContactMembership(contact['Id'],'813239'):
								break
							time.sleep(5)
						#TODO:approve membership
					auth_group_list = []
					for auth in user_authorizations:
						auth_group_list.append(auth_map[auth])
					print(auth_group_list)
					while(1):
						if WA_API.SetMemberGroups(contact['Id'], auth_group_list):
							break
						time.sleep(5)
					#read list of authorizations from contact membership field
					#add contact to appropriate groups according to authorizations
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
		mb.send([config.get('email', 'adminAddress')], "Authorization Backloader Crash", message)
		raise

# if datetime.now() - script_start_time > timedelta(minutes=60):
#   exit()


