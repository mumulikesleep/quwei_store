from django.shortcuts import render
from django.views import View

from contents.models import ContentCategory
from contents.utils import get_categories
# Create your views here.


class IndexView(View):
    '''首页广告'''
    def get(self,request):
        '''提供首页广告页面'''
        #查询并展示商品分类
        categories = get_categories()
        #查询首页广告数据
        #查询所有的广告类别
        contents = {}
        content_categories = ContentCategory.objects.all()
        for content_categorie in content_categories:
            contents[content_categorie.key] = content_categorie.content_set.filter(status=True).order_by('sequence')    #查询出未下架的广告并展示
        context = {
            'categories': categories,
            'contents': contents
        }
        return render(request, 'index.html', context)