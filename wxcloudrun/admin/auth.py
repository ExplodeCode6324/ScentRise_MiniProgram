"""JWT 认证装饰器"""
import jwt
import os
from functools import wraps
from flask import request, g
from wxcloudrun.response import make_err_response

JWT_SECRET = os.environ.get('JWT_SECRET', 'scentrise-admin-secret-2026')
JWT_ALGORITHM = 'HS256'
JWT_EXP_HOURS = 24


def generate_token(admin_id, username, role='editor'):
    """生成 JWT token"""
    import datetime
    payload = {
        'admin_id': admin_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_admin(f):
    """装饰器：验证 JWT，注入 g.admin_id"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return make_err_response('未登录或 token 无效'), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            g.admin_id = payload['admin_id']
            g.admin_username = payload['username']
            g.admin_role = payload.get('role', 'editor')
        except jwt.ExpiredSignatureError:
            return make_err_response('登录已过期，请重新登录'), 401
        except jwt.InvalidTokenError:
            return make_err_response('token 无效'), 401
        return f(*args, **kwargs)
    return decorated
