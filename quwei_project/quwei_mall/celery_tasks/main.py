#Celery的入口
from celery import Celery
# 为celery使用django配置文件进行设置
import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'quwei_mall.settings.dev'
#创建Celery实例
celery_app = Celery('quwei')#参数可以不传，只为标识该实例

#加载配置
celery_app.config_from_object('celery_tasks.config')

#注册任务
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])