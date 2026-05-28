"""Admin Blueprint — 后管 SPA 静态页面 + 文件服务"""
from flask import Blueprint, render_template, send_from_directory
import os

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin/static',
    url_prefix='/admin'
)


@admin_bp.route('/')
def admin_index():
    """后管入口 — 返回 SPA index.html"""
    return render_template('index.html')


@admin_bp.route('/<path:filename>')
def admin_static(filename):
    """后管静态文件（JS/CSS/图片）"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)
