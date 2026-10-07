"""
初始化数据：python manage.py shell < scripts/init_data.py
或: python scripts/init_data.py（需先 migrate）
"""
import os
import sys

import django

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from finance.models import Category, User  # noqa: E402
from finance.models_voice import CategoryKeyword  # noqa: E402

# 一级分类 (name, icon, type, sort_order)
PARENT_CATEGORIES = [
    ('餐饮', '🍽️', 'expense', 1),
    ('交通', '🚗', 'expense', 2),
    ('购物', '🛒', 'expense', 3),
    ('娱乐', '🎮', 'expense', 4),
    ('住房', '🏠', 'expense', 5),
    ('医疗', '💊', 'expense', 6),
    ('教育', '📚', 'expense', 7),
    ('其他支出', '💸', 'expense', 99),
    ('工资', '💰', 'income', 1),
    ('奖金', '🎁', 'income', 2),
    ('其他收入', '📥', 'income', 99),
]

# 二级分类 (parent_name, name, icon, sort_order)
SUB_CATEGORIES = [
    # 餐饮
    ('餐饮', '早餐', '🥛', 1),
    ('餐饮', '午餐', '🍱', 2),
    ('餐饮', '晚餐', '🍲', 3),
    ('餐饮', '宵夜', '🍜', 4),
    ('餐饮', '外卖', '🥡', 5),
    ('餐饮', '奶茶咖啡', '🧋', 6),
    ('餐饮', '零食水果', '🍉', 7),
    # 交通
    ('交通', '公交地铁', '🚇', 1),
    ('交通', '打车', '🚕', 2),
    ('交通', '加油', '⛽', 3),
    ('交通', '停车费', '🅿️', 4),
    ('交通', '高铁飞机', '✈️', 5),
    # 购物
    ('购物', '日用百货', '🧴', 1),
    ('购物', '服饰鞋包', '👗', 2),
    ('购物', '数码电子', '📱', 3),
    ('购物', '家居用品', '🛋️', 4),
    # 娱乐
    ('娱乐', '电影', '🎬', 1),
    ('娱乐', '游戏', '🎮', 2),
    ('娱乐', '运动健身', '🏋️', 3),
    ('娱乐', '旅游度假', '🏖️', 4),
    # 住房
    ('住房', '房租', '🏠', 1),
    ('住房', '水电燃气', '💡', 2),
    ('住房', '物业费', '📋', 3),
    ('住房', '维修', '🔧', 4),
    # 医疗
    ('医疗', '门诊', '🏥', 1),
    ('医疗', '药品', '💊', 2),
    ('医疗', '体检', '🩺', 3),
    # 教育
    ('教育', '学费', '📚', 1),
    ('教育', '培训', '📖', 2),
    ('教育', '书籍文具', '✏️', 3),
    # 收入
    ('工资', '基本工资', '💰', 1),
    ('工资', '加班补贴', '🕐', 2),
    ('奖金', '年终奖', '🎁', 1),
    ('奖金', '绩效奖金', '🏆', 2),
    ('奖金', '项目奖金', '📊', 3),
]

KEYWORDS = {
    '餐饮': ['吃饭', '聚餐', '下馆子', '请客'],
    '交通': ['出行', '通勤', '交通工具'],
    '购物': ['超市', '淘宝', '京东', '衣服', '鞋子', '数码', '购物', '买'],
    '娱乐': ['电影', '游戏', '健身', '旅游', 'KTV'],
    '住房': ['物业', '维修', '装修'],
    '医疗': ['医院', '药', '体检'],
    '教育': ['学费', '培训', '书'],
    '工资': ['工资', '薪水', '发工资'],
    '奖金': ['奖金', '年终奖', '绩效'],
}

SUB_KEYWORDS = {
    '早餐': ['早饭', '早点', '早餐'],
    '午餐': ['午饭', '午餐', '中午饭', '中饭'],
    '晚餐': ['晚饭', '晚餐', '晚飯'],
    '宵夜': ['夜宵', '宵夜', '夜宵'],
    '外卖': ['外卖', '美团', '饿了么'],
    '奶茶咖啡': ['奶茶', '咖啡', '星巴克', '瑞幸', '拿铁'],
    '零食水果': ['零食', '水果', '小吃', '点心'],
    '公交地铁': ['公交', '地铁', '巴士'],
    '打车': ['打车', '滴滴', '出租车', '网约车'],
    '加油': ['加油', '加油站', '油费'],
    '停车费': ['停车', '停车费'],
    '高铁飞机': ['高铁', '飞机', '火车票', '机票'],
    '日用百货': ['超市', '杂货', '日用'],
    '服饰鞋包': ['衣服', '鞋子', '鞋', '包', '裙子'],
    '数码电子': ['手机', '电脑', '平板', '耳机', '数码'],
    '家居用品': ['家具', '家居', '家纺'],
    '电影': ['电影', '电影院', '影院'],
    '游戏': ['游戏', '网游', '手游', '充值'],
    '运动健身': ['健身', '瑜伽', '跑步', '运动'],
    '旅游度假': ['旅游', '度假', '旅行', '门票'],
    '房租': ['房租', '租金', '房租费'],
    '水电燃气': ['水电', '电费', '水费', '燃气', '煤气'],
    '物业费': ['物业', '物业费'],
    '维修': ['维修', '修理', '修'],
    '门诊': ['看病', '门诊', '挂号', '医院'],
    '药品': ['药', '药品', '药店'],
    '体检': ['体检', '检查', '体检费'],
    '学费': ['学费', '学杂费'],
    '培训': ['培训', '课程', '网课'],
    '书籍文具': ['书', '本', '文具', '纸'],
    '基本工资': ['工资', '薪水', '发工资'],
    '加班补贴': ['加班', '补贴'],
    '年终奖': ['年终奖', '年终'],
    '绩效奖金': ['绩效', '绩效奖'],
    '项目奖金': ['项目奖', '项目奖金'],
}


def main():
    if not User.objects.filter(username='admin').exists():
        admin = User(username='admin', nickname='管理员', role=User.ROLE_ADMIN)
        admin.set_password('admin123')
        admin.save()
        print('创建管理员 admin / admin123')

    if not User.objects.filter(username='zhangsan').exists():
        m = User(username='zhangsan', nickname='张三', role=User.ROLE_MEMBER)
        m.set_password('123456')
        m.save()
        print('创建成员 zhangsan / 123456')

    # 创建一级分类
    parent_map = {}
    for name, icon, ctype, order in PARENT_CATEGORIES:
        cat, _ = Category.objects.get_or_create(
            name=name, parent__isnull=True,
            defaults={'icon': icon, 'type': ctype, 'sort_order': order, 'is_system': True},
        )
        parent_map[name] = cat
        for kw in KEYWORDS.get(name, []):
            CategoryKeyword.objects.update_or_create(
                category=cat, keyword=kw,
                defaults={'weight': 10},
            )

    # 创建二级分类（关键词权重 25，高于一级分类的 10 和内置的 15）
    for parent_name, name, icon, order in SUB_CATEGORIES:
        parent = parent_map.get(parent_name)
        if not parent:
            continue
        sub_cat, _ = Category.objects.get_or_create(
            name=name, parent=parent,
            defaults={'icon': icon, 'type': parent.type, 'sort_order': order, 'is_system': True},
        )
        for kw in SUB_KEYWORDS.get(name, []):
            CategoryKeyword.objects.update_or_create(
                category=sub_cat, keyword=kw,
                defaults={'weight': 25},
            )

    print('分类与关键词初始化完成（含二级分类）')


if __name__ == '__main__':
    main()
