from datetime import datetime
from wxcloudrun import db


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column('createdAt', db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column('updatedAt', db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'icon': self.icon, 'sortOrder': self.sort_order}


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    model = db.Column(db.String(100))
    price = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    spec = db.Column(db.String(200))
    origin = db.Column(db.String(100))
    description = db.Column(db.Text)
    images = db.Column(db.Text)
    custom_fields = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'))
    created_at = db.Column('createdAt', db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column('updatedAt', db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        import json
        return {
            'id': self.id, 'name': self.name, 'model': self.model,
            'price': self.price, 'brand': self.brand, 'spec': self.spec,
            'origin': self.origin, 'description': self.description,
            'images': json.loads(self.images) if self.images else [],
            'customFields': json.loads(self.custom_fields) if self.custom_fields else [],
            'isActive': self.is_active, 'sortOrder': self.sort_order,
            'categoryId': self.category_id,
        }


class Collection(db.Model):
    __tablename__ = 'collections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cover_image = db.Column(db.String(500))
    description = db.Column(db.Text)
    is_carousel = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    carousel_sort = db.Column(db.Integer, default=0)
    created_at = db.Column('createdAt', db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column('updatedAt', db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    products = db.relationship('Product', backref='collection', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'coverImage': self.cover_image,
            'description': self.description, 'isCarousel': self.is_carousel,
            'sortOrder': self.sort_order, 'carouselSort': self.carousel_sort,
        }


class CompanyInfo(db.Model):
    __tablename__ = 'company_info'
    id = db.Column(db.Integer, primary_key=True)
    logo = db.Column(db.String(500))
    name = db.Column(db.String(200))
    intro = db.Column(db.Text)
    phone = db.Column(db.String(20))
    wechat_qr = db.Column(db.String(500))
    wechat_id = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.String(500))
    business_hours = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id, 'logo': self.logo, 'name': self.name,
            'intro': self.intro, 'phone': self.phone, 'wechatQr': self.wechat_qr,
            'wechatId': self.wechat_id, 'email': self.email,
            'address': self.address, 'businessHours': self.business_hours,
        }
