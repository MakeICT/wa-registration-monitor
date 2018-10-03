from automationscript import Script

from datetime import datetime
from datetime import timedelta
from dateutil import tz

from wildapricot_api import WaApiClient
from mailer import MailBot
from database import Database

class ChildScript(Script):
	def Setup(self):
		self.WA_API = WaApiClient()        
		while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
			time.sleep(5)

	def CheckPendingPayment(self, registration):
		for field in registration["RegistrationFields"]:
			if field["FieldName"] == "StorageBinNumber":
				if field["Value"] == "PendingPayment":
					return True
		return False

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

	def ProcessUnpaidRegistrants(self, events):
			unpaid_registrants = []
			for event in events:
				if event["PendingRegistrationsCount"] > 0:
					registrants = self.WA_API.GetRegistrantsByEventID(event['Id'])
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
				registration_date = self.WA_API.WADateToDateTime(ur['RegistrationDate'])
				event_start_date = self.WA_API.WADateToDateTime(ur['Event']['StartDate'])
				time_before_class = event_start_date - datetime.now(self.tzlocal)
				registration_time_before_class = event_start_date - registration_date
				time_since_registration = datetime.now(self.tzlocal) - registration_date
				split_name = ur['Contact']['Name'].split(',')
				registrant_first_name = split_name[1].strip()
				registrant_last_name = split_name[0].strip()


				if registration_time_before_class > (self.unpaid_cutoff + self.unpaid_buffer):
					drop_date = event_start_date - self.unpaid_cutoff
				elif registration_time_before_class > self.unpaid_buffer:
					drop_date = registration_date + self.unpaid_buffer
				else:
					drop_date = event_start_date - self.noshow_drop
					
				toEmail = registrantEmail

				needs_email = False
				db_entry = self.db.GetEntryByRegistrationID(ur['Id'])
				if not db_entry:
					new_registration = True
				else:
					new_registration = False

				if not self.CheckPendingPayment(ur):
					if(time_since_registration > self.nag_buffer):
						if new_registration:
							print ("Sending nag email to %s:%d\n" % (ur['Contact']['Name'], ur['Contact']['Id']))
							if(registration_date < self.enforcement_date):
								template = open(self.config.get('files', 'pre-warningTemplate'), 'r')
							else:
								template = open(self.config.get('files', 'warningTemplate'), 'r')
							self.db.AddEntry(registrant_first_name, registrant_last_name, registrantEmail[0], ur['Contact']['Id'], ur['Id'])
							self.db.AddLogEntry(ur['Event']['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
										   action="Add unpaid registration to nag database.")
							self.db.SetFirstNagSent(ur['Id'])
							needs_email = True

						elif time_since_registration > self.unpaid_buffer:
							if time_before_class < self.unpaid_cutoff:
								if(registration_date > self.enforcement_date):
									print('Deleting registration %d and notifying %s'%(ur['Id'],ur['Contact']['Name']))
									if(not self.config.getboolean("script","debug")):
										self.WA_API.DeleteRegistration(ur['Id'])
									template = open(self.config.get('files', 'cancellationTemplate'), 'r')
									self.db.AddLogEntry(ur['Event']['Name'].strip(), ur['Contact']['Name'], registrantEmail[0],
												   action="Delete registration")
									self.db.SetRegistrationDeleted(ur['Id'])
									needs_email = True
					
						if needs_email: 
							replacements =	{"FirstName":ur['Contact']['Name'].split(',')[1], 
											 "EventName":ur['Event']['Name'].strip(),
											 "EventDate":event_start_date.strftime(self.time_format_string),
											 "UnpaidDropDate":drop_date.strftime(self.time_format_string),
											 "EnforcementDate":self.enforcement_date.strftime('%B %d, %Y'),
											 "CancellationWindow":self.unpaid_cutoff.days}
							template.seek(0)				 
							subject = template.read().format(**replacements).split('----')[0]
							success = self.mailer.SendTemplate(toEmail, template , replacements, self.config.getboolean("script","debug"))
							self.db.AddLogEntry(ur['Event']['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
												   action="Send email with subject `%s`" %(subject.strip()))

	def SendEventReminders(self, events):
		if events:
			for event in events:
				event_start_date = self.WA_API.WADateToDateTime(event['StartDate'])
				time_before_class = event_start_date - datetime.now(self.tzlocal)

				if not self.db.GetEntryByEventID(event['Id']):
					print("event '%s' not in database" % event['Name'].strip())
					self.db.AddEventToDB(event['Id'])
					self.db.AddLogEntry(event['Name'].strip(), None, None,
							   action="Add event `%s` to database" %(event['Name'].strip()))

					for tag in event['Tags']:
						split_tag = tag.split(':')
						if split_tag[0] == 'instructor_name':
							instructor_name = ' '.join(split_tag[1:])
						elif split_tag[0] == 'instructor_email':
							instructor_email = ' '.join(split_tag[1:])

					if(instructor_email):
						template = open(self.config.get('files', 'classConfirmation'), 'r')
						replacements =  {'FirstName':instructor_name.split()[0], 
										 'EventName':event['Name'].strip(),
										 'EventDate':event_start_date.strftime(self.time_format_string),
										}
						self.mailer.SendTemplate(instructor_email, template, replacements, self.config.getboolean("script","debug"))
						self.db.AddLogEntry(event['Name'].strip(), instructor_name, instructor_email,
									   action="Send class confirmation email")

				index = 1
				for r in self.reminders_days:
					needs_email = False
					if time_before_class < r:
						if index == 1:
							if not self.db.GetFirstEventNagSent(event['Id']) and time_before_class > self.reminders_days[index]:
								print("send first event reminder email for " + event['Name'].strip())
								self.db.SetFirstEventNagSent(event['Id'])
								template = open(self.config.get('files', 'eventReminder'), 'r')
								needs_email = True
						if index == 2:
							if not self.db.GetSecondEventNagSent(event['Id']) and time_before_class > self.reminders_days[index]:
								print("send second event reminder email for " + event['Name'].strip())
								self.db.SetSecondEventNagSent(event['Id'])
								template = open(self.config.get('files', 'eventReminder'), 'r')
								needs_email = True
						if index == 3:
							if not self.db.GetThirdEventNagSent(event['Id']):
								print("send third event reminder email for " + event['Name'])
								self.db.SetThirdEventNagSent(event['Id'])
								template = open(self.config.get('files', 'eventReminder'), 'r')
								needs_email = True

					if needs_email: 
						registrants = self.WA_API.GetRegistrantsByEventID(event['Id'])
						if registrants:
							for r in registrants:
								registrantEmail = [field['Value'] for field in r['RegistrationFields'] if field['SystemCode'] == 'Email']
								registration_date = self.WA_API.WADateToDateTime(r['RegistrationDate'])
								registration_time_before_class = event_start_date - registration_date
								time_since_registration = datetime.now(self.tzlocal) - registration_date
								registrant_first_name = r['Contact']['Name'].split(',')[1]
								registrant_last_name = r['Contact']['Name'].split(',')[0]

								toEmail = registrantEmail

								replacements =  {'FirstName':registrant_first_name, 
												 'EventName':event['Name'].strip(),
												 'EventDate':event_start_date.strftime(self.time_format_string),
												 'ReminderNumber':index}
								self.mailer.SendTemplate(toEmail, template, replacements, self.config.getboolean("script","debug"))
								self.db.AddLogEntry(event['Name'].strip(), registrant_first_name +' '+ registrant_last_name, registrantEmail[0],
											   action="Send event reminder email")
						else: 
							print("Failed to get registrant list")
                                                
					index+=1

	def ProcessEventsWithNoCheckinVolunteer(self, events):
		filtered_events = self.FilterClassesWithNoCheckinVolunteer(events)
		for event in filtered_events:
			pass

	def Run(self):
		self.tzlocal = tz.gettz('CST')

		self.db = Database(self.config.get('database','name'),self.config.get('database','username'),self.config.get('database','password'))
		#current_db = self.db.GetAll()
		# for entry in current_db:
			# print (entry)
		# print(self.config.items('api'))
		# print(self.config.items('thresholds'))

		self.time_format_string = '%B %d, %Y at %I:%M%p'
		self.unpaid_cutoff = timedelta(days=self.config.getint('thresholds','unpaidCutOff'))
		self.unpaid_buffer = timedelta(hours=self.config.getint('thresholds', 'unpaidBuffer'))
		self.noshow_drop = timedelta(minutes=self.config.getint('thresholds','noShowDrop'))
		# self.poll_interval = self.config.getint('api','pollInterval')
		self.nag_buffer = timedelta(minutes=self.config.getint('thresholds','nagBuffer'))
		self.enforcement_date = datetime.strptime(self.config.get('thresholds','enforcementDate'),'%m-%d-%y %z')
		self.reminders = len(self.config.get('thresholds', 'reminderDays').split(','))
		self.reminders_days = []
		for r in self.config.get('thresholds', 'reminderDays').split(','):
			self.reminders_days.append(timedelta(days=int(r)))

		self.mailer.setDisplayName(self.config.get('email', 'displayName'))
		self.mailer.setAdminAddress(self.config.get('email', 'adminAddress'))

		api_call_failures=0

		upcoming_events = self.WA_API.GetUpcomingEvents()
		if upcoming_events == False:
			api_call_failures += 1
			print("API call Failures: %d" %(api_call_failures))

		else:
			self.ProcessUnpaidRegistrants(upcoming_events)
			self.SendEventReminders(upcoming_events)

if __name__ == "__main__":
	s = ChildScript("New Registration Monitor")
	s.RunAndNotify()
