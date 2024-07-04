#静态化首页
from django.template import loader
from django.conf import settings
import os

from contents.utils import get_categories
from contents.models import ContentCategory

def generate_static_index_html():
    '''静态化首页'''
    #1、查询并展示商品分类(复制之前的代码)
    categories = get_categories()
    # 查询首页广告数据
    # 查询所有的广告类别
    contents = {}
    content_categories = ContentCategory.objects.all()
    for content_categorie in content_categories:
        contents[content_categorie.key] = content_categorie.content_set.filter(status=True).order_by(
            'sequence')  # 查询出未下架的广告并展示
    context = {
        'categories': categories,
        'contents': contents
    }
    '''不能return，也不能返回响应，是手动调用保存静态文件'''
    #2、渲染模板,先获取模板文件
    template = loader.get_template('index.html')
    #再使用上下文渲染模板文件
    html_text = template.render(context)
    #将模板文件写入到静态路径
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8')as f:
        f.write(html_text)
