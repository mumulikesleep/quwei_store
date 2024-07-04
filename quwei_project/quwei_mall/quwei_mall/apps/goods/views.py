from django.shortcuts import render
from django.views import View
from django import http
#需要考虑分页时每页记录(数据库)的条数，得到分多少页
from django.core.paginator import Paginator, EmptyPage #分页器,空页错误
from django.utils import timezone #处理时间的工具
from datetime import datetime

from goods.models import GoodsCategory, SKU, GoodsVisitCount
from contents.utils import get_categories
from goods.utils import get_breadcrumb
from quwei_mall.utils.response_code import RETCODE
from orders.models import OrderGoods, OrderInfo


# Create your views here.


class GoodsCommentView(View):
    '''订单商品评价信息'''
    def get(self, request, sku_id):
        # 获取被评价的订单商品信息
        order_goods_list  = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True).order_by('-create_time')[:30]
        #序列化
        comment_list = []
        for order_goods in order_goods_list:
            username  = order_goods.order.user.username
            comment_list.append({
                'username': username[0] + '***' + username[-1] if order_goods.is_anonymous else username,
                'comment': order_goods.comment,
                'score': order_goods.score,
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'comment_list': comment_list})

class DetailVisitView(View):
    """详情页分类商品访问量"""
    def post(self, request, category_id):
        #接收参数和检验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')
        #获取当天的日期
        t = timezone.localtime()
        #获取当天的时间字符串
        today_str = '%d-%02d-%02d'%(t.year, t.month, t.day)
        #将当天的时间字符串转成时间对象datetime，为了跟date字段的类型匹配
        today_date = datetime.strptime(today_str, '%Y-%m-%d') #时间字符串转时间对象，datetime.strftime() #时间对象转时间字符串
        #判断当天中指定的分类商品对应的记录是否存在
        try:
            #如果存在，直接获取到记录对应的对象
            counts_data = GoodsVisitCount.objects.get(date=today_date, category=category)
        except GoodsVisitCount.DoesNotExist:
            # 如果不存在，直接获取到记录对应的对象
            counts_data = GoodsVisitCount()
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.date = today_date
            counts_data.save()
        except Exception:
            return http.HttpResponseServerError('统计失败')
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

class DetailView(View):
    '''商品详情页'''
    def get(self, request, sku_id):
        """提供商品详情页"""
        #接收和校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            # return http.HttpResponseForbidden('sku_id不存在')
            return render(request, '404.html')
        #查询商品分类
        categories = get_categories()
        #查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)
        #查询sku,构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:  #遍历规格，获取固定id的商品的规格信息
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        #下面的代码用于页面的渲染(每个网页都不一样)，上面的代码使用规格来选取商品id(比如颜色为黑色，内存是256g是1号商品)
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options
        #构造上下文
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs
        }
        return render(request, 'detail.html', context)

class HotGoodsView(View):
    '''热销排行'''
    def get(self, request, category_id):
        #查询指定分类的SKU信息，而且必须是上架的状态，然后按照销量由高到低排序，最后切片取出前两个
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        #将模型列表转字典列表，构造JSON数据
        hot_skus = []
        for sku in skus:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url #取图片的全路径
            }
            hot_skus.append(sku_dict)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})

class ListView(View):
    '''商品列表页'''
    def get(self, request, category_id, page_num):
        '''查询并渲染商品列表页'''
        #校验参数category_id的范围
        try:
            #三级类别
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('参数category_id不存在')
        #获取sort(排序规则):如果sort没有值，取'default'
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            sort_field = 'price'#按照价格由低到高排序
        elif sort == 'hot':
            sort_field = '-sales'#按照销量由高到低排序
        else:#其他均为default
            sort = 'default'#当出现?sort=itcast也为'default'
            sort_field = 'create_time'
        #查询商品分类
        categories = get_categories()
        #查询面包屑导航    三级《== 二级 《== 一级
        breadcrumb = get_breadcrumb(category)
        #分页和排序查询：category查询sku，一查多，一方的模型对象.多方的关联字段.all/filter
        skus = category.sku_set.filter(is_launched=True).order_by(sort_field)
        #创建分页器
        #Paginator('要分页的记录','每页记录的条数')
        paginator = Paginator(skus, 5)
        #获取当前用户看到的那一页(核心)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseNotFound('Empty Page')
        #获取总页数：前端的分页插件需要使用
        total_page = paginator.num_pages
        #构造上下文
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            'total_page': total_page,
            'page_num': page_num,
            'sort': sort,
            'category_id': category_id
        }
        return render(request, 'list.html', context)