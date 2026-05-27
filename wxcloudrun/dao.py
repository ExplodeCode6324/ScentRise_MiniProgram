import logging
from sqlalchemy.exc import OperationalError
from wxcloudrun import db
from wxcloudrun.model import Category, Product, Collection, CompanyInfo

logger = logging.getLogger('log')


def get_products(category_id=None, keyword=None, page=1, page_size=20):
    try:
        q = Product.query.filter(Product.is_active == True)
        if category_id:
            q = q.filter(Product.category_id == category_id)
        if keyword:
            like = f'%{keyword}%'
            q = q.filter(db.or_(
                Product.name.like(like),
                Product.model.like(like),
                Product.brand.like(like),
            ))
        total = q.count()
        products = q.order_by(Product.sort_order.asc(), Product.id.desc())\
                    .offset((page - 1) * page_size).limit(page_size).all()
        return [p.to_dict() for p in products], total
    except OperationalError as e:
        logger.error(f"get_products error: {e}")
        return [], 0


def get_product_by_id(product_id):
    try:
        return Product.query.get(product_id)
    except OperationalError as e:
        logger.error(f"get_product_by_id error: {e}")
        return None


def get_categories():
    try:
        return [c.to_dict() for c in Category.query.order_by(Category.sort_order.asc()).all()]
    except OperationalError as e:
        logger.error(f"get_categories error: {e}")
        return []


def get_collections(carousel_only=False):
    try:
        q = Collection.query
        if carousel_only:
            q = q.filter(Collection.is_carousel == True)
        return [c.to_dict() for c in q.order_by(Collection.sort_order.asc()).all()]
    except OperationalError as e:
        logger.error(f"get_collections error: {e}")
        return []


def get_collection_products(collection_id, page=1, page_size=20):
    try:
        q = Product.query.filter(Product.collection_id == collection_id, Product.is_active == True)
        total = q.count()
        products = q.order_by(Product.sort_order.asc())\
                    .offset((page - 1) * page_size).limit(page_size).all()
        return [p.to_dict() for p in products], total
    except OperationalError as e:
        logger.error(f"get_collection_products error: {e}")
        return [], 0


def get_company_info():
    try:
        return CompanyInfo.query.first()
    except OperationalError as e:
        logger.error(f"get_company_info error: {e}")
        return None
