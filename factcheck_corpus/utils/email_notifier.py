import sys
import os
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

import smtplib, ssl
from email.mime.text import MIMEText
from utils.email_credential import *

smtpServer = "smtp.gmail.com"
port = 587 
sender = "youremail"
receivers = ['youremail']
password = credential_password 
#email and password can also be user input fields
context = ssl.create_default_context()

with open('log.txt') as f:
    lines = f.readlines()
    n = 7
    body = ''
    while n:
        l = lines.pop()
        body += l+'<br>'
        if l=='--------------------------------------------------\n': n -= 1

msg = MIMEText(body, 'html')
msg['Subject'] = 'Factcheck scrappers daily report'
msg['From'] = sender
msg['To'] = ','.join(receivers)
try:
    server = smtplib.SMTP_SSL(host = 'smtp.gmail.com', port = 465)
    server.login(user = sender, password = credential_password)
    server.sendmail(sender, receivers, msg.as_string())
    server.quit()
except Exception as e:
    print("the email could not be sent.")