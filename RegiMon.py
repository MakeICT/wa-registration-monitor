#!/usr/bin/python3

try:
	import logging, time, traceback, os
	from datetime import datetime
	from datetime import timedelta
	from dateutil import tz
	import urllib
	import configparser
	import MySQLdb

	from WildApricotAPI.WildApricotAPI import WaApiClient
	from MailBot.mailer import MailBot
	from Database import Database

	config = configparser.SafeConfigParser()
	config.read('config.ini')
	os.chdir(config.get('files','installDirectory'))

	tzlocal = tz.gettz('CST')

	class RegiMon():
		def __init__(self, api_key):		
			self.options = {"API_key":api_key}
			while(not self.ConnectAPI()):
				time.sleep(5)

		def ConnectAPI(self):
			logging.debug('Connecting to API')
			self.api = WaApiClient()
			try:
				self.api.authenticate_with_apikey(self.options["API_key"])
				return True
			except urllib.error.HTTPError as e:
				print('The server couldn\'t fulfill the request.')
				print('Error code: ', e.code)
			except urllib.error.URLError as e:
				print('We failed to reach a server.')
				print('Reason: ', e.reason)
			return False

		def _make_api_request(self, request_string, api_request_object=None, method=None):
			try:	
				return self.api.execute_request(request_string, api_request_object, method)
			except urllib.error.HTTPError as e:
				print('The server couldn\'t fulfill the request.')
				print('Error code: ', e.code)
			except urllib.error.URLError as e:
				print('We failed to reach a server.')
				print('Reason: ', e.reason)
			return False

		def GetRegistrantsByEventID(self, event_id):
			registrants = self._make_api_request('EventRegistrations?eventID='+str(event_id))
			return registrants

		def FindUnpaidRegistrants(self):
			logging.debug('Searching for unpaid registrants in upcoming events')
			events = self._make_api_request('Events?$filter=IsUpcoming+eq+true')
			if events == False:
				return False
			# for event in events:
			#	if "TEST" in event["Name"].split(','):
			#		registrants = self._make_api_request('EventRegistrations?eventID='+str(event['Id']))
			#		print(event)
			#		print('\n')
			#		print(registrants)

			#events = api.execute_request('Events')
			#print (events)
			total_lost_fees = 0
			unpaid_registrants = []
			for event in events:
				if event["PendingRegistrationsCount"] > 0:
					registrants = self._make_api_request('EventRegistrations?eventID='+str(event['Id']))
					if registrants == False:
						return False
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

		def CheckPendingPayment(self, registration):
			for field in registration["RegistrationFields"]:
				if field["FieldName"] == "StorageBinNumber":
					if field["Value"] == "PendingPayment":
						return True
			return False

		def MarkPendingPayment(self, registration_id, registration):
			for field in registration["RegistrationFields"]:
				if field["FieldName"] == "StorageBinNumber":
					print("Found Last Name!")
					field["Value"] = "PendingPayment"

			response = self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/EventRegistrations/%d' %(registration_id), registration, method="PUT")

		def DeleteRegistration(self, registration_id):
			try:
				response = self._make_api_request('https://api.wildapricot.org/v2.1/accounts/84576/EventRegistrations/%d' %(registration_id), method="DELETE")
				if response == False:
					return False
			except ValueError:
				pass

		def GetRegistrationsByContact(self, contact_id): 
			registrations = self._make_api_request('/EventRegistrations?contactId=%d'%contact_id)
			return registrations


		def FindUpcomingClasses(self):
			logging.debug('Finding all upcoming classes')
			events = self._make_api_request('Events?$filter=IsUpcoming+eq+true')
			if events == False:
				return False

			return events

		def FindUpcomingClassesWithOpenSpots(self):
			logging.debug('Searching for open spots in upcoming events')
			events = self._make_api_request('Events?$filter=IsUpcoming+eq+true')
			if events == False:
				return False
			open_events = []
			for event in events:
				if event["RegistrationsLimit"] != None:
					#print(event)
					open_spots = event["RegistrationsLimit"] - (event["ConfirmedRegistrationsCount"] + event["PendingRegistrationsCount"])
					if open_spots:
						open_events += event
						print(event['Name'].strip() + " has %d spot%s open." % (open_spots, ('s' if open_spots > 1 else '')))

			return open_events

		def FilterClassesWithNoCheckinVolunteer(self, events):
			if events == False:
				return False
			no_checkin_events = []
			for event in events:
				no_checkin_volunteer = True
				if event["Tags"]:
					for tag in event["Tags"]:
						split_tag = tag.split(':')
						if split_tag[0] == 'checkin':
							no_checkin_volunteer = False

					#print(event)
				if no_checkin_volunteer:
					no_checkin_events.append(event)
					print(event['Name'].strip() + " has no checkin volunteer.")

			return no_checkin_events

		def GetInvoiceByID(self, invoice_id):
			invoice = self._make_api_request('Invoices/%s' % (invoice_id))
			return invoice

		def GetLogItems(self):
			log = self._make_api_request("AuditLogItems/?StartDate=2017-04-25&EndDate=2017-04-27")
			return log

		def ConvertWADate(self, wa_date):
			fixed_date = wa_date[0:22]+wa_date[23:]
			py_date = datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S%z')
			return py_date


