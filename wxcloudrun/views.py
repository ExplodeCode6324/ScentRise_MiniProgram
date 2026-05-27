import json
from datetime import datetime
from flask import render_template, request
from wxcloudrun import app, db
from wxcloudrun.dao import (
    get_products, get_product_by_id, get_categories,
    get_collections, get_collection_products, get_company_info,
)
from wxcloudrun.model import Product
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response


@app.route('/')
def index():
    return render_template('index.html')


# ==================== 小程序 API ====================

@app.route('/api/products', methods=['GET'])
def api_products():
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    products, total = get_products(category_id=category_id, keyword=keyword, page=page, page_size=page_size)
    return make_succ_response({'list': products, 'total': total, 'page': page, 'pageSize': page_size})


@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return make_err_response('产品不存在')
    return make_succ_response(product.to_dict())


@app.route('/api/categories', methods=['GET'])
def api_categories():
    return make_succ_response(get_categories())


@app.route('/api/collections', methods=['GET'])
def api_collections():
    carousel_only = bool(request.args.get('carousel', type=int))
    return make_succ_response(get_collections(carousel_only=carousel_only))


@app.route('/api/collections/<int:collection_id>/products', methods=['GET'])
def api_collection_products(collection_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    products, total = get_collection_products(collection_id, page, page_size)
    return make_succ_response({'list': products, 'total': total, 'page': page, 'pageSize': page_size})


@app.route('/api/company', methods=['GET'])
def api_company_info():
    info = get_company_info()
    return make_succ_response(info.to_dict() if info else {})


# ==================== 后管 API ====================

@app.route('/api/admin/products', methods=['POST'])
def admin_create_product():
    data = request.get_json()
    product = Product(
        name=data.get('name'), model=data.get('model'),
        price=data.get('price'), brand=data.get('brand'),
        spec=data.get('spec'), origin=data.get('origin'),
        description=data.get('description'),
        images=json.dumps(data.get('images', []), ensure_ascii=False),
        custom_fields=json.dumps(data.get('customFields', []), ensure_ascii=False),
        category_id=data.get('categoryId'),
    )
    db.session.add(product)
    db.session.commit()
    return make_succ_response(product.to_dict())


@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
def admin_update_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return make_err_response('产品不存在')
    data = request.get_json()
    for field in ['name', 'model', 'price', 'brand', 'spec', 'origin', 'description', 'category_id']:
        if field in data:
            setattr(product, field, data[field])
    if 'images' in data:
        product.images = json.dumps(data['images'], ensure_ascii=False)
    if 'customFields' in data:
        product.custom_fields = json.dumps(data['customFields'], ensure_ascii=False)
    if 'isActive' in data:
        product.is_active = data['isActive']
    product.updated_at = datetime.now()
    db.session.commit()
    return make_succ_response(product.to_dict())


@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return make_err_response('产品不存在')
    db.session.delete(product)
    db.session.commit()
    return make_succ_empty_response()
