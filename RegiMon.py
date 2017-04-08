# -*- coding: utf-8 -*-

import logging, time
from datetime import datetime
from datetime import timedelta
from dateutil import tz
import urllib
import configparser
# import ui
# from PySide import QtCore

from WildApricotAPI.WildApricotAPI import WaApiClient
from MailBot.mailer import MailBot

tzlocal = tz.gettz('CST')

class RegiMon():
	def __init__(self, api_key):		
		self.options = {"API_key":api_key}
		while(not self.ConnectAPI()):
			pass

	def ConnectAPI(self):
		logging.debug('Connecting to API')
		self.api = WaApiClient()
		try:
			self.api.authenticate_with_apikey(self.options["API_key"])
			return True
		except urllib.error.URLError as URLerr:
			print("NO INTERWEBZ!?")
			#print(str(URLerr.reason))
			if "[Errno -2]" in str(URLerr.reason):
				print("NOPE")
				return False
			else:
				raise
		except urllib.error.HTTPError as HTTPError:
			if err.code == 401:
				print("API key not valid")
			else:
				raise

	def _make_api_request(self, request_string, api_request_object=None, method=None):
		try:	
			return self.api.execute_request(request_string, api_request_object, method)
		except urllib.error.URLError as URLerr:
			print("NO INTERWEBZ!?")
			#print(str(URLerr.reason))
			if "[Errno -2]" in str(URLerr.reason):
				print("NOPE")
				return False
			else:
				raise
		except urllib.error.HTTPError as HTTPerr:
			if HTTPerr.code == 429:
				print("too many requests")
				return False
			if HTTPerr.code == 110:
				print("timeout")
				return False
			else:
				raise



	def FindUnpaidRegistrants(self):
		logging.debug('Searching for unpaid registrants in upcoming events')
		events = self._make_api_request('Events?$filter=IsUpcoming+eq+true')
		if events == False:
			return False
		#events = api.execute_request('Events')
		#print (events)
		total_lost_fees = 0
		unpaid_registrants = []
		for event in events:
			if event["PendingRegistrationsCount"] > 0:
				registrants = self._make_api_request('EventRegistrations?eventID='+str(event['Id']))
				#print(event)
				#print(event["Name"].strip() + "(" + event["StartDate"] + ")" + ": " + str(event["PendingRegistrationsCount"]))
				for registrant in registrants:
					#print(registrant['PaidSum'])
					if registrant['PaidSum'] != registrant['RegistrationFee']:
						unpaid_registrants.append(registrant)

						#print(registrant['RegistrationFields'])
						#print (registrant)

		#print ("lost fees: " + str(total_lost_fees))

		return unpaid_registrants

	def DeleteRegistration(self, registration_id):
		try:
			self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/EventRegistrations/%d' %(registration_id), method="DELETE")
		except ValueError:
			pass

	def GetRegistrationsByContact(self, contact_id): 
		registrations = self._make_api_request('/EventRegistrations?contactId=%d'%contact_id)
		return registrations

	def FindUpcomingClassesWithOpenSpots(self):
		logging.debug('Searching for open spots in upcoming events')
		events = self._make_api_request('Events?$filter=IsUpcoming+eq+true')
		open_events = []
		for event in events:
			if event["RegistrationsLimit"] != None:
				#print(event)
				open_spots = event["RegistrationsLimit"] - (event["ConfirmedRegistrationsCount"] + event["PendingRegistrationsCount"])
				if open_spots:
					open_events += event
					print(event['Name'].strip() + " has %d spot%s open." % (open_spots, ('s' if open_spots > 1 else '')))

		return open_events

def ConvertWADate(wa_date):
	fixed_date = wa_date[0:22]+wa_date[23:]
	py_date = datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S%z')
	return py_date



config = configparser.SafeConfigParser()
config.read('myconfig.ini')
print(config.items('api'))
print(config.items('thresholds'))

