#!/usr/bin/python

import MySQLdb
import time
import datetime

class Database():
	def __init__(self):
		self.Connect()

		# Drop table if it already exist using execute() method.
		# self.NewCursor().execute("DROP TABLE IF EXISTS UNPAID_REGISTRATIONS")
		# self.NewCursor().execute("DROP TABLE IF EXISTS EVENT_CHECKINS")
		# self.NewCursor().execute("DROP TABLE IF EXISTS ACTION_LOG")

		init_funcs = self.CreateUnpaidRegistrationsDB, self.CreateEventCheckinsDB, self.CreateActionLogDB

		try:
			for f in init_funcs:
				try:
					f()
				except MySQLdb.OperationalError as err:
					if '1050' in str(err):
						print("database already exists")
				# else:
				# 	raise

		finally:
			self.Disconnect()

	def Connect(self):
		self.db = MySQLdb.connect('localhost', 'regimon', 'regimon', 'regimon_db');

	def NewCursor(self):
		self.Connect()
		return self.db.cursor()

	def Disconnect(self):
		self.db.commit()
		self.db.close()

	def CreateUnpaidRegistrationsDB(self):		
		# Create table as per requirement
		sql = """CREATE TABLE UNPAID_REGISTRATIONS (
				 FIRST_NAME CHAR(20),
				 LAST_NAME CHAR(20),
				 EMAIL VARCHAR(255),
		         USER_ID INT,
		         REGISTRATION_ID INT,
		         INITIAL_NAG_SENT BOOLEAN,
		         FINAL_NAG_SENT BOOLEAN,
		         REGISTRATION_DELETED BOOLEAN
		         )"""
		self.NewCursor().execute(sql)

	def AddEntry(self, first_name, last_name, email, user_id, registration_id):
		self.Connect()
		sql = """INSERT INTO UNPAID_REGISTRATIONS(FIRST_NAME,
	         LAST_NAME, EMAIL, USER_ID, REGISTRATION_ID)
	         VALUES ('%s', '%s', '%s', '%d', '%d')""" % (first_name, last_name, email, user_id, registration_id)
		self.NewCursor().execute(sql)
		self.Disconnect()


	def GetEntryByRegistrationID(self, reg_id):
		self.Connect()
		sql = "SELECT * FROM UNPAID_REGISTRATIONS WHERE REGISTRATION_ID = '%d'" % reg_id
		cursor = self.NewCursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		self.Disconnect()
		return results

	def GetAll(self):
		self.Connect()
		sql = "SELECT * FROM UNPAID_REGISTRATIONS"
		cursor = self.NewCursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		self.Disconnect()
		return results

	def UpdateEntryByRegistrationID(self, reg_id, field, value):
		sql = "UPDATE UNPAID_REGISTRATIONS SET %s = %s WHERE REGISTRATION_ID = %r" % (field, value, reg_id)
		self.NewCursor().execute(sql)
		self.Disconnect()

	def SetFirstNagSent(self, reg_id, state=True):
		self.UpdateEntryByRegistrationID(reg_id, 'INITIAL_NAG_SENT', state)

	def SetLastNagSent(self, reg_id, state=True):
		self.UpdateEntryByRegistrationID(reg_id, 'FINAL_NAG_SENT', state)

	def SetRegistrationDeleted(self, reg_id, state=True):
		self.UpdateEntryByRegistrationID(reg_id, 'REGISTRATION_DELETED', state)

	# Event Check-in database
	def CreateEventCheckinsDB(self):
		sql = """CREATE TABLE EVENT_CHECKINS(
				 EVENT_ID INT,
				 VOLUNTEER_EMAIL VARCHAR(255),
				 INITIAL_NAG_SENT BOOLEAN,
				 MIDDLE_NAG_SENT BOOLEAN,
		         FINAL_NAG_SENT BOOLEAN
		         )"""
		self.NewCursor().execute(sql)

	def AddEventToDB(self, event_id):
		self.Connect()
		sql = """INSERT INTO EVENT_CHECKINS(EVENT_ID)
	         VALUES ('%d')""" % (event_id)
		self.NewCursor().execute(sql)
		self.Disconnect()

	def UpdateEventEntryByEventID(self, event_id, field, value):
		sql = "UPDATE EVENT_CHECKINS SET %s = %s WHERE EVENT_ID = %r" % (field, value, event_id)
		self.NewCursor().execute(sql)
		self.Disconnect()

	def SetFirstEventNagSent(self, event_id, state=True):
		self.UpdateEventEntryByEventID(event_id, 'INITIAL_NAG_SENT', state)

	def SetSecondEventNagSent(self, event_id, state=True):
		self.UpdateEventEntryByEventID(event_id, 'MIDDLE_NAG_SENT', state)

	def SetThirdEventNagSent(self, event_id, state=True):
		self.UpdateEventEntryByEventID(event_id, 'FINAL_NAG_SENT', state)

	def GetEntryByEventID(self, event_id):
		self.Connect()
		sql = "SELECT * FROM EVENT_CHECKINS WHERE EVENT_ID = '%d'" % event_id
		cursor = self.NewCursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		self.Disconnect()
		return results

	def GetOneEventField(self, event_id, field):
		self.Connect()
		sql = "SELECT %s FROM EVENT_CHECKINS WHERE EVENT_ID = '%d'" % (field, event_id)
		cursor = self.NewCursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		self.Disconnect()
		return results[0][0]

	def GetFirstEventNagSent(self, event_id):
		event = self.GetOneEventField(event_id, 'INITIAL_NAG_SENT')
		return event
	
	def GetSecondEventNagSent(self, event_id):
		event = self.GetOneEventField(event_id, 'MIDDLE_NAG_SENT')
		return event
	
	def GetThirdEventNagSent(self, event_id):
		event = self.GetOneEventField(event_id, 'FINAL_NAG_SENT')
		return event


	# Event Reminders Table
	def CreateEventRemindersDB(self):
		sql = """CREATE TABLE EVENT_REMINDERS(
				 EVENT_ID INT,
				 VOLUNTEER_EMAIL VARCHAR(255),
				 LAST_EMAIL_SENT TIMESTAMP
		         )"""
		self.NewCursor().execute(sql) 
	
	# Action Log Table
	def CreateActionLogDB(self):
		sql = """CREATE TABLE ACTION_LOG(
				 TIME_STAMP TIMESTAMP,
				 EVENT_NAME VARCHAR(255),
				 REGISTRANT_NAME VARCHAR(255),
				 REGISTRANT_EMAIL VARCHAR(255),
				 ACTION VARCHAR(255)
		         )"""
		self.NewCursor().execute(sql)

	def AddLogEntry(self, event_name, registrant_name, registrant_email, action):
		self.Connect()

		ts = time.time()
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

		sql = """INSERT INTO ACTION_LOG(TIME_STAMP,
	         EVENT_NAME, REGISTRANT_NAME, REGISTRANT_EMAIL, ACTION)
	         VALUES ('%s', '%s', '%s', '%s', '%s')""" % (timestamp, event_name, registrant_name, registrant_email, action)
		
		self.NewCursor().execute(sql)
		self.Disconnect()

	def GetLog(self):
		self.Connect()
		sql = "SELECT * FROM ACTION_LOG"
		cursor = self.NewCursor()
		cursor.execute(sql)
		results = cursor.fetchall()
		self.Disconnect()
		return results



# testdb = Database()

# testdb.AddEntry('Christian', 'Kindel', 'user@mail.com', 12342342, 23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetFirstNagSent(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetLastNagSent(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetRegistrationDeleted(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))