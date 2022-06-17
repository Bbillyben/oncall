from oncall.constants import EMAIL_SUPPORT
import logging
import requests
from oncall import db
import re
from datetime import datetime
from pytz import timezone
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('smtp_messenger')


class smtp_messenger(object):
    supports = frozenset([EMAIL_SUPPORT])

    def __init__(self, config):
        print("*********** config SMTP :", config)
        self.user = config['user']
        self.password = config.get('password', False)
        self.smtp_server = config.get('smtp_server', False)
        self.smtp_port = config.get('smtp_port', False)
        self.default_mail = config.get('use_default', False)
        self.footer = config.get('footer', False) # config['use_oauth']


    def send(self, message):
        logger.info('smtp trye send message : sent message %s' % message)
        if self.password == False or self.user == False:
            logger.error('No Credentials found for smtp messenger')
        # select email adresse from db
        connection = db.connect()
        cursor = connection.cursor()
        try:
            cursor.execute('''SELECT `destination` FROM `user_contact`
                              WHERE `user_id` = (SELECT `id` FROM `user` WHERE `name` = %s)
                              AND `mode_id` = (SELECT `id` FROM `contact_mode` WHERE `name` = 'email')''',
                           message['user'])
            if cursor.rowcount == 0:
                raise ValueError('Email contact not found for %s' % message['user'])
            recipient = cursor.fetchone()[0]
        finally:
            cursor.close()
            connection.close()

        # recipient selection based on smtp default for test uses        
        logger.info("~~~~~~ recipient should be :%s", recipient)
        if self.default_mail:
            recipient = self.default_mail
        logger.info("~~~~~~ recipient finally is :%s", recipient)

        subject = message.get("subject")
        body = message.get("body")
        # cleaning of timestamp in message
        pattern = re.compile(r'([0-9]{10})')
        for timestamp in re.findall(pattern, body):
            logger.info("time stamp found : %s", timestamp)
            trD = datetime.fromtimestamp(int(timestamp),timezone('Europe/Paris')).strftime('%Y-%m-%d %H:%M')
            body = body.replace(timestamp, trD)
            print(" --- replacement of ", timestamp, "by : ", trD)
        if self.footer:
            body = body + self.footer
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.user
        message["To"] = self.password

        part = MIMEText(body, "html")
        message.attach(part)
        context = ssl.create_default_context()
        # message sending
        try:
            server = smtplib.SMTP(self.smtp_server,self.smtp_port)
            server.ehlo() # Can be omitted
            server.starttls(context=context) # Secure the connection
            server.ehlo() # Can be omitted
            server.login(self.user, self.password)
            server.sendmail(self.user, recipient, message.as_string())
        except:
            logger.error("An issue occured while sending message to gmail messenger for user %s",message['user'])
        finally:
            server.quit()