time_format_string = '%B %d, %Y at %I:%M%p'
unpaid_cutoff = timedelta(days=config.getint('thresholds','unpaidCutOff'))
unpaid_buffer = timedelta(hours=config.getint('thresholds', 'unpaidBuffer'))
noshow_drop = timedelta(minutes=config.getint('thresholds','noShowDrop'))
poll_interval = config.getint('api','pollInterval')
nag_buffer = timedelta(minutes=config.getint('thresholds','nagBuffer'))
enforcement_date = datetime.strptime(config.get('thresholds','enforcementDate'),'%m-%d-%y %z')


monitor = RegiMon(config.get('api','key'))
mb = MailBot(config.get('email','username'), config.get('email','password'))

registrations = monitor.GetRegistrationsByContact(24937088)
for registration in registrations:
 	print ("%s : %d" % (registration['Event']['Name'], registration['Id']))
print()
#monitor.DeleteRegistration(18261255)
# print("registration deleted?")
#open_events = monitor.FindUpcomingClassesWithOpenSpots()

nag_list = []
delete_list = []
api_call_failures = 0
while(1):
	time.sleep(poll_interval)
	unpaid_registrants = monitor.FindUnpaidRegistrants()
	if unpaid_registrants == False:
		api_call_failures += 1
		print("API call Failures: %d" %(api_call_failures))
		continue
	
	for ur in unpaid_registrants:
		registrantEmail = [field['Value'] for field in ur['RegistrationFields'] if field['SystemCode'] == 'Email']
		registration_date = ConvertWADate(ur['RegistrationDate'])
		event_start_date = ConvertWADate(ur['Event']['StartDate'])
		time_before_class = event_start_date - datetime.now(tzlocal)
		registration_time_before_class = event_start_date - registration_date
		time_since_registration = datetime.now(tzlocal) - registration_date
		#toEmail = registrantEmail
		toEmail = ['iceman81292@gmail.com']
		needs_email = False
		new_registration = ur['Id'] not in nag_list
		deleted = ur['Id'] in delete_list

		if new_registration:
			print("Registration from %s ago."%(time_since_registration))
			print('    %s : $%d : %s : %s : %s : %s\n' 
				   %(ur['Contact']['Name'],
				   	ur['RegistrationFee'],
				   	registrantEmail,
				   	ur['RegistrationDate'],
				   	ur['Event']['Name'].strip(),
				   	time_before_class)
				   #	ur['Id'])
		 		 )
		if not deleted:
			if(time_since_registration > nag_buffer):
				if new_registration:
					print ("Sending nag email to %s:%d\n" % (ur['Contact']['Name'], ur['Contact']['Id']))
					if(registration_date < enforcement_date):
						template = open(config.get('files', 'pre-warningTemplate'), 'r')
					else:
						template = open(config.get('files', 'warningTemplate'), 'r')
					if registration_time_before_class > (unpaid_cutoff + unpaid_buffer):
						drop_date = event_start_date - unpaid_cutoff
					elif registration_time_before_class > unpaid_buffer:
						drop_date = registration_date + unpaid_buffer
					else:
						drop_date = event_start_date - noshow_drop
					nag_list.append(ur['Id'])
					needs_email = True

				elif time_since_registration > unpaid_buffer:
					if registration_time_before_class < unpaid_cutoff:
						if(registration_date > enforcement_date):
							print('Deleting registration %d and notifying %s'%(ur['Id'],ur['Contact']['Name']))
							#monitor.DeleteRegistration(18249306)
							template = open(config.get('files', 'cancellationTemplate'), 'r')
							delete_list.append(ur['Id'])
							needs_email = True
			
				if needs_email:	
					template.seek(0)
					t = template.read().format(
											     FirstName = ur['Contact']['Name'].split(',')[1], 
												 EventName = ur['Event']['Name'].strip(),
												 EventDate = event_start_date.strftime(time_format_string),
												 UnpaidDropDate = drop_date.strftime(time_format_string),
												 EnforcementDate = enforcement_date.strftime('%B %d, %Y'),
												 CancellationWindow = unpaid_cutoff.days
												 )
					subject = t.split('----')[0]
					message = t.split('----')[1]

					mb.send(toEmail, subject , message)
		#mb.check()

	