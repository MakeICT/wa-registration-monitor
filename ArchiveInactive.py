#!/usr/bin/python3

from automationscript import Script

from datetime import datetime
from datetime import timedelta

from wildapricot_api import WaApiClient

import urllib, time

class ChildScript(Script):
    def Setup(self):
        self.WA_API = WaApiClient()        
        while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
            time.sleep(5)
        self.processed_filename = "followup_processed.txt"

    def Run(self):
        cutoff_date=self.WA_API.DateTimeToWADate(datetime.now() - timedelta(days=180))
        inactive_contacts = self.WA_API.GetFilteredContacts("'Profile+last+updated'+le+%s+and+'Last+login+date'+le+%s+and+'Membership+level+ID'+eq+813239" % (cutoff_date,cutoff_date))
        for contact in inactive_contacts:
            print(contact,'\n')
        ids = [contact['Id'] for contact in inactive_contacts]
        print(ids)
        for id in ids:
            try:
                self.WA_API.UpdateContactField(int(id), "Archived", False)
            except Exception as e:
                print("issue with user id:", id )
                print(e)
                # print(sys.exc_info()[0])

s = ChildScript("Archive Inactive WA Contacts")
s.RunAndNotify()
