import logging
import mailer
import configparser
from datetime import datetime
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import *

from mailer import MailBot

#import scripts to run
import test
import WaiverCheck
import SendClassFollowup
import RegistrationMonitor

print("Scripts imported")

waiver_check = WaiverCheck.ChildScript('Waiver Check')
class_followup = SendClassFollowup.ChildScript('Class Followup')
registration_monitor = RegistrationMonitor.ChildScript('Registration Monitor')

test = test.ChildScript('test job')

start_time = datetime.now()
config = configparser.SafeConfigParser()
config.read('config.ini')
os.chdir(config.get('files','installDirectory'))

mailer = MailBot(config.get('email','username'), config.get('email','password'))
mailer.setDisplayName(config.get('email', 'displayName'))
mailer.setAdminAddress(config.get('email', 'adminAddress'))

message = "Dispatcher started"
mailer.send([config.get('email', 'adminAddress')], "Dispatcher script has restarted!", message)

def result_listener(event):
    if event.exception:
        #if a job crashes, send an email
        print('The job crashed :(')
        print(event)
        # print(event.exception)
        # print(event.traceback)
        message = "The following exception was thrown:\r\n\r\n" + str(event.exception) + "\r\n\r\n" + event.traceback
        mailer.send([config.get('email', 'adminAddress')], "A script has crashed!", message)
    else:
        #if a job doesn't crash, do nothing?
        print('The job worked :)')
        # print(event.retval)

#set up scheduler
scheduler = BlockingScheduler()
scheduler.add_listener(result_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

#add jobs to scheduler
# print('adding test job')
# test_job = scheduler.add_job(test.Run, 'interval', seconds=5, id='waiver_check_job')
# print('finished adding test job')
job1=scheduler.add_job(waiver_check.Run, 'interval', minutes=60)
job2=scheduler.add_job(registration_monitor.Run, 'interval', minutes=10)
job3=scheduler.add_job(class_followup.Run, 'cron', hour=12)
# print(job1)
# print(job2)

#start scheduler
print('starting scheduler')
scheduler.start()