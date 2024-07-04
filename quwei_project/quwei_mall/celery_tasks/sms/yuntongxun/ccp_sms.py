# -*- coding:utf-8 -*-

# import ssl
# ssl._create_default_https_context =ssl._create_stdlib_context # 解决Mac开发环境下，网络错误的问题

from celery_tasks.sms.yuntongxun import REST

# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
_accountSid = '8aaf070862181ad5016236f3bcc811d5'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
_accountToken = '4e831592bd464663b0de944df13f16ef'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
_appId = '8aaf070868747811016883f12ef3062c'

# 说明：请求地址，生产环境配置成app.cloopen.com
_serverIP = 'sandboxapp.cloopen.com'

# 说明：请求端口 ，生产环境为8883
_serverPort = "8883"

# 说明：REST API版本号保持不变
_softVersion = '2013-12-26'

# 云通讯官方提供的发送短信代码实例
# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id
# def sendTemplateSMS(to, datas, tempId):
#     # 初始化REST SDK
#     rest = REST(_serverIP, _serverPort, _softVersion)
#     rest.setAccount(_accountSid, _accountToken)
#     rest.setAppId(_appId)
#
    # result = rest.sendTemplateSMS(to, datas, tempId)
#     print(result)
#此文件只有该单例类是自己写的
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
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)   #调用父类中的new方法来实例化对象
            cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
            cls._instance.rest.setAccount(_accountSid, _accountToken)
            cls._instance.rest.setAppId(_appId)
            #返回单例
        return cls._instance

    def send_teleplate_sms(self,to, datas, tempId):
        '''
        发送短信验证码单例方法
        :param to:  手机号
        :param datas:   内容数据
        :param tempId:  模板ID
        :return:    成功：0    失败：-1
        '''
        result = self.rest.sendTemplateSMS(to, datas, tempId)
        print(result)
        if result.get('statusCode') == '000000':
            return 0
        else:
            return -1
if __name__ == '__main__':
    # 注意： 测试的短信模板编号为1
    # sendTemplateSMS('17600992168', ['123456', 5], 1)
    CCP().send_teleplate_sms('手机号',['要发送的验证码',5], 1)