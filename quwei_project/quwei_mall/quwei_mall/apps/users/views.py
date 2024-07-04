from django.shortcuts import render,redirect
from django.views import View
from django import http
from django.db import DatabaseError
from django.urls import reverse
from django.contrib.auth import login,authenticate,logout
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
import re,json,logging

from users.models import Users,Address
from quwei_mall.utils.response_code import RETCODE
from quwei_mall.utils.views import LoginRequiredJsonMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url,check_verify_email_token
from . import constants
from goods.models import SKU
from carts.utils import merge_carts_cookies_redis


# Create your views here.
#创建日志输出器
logger = logging.getLogger('django')

class UserBrowseHistory(LoginRequiredJsonMixin, View):
    '''用户浏览记录'''
    def post(self, request):
        '''保存用户商品浏览记录'''
        #接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        #校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')
        #保存sku_id到redis
        redis_conn = get_redis_connection('history')
        user = request.user #该用户是认证后的用户
        pl = redis_conn.pipeline() #创建管道
        #先去重
        pl.lrem('history_%s'%user.id, 0, sku_id)
        #再保存，最近浏览的商品在最前面
        pl.lpush('history_%s'%user.id, sku_id)
        #最后截取
        pl.ltrim('history_%s'%user.id, 0, 4)
        #执行
        pl.execute()
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        '''查询用户商品记录'''
        #获取用户登录信息
        user = request.user
        #创建连接redis对象
        redis_conn = get_redis_connection('history')
        #取出列表数据(核心代码)
        sku_ids = redis_conn.lrange('history_%s'%user.id, 0, -1)
        #将模型类转字典
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id':sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })
        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': 'OK', 'skus': skus})

class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""
    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            request.user.check_password(old_password)
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_password != new_password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})
        # 清理状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        # # 响应密码修改结果：重定向到登录界面
        return response

class UpdateTitleAddressView(LoginRequiredJsonMixin, View):
    '''更新地址标题'''
    def put(self, request, address_id):
        '''实现更新地址标题逻辑'''
        #接收参数
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        #校验参数
        if not title:
            return http.HttpResponseForbidden('缺少title')
        try:
            #查询当前要更新标题的地址
            address = Address.objects.get(id=address_id)
            #将新地址标题覆盖地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新标题失败'})
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新标题成功'})

class DefaultAddressView(LoginRequiredJsonMixin, View):
    '''设置默认地址'''
    def put(self, request, address_id):
        '''实现设置默认地址逻辑'''
        try:
            #查询出当前哪个地址会作为登录用户的默认地址
            address = Address.objects.get(id=address_id)
            #将指定的地址设置为当前登录用户的默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})