####################################################################################################################################################

		def SendEmail(self, to_address, template, replacements):
			template.seek(0)
			t = template.read().format(**replacements)
			subject = t.split('----')[0]
			message = t.split('----')[1]
			mb.send(to_address, subject , message)
			# db.AddLogEntry(event['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
			#			   action="Send email with subject `%s`" %(subject.strip()))

		def ProcessUnpaidRegistrants(self, events):
				unpaid_registrants = []
				for event in events:
					if event["PendingRegistrationsCount"] > 0:
						registrants = self._make_api_request('EventRegistrations?eventID='+str(event['Id']))
						if registrants == False:
							return False
						#print(event)
						#print(event["Name"].strip() + "(" + event["StartDate"] + ")" + ": " + str(event["PendingRegistrationsCount"]))
						for registrant in registrants:
							#print(registrant['PaidSum'])
							if registrant['PaidSum'] != registrant['RegistrationFee']:
								unpaid_registrants.append(registrant)

								#print(registrant['RegistrationFields'])
								#print (registrant)

				#print ("lost fees: " + str(total_lost_fees))

				#return unpaid_registrants

				for ur in unpaid_registrants:
					registrantEmail = [field['Value'] for field in ur['RegistrationFields'] if field['SystemCode'] == 'Email']
					registration_date = self.ConvertWADate(ur['RegistrationDate'])
					event_start_date = self.ConvertWADate(ur['Event']['StartDate'])
					time_before_class = event_start_date - datetime.now(tzlocal)
					registration_time_before_class = event_start_date - registration_date
					time_since_registration = datetime.now(tzlocal) - registration_date
					split_name = ur['Contact']['Name'].split(',')
					registrant_first_name = split_name[1].strip()
					registrant_last_name = split_name[0].strip()

					#TEST
					# print(registrant_first_name)
					# if(registrant_first_name.strip()=='Testy' or registrant_last_name=='Testy'):
					#	print("Found Test User!")
					#	self.MarkPendingPayment(ur['Id'], ur)

					if registration_time_before_class > (unpaid_cutoff + unpaid_buffer):
						drop_date = event_start_date - unpaid_cutoff
					elif registration_time_before_class > unpaid_buffer:
						drop_date = registration_date + unpaid_buffer
					else:
						drop_date = event_start_date - noshow_drop
						
					if (config.getint('script','debug')==1):
						toEmail = config.get('email', 'adminAddress')
					else:
						toEmail = registrantEmail

					needs_email = False
					#new_registration = ur['Id'] not in nag_list
					db_entry = db.GetEntryByRegistrationID(ur['Id'])
					if not db_entry:
						new_registration = True
					else:
						new_registration = False
					#deleted = ur['Id'] in delete_list


					# if new_registration:
					#	print("Registration from %s ago."%(time_since_registration))
					#	print('    %s : $%d : %s : %s : %s : %s\n' 
					#		   %(ur['Contact']['Name'],
					#			ur['RegistrationFee'],
					#			registrantEmail,
					#			ur['RegistrationDate'],
					#			ur['Event']['Name'].strip(),
					#			time_before_class)
					#		   #	ur['Id'])
					#		 )
					#if not deleted:
					if not self.CheckPendingPayment(ur):
						if(time_since_registration > nag_buffer):
							if new_registration:
								print ("Sending nag email to %s:%d\n" % (ur['Contact']['Name'], ur['Contact']['Id']))
								if(registration_date < enforcement_date):
									template = open(config.get('files', 'pre-warningTemplate'), 'r')
								else:
									template = open(config.get('files', 'warningTemplate'), 'r')
								#nag_list.append(ur['Id'])
								db.AddEntry(registrant_first_name, registrant_last_name, registrantEmail[0], ur['Contact']['Id'], ur['Id'])
								db.AddLogEntry(ur['Event']['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
											   action="Add unpaid registration to nag database.")
								db.SetFirstNagSent(ur['Id'])
								needs_email = True

							elif time_since_registration > unpaid_buffer:
								if time_before_class < unpaid_cutoff:
									if(registration_date > enforcement_date):
										print('Deleting registration %d and notifying %s'%(ur['Id'],ur['Contact']['Name']))
										monitor.DeleteRegistration(ur['Id'])
										template = open(config.get('files', 'cancellationTemplate'), 'r')
										#delete_list.append(ur['Id'])
										db.AddLogEntry(ur['Event']['Name'].strip(), ur['Contact']['Name'], registrantEmail[0],
													   action="Delete registration")
										db.SetRegistrationDeleted(ur['Id'])
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

								db.AddLogEntry(ur['Event']['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
													   action="Send email with subject `%s`" %(subject.strip()))
								mb.send(toEmail, subject , message)

		def SendEventReminders(self, events):
			if events:
				for event in events:
					event_start_date = self.ConvertWADate(event['StartDate'])
					time_before_class = event_start_date - datetime.now(tzlocal)

					if not db.GetEntryByEventID(event['Id']):
						print("event '%s' not in database" % event['Name'].strip())
						db.AddEventToDB(event['Id'])
						db.AddLogEntry(event['Name'].strip(), None, None,
								   action="Add event `%s` to database" %(event['Name'].strip()))

					index = 1
					for r in reminders_days:
						needs_email = False
						if time_before_class < r:
							if index == 1:
								if not db.GetFirstEventNagSent(event['Id']) and time_before_class > reminders_days[index]:
									print("send first event reminder email for " + event['Name'].strip())
									db.SetFirstEventNagSent(event['Id'])
									template = open(config.get('files', 'eventReminder'), 'r')
									needs_email = True
							if index == 2:
								if not db.GetSecondEventNagSent(event['Id']) and time_before_class > reminders_days[index]:
									print("send second event reminder email for " + event['Name'].strip())
									db.SetSecondEventNagSent(event['Id'])
									template = open(config.get('files', 'eventReminder'), 'r')
									needs_email = True
							if index == 3:
								if not db.GetThirdEventNagSent(event['Id']):
									print("send third event reminder email for " + event['Name'])
									db.SetThirdEventNagSent(event['Id'])
									template = open(config.get('files', 'eventReminder'), 'r')
									needs_email = True

						if needs_email:	
							registrants = monitor.GetRegistrantsByEventID(event['Id'])
							if registrants:
								for r in registrants:
									registrantEmail = [field['Value'] for field in r['RegistrationFields'] if field['SystemCode'] == 'Email']
									registration_date = self.ConvertWADate(r['RegistrationDate'])
									registration_time_before_class = event_start_date - registration_date
									time_since_registration = datetime.now(tzlocal) - registration_date
									registrant_first_name = r['Contact']['Name'].split(',')[1]
									registrant_last_name = r['Contact']['Name'].split(',')[0]

									if config.getint('script', 'debug') == 1:
										# print("debug succeeded")
										toEmail = config.get('email', 'AdminAddress')
									else:
										# print("debug failed")
										toEmail = registrantEmail

									replacements =  {'FirstName':registrant_first_name, 
													 'EventName':event['Name'].strip(),
													 'EventDate':event_start_date.strftime(time_format_string),
													 'ReminderNumber':index}
									self.SendEmail(toEmail, template, replacements)
									db.AddLogEntry(event['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
												   action="Send event reminder email")
							else: 
								print("Failed to get registrant list")

								# template.seek(0)
								# t = template.read().format(
								#						     FirstName = registrant_first_name, 
								#							 EventName = event['Name'].strip(),
								#							 EventDate = event_start_date.strftime(time_format_string),
								#							 ReminderNumber = index
								#							 )
								# subject = t.split('----')[0]
								# message = t.split('----')[1]

								# mb.send(toEmail, subject , message)

						index+=1

		def ProcessEventsWithNoCheckinVolunteer(self, events):
			filtered_events = self.FilterClassesWithNoCheckinVolunteer(events)
			for event in filtered_events:
				pass

	script_start_time = datetime.now()
	db = Database(config.get('database','name'),config.get('database','username'),config.get('database','password'))
	current_db = db.GetAll()
	# for entry in current_db:
		# print (entry)
	# print(config.items('api'))
	# print(config.items('thresholds'))

	time_format_string = '%B %d, %Y at %I:%M%p'
	unpaid_cutoff = timedelta(days=config.getint('thresholds','unpaidCutOff'))
	unpaid_buffer = timedelta(hours=config.getint('thresholds', 'unpaidBuffer'))
	noshow_drop = timedelta(minutes=config.getint('thresholds','noShowDrop'))
	poll_interval = config.getint('api','pollInterval')
	nag_buffer = timedelta(minutes=config.getint('thresholds','nagBuffer'))
	enforcement_date = datetime.strptime(config.get('thresholds','enforcementDate'),'%m-%d-%y %z')
	reminders = len(config.get('thresholds', 'reminderDays').split(','))
	reminders_days = []
	for r in config.get('thresholds', 'reminderDays').split(','):
		reminders_days.append(timedelta(days=int(r)))

	monitor = RegiMon(config.get('api','key'))
	mb = MailBot(config.get('email','username'), config.get('email','password'))
	mb.setDisplayName(config.get('email', 'displayName'))
	mb.setAdminAddress(config.get('email', 'adminAddress'))

	#monitor.GetInvoiceByID('34694085')

	# log = monitor.GetLogItems()
	# for entry in log:
	#	print(entry)

	# registrations = monitor.GetRegistrationsByContact(24937088)
	# for registration in registrations:
	#	print ("%s : %d" % (registration['Event']['Name'], registration['Id']))
	# print()
	#monitor.DeleteRegistration(18261255)
	# print("registration deleted?")
	#open_events = monitor.FindUpcomingClassesWithOpenSpots()

	#nag_list = []
	#delete_list = []
	# api_call_failures = 0
	# while(1):
	#	time.sleep(poll_interval)

	##### Find and email unpaid registrants #####
	#unpaid_registrants = monitor.FindUnpaidRegistrants()


	# for entry in db.GetLog():
	#	print(entry)

	##### Find events that need check-in volunteers and email event-team #####
	# events_without_checkin = monitor.FindUpcomingClassesWithNoCheckinVolunteer()
	# #print(events_without_checkin)
	# for event in events_without_checkin:
	#	print(event)
	#	template = open(config.get('files', 'checkinRequ0estTemplate'), 'r')
	#	template.seek(0)
	#	t = template.read().format(
	#								 EventName = event['Name'].strip(),
	#								 EventDate = event_start_date.strftime(time_format_string),
	#								 )
	#	subject = t.split('----')[0]
	#	message = t.split('----')[1]

	#	mb.send(toEmail, subject , message)
	#	#mb.check()

	##### Send Reminders to registrants in upcoming events #####
	upcoming_events = monitor.FindUpcomingClasses()
	if upcoming_events == False:
		api_call_failures += 1
		print("API call Failures: %d" %(api_call_failures))

	else:
		monitor.ProcessUnpaidRegistrants(upcoming_events)
		monitor.SendEventReminders(upcoming_events)
		# print(config.get('email', 'adminAddress'))
		message = "Registration Monitor completed successfully"
		mb.send([config.get('email', 'adminAddress')], "Registration Monitor Success", message)

		# if datetime.now() - script_start_time > timedelta(minutes=60):
		#	exit()

except Exception as e:
	message = "The following exception was thrown:\r\n\r\n" + str(e) + "\r\n\r\n" + traceback.format_exc()
	mb.send([config.get('email', 'adminAddress')], "Registration Monitor Crash", message)
	raise
