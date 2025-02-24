from django.shortcuts import render
from django.views import View
from django import http
import logging
from django.core.cache import cache

from areas.models import Area
from quwei_mall.utils.response_code import RETCODE
# Create your views here.


logger = logging.getLogger('django')

class AreasView(View):
    '''省市区三级联动'''
    def get(self,request):
        #判断当前是要查询省份数据还是市区数据
        area_id = request.GET.get('area_id')
        if not area_id:
            province_list = cache.get('province_list')
            if not province_list:
                #查询省级数据
                #Area.objects.filter(属性名__条件表达式=值),查询出来的是模型查询集，JsonResponse不识别查询集列表，要转换为普通列表或字典
                try:
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    province_list = []
                    for province_model in province_model_list:
                        province_dict = {
                            "id": province_model.id,
                            "name": province_model.name
                        }
                        province_list.append(province_dict)
                    #缓存省份字典列表数据
                    cache.set('province_list', province_list, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
                    # 响应省级json数据
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "province_list": province_list})
        else:
            #判断是否有缓存
            sub_data = cache.get('sub_area' + area_id)
            if not sub_data:
                #查询市区数据
                try:
                    parent_model = Area.objects.get(id=area_id)
                    #sub_model_list = parent_model.area_set.all()
                    sub_model_list = parent_model.subs.all()
                    #将子级模型列表转换成字典列表
                    subs = []
                    for sub_model in sub_model_list:
                        sub_dict = {
                            'id': sub_model.id,
                            'name': sub_model.name
                        }
                        subs.append(sub_dict)
                    #构造子级json数据
                    sub_data = {
                        'id': parent_model.id,
                        'name': parent_model.name,
                        'subs': subs
                    }
                    #缓存城市或区县
                    cache.set('sub_area' + area_id, sub_data, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
            #响应城市或区县json数据
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})