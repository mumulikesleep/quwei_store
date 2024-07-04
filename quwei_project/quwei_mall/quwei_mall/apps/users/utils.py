#自定义用户认证的后端：实现多账号(用户名或qq邮箱)的登录
from django.contrib.auth.backends import ModelBackend
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from itsdangerous import BadData

from users.models import Users
from . import constants


def check_verify_email_token(token):
    '''
    反序列化token，获取到user
    :param user:  序列化后的用户信息
    :return:    user
    '''
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = s.loads(token)
    except BadData:
        return None
    else:
        #从data中取出user_id和email
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = Users.objects.get(id=user_id, email=email)
        except Users.DoesNotExist:
            return None
        else:
            return user

def generate_verify_email_url(user):
    '''
    生成商城邮箱激活链接
    :param user: 当前登录用户
    :return: http://www.quwei.site:8000/emails/verification/?token=登录用户的唯一标识
    '''
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'user_id': user.id, 'email': user.email}
    token = s.dumps(data)
    return settings.EMAIL_VERIFY_URL + '?token=' + token.decode()

def get_user_by_account(accounnt):
    '''
    通过账号获取用户
    :param accounnt: 用户名或qq邮箱
    :return: user
    '''
    try:
        if re.match(r'^[1-9][0-9]{4,}@qq.com$', accounnt):
            user = Users.objects.get(mobile=accounnt)
        else:
            user = Users.objects.get(username=accounnt)
    except Users.DoesNotExist:
        return None
    else:
        return user

class UsernameMobileBackend(ModelBackend):
    #自定义用户认证后端
    def authenticate(self, request, username=None, password=None, **kwargs):
        '''
        重写用户认证的方法
        :param username: 用户名或qq邮箱
        :param password: 密码明文
        :param kwargs:  额外参数
        :return:   user
        '''
        #查询用户
        user = get_user_by_account(username)
        #如果可以查询到用户，还需要校验密码是否正确
        if user and user.check_password(password):
            # 返回user
            return user
        else:
            return None

