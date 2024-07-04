from django.urls import re_path

from . import views


urlpatterns = [
    #结算订单
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),
    #提交订单
    re_path(r'^orders/commit/$', views.OrderCommitView.as_view()),
    # 提交订单成功
    re_path(r'^orders/success/$', views.OrderSuccessView.as_view()),
    #我的订单
    re_path(r'^orders/info/(?P<page_num>\d+)/$', views.UserOrderInfoView.as_view(), name='info'),
    #展示评价页面,商品评价
    re_path(r'^orders/comment/$', views.OrderCommentView.as_view()),
]