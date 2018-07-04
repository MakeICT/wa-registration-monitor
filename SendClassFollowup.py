#!/usr/bin/python3

from automationscript import Script

from datetime import datetime
from datetime import timedelta
# from dateutil import tz

from wildapricot_api import WaApiClient
# from database import Database

import urllib


class ChildScript(Script):
	def SendSurveys(self):
		processed_ids = self.ReadProcessedIDs()
		print(processed_ids)
		start_date = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0)
		end_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59)
		print(start_date.strftime("%Y-%m-%dT%H:%M:%S%z"))
		print(end_date.strftime("%Y-%m-%dT%H:%M:%S%z"))
		events = self.WA_API.GetEventsByDate(start_date.strftime("%Y-%m-%dT%H:%M:%S%z"), end_date.strftime("%Y-%m-%dT%H:%M:%S%z"))
		for event in events:
			encoded_name = urllib.parse.quote_plus(event["Name"])
			survey_link = "https://docs.google.com/forms/d/e/1FAIpQLSew_pFQ26mvqMUUWUHFsVZHWikXuAsuupSNVmhJv3kvYxHbDw/viewform?entry.1220350320=%s" % (encoded_name)
			
			attended_registrants = self.WA_API.GetRegistrantsByEventID(event["Id"], checked_in=True)
			template = open(self.config.get('files', 'classSurveyRequest'), 'r')

			reg_info = []
			for r in attended_registrants:
				flattened_reg_fields = {field["SystemCode"]:field["Value"] for field in r['RegistrationFields']}
				flattened_reg_fields['Id'] = r['Id']
				print(r['Id'])
				reg_info.append(flattened_reg_fields)
			
			for reg in reg_info:
				if not reg['Email']:
					print("Email is missing from registration!")
					continue
				if reg['Id'] in processed_ids:
					print("This registration has already been processed!")
					continue
				# for field in reg:
				# 	print(field, reg[field])
				print(reg['Email'])
				replacements =  {
					'FirstName':reg['FirstName'], 
					'EventName':event['Name'].strip(),
					'SurveyLink':survey_link,
					# 'EventDate':event['Startdate'].strftime(self.time_format_string),
				}
				self.mailer.SendTemplate(reg['Email'], template, replacements, test=self.config.getboolean("script","debug"))
				self.WriteProcessedID(reg['Id'])
				print(event["Name"])
				print(survey_link)


	def WriteProcessedID(self, id):
		with open(self.processed_filename, 'a') as f:
			f.write(str(id) + '\n')


	def ReadProcessedIDs(self):
		with open(self.processed_filename, 'r') as f:
			id_list = [int(line.rstrip('\n')) for line in f]
		return id_list

	def Setup(self):
		self.WA_API = WaApiClient()        
		while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
			time.sleep(5)
		self.processed_filename = "followup_processed.txt"

	def Run(self):
		self.SendSurveys()

if __name__ == "__main__":
	s = ChildScript("Class Followup Sender")
	s.RunAndNotify()
