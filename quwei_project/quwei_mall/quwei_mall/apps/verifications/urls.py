from django.urls import re_path
from . import views

urlpatterns = [
    #图形验证码
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$',views.ImageCodeView.as_view()),
    #邮箱验证码
    re_path(r'^sms_codes/(?P<mobile>[1-9][0-9]{4,}@qq.com)/$',views.SMSCodeView.as_view()),
]