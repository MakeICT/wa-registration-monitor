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
		start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0)
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
				reg_info.append(flattened_reg_fields)
			
			for reg in reg_info:
				replacements =  {
					'FirstName':reg['FirstName'], 
					'EventName':event['Name'].strip(),
					'SurveyLink':survey_link,
					# 'EventDate':event['Startdate'].strftime(self.time_format_string),
				}
				self.mailer.SendTemplate('christian@makeict.org', template, replacements)
				print(event["Name"])
				print(survey_link)

	def Setup(self):
		self.WA_API = WaApiClient()        
		while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
			time.sleep(5)

	def Run(self):
		self.SendSurveys()

s = ChildScript("Class Followup Sender")
s.RunAndNotify()
