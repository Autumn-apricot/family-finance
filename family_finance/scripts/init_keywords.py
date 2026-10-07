"""
初始化 category_keywords — 在项目根目录执行:
  python manage.py shell < scripts/init_keywords.py
或:
  python scripts/init_keywords.py  (需配置 DJANGO_SETTINGS_MODULE)
"""
import os
import sys

# 将项目根目录加入 path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from finance.models import Category
from finance.models_voice import CategoryKeyword

SEED = [
    ('餐饮', [('吃饭', 15), ('午餐', 15), ('晚餐', 15), ('外卖', 12), ('奶茶', 10)]),
    ('交通', [('打车', 15), ('滴滴', 12), ('地铁', 12), ('公交', 10)]),
    ('购物', [('超市', 12), ('淘宝', 10), ('京东', 10), ('购物', 12)]),
    ('娱乐', [('电影', 12), ('KTV', 12), ('游戏', 10)]),
    ('住房', [('房租', 15), ('水电', 10), ('物业', 10)]),
    ('医疗', [('医院', 12), ('药', 8), ('体检', 10)]),
    ('教育', [('学费', 15), ('培训', 10), ('书本', 8)]),
    ('工资', [('工资', 15), ('薪水', 12)]),
    ('奖金', [('奖金', 12), ('年终奖', 15)]),
]


def main():
    created = 0
    for cat_name, keywords in SEED:
        cat = Category.objects.filter(name=cat_name).first()
        if not cat:
            print(f'跳过：分类 {cat_name} 不存在')
            continue
        for kw, weight in keywords:
            _, is_new = CategoryKeyword.objects.get_or_create(
                category=cat,
                keyword=kw,
                defaults={'weight': weight},
            )
            if is_new:
                created += 1
    print(f'完成，新增关键词 {created} 条')


if __name__ == '__main__':
    main()
