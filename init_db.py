"""数据库初始化：建表 + 种子数据"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wxcloudrun import app, db
from wxcloudrun.model import Category, Product, Collection, CompanyInfo


def init_db():
    with app.app_context():
        db.create_all()
        print('OK 数据库表已创建')

        cats = [
            Category(name='洗发水', sort_order=1),
            Category(name='护发素', sort_order=2),
            Category(name='沐浴露', sort_order=3),
            Category(name='套装', sort_order=4),
        ]
        db.session.add_all(cats)
        db.session.flush()

        products = [
            Product(name='柔顺丝滑洗发水', model='XS-001', price='89.00', brand='ScentRise',
                    spec='500ml', origin='广州', category_id=cats[0].id,
                    description='深层滋养，柔顺丝滑，适合干枯毛躁发质。',
                    images='["/static/demo/shampoo1.jpg"]'),
            Product(name='控油清爽洗发水', model='XS-002', price='79.00', brand='ScentRise',
                    spec='500ml', origin='广州', category_id=cats[0].id,
                    description='清爽控油，持久蓬松，适合油性发质。',
                    images='["/static/demo/shampoo2.jpg"]'),
            Product(name='修护蛋白护发素', model='HF-001', price='69.00', brand='ScentRise',
                    spec='500ml', origin='广州', category_id=cats[1].id,
                    description='蛋白修护，深层滋养发丝。',
                    images='["/static/demo/conditioner1.jpg"]'),
            Product(name='香氛沐浴露', model='MY-001', price='59.00', brand='ScentRise',
                    spec='750ml', origin='广州', category_id=cats[2].id,
                    description='持久留香，温和清洁。',
                    images='["/static/demo/shower1.jpg"]'),
        ]
        db.session.add_all(products)
        db.session.flush()

        coll = Collection(
            name='2026 春季新品', description='春季主打产品合集',
            is_carousel=True, carousel_sort=1, sort_order=1,
            cover_image='/static/demo/spring2026.jpg',
        )
        db.session.add(coll)
        db.session.flush()
        for p in products[:2]:
            p.collection_id = coll.id

        info = CompanyInfo(
            name='ScentRise 香氛科技',
            intro='专注于个人护理产品研发，致力于为消费者带来高品质的香氛洗护体验。',
            phone='13800138000', email='contact@scentrise.com',
            address='广州市天河区某某路100号',
        )
        db.session.add(info)

        db.session.commit()
        print(f'OK 种子数据：{len(cats)} 分类, {len(products)} 产品, 1 合集')


if __name__ == '__main__':
    init_db()
