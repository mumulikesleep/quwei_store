import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import time,random

class Email():
    def __init__(self):
        # 邮件发送者
        self.sender_email = "2503838394@qq.com"

    def send_em(self,receiver_email,html):
        # 输入你的 QQ 邮箱授权码: nupfcaprhjuidijh
        password = 'nupfcaprhjuidijh'

        # 创建 MIMEText 对象，HTML 邮件正文
        message = MIMEMultipart("alternative")  #类型对象，alternative:包括纯文本和html
        message["Subject"] = Header("邮箱验证码") #设置主题
        message["From"] = self.sender_email  #发件人的邮箱地址
        message["To"] = receiver_email  #收件人的邮箱地址

        # 创建邮件正文的第一部分
        part1 = MIMEText(html, "plain") #plain：纯文本格式，html：html格式
        message.attach(part1)
        li = ['a','b','c','d','e','f','g','h','fg','as','po','rf','uy','pd']
        num = str(random.randint(100000,999999)) + random.choice(li) + str(random.randint(100000,999999)) + random.choice(li) + str(random.randint(100000,999999)) + random.choice(li) + str(random.randint(100000,999999)) + str(random.randint(100000,999999)) + random.choice(li)
        # 创建安全连接并发送邮件
        # 如果使用 TLS，取消下面一行的注释
        # server = smtplib.SMTP('smtp.qq.com', 587)
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(self.sender_email, password)
        try:
            server.sendmail(self.sender_email, receiver_email, message.as_string())
            server.quit()  # 不要忘记退出 SMTP 服务器
            return {'statusCode': '000000','templateSMS':{'smsMessageSid': num,'dateCreated': int(time.time())}}
        except Exception:
            server.quit()
            return {'statusCode': '','templateSMS':{'smsMessageSid': '','dateCreated': int(time.time())}}

#实例类
class CCP(object):
    '''发送短信验证码的单例类'''
    def __new__(cls, *args, **kwargs):  #创建类的新实例时被调用
        '''
        定义单例的初始化
        :return: 单例(初始化一次)
        '''
        #判断单例是否存在
        if not hasattr(cls, '_instance'):   #判断某个对象是否有一个名为 _instance 的属性，这里对象是cls
            #如果单例不存在，初始化单例
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)   #调用父类中的new方法
            cls._instance.rest = Email()
            #返回单例
        return cls._instance

    def send_teleplate_sms(self,qq_email,html):
        '''
        发送邮箱验证码单例方法
        :return:    成功：0    失败：-1
        '''
        result = self.rest.send_em(qq_email,html)
        print(result)
        if result.get('statusCode') == '000000':
            return 0
        else:
            return -1

# if __name__ == '__main__':
#     CCP().send_teleplate_sms('2503838394@qq.com', '123456')
