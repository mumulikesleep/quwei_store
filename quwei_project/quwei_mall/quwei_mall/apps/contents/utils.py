from goods.models import GoodsChannel

def get_categories():
    '''获取商品分类'''
    # 准备商品分类对应的字典
    categories = {}
    # 查询所有的商品频道：37个一级类别，要有顺序(优化)
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    # 遍历所有频道
    for channel in channels:
        # 获取当前频道所在的组
        group_id = channel.group_id
        # 构造基本的数据框架：只有11个组
        if group_id not in categories:  # 为防止重复创建字典
            categories[group_id] = {'channels': [], 'sub_cats': []}
        # 查询当前频道对应的一级频道
        cat1 = channel.category
        # 将cat1添加到channels
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })
        # 查询二级和三级数据
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)
    return categories