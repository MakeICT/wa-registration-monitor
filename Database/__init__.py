#!/usr/bin/python

import MySQLdb

class Database():
	def __init__(self):
		self.Connect()

		# Drop table if it already exist using execute() method.
		#self.NewCursor().execute("DROP TABLE IF EXISTS UNPAID_REGISTRATIONS")

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
		try:
			self.NewCursor().execute(sql)
		except MySQLdb.OperationalError as err:
			if '1050' in str(err):
				print("database already exists")
				pass
			else:
				raise

		self.Disconnect()

	def Connect(self):
		self.db = MySQLdb.connect('localhost', 'regimon', 'regimon', 'regimon_db');

	def NewCursor(self):
		self.Connect()
		return self.db.cursor()

	def Disconnect(self):
		self.db.commit()
		self.db.close()


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

# testdb = Database()

# testdb.AddEntry('Christian', 'Kindel', 'user@mail.com', 12342342, 23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetFirstNagSent(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetLastNagSent(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))
# testdb.SetRegistrationDeleted(23549458)
# print (testdb.GetEntryByRegistrationID(23549458))