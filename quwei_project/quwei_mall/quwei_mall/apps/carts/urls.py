from django.urls import re_path
from . import views

urlpatterns = [
    #购物车管理
    re_path(r'^carts/$', views.CartsView.as_view(), name='info'),
    #全选购物车
    re_path(r'^carts/selection/$', views.CartsSelectAllView.as_view()),
    #简单展示购物车
    re_path(r'^carts/simple/$', views.CartsSimpleView.as_view()),
]