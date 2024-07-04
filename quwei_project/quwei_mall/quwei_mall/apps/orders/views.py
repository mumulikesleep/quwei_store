from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from decimal import Decimal
from django import http
from django.utils import timezone
from django.db import transaction #数据库事务的使用
import json

from oauth import constants
from quwei_mall.utils.views import LoginRequiredMixin, LoginRequiredJsonMixin
from users.models import Address
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from quwei_mall.utils.response_code import RETCODE
# Create your views here.


class OrderCommentView(LoginRequiredMixin, View):
    """我的订单:订单商品评价"""
    def get(self, request):
        """展示商品评价页面"""
        #接收参数
        order_id = request.GET.get('order_id')
        #校验参数
        try:
            OrderInfo.objects.get(order_id=order_id, user=request.user)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseNotFound('订单不存在')
        # 查询订单中未被评价的商品信息
        try:
            uncomment_goods = OrderGoods.objects.filter(order_id=order_id, is_commented=False)
        except OrderGoods.DoesNotExist:
            return http.HttpResponseServerError('订单商品信息出错')
        # 构造待评价商品数据
        uncomment_goods_list = []
        for goods in uncomment_goods:
            uncomment_goods_list.append({
                'order_id': goods.order.order_id,
                'sku_id': goods.sku.id,
                'name': goods.sku.name,
                'price': str(goods.price),
                'default_image_url': goods.sku.default_image.url,
                'comment': goods.comment,
                'score': goods.score,
                'is_anonymous': str(goods.is_anonymous)
            })
        #响应参数
        context = {
            'uncomment_goods_list': uncomment_goods_list
        }
        return render(request, 'goods_judge.html', context)

    def post(self, request):
        '''评价订单商品'''
        #接收参数
        order_id = request.GET.get('order_id')
        sku_id = request.POST.get('sku_id')
        score = request.POST.get('score')
        comment = request.POST.get('comment')
        is_anonymous = bool(request.POST.get('is_anonymous'))
        #校验参数
        if not all([order_id, sku_id, score, comment]):
            return http.HttpResponseForbidden('缺少必传参数')
        #查询订单号
        try:
            OrderInfo.objects.filter(order_id=order_id, user=request.user, status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数order_id错误')
        #查询商品id
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')
        #查看是否匿名评价
        if is_anonymous:
            if not isinstance(is_anonymous, bool):
                return http.HttpResponseForbidden('参数is_anonymous错误')
        # 保存订单商品评价数据
        OrderGoods.objects.filter(order_id=order_id, sku_id=sku_id, is_commented=False).update(
            comment = comment,
            score = score,
            is_commented = True,
            is_anonymous = is_anonymous
        )
        # 累计评论数据
        sku.comments += 1
        sku.save()
        sku.spu.comments += 1
        sku.spu.save()
        # 如果所有订单商品都已评价，则修改订单状态为已完成
        if OrderGoods.objects.filter(order_id=order_id, is_commented=False).count() == 0:
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])
        return render(request, 'goods_judge.html')

class UserOrderInfoView(LoginRequiredMixin, View):
    """全部订单"""
    def get(self, request, page_num):
        """提供我的订单页面"""
        user = request.user
        # 查询订单
        orders = user.orderinfo_set.all().order_by("-create_time")
        # 遍历所有订单
        for order in orders:
            # 绑定订单状态,减1是因为下标从0开始
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status - 1][1]
            # 绑定支付方式
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method - 1][1]
            order.sku_list = []
            # 查询订单商品
            order_goods = order.skus.all()
            # 遍历订单商品
            for order_good in order_goods:
                sku = order_good.sku
                sku.count = order_good.count
                sku.amount = sku.price * sku.count
                order.sku_list.append(sku)

        # 分页
        page_num = int(page_num)
        try:
            #创建分页器
            paginator = Paginator(orders, constants.ORDERS_LIST_LIMIT)
            #获取用户要看的那页
            page_orders = paginator.page(page_num)
            #获取总页数：前端的分页插件需要使用
            total_page = paginator.num_pages
        except EmptyPage:
            return http.HttpResponseNotFound('订单不存在')

        context = {
            "page_orders": page_orders,
            'total_page': total_page,
            'page_num': page_num,
        }
        return render(request, "user_center_order.html", context)

