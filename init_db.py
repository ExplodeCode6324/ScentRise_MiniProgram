"""数据库初始化：建表 + 种子数据（基于Excel模板）"""
import sys, os, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wxcloudrun import app, db
from wxcloudrun.model import (
    Category, Product, Tag, Collection,
    CompanyInfo, Admin, product_tags
)


def init_db():
    with app.app_context():
        # 表已由 schema.sql 创建，这里只做种子数据

        # --- 产品系列 ---
        series_names = ['乳化系列', '水质系列', '油质系列', '水油系列', '甜味粉末', '咸味粉末']
        cats = {}
        for i, name in enumerate(series_names):
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name, sort_order=i)
                db.session.add(cat)
                db.session.flush()
            cats[name] = cat

        # --- 标签（适用产品） ---
        tag_names = ['烘培', '糖果', '饮料', '炒货', '乳品', '膨化', '电子烟']
        tags_map = {}
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name, category='适用产品')
                db.session.add(tag)
                db.session.flush()
            tags_map[name] = tag

        # --- Excel 产品数据 ---
        excel_data = [
            {'series': '乳化系列', 'name': '乳化可乐', 'model': '1251', 'desc': '乳化系列可乐香精',
             'tags': ['糖果', '饮料', '乳品']},
            {'series': '水质系列', 'name': '草莓香精', 'model': 'AY224', 'desc': '水质草莓香精',
             'tags': ['糖果', '饮料']},
            {'series': '油质系列', 'name': '葱油香精', 'model': '6932', 'desc': '油质葱油香精',
             'tags': ['烘培', '炒货', '膨化']},
            {'series': '水油系列', 'name': '浓缩黑加仑香精', 'model': 'XR2410-1', 'desc': '水油两用黑加仑香精',
             'tags': ['糖果', '饮料', '电子烟']},
            {'series': '甜味粉末', 'name': '巧克力粉末香精', 'model': 'WL4326', 'desc': '甜味巧克力粉末香精',
             'tags': ['烘培', '糖果']},
            {'series': '咸味粉末', 'name': '土豆粉香精', 'model': '17029805', 'desc': '咸味土豆粉末香精',
             'tags': ['炒货', '膨化']},
        ]

        for item in excel_data:
            existing = Product.query.filter_by(product_model=item['model']).first()
            if existing:
                continue
            product = Product(
                product_series=item['series'],
                product_name=item['name'],
                product_model=item['model'],
                product_desc=item['desc'],
                category_id=cats[item['series']].id,
            )
            db.session.add(product)
            db.session.flush()
            # 关联标签
            for tag_name in item['tags']:
                db.session.execute(
                    product_tags.insert().values(product_id=product.id, tag_id=tags_map[tag_name].id)
                )

        # --- 合集（首页轮播） ---
        if not Collection.query.first():
            coll = Collection(
                name='人气热销', description='最受欢迎的热门香精产品',
                is_carousel=True, carousel_sort=1, sort_order=1,
            )
            db.session.add(coll)
            db.session.flush()
            # 把前3个产品加入合集
            products = Product.query.limit(3).all()
            from wxcloudrun.model import collection_products
            for p in products:
                db.session.execute(
                    collection_products.insert().values(collection_id=coll.id, product_id=p.id)
                )

        # --- 示例文章 ---
        from wxcloudrun.model import Article as ArticleModel
        if not ArticleModel.query.first():
            db.session.add(ArticleModel(
                title='2026春季新品发布', author='ScentRise',
                content='<p>春季新品系列正式发布，涵盖乳化、水质、油质等六大系列。</p>',
                is_published=True, published_at=datetime(2026, 5, 1),
            ))

        # --- 公司信息 ---
        if not CompanyInfo.query.first():
            db.session.add(CompanyInfo(
                name='ScentRise 香精科技',
                intro='专注于食品香精研发与生产，产品涵盖乳化、水质、油质、粉末等系列。',
                phone='13800138000', email='contact@scentrise.com',
                address='广州市天河区某某路100号',
            ))

        # --- 管理员 ---
        if not Admin.query.first():
            import bcrypt
            passwd = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            db.session.add(Admin(username='admin', passwd=passwd, real_name='管理员', role='admin'))

        db.session.commit()

        from wxcloudrun.model import Article as ArticleModel
        print(f'OK: {Category.query.count()} 系列, {Product.query.count()} 产品, '
              f'{Tag.query.count()} 标签, {Collection.query.count()} 合集, '
              f'{ArticleModel.query.count()} 文章, {Admin.query.count()} 管理员')


if __name__ == '__main__':
    init_db()
