#!/usr/bin/python3

import time

from wildapricot_api import WaApiClient
from pydiscourse import DiscourseClient
from pydiscourse.exceptions import DiscourseClientError

from automationscript import Script


class ChildScript(Script):
    def Setup(self):
        self.WA_API = WaApiClient()
        while(not self.WA_API.ConnectAPI(self.config.get('api', 'key'))):
            time.sleep(5)
        self.processed_filename = "followup_processed.txt"
        self.discourse_api = DiscourseClient(
            self.config.get('discourse_api', 'site'),
            api_username=self.config.get('discourse_api', 'username'),
            api_key=self.config.get('discourse_api', 'key'))

        self.member_levels = ['Monthly',
                              '6 months',
                              '12 months',
                              "Scholarship (monthly)",
                              "Scholarship (6 months)",
                              "Scholarship (12 months)"]
        self.group_name = 'MakeICT_Members'
        self.member_group_id = \
            self.discourse_api.group(self.group_name)['group']['id']

    def SyncUser(self, d_user, wa_contacts):
        # print(self.discourse_api.user_emails(d_user['user']['username']))
        print(d_user['user']['username'], ':',
              d_user['user']['emails'], ':',
              [c['Email'] for c in wa_contacts])
        is_member = False
        is_active = False

        # assert wa_contacts['Email'] in d_user['user']['emails']
        for contact in wa_contacts:
            try:
                is_member = contact['MembershipLevel']['Name'] in self.member_levels
            except KeyError:
                print("No WA membership level found")

            try:
                is_active = contact['Status'] == 'Active' and contact['MembershipEnabled']
            except KeyError:
                print("WA contact is not active")

            # If an active WildApricot account is found, stop looking and sync
            if is_member and is_active:
                break

        if is_member and is_active:
            print("User is an active member, adding user to group")

            try:
                if d_user['user']['primary_group_name'] == self.group_name:
                    print("User is already in group")
                    return
            except KeyError:
                print("User has no primary group")

            try:
                self.discourse_api.add_group_member(
                    self.member_group_id, d_user['user']['username'])
            except DiscourseClientError:
                print("Failed to add user to group")

        else:
            print("user is not an active member, removing user from group")
            self.discourse_api.delete_group_member(
                self.member_group_id, d_user['user']['id'])

    def SyncUsers(self, disc_users, wa_users):
        for u in disc_users:
            # if u['user']['username'] != '':
            #     continue
            emails = self.discourse_api.user_emails(u['user']['username'])
            email_list = [emails['email']]
            email_list += emails['secondary_emails']
            u['user']['emails'] = email_list

            found_contacts = []
            for contact in wa_users:
                if contact['Email'] in u['user']['emails']:
                    print("Found WA user for %s" % contact['Email'])
                    found_contacts.append(contact)

            self.SyncUser(u, found_contacts)

            time.sleep(2)

    def SyncAllUsers(self):
        discourse_users = self.discourse_api.user_list()
        wa_contacts = self.WA_API.GetAllContacts()

        self.SyncUsers(discourse_users, wa_contacts)

    def SyncNewUsers(self):
        discourse_users = self.discourse_api.list_users("new")
        wa_contacts = self.WA_API.GetAllContacts()

        self.SyncUsers(discourse_users, wa_contacts)

    def Run(self):
        self.SyncAllUsers()


if __name__ == "__main__":
    s = ChildScript("Sync Discourse Groups")
    s.RunAndNotify()