class OrderSuccessView(LoginRequiredMixin, View):
    '''提交订单成功页面'''
    def get(self, request):
        '''提供提交订单成功页面'''
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)

class OrderCommitView(LoginRequiredJsonMixin, View):
    '''提交订单'''
    def post(self, request):
        '''保存订单基本信息和订单商品信息'''
        #接收参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        #校验参数
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
            # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return http.HttpResponseForbidden('参数address_id错误')
        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数pay_method错误')
        #开启一次事务
        with transaction.atomic():
            #在数据库操作之前需要指定保存点（保存数据库最初的状态）
            save_id = transaction.savepoint()
            #暴力回滚
            try:
                #获取登录用户
                user = request.user
                #获取订单编号：时间+user_id == '20240623205242000000001'
                order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
                #保存订单基本信息(一)
                order = OrderInfo.objects.create(
                    order_id = order_id,
                    user = user,
                    address = address,
                    total_count = 0,
                    total_amount = Decimal(0.00),
                    freight = Decimal(10.00),
                    pay_method = OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )
                #保存订单商品信息(多)
                # 查询redis购物车中被勾选的商品
                redis_conn = get_redis_connection('carts')
                # 登录用户所有的购物车数据，包含了勾选和未勾选：{b'1':b'1',b'2':b'2',...}
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                # 被勾选商品的sku_id：[b'1',...]
                redis_selected = redis_conn.smembers('selected_%s' % user.id)
                new_cart_dict = {}
                for sku_id in redis_selected:
                    new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])
                #获取被勾选的商品的sku_id
                sku_ids = new_cart_dict.keys()
                for sku_id in sku_ids:
                    #每个商品都有多次下单的机会，直到库存不足
                    while True:
                        #读取购物车商品信息
                        sku = SKU.objects.get(id=sku_id) #查询商品和库存信息时，不能出现缓存(查询集)，所以不能用filter(id__in=sku_id)
                        #获取原始的库存和销量
                        origin_stock = sku.stock
                        origin_sales = sku.sales
                        #获取要提交订单的商品的数量
                        sku_count = new_cart_dict[sku_id]
                        if sku_count > origin_stock:
                            #库存不足，回滚
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code':RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # #SKU 减销量 加库存
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        #测试并发
                        # import time
                        # time.sleep(7)
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        #如果在更新数据时，原始数据变化了，返回0，表示有资源抢夺
                        if result == 0:
                            #库存被购买时，发生资源抢夺，抢夺完后，库存足够，应该继续下单
                            continue
                        #SPU 加销量
                        sku.spu.sales += sku_count
                        sku.spu.save()
                        OrderGoods.objects.create(
                            order = order,
                            sku = sku,
                            count = sku_count,
                            price = sku.price,
                        )
                        #累加订单商品的数量和总价到订单基本信息表
                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price
                        #下单成功，break
                        break
                #再加最后的运费
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.DBERR , 'errmsg': '下单失败'})
            #数据库操作成功，提交一次事务
            transaction.savepoint_commit(save_id)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': order_id})

class OrderSettlementView(LoginRequiredMixin, View):
    '''结算订单'''
    def get(self, request):
        '''查询并展示要结算的订单数据'''
        #获取登录用户
        user = request.user
        #查询用户收获地址：查询登录用户没有被删除的地址
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            addresses = None
        #查询redis购物车中被勾选的商品
        redis_conn = get_redis_connection('carts')
        #登录用户所有的购物车数据，包含了勾选和未勾选：{b'1':b'1',b'2':b'2',...}
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        #被勾选商品的sku_id：[b'1',...]
        redis_selected = redis_conn.smembers('selected_%s' % user.id)
        new_cart_dict = {}
        for sku_id in redis_selected:
            new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])
        #获取被勾选商品的sku_id
        sku_ids = new_cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        total_count = 0
        total_amount = Decimal(0.00) #可以写0或'0'，对于Decimal而言0.00不等于0
        # 遍历skus给每个sku补充count(数量)和amount(价格)
        for sku in skus:
            sku.count = new_cart_dict[sku.id]
            sku.amount = sku.price * sku.count #Decimal类型数据
            #累加数量和金额
            total_count += sku.count
            total_amount += sku.amount #类型不同不能运算
        #指定默认邮费
        freight = Decimal(10.00)
        #构造上下文
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight,
        }
        return render(request, 'place_order.html', context)
