import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header

def send_email(to_email: str, body: str, subject: str) -> None:
    """
    发送一封固定主题的测试邮件到指定的QQ邮箱。

    参数:
        to_email (str): 收件人的QQ邮箱地址。
        body (str): 邮件的内容。
        subject (str): 邮件的主题。

    返回:
        None
    """
    sender_email = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    smtp_server = ''
    smtp_port =  ''
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender_email
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
        print('邮件发送成功')
    except smtplib.SMTPException as e:
        print('邮件发送失败:', e)
