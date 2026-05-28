"""CloudBase 云存储上传模块

通过 CloudBase Admin HTTP API 上传文件到云存储。
认证凭据通过环境变量注入（CloudRun 控制台配置）。
"""

import os
import logging
import requests

logger = logging.getLogger('log')

# CloudBase 环境配置
TCB_ENV_ID = os.environ.get('TCB_ENV_ID', 'prod-d5gzqpr0f7ac5e384')
TCB_API_KEY = os.environ.get('TCB_API_KEY', '')

# API 网关
API_BASE = f'https://{TCB_ENV_ID}.api.tcloudbasegateway.com'

# 云存储 CDN 域名（上传成功后返回的下载域名）
CDN_BASE = f'https://7072-prod-d5gzqpr0f7ac5e384-1437634411.tcb.qcloud.la'

# 请求超时
TIMEOUT = 30


def upload(file_data: bytes, cloud_path: str, content_type: str = 'image/png') -> dict:
    """上传文件到 CloudBase 云存储

    Args:
        file_data: 文件二进制内容
        cloud_path: 云存储路径，如 'company/1/logo.png'
        content_type: MIME 类型

    Returns:
        dict: {'success': True, 'url': '...', 'file_id': '...'}
              或 {'success': False, 'error': '...'}
    """
    if not TCB_API_KEY:
        logger.warning('storage.upload: TCB_API_KEY 未配置，返回占位 URL')
        return {
            'success': True,
            'url': f'{CDN_BASE}/{cloud_path}',
            'file_id': None,
            '_placeholder': True,
        }

    url = f'{API_BASE}/admin/v1/storages/upload'

    try:
        resp = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {TCB_API_KEY}',
            },
            files={
                'file': (cloud_path.rsplit('/', 1)[-1], file_data, content_type),
            },
            data={
                'path': cloud_path,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get('code'):
            logger.error(f'storage.upload failed: {result}')
            return {'success': False, 'error': result.get('message', '上传失败')}

        file_id = result.get('fileId', '')
        # CloudBase 存储的 CDN 访问 URL
        download_url = f'{CDN_BASE}/{cloud_path}'

        logger.info(f'storage.upload OK: {cloud_path} -> {file_id}')
        return {
            'success': True,
            'url': download_url,
            'file_id': file_id,
        }

    except requests.RequestException as e:
        logger.error(f'storage.upload error: {e}')
        return {'success': False, 'error': str(e)}


def get_download_url(cloud_path: str) -> str:
    """根据云存储路径构造 CDN 下载 URL"""
    return f'{CDN_BASE}/{cloud_path}'
