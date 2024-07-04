from django.shortcuts import render
from django.views import View
from alipay import AliPay
from django.conf import settings
from django import http
import os

from quwei_mall.utils.views import LoginRequiredJsonMixin
from orders.models import OrderInfo
from quwei_mall.utils.response_code import RETCODE
from payment.models import Payment
# Create your views here.


class PaymentStatusView(LoginRequiredJsonMixin, View):
    '''保存支付的订单状态'''
    def get(self, request):
        #获取到所有的查询字符串参数
        query_dict = request.GET
        #将查询字符串参数的类型转成标准的字典类型
        data = query_dict.dict()
        #从查询字符串参数中提取并移除sign，不能参与签名验证
        signature = data.pop('sign')
        #创建SDK对象
        alipay = AliPay(  # 传入公共参数（对接任何接口都要传递）
            appid=settings.ALIPAY_APPID,  # 应用ID
            app_notify_url=None,  # 默认回调url，如果采用同步通知就不传
            # 读取应用的私钥和支付宝的公钥
            app_private_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
            alipay_public_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
            sign_type="RSA2",  # 加密标准
            debug=settings.ALIPAY_DEBUG  # 指定是否是开发环境
        )
        #使用SDK对象，调用验证签名接口函数，得到验证结果
        success = alipay.verify(data, signature)
        #如果验证通过，需要将支付宝状态进行处理（将电子商城的订单ID和支付宝的订单ID绑定在一起，修改订单状态）
        if success:
            #商城维护的订单id
            order_id = data.get('out_trade_no')
            # 支付宝维护的订单id
            trade_id = data.get('trade_no')
            Payment.objects.create(
                #能拿对象作为条件就拿对象，拿不到就拿id
                order_id = order_id,
                trade_id = trade_id
            )
            # 修改订单状态为待评价
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            #响应结果
            context = {
                'trade_id': trade_id
            }
            return render(request, 'pay_success.html', context)
        else:
            return http.HttpResponseForbidden('非法请求')

class PaymentView(LoginRequiredJsonMixin, View):
    '''对接支付宝的支付接口'''
    def get(self, request, order_id):
        '''
        :param order_id: 当前要支付的订单ID
        :return: JSON
        '''
        user = request.user
        #校验order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单信息错误')
        #创建对接支付宝接口的SDK对象
        alipay = AliPay( #传入公共参数（对接任何接口都要传递）
            appid=settings.ALIPAY_APPID, #应用ID
            app_notify_url=None,  # 默认回调url，如果采用同步通知就不传
            #读取应用的私钥和支付宝的公钥
            app_private_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
            alipay_public_key_string=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/alipay_public_key.pem")).read(),
            sign_type="RSA2", #加密标准
            debug=settings.ALIPAY_DEBUG #指定是否是开发环境
        )
        #SDK对象对接支付宝支付的接口，得到登录页的地址
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, #订单编号
            total_amount=str(order.total_amount), #订单支付金额
            subject="趣味商城%s" % order_id, #订单标题
            return_url=settings.ALIPAY_RETURN_URL, #同步通知的回调地址，如果不是同步通知，就不传
        )
        #拼接完整的支付宝登录页地址
        # 电脑网站支付，需要跳转到(正式环境)：https://openapi.alipay.com/gateway.do? + order_string
        # 电脑网站支付，需要跳转到(开发环境)：https://openapi-sandbox.dl.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url':alipay_url})