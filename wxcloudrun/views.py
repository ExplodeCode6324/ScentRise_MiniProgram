import json
from datetime import datetime
from flask import render_template, request
from wxcloudrun import app, db
from wxcloudrun.dao import (
    get_products, get_product_by_id, get_product_by_model,
    get_categories, get_or_create_category,
    get_tags, get_or_create_tag,
    get_collections, get_articles, get_article_by_id,
    get_company_info, get_admin_by_username,
)
from wxcloudrun.model import Product, Article, Category, CompanyInfo, Admin
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response


@app.route('/')
def index():
    return render_template('index.html')


# ==================== 小程序 API ====================

@app.route('/api/products', methods=['GET'])
def api_products():
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    products, total = get_products(category_id=category_id, tag_id=tag_id, keyword=keyword, page=page, page_size=page_size)
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


@app.route('/api/tags', methods=['GET'])
def api_tags():
    tag_category = request.args.get('category')
    return make_succ_response(get_tags(category=tag_category))


@app.route('/api/collections', methods=['GET'])
def api_collections():
    carousel_only = bool(request.args.get('carousel', type=int))
    return make_succ_response(get_collections(carousel_only=carousel_only))


@app.route('/api/articles', methods=['GET'])
def api_articles():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    articles, total = get_articles(page=page, page_size=page_size, published_only=True)
    return make_succ_response({'list': articles, 'total': total, 'page': page, 'pageSize': page_size})


@app.route('/api/articles/<int:article_id>', methods=['GET'])
def api_article_detail(article_id):
    article = get_article_by_id(article_id)
    if not article:
        return make_err_response('文章不存在')
    return make_succ_response(article.to_dict())


@app.route('/api/company', methods=['GET'])
def api_company_info():
    info = get_company_info()
    return make_succ_response(info.to_dict() if info else {})


# ==================== 后管 API ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin = get_admin_by_username(data.get('username'))
    if not admin:
        return make_err_response('账号或密码错误')
    import bcrypt
    if not bcrypt.checkpw(data.get('password', '').encode(), admin.passwd.encode()):
        return make_err_response('账号或密码错误')
    admin.last_login = datetime.now()
    db.session.commit()
    return make_succ_response({'token': 'session', 'admin': admin.to_dict()})


# --- 产品 CRUD ---

@app.route('/api/admin/products', methods=['POST'])
def admin_create_product():
    data = request.get_json()
    product = Product(
        product_series=data.get('productSeries'),
        product_name=data.get('productName'),
        product_model=data.get('productModel'),
        product_desc=data.get('productDesc'),
        product_image=data.get('productImage'),
        product_images=json.dumps(data.get('productImages', []), ensure_ascii=False),
        category_id=data.get('categoryId'),
    )
    db.session.add(product)
    # 关联标签
    if data.get('tagIds'):
        from wxcloudrun.model import Tag
        tags = Tag.query.filter(Tag.id.in_(data['tagIds'])).all()
        product.tags = tags
    db.session.commit()
    return make_succ_response(product.to_dict())


@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
def admin_update_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return make_err_response('产品不存在')
    data = request.get_json()
    for field in ['product_series', 'product_name', 'product_model', 'product_desc',
                   'product_image', 'category_id', 'sort_order']:
        if field in data:
            setattr(product, field, data[field])
    if 'productImages' in data:
        product.product_images = json.dumps(data['productImages'], ensure_ascii=False)
    if 'isActive' in data:
        product.is_active = data['isActive']
    if 'tagIds' in data:
        from wxcloudrun.model import Tag
        product.tags = Tag.query.filter(Tag.id.in_(data['tagIds'])).all()
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


# --- Excel 导入 ---

@app.route('/api/admin/import', methods=['POST'])
def admin_import_excel():
    """Excel 导入：遇新产品系列/标签自动创建，重复型号自动 UPDATE"""
    data = request.get_json()
    rows = data.get('rows', [])
    imported = {'created': 0, 'updated': 0, 'errors': []}

    for i, row in enumerate(rows):
        try:
            series_name = row.get('productSeries', '').strip()
            tag_names = row.get('tags', [])  # ["烘培","糖果","饮料"]

            if not series_name or not row.get('productModel'):
                imported['errors'].append(f'第{i+2}行: 缺少产品系列或型号')
                continue

            # 自动创建/匹配产品系列
            cat = get_or_create_category(series_name)

            # 产品：按型号查重，存在则更新
            existing = get_product_by_model(row['productModel'])
            if existing:
                existing.product_name = row.get('productName', existing.product_name)
                existing.product_series = series_name
                existing.product_desc = row.get('productDesc')
                existing.category_id = cat.id
                imported['updated'] += 1
                product = existing
            else:
                product = Product(
                    product_series=series_name,
                    product_name=row.get('productName'),
                    product_model=row['productModel'],
                    product_desc=row.get('productDesc'),
                    category_id=cat.id,
                )
                db.session.add(product)
                db.session.flush()
                imported['created'] += 1

            # 自动创建/关联标签
            if tag_names:
                tags = [get_or_create_tag(name) for name in tag_names if name]
                product.tags = [t for t in tags if t]

        except Exception as e:
            imported['errors'].append(f'第{i+2}行: {str(e)}')

    db.session.commit()
    return make_succ_response(imported)


# --- 文章管理 ---

@app.route('/api/admin/articles', methods=['POST'])
def admin_create_article():
    data = request.get_json()
    article = Article(
        title=data['title'], author=data.get('author'),
        content=data['content'], cover_image=data.get('coverImage'),
        is_published=data.get('isPublished', False),
        published_at=datetime.now() if data.get('isPublished') else None,
        sort_order=data.get('sortOrder', 0),
    )
    db.session.add(article)
    db.session.commit()
    return make_succ_response(article.to_dict())


@app.route('/api/admin/articles/<int:article_id>', methods=['PUT'])
def admin_update_article(article_id):
    article = get_article_by_id(article_id)
    if not article:
        return make_err_response('文章不存在')
    data = request.get_json()
    for field in ['title', 'author', 'content', 'cover_image', 'sort_order']:
        if field in data:
            setattr(article, field, data[field])
    if 'isPublished' in data:
        article.is_published = data['isPublished']
        if data['isPublished'] and not article.published_at:
            article.published_at = datetime.now()
    db.session.commit()
    return make_succ_response(article.to_dict())


@app.route('/api/admin/articles/<int:article_id>', methods=['DELETE'])
def admin_delete_article(article_id):
    article = get_article_by_id(article_id)
    if not article:
        return make_err_response('文章不存在')
    db.session.delete(article)
    db.session.commit()
    return make_succ_empty_response()
