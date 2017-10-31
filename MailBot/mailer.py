import smtplib
import imaplib

class MailBot():
	def __init__(self, email, password):
		self.email = email
		self.password = password
		self.server = None
		self.display_name = None
		self.admin_address = None

	def connect(self):
		self.server = smtplib.SMTP_SSL()
		self.server.connect('smtp.gmail.com', 465)
		self.server.ehlo()
		#self.server.starttls()
		self.server.login(self.email, self.password)

	def disconnect(self):
		try:
			self.server.quit()
			self.server = None
		except smtplib.SMTPServerDisconnected:
			pass

	def setDisplayName(self, name):
		self.display_name = name

	def setAdminAddress(self, addr):
		self.admin_address = addr

	def send(self, to_addrs, subj, body):
		if not self.display_name:
			from_field = self.email
		else:
			from_field = '"%s" <%s>' % (self.display_name, self.email)
		msg = "\r\n".join([
			"From: " + from_field,
			"To: " + ",".join(to_addrs),
			"Subject: " + subj,
			"",
			body
		])
		if self.server == None:
			self.connect()
		try:
			# if self.admin_address:
			# 	to_addrs.append(self.admin_address)
			self.server.sendmail(self.email, to_addrs, msg)
		except smtplib.SMTPSenderRefused:
			#print("\n===server timeout====\n")
			self.disconnect()
			self.connect()
			self.server.sendmail(self.email, to_addrs, msg)

	def check(self):
		mail = imaplib.IMAP4_SSL('imap.gmail.com')
		mail.login(self.email, self.password)
		mail.list()
		mail.select('inbox')
		typ, data = mail.search(None, '(SUBJECT "test")')
		for num in data[0].split():
		   typ, data = mail.fetch(num, '(RFC822)')
		   print('Message %s\n%s\n' % (num, data[0][1]))
		mail.close()

		#need to add some stuff in here

		mail.logout()