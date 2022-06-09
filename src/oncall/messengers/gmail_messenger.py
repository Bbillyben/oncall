from oncall.constants import EMAIL_SUPPORT
import logging
import yagmail
import requests
from oncall import db
import re
from datetime import datetime
from pytz import timezone

logger = logging.getLogger('gmail_messenger')


class gmail_messenger(object):
    supports = frozenset([EMAIL_SUPPORT])

    def __init__(self, config):
        print("*********** config :", config)
        self.user = config['user']
        self.password = config.get('password', False) # config['password']
        self.use_oauth = config.get('use_oauth', False) # config['use_oauth']
        self.default_mail = config.get('use_default', False) # config['use_oauth']
        self.footer = config.get('footer', False) # config['use_oauth']


    def send(self, message):
        logger.info('gmail trye send message : sent message %s' % message)
        if self.use_oauth:
            yag = yag = yagmail.SMTP("rhu.precinash@gmail.com", oauth2_file="/home/ben/oncall/configs/oauth2_creds.json")
        elif self.password:
            yag = yag = yagmail.SMTP(self.user,self.password)
        else:
            logger.error('No Credentials found for gmail messenger')
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
        
        logger.info("~~~~~~ recipient should be :%s", recipient)
        if self.default_mail:
            recipient = self.default_mail
        logger.info("~~~~~~ recipient finally is :%s", recipient)
        subject = message.get("subject")
        body = message.get("body")
        pattern = re.compile(r'([0-9]{10})')
        for timestamp in re.findall(pattern, body):
            logger.info("time stamp found : %s", timestamp)
            trD = datetime.fromtimestamp(int(timestamp),timezone('Europe/Paris')).strftime('%Y-%m-%d %H:%M')
            body = body.replace(timestamp, trD)
            print(" --- replacement of ", timestamp, "by : ", trD)
        if self.footer:
            body = body + self.footer
        
        try:
            yag.send(to=recipient, subject=subject, contents=body)
        except:
            logger.error("An issue occured while sending message to gmail messenger for user %s",message['user'])


