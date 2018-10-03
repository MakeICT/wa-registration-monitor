#!/usr/bin/python3

from automationscript import Script

from datetime import datetime
from datetime import timedelta

from wildapricot_api import WaApiClient

import urllib, time
from pydiscourse import DiscourseClient
import pydiscourse

class ChildScript(Script):
    def Setup(self):
        self.WA_API = WaApiClient()        
        while(not self.WA_API.ConnectAPI(self.config.get('api','key'))):
            time.sleep(5)
        self.processed_filename = "followup_processed.txt"
        self.discourse_api = DiscourseClient(
            self.config.get('discourse_api','site'),
            api_username=self.config.get('discourse_api','username'),
            api_key=self.config.get('discourse_api','key'))


    def SyncNewUsers(self):
        member_levels = ['Monthly', '6 months', '12 months', "Scholarship (monthly)", "Scholarship (6 months)", "Scholarship (12 months)"]
        member_group_id = self.discourse_api.group('MakeICT_Members')['group']['id']

        discourse_users =  self.discourse_api.list_users("new")
        wa_contacts = self.WA_API.GetAllContacts()
        print("%d users" % len(discourse_users))
        # self.discourse_api.add_group_member(member_group_id, users_to_add)
        for u in discourse_users:
            # print(self.discourse_api.user_emails(u['user']['username']))
            u['email'] = self.discourse_api.user_emails(u['username'])['email']
            print(u['username'],':', u['email'] )
            wa_contact_info = None
            for contact in wa_contacts:
                if contact['Email'] == u['email']:
                    print("Found WA user for %s" % u['email'])
                    try:
                        if contact['MembershipLevel']['Name'] in member_levels:
                            if contact['Status'] == 'Active':
                                try:
                                    print("adding user to group")
                                    self.discourse_api.add_group_member(member_group_id, u['username'])
                                except pydiscourse.exceptions.DiscourseClientError:
                                    print("failed to add user to group")
                    except KeyError:
                        print("No membership level found")
            # if u['user']['email'] in [contact['Email'] for contact in wa_contacts]:
            #     if 
            # else:
            #     print("Did not find WA user for %s" % u['user']['email'])
            time.sleep(2)

    def SyncAllUsers(self):
        member_levels = ['Monthly', '6 months', '12 months', "Scholarship (monthly)", "Scholarship (6 months)", "Scholarship (12 months)"]
        member_group_id = self.discourse_api.group('MakeICT_Members')['group']['id']

        discourse_users =  self.discourse_api.user_list()
        # for u in discourse_users:
        #     print(u)
        # for thing in dir(client):
        #     print(thing)
        wa_contacts = self.WA_API.GetAllContacts()
        for contact in wa_contacts:
            print(contact['Email'])
        print("%d users" % len(discourse_users))

        for u in discourse_users:
            # print(self.discourse_api.user_emails(u['user']['username']))
            u['user']['email'] = self.discourse_api.user_emails(u['user']['username'])['email']
            print(u['user']['username'],':', u['user']['email'] )
            active_member = False
            for contact in wa_contacts:
                if contact['Email'] == u['user']['email']:
                    print("Found WA user for %s" % u['user']['email'])
                    try:
                        if contact['MembershipLevel']['Name'] in member_levels:
                            if contact['Status'] == 'Active':
                                active_member=True
                                print("member is active")
                            else:
                                print("member is not active")

                    except KeyError:
                        print("No membership level found")

            if active_member:
                try:
                    print("adding user to group")
                    self.discourse_api.add_group_member(member_group_id, u['user']['username'])
                except pydiscourse.exceptions.DiscourseClientError:
                    print("failed to add user to group")
            else:
                print("removing user from group")
                self.discourse_api.delete_group_member(member_group_id, u['user']['id'])

            # if u['user']['email'] in [contact['Email'] for contact in wa_contacts]:
            #     if 
            # else:
            #     print("Did not find WA user for %s" % u['user']['email'])
            time.sleep(2)

    def Run(self):
        self.SyncAllUsers()
        # self.SyncNewUsers()
        # print("adding all identified users to member group")
        # cutoff_date=self.WA_API.DateTimeToWADate(datetime.now() - timedelta(days=180))
        # inactive_contacts = self.WA_API.GetFilteredContacts("'Profile+last+updated'+le+%s+and+'Last+login+date'+le+%s+and+'Membership+level+ID'+eq+813239" % (cutoff_date,cutoff_date))
        # for contact in inactive_contacts:
        #     print(contact,'\n')
        # ids = [contact['Id'] for contact in inactive_contacts]
        # print(ids)
        # for id in ids:
        #     try:
        #         self.WA_API.UpdateContactField(int(id), "Archived", False)
        #     except Exception as e:
        #         print("issue with user id:", id )
        #         print(e)
        #         # print(sys.exc_info()[0])

if __name__ == "__main__":
    s = ChildScript("Sync Discourse Groups")
    s.RunAndNotify()
