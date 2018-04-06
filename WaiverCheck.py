#!/usr/bin/python3

from automationscript import Script

from datetime import datetime, date
from datetime import timedelta

import smartwaiver
from wildapricot_api import WaApiClient



class ChildScript(Script):
	def Setup(self):
		self.WA_API = WaApiClient()        
		while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
			time.sleep(5)

	def SetWaiverDate(self, contact_ID, date):
		self.WA_API.UpdateContactField(contact_ID, 'WaiverDate', date)
	
	def SetDOB(self, contact_ID, date):
		self.WA_API.UpdateContactField(contact_ID, 'DOB', date)

	def GetWaiverlessMembers(self):
		contacts = self.WA_API.GetAllContacts()
		waiverless_members=[]
		for contact in contacts:
			flattened_contact_fields = {field["SystemCode"]:field["Value"] for field in contact['FieldValues']}
			if flattened_contact_fields["IsMember"]:
				if flattened_contact_fields["MembershipLevelId"] != 813239:
					# check for oldWaiverLink, Waiverlink, and WaiverDate field, respectively
					# if not flattened_contact_fields["custom-7903153"]:
					if flattened_contact_fields["custom-7973495"].strip()=='' and flattened_contact_fields["custom-9876059"].strip()=='':
						waiverless_members.append(contact)
		for member in waiverless_members:
			print(member['FirstName'], member['LastName'])
		print (len(waiverless_members))

	def Run(self):
		self.GetWaiverlessMembers()



		script_start_time = datetime.now()

		time_format_string = '%B %d, %Y at %I:%M%p'

		sw = smartwaiver.Smartwaiver(self.config.get('smartwaiver', 'api_key'))

		templates = sw.get_waiver_templates()

		for template in templates:
			print(template.template_id + ': ' + template.title)

		# Get a list of recent signed waivers for this account
		summaries = sw.get_waiver_summaries(100)

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
					contact = self.WA_API.GetContactByEmail(waiver.email)[0]
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
			if saved_waiver_date.strip() != '':
				print("Has waiver date")
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
			self.SetWaiverDate(WA_ID, summary.created_on)
			time.sleep(3)
			self.SetDOB(WA_ID, summary.dob)


			
			#print(waiver.pdf)

s = ChildScript("Waiver Check")
s.RunAndNotify()



#Send waiver email if no waiver
#   -When a new member signs up
#   -When somebody registers for an event
#   -Periodically when a member doesn't have a current waiver (rate limit)