class UpdateDestoryAddressView(LoginRequiredJsonMixin, View):
    '''更新和删除地址'''
    def put(self, request, address_id):
        '''更新地址'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[1-9][0-9]{4,}@qq.com$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        #使用最新的地址信息覆盖指定的旧的地址信息
        # address = Address.objects.get(id=address_id)  方案一
        # address.title = ''
        # address.user = ''
        # address.save()
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '获取更新地址失败'})
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        '''删除地址'''
        #实现指定地址的逻辑删除：is_delete = True
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        #响应结果：code、errmsg
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})

class AddressCreateView(LoginRequiredJsonMixin, View):
    '''新增地址'''
    def post(self,request):
        '''实现新增地址逻辑'''
        #判断用户数量是否超过上限：查询当前用户的地址数量
        # count = Address.objects.filter(user=request.user).count() 方法一
        count = request.user.addresses.count()  #方法二
        if count > constants.USER_ADDRESS_COUNTS_LIMIT:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超出用户地址上限'})
        #接收参数
        json_str = request.body.decode()    #body中的数据为bytes类型
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        #校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[1-9][0-9]{4,}@qq.com$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        #保存用户传入的地址信息
        try:
            address = Address.objects.create(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email,
            )
            #如果登录用户没有默认地址，需要指定默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})
        #构造新增地址字典数据
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,#通过外键获取的是主表的对象
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        #响应新增地址结果，需要将新增的地址返回给前端渲染
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})

class AddressView(LoginRequiredMixin, View):
    '''用户收货地址'''
    def get(self,request):
        '''查询并展示用户地址信息'''
        #获取当前登录用户对象
        login_user = request.user
        #使用当前登录用户对象和is_delete=False作为条件查询地址数据
        addresses = Address.objects.filter(user=login_user, is_deleted=False)
        #将用户地址模型列表转换为普通字典列表：因为JsonResponse和Vue.js不认识模型列表，只有django和jinja2模板引擎认识
        address_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_list.append(address_dict)
        context = {
            'default_address_id': login_user.default_address_id or '0', #随便给个字符串，用户首次没有默认地址值会传给前端None，但前端不认识None
            'addresses': address_list,
        }
        return render(request,'user_center_site.html',context)

class VerifyEmailView(View):
    '''验证邮箱'''
    def get(self,request):
        #接收参数
        token = request.GET.get('token')
        #校验参数
        if not token:
            return http.HttpResponseForbidden('缺少token')
        #从token中提取用户信息user_id ==> user
        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseBadRequest('无效的token')
        #将用户的email_active字段设置为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('邮箱激活失败')
        #响应结果：重定向到用户中心
        return redirect(reverse('users:info'))

class EmailView(LoginRequiredJsonMixin,View):
    '''增添邮箱'''
    def put(self,request):
        #接收参数
        json_str = request.body.decode()#body是bytes类型
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        #校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')
        #将用户传入的邮箱保存在用户数据库的email字段中
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '增添邮箱失败'})
        #发送邮箱验证邮件
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.apply_async(args=(email, verify_url))#apply_async一定要写，把任务放到队列中
        #响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

class UserInfoView(LoginRequiredMixin,View):
    '''用户中心'''
    def get(self,request):
        '''提供用户中心页面'''
        #如果LoginRequiredMixin判断出用户已登录，那么request.user就是登录用户对象
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }
        return render(request, 'user_center_info.html',context)

class LogoutView(View):
    '''用户退出登录'''
    def get(self,request):
        '''实现用户退出登录的逻辑'''
        #清除状态保持信息
        logout(request)
        #退出登录重定向到首页
        response = redirect(reverse('contents:index'))
        #删除cookies中的用户名
        response.delete_cookie('username')
        #响应结果
        return response

class LoginView(View):
    '''用户登录'''
    def get(self, request):
        '''提供用户登录页面'''
        return render(request, 'login.html')

    def post(self, request):
        '''实现用户登录逻辑'''
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_@.-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或qq邮箱')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最多20位')
        # 认证用户：使用账号查询用户是否存在，如果用户存在，再校验密码是否正确
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
        # 状态保持
        login(request, user)
        # 使用remembered确定状态保持周期(实现记住登录)
        if remembered != 'on':
            # 没有记住登录：状态保持周期在浏览器会话结束后就销毁
            request.session.set_expiry(0)
        else:
            # 记住登录：状态保持周期为两周：默认为两周
            request.session.set_expiry(None)
        # 响应结果
        #取出next
        next = request.GET.get('next')
        if next:
            #重定向到next
            response = redirect(next)
        else:
            #重定向到首页
            response = redirect(reverse('contents:index'))
        #为了实现在首页右上角展示用户名信息，我们需要将用户名缓存在cookie中
        response.set_cookie('username', user.username, max_age=3600*24*15)

        #用户登录成功，合并cookie购物车到redis购物车
        response = merge_carts_cookies_redis(request, user, response)
        # 响应结果:重定向到首页
        return response

class UsernameCountView(View):
    '''判断用户名是否重复注册'''
    def get(self,request,username):
        '''
        :param request: 用户名
        :return: JSON格式
        '''
        count = Users.objects.filter(username=username).count()
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','count':count})#根据设计手册来写需要传输的数据

class MobileCountView(View):
    '''判断邮箱是否重复注册'''
    def get(self,request,mobile):
        '''
        :param request: 邮箱
        :return:  JSON格式
        '''
        count = Users.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','count':count})#同样是按照手册来设计
class RegisterView(View):
    '''用户注册'''
    def get(self,request):
        return render(request,'register.html')

    def post(self,request):
        '''实现用户注册逻辑'''
        #接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')
        #校验参数:前后端的校验需要分开，避免恶意用户越过前端逻辑发请求，要保证后端的安全，前后端的校验逻辑相同
            #判断参数是否齐全
        if not all([username,password,password2,mobile,allow]):
            return http.HttpResponseForbidden('缺少必传参数')
            #判断用户是否为5-20字符
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20位字符的用户名')
            # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
            # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
            # 判断邮箱是否合法
        if not re.match(r'^[1-9][0-9]{4,}@qq.com$', mobile):
            return http.HttpResponseForbidden('请输入正确的qq邮箱')
            #判断邮箱验证码是否正确
        redis_coon = get_redis_connection('verify_code')
        sms_code_server = redis_coon.get('sms_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '邮箱验证码已失效'})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg': '验证码输入有误'})
            # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')
        #保存注册数据，业务的核心
        try:
            user = Users.objects.create_user(username=username,password=password,mobile=mobile)
        except DatabaseError:
            return render(request,'register.html',{'register_errmsg':'注册失败'})
        #login方法内部设置了session
        login(request,user)
        # 响应结果:重定向到首页
        response = redirect(reverse('contents:index'))
        # 为了实现在首页右上角展示用户名信息，我们需要将用户名缓存在cookie中
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        print(user.username)
        # 响应结果:重定向到首页
        return response

