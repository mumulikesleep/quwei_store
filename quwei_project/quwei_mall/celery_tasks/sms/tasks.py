#定义任务
from celery_tasks.sms.yuntongxun.emailver import CCP
from celery_tasks.main import celery_app

#使用装饰器装饰异步任务，保证celery识别任务
@celery_app.task(bind=True, name='send_sms_code', retry_backoff=3)#name是给该任务起个名字
def send_sms_code(self, mobile, sms_code):
    '''
    发送邮箱验证码的异步任务
    :param mobile:  qq邮箱
    :param sms_code:  邮箱验证码
    :return:  成功：0  失败：-1
    '''
    try:
        send_ret = CCP().send_teleplate_sms(mobile, sms_code)
    except Exception as e:
        raise self.retry(exc=e, max_retries=3)
    return send_ret

