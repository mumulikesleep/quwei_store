from django.urls import re_path
from . import views


urlpatterns = [
    #提供QQ登录页面
    re_path(r'^qq/login/$', views.QQAuthURLView.as_view()),
    #处理QQ登录回调
    re_path(r'^oauth_callback/$', views.QQAuthUserView.as_view()),
]