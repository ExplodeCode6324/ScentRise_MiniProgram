"""初始化管理员账号 — 运行一次即可"""
import bcrypt
from wxcloudrun import db, app
from wxcloudrun.model import Admin

with app.app_context():
    existing = Admin.query.filter_by(username='admin').first()
    if existing:
        print('管理员账号已存在，跳过')
    else:
        pw_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        admin = Admin(username='admin', passwd=pw_hash, real_name='管理员', role='admin', is_active=True)
        db.session.add(admin)
        db.session.commit()
        print('管理员账号创建成功！用户名：admin  密码：admin123')
