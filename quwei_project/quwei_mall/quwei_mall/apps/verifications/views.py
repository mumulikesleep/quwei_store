from django.views import View
from django_redis import get_redis_connection
from django import http
import random,logging

from verifications.libs.captcha.captcha import captcha
from . import constants
from quwei_mall.utils.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms_code
# from celery_tasks.sms.yuntongxun.emailver import CCP


# Create your views here.

#创建日志输出器
logger = logging.getLogger('django')

class SMSCodeView(View):
    '''邮箱验证码'''
    def get(self,request,mobile):
        '''
        :param mobile: 手机号
        :return:    JSON
        '''
        #接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        if not all([image_code_client, uuid]):
            return http.HttpResponseForbidden('缺少必传参数')
        #创建连接redis2号库的对象
        redis_conn = get_redis_connection('verify_code')
        #判断用户是否频繁发送邮箱验证码
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})
        #提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码已失效'})
        #删除图形验证码
        redis_conn.delete('img_%s' % uuid)
        #对比图形验证码
        image_code_server = image_code_server.decode()  #将bytes转字符串再比较
        if image_code_client.lower() != image_code_server.lower():#转换为小写再比较
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入的图形验证码有误'})
        #生成6位邮箱验证码
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code)

        # #保存邮箱验证码
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # #保存发送邮箱验证码的标记，值(1)可以随便写，只作为标记
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        #创建redis管道
        pl = redis_conn.pipeline()
        #将命令增添到队列中
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        #执行
        pl.execute()
        #发送邮箱验证码
        #CCP().send_teleplate_sms(mobile, sms_code)
        send_sms_code.apply_async(args=(mobile, sms_code))
        # send_sms_code.delay(mobile, sms_code)   老版本固定写法，参数交给delay放在队列中再由delay交给send_sms_code
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送邮箱成功'})

class ImageCodeView(View):
    '''图片验证码'''
    def get(self,request,uuid):
        '''
        :param uuid: uuid 用户通用唯一识别码，用于识别该图形验证码是属于哪个用户的
        :return:  image/jpg
        '''
        #实现主体业务逻辑：生成、保存、响应图形验证码
        #生成图形验证码,captcha.generate_captcha()是扩展包中.py文件的最后一行
        text, image = captcha.generate_captcha()
        #连接redis,verify_code是配置文件中配置redis2号库的所对应的键
        redis_conn = get_redis_connection('verify_code')
        #setex是redis操作字符型数据的增添方法(可以参考redis笔记)
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        #响应图形验证码    content_type是响应类型
        return http.HttpResponse(image,content_type='image/jpg')
