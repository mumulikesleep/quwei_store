from django.db import models

# Create your models here.
class Area(models.Model):
    """省市区"""
    name = models.CharField(max_length=20, verbose_name='名称')
    #related_name是关联字段，连表查询一对多，会在数据少的一方自动生成多的一方表名_set，related_name是自定义该关联字段的字段名
    #第一个参数表示自己与自己关联
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True, verbose_name='上级行政区划')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = '省市区'

    def __str__(self):
        return self.name