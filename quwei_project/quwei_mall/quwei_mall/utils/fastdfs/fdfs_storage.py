from django.core.files.storage import Storage
from django.conf import settings

class FastDFSStorage(Storage):
    '''自定义文件存储类'''
    def __init__(self, fdfs_base_url=None):
        '''文件存储类的初始化方法'''
        # if not fdfs_base_url:
        #   self.fdfs_base_url = settings.FDFS_BASE_URL
        # else:
        #     self.fdfs_base_url = fdfs_base_url
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        '''
        打开文件时会被调用：文档说明必须重写
        :param name: 文件路径
        :param mode: 文件打开方式
        :return: None
        '''
        #因为当前不是去打开某个文件，所以这个方法目前无用，但是又必须重写，所以pass
        pass

    def _save(self, name, content):
        '''
        PS：将来后台管理系统中，需要在这个方法中实现文件上传到FastDFS服务器
        保存文件时会被调用：文档说明必须重写
        :param name: 文件路径
        :param content: 文件二进制内容
        :return: None
        '''
        # 因为当前不是去保存某个文件，所以这个方法目前无用，但是又必须重写，所以pass
        pass

    def url(self, name):
        '''
        返回文件的全路径
        :param name: 文件相对路径(数据库中的数据)
        :return: 文件的全路径(像http://192.168.103.158:8888/group1/M00/00/00/wKhnnlxw_gmAcoWmAAEXU5wmjPs35.jpeg)
        '''
        return self.fdfs_base_url + name