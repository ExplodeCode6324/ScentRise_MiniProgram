"""微信云开发 云存储上传模块

通过微信 HTTP API 两步流程上传文件到云存储：
  1. POST api.weixin.qq.com/tcb/uploadfile  获取上传链接 + 鉴权信息
  2. POST multipart/form-data 到 COS URL

Access Token 获取：优先读环境变量 WECHAT_ACCESS_TOKEN，
否则通过 WECHAT_APPID + WECHAT_APPSECRET 调用 /cgi-bin/token 获取（自动缓存刷新）。
"""

import os
import time
import logging
import requests

logger = logging.getLogger('log')

# CloudBase 环境配置
TCB_ENV_ID = os.environ.get('TCB_ENV_ID', 'prod-d5gzqpr0f7ac5e384')

# 微信 Access Token
WECHAT_APPID = os.environ.get('WECHAT_APPID', '')
WECHAT_APPSECRET = os.environ.get('WECHAT_APPSECRET', '')
WECHAT_ACCESS_TOKEN = os.environ.get('WECHAT_ACCESS_TOKEN', '')

# 请求超时
TIMEOUT = 30

# --- Token 缓存 ---
_cached_token = None
_cached_token_expires = 0


def _get_access_token() -> str:
    """获取微信 access_token，带缓存和自动刷新"""
    global _cached_token, _cached_token_expires

    # 如果环境变量直接提供了 token，优先使用
    if WECHAT_ACCESS_TOKEN:
        return WECHAT_ACCESS_TOKEN

    # 检查缓存
    now = time.time()
    if _cached_token and now < _cached_token_expires - 300:
        return _cached_token

    # 通过 AppID/Secret 获取
    if not WECHAT_APPID or not WECHAT_APPSECRET:
        raise RuntimeError(
            '缺少微信凭证：请设置 WECHAT_ACCESS_TOKEN 或 '
            'WECHAT_APPID + WECHAT_APPSECRET 环境变量'
        )

    resp = requests.get(
        'https://api.weixin.qq.com/cgi-bin/token',
        params={
            'grant_type': 'client_credential',
            'appid': WECHAT_APPID,
            'secret': WECHAT_APPSECRET,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    if 'errcode' in data and data['errcode'] != 0:
        raise RuntimeError(
            f'获取 access_token 失败: [{data["errcode"]}] {data.get("errmsg", "")}'
        )

    _cached_token = data['access_token']
    _cached_token_expires = now + data.get('expires_in', 7200)
    logger.info('access_token refreshed, expires in %ds', data.get('expires_in', 7200))
    return _cached_token


def upload(file_data: bytes, cloud_path: str, content_type: str = 'image/png') -> dict:
    """上传文件到微信云开发云存储

    Step 1: POST /tcb/uploadfile 获取 COS 上传信息
    Step 2: POST multipart/form-data 到 COS

    Args:
        file_data: 文件二进制内容
        cloud_path: 云存储路径，如 'company/1/logo.png'
        content_type: MIME 类型

    Returns:
        dict: {'success': True, 'url': 'cloud://...', 'cloudPath': '...'}
              或 {'success': False, 'error': '...'}
    """
    try:
        access_token = _get_access_token()
    except RuntimeError as e:
        logger.warning('storage.upload: 无法获取 access_token: %s', e)
        # 无 token 时返回占位 URL（开发环境降级）
        return {
            'success': True,
            'url': f'cloud://{TCB_ENV_ID}.0/{cloud_path}',
            'cloudPath': cloud_path,
            '_placeholder': True,
        }

    # --- Step 1: 获取 COS 上传信息 ---
    step1_url = 'https://api.weixin.qq.com/tcb/uploadfile'

    try:
        resp = requests.post(
            step1_url,
            params={'access_token': access_token},
            json={
                'env': TCB_ENV_ID,
                'path': cloud_path,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        info = resp.json()

        errcode = info.get('errcode', -1)
        if errcode != 0:
            logger.error('storage.upload step1 failed: [%s] %s', errcode, info.get('errmsg', ''))
            return {'success': False, 'error': f'获取上传链接失败: [{errcode}] {info.get("errmsg", "")}'}

        upload_url = info.get('url')
        token = info.get('token')
        authorization = info.get('authorization')
        cos_file_id = info.get('cos_file_id')
        file_id = info.get('file_id')

        if not upload_url:
            logger.error('storage.upload step1: 缺少 url, %s', info)
            return {'success': False, 'error': '获取上传链接失败：缺少上传地址'}

        logger.info('storage.upload step1 OK: %s -> uploadUrl ready', cloud_path)

    except requests.RequestException as e:
        logger.error('storage.upload step1 error: %s', e)
        return {'success': False, 'error': f'获取上传链接网络错误: {str(e)}'}

    # --- Step 2: POST 文件到 COS ---
    try:
        put_resp = requests.post(
            upload_url,
            files={'file': (cloud_path.rsplit('/', 1)[-1], file_data, content_type)},
            data={
                'key': cloud_path,
                'Signature': authorization,
                'x-cos-security-token': token,
                'x-cos-meta-fileid': cos_file_id,
            },
            timeout=TIMEOUT,
        )

        if put_resp.status_code not in (200, 204):
            logger.error('storage.upload step2 failed: HTTP %d %s',
                         put_resp.status_code, put_resp.text[:500])
            return {'success': False, 'error': f'文件上传到COS失败: HTTP {put_resp.status_code}'}

        logger.info('storage.upload OK: %s -> %s', cloud_path, file_id)
        # 构造 CDN 直链（网页端可直接访问，需存储桶开通公共读）
        cdn = f'https://7072-prod-d5gzqpr0f7ac5e384-1437634411.tcb.qcloud.la'
        cdn_url = f'{cdn}/{cloud_path}'
        return {
            'success': True,
            'url': cdn_url,           # CDN HTTP 地址，网页端 <img> 可用
            'fileId': file_id,        # cloud:// 格式，供小程序/API 调用
            'cloudPath': cloud_path,
        }

    except requests.RequestException as e:
        logger.error('storage.upload step2 error: %s', e)
        return {'success': False, 'error': f'文件上传网络错误: {str(e)}'}


def get_download_url(cloud_path_or_fileid: str) -> str:
    """根据 cloud://file_id 或路径构造下载 URL

    返回 cloud:// 格式的 file_id（前端组件直接可用），
    或 CDN 直链（需存储桶配置公共读）。
    """
    if cloud_path_or_fileid.startswith('cloud://'):
        return cloud_path_or_fileid

    # 没有 file_id 时用 CDN 兜底
    cdn = f'https://7072-prod-d5gzqpr0f7ac5e384-1437634411.tcb.qcloud.la'
    return f'{cdn}/{cloud_path_or_fileid}'
