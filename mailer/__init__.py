import smtplib
import imaplib

class MailBot():
    def __init__(self, email, password, address, port):
        self.email = email
        self.password = password
        self.address = address
        self.port = port
        self.server = None
        self.display_name = None
        self.from_address = None
        self.admin_address = None

    def connect(self):
        self.server = smtplib.SMTP_SSL(self.address, self.port)
        print("Mail connect:", self.server.connect(self.address, self.port))
        self.server.ehlo()
        #self.server.starttls()
        self.server.login(self.email, self.password)
        print("Mail Server:", self.server)
        assert not self.server == None, "Could not connect to mail server"

    def disconnect(self):
        try:
            self.server.quit()
            self.server = None
        except smtplib.SMTPServerDisconnected:
            pass

    def setDisplayName(self, name):
        self.display_name = name

    def setFromAddress(self, from_addr):
        self.from_address = from_addr

    def setAdminAddress(self, addr):
        self.admin_address = addr

    def send(self, to_addrs, subj, body, test=False):
        print("Sending mail")
        if not self.display_name:
            from_field = self.email if not self.from_address else self.from_address
        else:
            from_field = '"%s" <%s>' % (self.display_name, self.email if not self.from_address else self.from_address)

        if not type(to_addrs) == list:
            to_addrs = [to_addrs]
        if test:
            to_addrs = [self.admin_address]
        # else:
        #     to_addrs.append(self.admin_address)

        msg = "\r\n".join([
            "From: " + from_field,
            "To: " + ",".join(to_addrs),
            "Subject: " + subj,
            "",
            body
        ])
        if self.server == None:
            print("Connecting")
            self.connect()
        try:
            # if self.admin_address:
            #   to_addrs.append(self.admin_address)
            self.server.sendmail(self.email, to_addrs, msg)
            return True
        except smtplib.SMTPSenderRefused:
            try:
                print("\n====SMTP Sender Refused====\n")
                self.disconnect()
                self.connect()
                self.server.sendmail(self.email, to_addrs, msg)
                return True
            except smtplib.SMTPSenderRefused as e:
                raise e
                return False


    def SendTemplate(self, to_address, template, replacements, test=False):
        template.seek(0)
        t = template.read().format(**replacements)
        subject = t.split('----')[0]
        message = t.split('----')[1]
        self.send(to_address, subject , message, test)

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
