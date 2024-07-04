"""
Django settings for quwei_mall project.

Generated by 'django-admin startproject' using Django 4.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
from pathlib import Path
import os,sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0,os.path.join(BASE_DIR,'apps'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-09)7_bv$2wc1o)!xw4dlv8hcqyhx8zderw^x)73x7jo-+%2$s3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['www.quwei.site']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'haystack', # 全文检索
    # 'django_crontab', # 定时任务
    'users',  #用户模块
    'contents', #首页广告模块
    'verifications',  #验证码模块，可以不用注册，因为不需要迁移文件
    'oauth', #第三方登录
    'areas', #省市区三级联动
    'goods', #商品模块
    'carts', #购物车
    'orders',#订单
    'payment'#支付
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'quwei_mall.urls'

TEMPLATES = [
{
        'BACKEND': 'django.template.backends.jinja2.Jinja2',    #配置jinja2模板引擎
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            #补充jinja2环境模板引擎
            'environment': 'quwei_mall.utils.jinja2_env.jinja2_environment'
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'quwei_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': { #写（主机，但数据库镜像无法拉取8版本和配置，所以实质还是使用一个数据库进行读和写）
        'ENGINE': 'django.db.backends.mysql',#数据库引擎
        'NAME': 'quwei',
        'HOST': '192.168.42.134',
        'PORT': '3306',
        'USER': 'mumu',
        'PASSWORD': '123456'
    },
    # 'slave': { # 读（从机，数据库的镜像没拉取和配置好）
    #     'ENGINE': 'django.db.backends.mysql',
    #     'HOST': '192.168.42.134',
    #     'PORT': 8306,
    #     'USER': 'root',
    #     'PASSWORD': 'mysql',
    #     'NAME': 'quwei''
    # }
}

#配置Redis数据库
CACHES = {
    'default': {	#默认
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://192.168.42.134:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
    'session': {	#session
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://192.168.42.134:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
    'verify_code': {  #验证码
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://192.168.42.134:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
    'history': {  #用户商品浏览记录
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://192.168.42.134:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
    'carts': {  #购物车
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://192.168.42.134:6379/4',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai' #django时间工具会读取该地方的时区

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
#配置静态文件
STATIC_URL = '/static/'
#配置静态文件加载路径
STATICFILES_DIRS = ['static']

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#配置工程日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(BASE_DIR), 'logs/quwei.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

#指定自定义的用户模型类：值的语法：==> '子应用.用户模型类'
AUTH_USER_MODEL = 'users.Users'

#指定自定义用户认证后端
AUTHENTICATION_BACKENDS = ["users.utils.UsernameMobileBackend"]

#指定用户未登录时用户重定向的地址
LOGIN_URL = '/login/'

#QQ登录的配置参数(该参数已失效，需要在QQ关联申请)
QQ_CLIENT_ID = '101518219'
QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

#邮件参数
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' # 指定邮件后端
EMAIL_HOST = 'smtp.163.com' # 发邮件主机
EMAIL_PORT = 25 # 发邮件端口
EMAIL_HOST_USER = 'wang_4563@163.com' # 授权的邮箱
EMAIL_HOST_PASSWORD = 'CQKWQYTCGZCBMIOP' # 邮箱授权时获得的密码，非注册登录密码
EMAIL_FROM = '电子商城<wang_4563@163.com>' # 发件人抬头

# 邮箱验证链接
EMAIL_VERIFY_URL = 'http://www.quwei.site:8000/emails/verification/'

# 指定自定义的Django文件存储类
DEFAULT_FILE_STORAGE = 'quwei_mall.utils.fastdfs.fdfs_storage.FastDFSStorage'

# FastDFS相关参数
FDFS_BASE_URL = 'http://192.168.42.134:8888/'

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://192.168.42.134:9200/', # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'quwei_mall', # Elasticsearch建立的索引库的名称
    },
}
# 当数据库添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

#Haystack通过HAYSTACK_SEARCH_RESULTS_PER_PAGE可以控制每页显示数量
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 5

#支付宝
ALIPAY_APPID = '9021000138654686'
ALIPAY_DEBUG = True
ALIPAY_URL = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = 'http://www.quwei.site:8000/payment/status/'

#定时器
CRONJOBS = [
    # 每1分钟生成一次首页静态文件；执行的生成文件的自定义函数；日志的写入路径
    ('*/1 * * * *', 'contents.crons.generate_static_index_html', '>> ' + os.path.join(os.path.dirname(BASE_DIR), 'logs/crontab.log'))
]
#指定中文的编码格式
CRONTAB_COMMAND_PREFIX = 'LANG_ALL=zh_cn.UTF-8'

#Mysql读写分离路由
# DATABASE_ROUTERS = ['mquwei_mall.utils.db_router.MasterSlaveDBRouter']