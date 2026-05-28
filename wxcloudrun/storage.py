"""CloudBase 云存储上传模块

通过 CloudBase HTTP API 两步流程上传文件到云存储：
  1. POST /v1/storages/get-objects-upload-info  获取上传 URL + 鉴权
  2. PUT 文件到返回的 COS URL

认证凭据 (TCB_API_KEY) 通过环境变量注入（CloudRun 控制台配置）。
API Key 在 TCB 控制台 → 环境设置 → API Key 管理页获取（服务端密钥）。
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

# 请求超时
TIMEOUT = 30


def upload(file_data: bytes, cloud_path: str, content_type: str = 'image/png') -> dict:
    """上传文件到 CloudBase 云存储（两步流程）

    Step 1: 获取上传信息（uploadUrl + 鉴权头）
    Step 2: PUT 文件到 COS

    Args:
        file_data: 文件二进制内容
        cloud_path: 云存储路径，如 'company/1/logo.png'
        content_type: MIME 类型

    Returns:
        dict: {'success': True, 'url': '下载URL', 'cloudObjectId': 'cloud://...'}
              或 {'success': False, 'error': '...'}
    """
    if not TCB_API_KEY:
        logger.warning('storage.upload: TCB_API_KEY 未配置，返回占位 URL')
        cdn = f'https://7072-prod-d5gzqpr0f7ac5e384-1437634411.tcb.qcloud.la'
        return {
            'success': True,
            'url': f'{cdn}/{cloud_path}',
            'cloudObjectId': None,
            '_placeholder': True,
        }

    # --- Step 1: 获取上传信息 ---
    step1_url = f'{API_BASE}/v1/storages/get-objects-upload-info'

    try:
        resp = requests.post(
            step1_url,
            headers={
                'Authorization': f'Bearer {TCB_API_KEY}',
                'Content-Type': 'application/json',
            },
            json=[{'objectId': cloud_path}],
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json()

        if not isinstance(results, list) or len(results) == 0:
            logger.error(f'storage.upload step1: 非预期响应格式 {results}')
            return {'success': False, 'error': '获取上传信息失败：响应格式异常'}

        info = results[0]
        if 'code' in info and info.get('code'):
            logger.error(f'storage.upload step1 failed: {info}')
            return {'success': False, 'error': info.get('message', '获取上传信息失败')}

        upload_url = info.get('uploadUrl')
        authorization = info.get('authorization')
        token = info.get('token')
        cloud_meta = info.get('cloudObjectMeta')
        download_url = info.get('downloadUrl')
        cloud_object_id = info.get('cloudObjectId')

        if not upload_url:
            logger.error(f'storage.upload step1: 缺少 uploadUrl, {info}')
            return {'success': False, 'error': '获取上传信息失败：缺少上传地址'}

        logger.info(f'storage.upload step1 OK: {cloud_path} -> uploadUrl ready')

    except requests.RequestException as e:
        logger.error(f'storage.upload step1 error: {e}')
        return {'success': False, 'error': f'获取上传信息网络错误: {str(e)}'}

    # --- Step 2: PUT 文件到 COS ---
    try:
        put_headers = {
            'Authorization': authorization,
            'X-Cos-Security-Token': token,
            'X-Cos-Meta-Fileid': cloud_meta,
            'Content-Type': content_type,
        }

        put_resp = requests.put(
            upload_url,
            headers=put_headers,
            data=file_data,
            timeout=TIMEOUT,
        )

        if put_resp.status_code not in (200, 204):
            logger.error(f'storage.upload step2 failed: HTTP {put_resp.status_code} {put_resp.text[:500]}')
            return {'success': False, 'error': f'文件上传失败: HTTP {put_resp.status_code}'}

        logger.info(f'storage.upload OK: {cloud_path} -> {download_url}')
        return {
            'success': True,
            'url': download_url,
            'cloudObjectId': cloud_object_id,
        }

    except requests.RequestException as e:
        logger.error(f'storage.upload step2 error: {e}')
        return {'success': False, 'error': f'文件上传网络错误: {str(e)}'}


def get_download_url(cloud_path: str) -> str:
    """根据云存储路径构造 CDN 下载 URL（仅用于无 API Key 场景的占位 URL）"""
    cdn = f'https://7072-prod-d5gzqpr0f7ac5e384-1437634411.tcb.qcloud.la'
    return f'{cdn}/{cloud_path}'
