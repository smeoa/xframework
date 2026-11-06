"""Gewe API 统一服务模块

集中管理所有与 Gewe API 的交互,提供统一的请求头、错误处理和超时控制。
"""

import logging
import asyncio
import re
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from framework.core.config import config

logger = logging.getLogger(__name__)

GEWE_API_BASE_URL = "http://api.geweapi.com"

REQUEST_TIMEOUT = 10
MAX_RETRIES = 2
CACHE_TTL = 300

CONTACT_LIST_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/fetchContactsList"
CONTACT_BRIEF_INFO_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/getBriefInfo"
CONTACT_DETAIL_INFO_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/getDetailInfo"
GROUP_MEMBER_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/getGroupMembers"
DOWNLOAD_IMAGE_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadImage"
DOWNLOAD_VOICE_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadVoice"
DOWNLOAD_FILE_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadFile"
DOWNLOAD_VIDEO_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadVideo"
DOWNLOAD_EMOJI_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadEmojiMd5"
DOWNLOAD_CDN_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/downloadCdn"
PERSONAL_INFO_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/personal/getProfile"
SEND_TEXT_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/postText"
SEND_IMAGE_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/postImage"
SEND_FILE_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/message/postFile"

GROUP_CHATROOM_INFO_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/group/getChatroomInfo"
GROUP_CHATROOM_MEMBER_LIST_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/group/getChatroomMemberList"

DELETE_CONTACT_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/deleteContact"
UPDATE_REMARK_API = f"{GEWE_API_BASE_URL}/gewe/v2/api/contacts/setRemark"


class GeweApiService:

    def __init__(self):
        self._headers = {}
        self._request_cache = {}
        self._cache_lock = asyncio.Lock()
        self._api_health = {}
        self._failed_endpoints = set()

    def get_headers(self) -> Dict[str, str]:
        return self._headers
    
    def get_failed_endpoints(self) -> set:
        return self._failed_endpoints
    
    def is_endpoint_failed(self, url: str) -> bool:
        return url in self._failed_endpoints

    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        async with self._cache_lock:
            entry = self._request_cache.get(cache_key)
            if entry:
                if datetime.now() - entry['timestamp'] < timedelta(seconds=CACHE_TTL):
                    return entry['data']
                else:
                    del self._request_cache[cache_key]
        return None

    async def _set_cached_result(self, cache_key: str, data: Any):
        async with self._cache_lock:
            self._request_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': data
            }
            if len(self._request_cache) > 100:
                oldest_key = min(self._request_cache.keys(), 
                               key=lambda k: self._request_cache[k]['timestamp'])
                del self._request_cache[oldest_key]

    async def _post(self, url: str, data: dict, use_cache: bool = False) -> Any:
        cache_key = f"{url}_{hash(str(data))}"
        
        if use_cache:
            cached = await self._get_cached_result(cache_key)
            if cached is not None:
                logger.debug(f"[GeweAPI] 缓存命中: {url}")
                return cached
        
        health = self._api_health.get(url)
        if health and not health['healthy']:
            if datetime.now() - health['last_check'] < timedelta(seconds=60):
                logger.warning(f"[GeweAPI] 接口不可用,跳过请求: {url}")
                return None
        
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"[GeweAPI] 请求: {url}")
                await asyncio.sleep(0.1)
                
                token = config.get_str("GEWE_API_TOKEN", "")
                headers = {
                    "X-GEWE-TOKEN": token,
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    response = await client.post(url, json=data, headers=headers)
                    response.raise_for_status()
                    result = response.json()
                
                self._api_health[url] = {
                    'healthy': True,
                    'last_check': datetime.now(),
                    'error': None
                }
                
                if url in self._failed_endpoints:
                    self._failed_endpoints.remove(url)
                    logger.info(f"[GeweAPI] 接口恢复正常: {url}")
                
                if use_cache:
                    await self._set_cached_result(cache_key, result)
                
                return result
            
            except asyncio.TimeoutError:
                last_error = "请求超时"
                logger.warning(f"[GeweAPI] 请求超时 ({attempt+1}/{MAX_RETRIES+1}): {url}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[GeweAPI] 请求失败 ({attempt+1}/{MAX_RETRIES+1}): {url}, error: {str(e)}")
            
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
        
        self._api_health[url] = {
            'healthy': False,
            'last_check': datetime.now(),
            'error': last_error
        }
        
        self._failed_endpoints.add(url)
        logger.error(f"[GeweAPI] 请求最终失败: {url}, error: {last_error}")
        return None

    async def fetch_contacts_list(self, app_id: str) -> List[str]:
        if not app_id:
            logger.error("[GeweAPI] app_id 未配置")
            return []
        response = await self._post(CONTACT_LIST_API, {"appId": app_id})
        if response and response.get("ret") == 200:
            friends = response.get("data", {}).get("friends", [])
            logger.info(f"[GeweAPI] 获取到 {len(friends)} 个联系人")
            return friends
        logger.warning(f"[GeweAPI] 联系人列表接口返回异常: {response}")
        return []

    async def get_brief_info(self, app_id: str, wxids: List[str]) -> List[dict]:
        if not app_id or not wxids:
            return []
        response = await self._post(CONTACT_BRIEF_INFO_API, {"appId": app_id, "wxids": wxids})
        if response and response.get("ret") == 200:
            data = response.get("data", [])
            return data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        logger.warning(f"[GeweAPI] getBriefInfo 返回异常: {response}")
        return []

    async def get_detail_info(self, app_id: str, wxids: List[str]) -> List[dict]:
        if not app_id or not wxids:
            return []
        response = await self._post(CONTACT_DETAIL_INFO_API, {"appId": app_id, "wxids": wxids})
        if response and response.get("ret") == 200:
            data = response.get("data", [])
            return data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        logger.warning(f"[GeweAPI] getDetailInfo 返回异常: {response}")
        return []

    async def download_image(self, app_id: str, xml: str, img_type: int = 2) -> str:
        if not app_id or not xml:
            return ""
        response = await self._post(DOWNLOAD_IMAGE_API, {
            "appId": app_id,
            "type": img_type,
            "xml": xml,
        })
        if response and response.get("ret") == 200:
            url = response.get("data", {}).get("fileUrl", "")
            if url:
                logger.info(f"[GeweAPI] 图片下载成功 | type={img_type}")
                return url
        logger.debug(f"[GeweAPI] 图片下载失败 | type={img_type}")
        return ""

    async def download_voice(self, app_id: str, xml: str) -> str:
        if not app_id or not xml:
            return ""
        data = {"appId": app_id, "xml": xml}
        response = await self._post(DOWNLOAD_VOICE_API, data)
        if response and response.get("ret") == 200:
            url = response.get("data", {}).get("fileUrl", "")
            if url:
                logger.info(f"[GeweAPI] 语音下载成功")
                return url
        logger.debug(f"[GeweAPI] 语音下载失败")
        return ""

    async def download_file(self, app_id: str, xml: str) -> str:
        if not app_id or not xml:
            return ""
        response = await self._post(DOWNLOAD_FILE_API, {
            "appId": app_id,
            "xml": xml,
        })
        if response and response.get("ret") == 200:
            url = response.get("data", {}).get("fileUrl", "")
            if url:
                logger.info(f"[GeweAPI] 文件下载成功")
                return url
        logger.debug(f"[GeweAPI] 文件下载官方接口失败,尝试CDN降级")
        return await self._download_file_cdn(app_id, xml)

    async def _download_file_cdn(self, app_id: str, xml: str) -> str:
        if not app_id or not xml:
            return ""
        try:
            aeskey_match = re.search(r'<aeskey>([^<]+)</aeskey>', xml, re.IGNORECASE)
            fileid_match = re.search(r'<cdnurl>([^<]+)</cdnurl>', xml, re.IGNORECASE)
            
            aes_key = aeskey_match.group(1).strip() if aeskey_match else ""
            file_id = fileid_match.group(1).strip() if fileid_match else ""

            if not file_id:
                logger.warning(f"[GeweAPI] CDN降级失败: 未找到fileId")
                return ""

            data = {"appId": app_id, "type": "5"}
            if aes_key:
                data["aesKey"] = aes_key
            if file_id:
                data["fileId"] = file_id

            response = await self._post(DOWNLOAD_CDN_API, data)
            if response and response.get("ret") == 200:
                url = response.get("data", {}).get("fileUrl", "")
                if url:
                    logger.info(f"[GeweAPI] CDN降级下载成功")
                    return url
            logger.debug(f"[GeweAPI] CDN降级下载失败")
        except Exception as e:
            logger.error(f"[GeweAPI] CDN降级下载异常: {e}")
        return ""

    async def download_video(self, app_id: str, xml: str) -> str:
        if not app_id or not xml:
            return ""
        response = await self._post(DOWNLOAD_VIDEO_API, {
            "appId": app_id,
            "xml": xml,
        })
        if response and response.get("ret") == 200:
            url = response.get("data", {}).get("fileUrl", "")
            if url:
                logger.info(f"[GeweAPI] 视频下载成功")
                return url
        logger.debug(f"[GeweAPI] 视频下载失败")
        return ""

    async def download_emoji(self, app_id: str, xml: str) -> str:
        if not app_id or not xml:
            return ""
        
        import html
        
        decoded_xml = html.unescape(xml)
        
        md5_match = re.search(r'<emoji[^>]*md5="([^"]+)"', decoded_xml, re.IGNORECASE)
        if not md5_match:
            md5_match = re.search(r'<md5>([^<]+)</md5>', decoded_xml, re.IGNORECASE)
        
        emoji_md5 = md5_match.group(1).strip() if md5_match else ""
        
        if not emoji_md5:
            logger.warning(f"[GeweAPI] 表情包下载失败: 未找到emojiMd5")
            return ""
        
        response = await self._post(DOWNLOAD_EMOJI_API, {
            "appId": app_id,
            "emojiMd5": emoji_md5,
        })
        
        if response and response.get("ret") == 200:
            url = response.get("data", {}).get("fileUrl", "")
            if url:
                logger.info(f"[GeweAPI] 表情包下载成功")
                return url
        logger.warning(f"[GeweAPI] 表情包下载失败")
        return ""

    async def fetch_friend_info(self, app_id: str, wx_id: str) -> Tuple[str, str]:
        records = await self.get_brief_info(app_id, [wx_id])
        if records:
            info = records[0] if isinstance(records, list) else records
            nickname = info.get("nickName", "") or info.get("nickname", "") or wx_id
            avatar = info.get("bigHeadImgUrl", "") or info.get("smallHeadImgUrl", "")
            return nickname, avatar
        return wx_id, ""

    async def fetch_group_info(self, app_id: str, group_id: str) -> Tuple[str, str]:
        if not app_id or not group_id:
            logger.warning(f"[GeweAPI] 获取群信息失败:参数无效")
            return group_id, ""

        logger.info(f"[GeweAPI] 尝试获取群信息")
        response = await self._post(GROUP_CHATROOM_INFO_API, {"appId": app_id, "chatroomId": group_id}, use_cache=True)

        if response:
            ret_code = response.get("ret")
            data = response.get("data", {})

            if ret_code == 200 and data:
                name = (
                    data.get("nickName", "")
                    or data.get("nickname", "")
                    or data.get("groupName", "")
                    or data.get("group_name", "")
                    or data.get("name", "")
                    or group_id
                )

                big_head = data.get("bigHeadImgUrl", "")
                small_head = data.get("smallHeadImgUrl", "")
                head_img = data.get("headImgUrl", "")
                avatar_val = data.get("avatar", "")
                avatar_url = data.get("avatarUrl", "")

                avatar = big_head or small_head or head_img or avatar_val or avatar_url or ""
                avatar = avatar.replace("http://", "https://")

                logger.info(f"[GeweAPI] 获取群信息成功 | group_id={group_id}")
                return name, avatar

        logger.info(f"[GeweAPI] 降级使用旧接口获取群信息")
        return await self._fetch_group_info_old(app_id, group_id)

    async def _fetch_group_info_old(self, app_id: str, group_id: str) -> Tuple[str, str]:
        logger.info(f"[GeweAPI] 旧接口获取群信息")
        records = await self.get_detail_info(app_id, [group_id])
        if records:
            info = records[0] if isinstance(records, list) else records
            name = info.get("nickName", "") or info.get("nickname", "") or group_id
            avatar = (info.get("bigHeadImgUrl", "") or info.get("smallHeadImgUrl", "")).replace("http://", "https://")
            logger.info(f"[GeweAPI] 旧接口获取成功")
            return name, avatar
        logger.warning(f"[GeweAPI] 旧接口获取群信息失败")
        return group_id, ""

    async def get_group_members(self, app_id: str, group_id: str) -> List[dict]:
        if not app_id or not group_id:
            return []
        
        response = await self._post(GROUP_CHATROOM_MEMBER_LIST_API, {"appId": app_id, "chatroomId": group_id}, use_cache=True)
        if response and response.get("ret") == 200:
            data = response.get("data", {})
            if isinstance(data, dict):
                members = data.get("memberList", [])
            else:
                members = data if isinstance(data, list) else []
            
            logger.info(f"[GeweAPI] 获取群成员成功 | count={len(members)}")
            return members
        
        logger.warning(f"[GeweAPI] getChatroomMemberList 返回异常,降级使用旧接口")
        return await self._get_group_members_old(app_id, group_id)

    async def _get_group_members_old(self, app_id: str, group_id: str) -> List[dict]:
        response = await self._post(GROUP_MEMBER_API, {"appId": app_id, "groupWxid": group_id}, use_cache=True)
        if response and response.get("ret") == 200:
            data = response.get("data", [])
            return data if isinstance(data, list) else []
        logger.warning(f"[GeweAPI] getGroupMembers 返回异常")
        return []

    def get_api_health_status(self) -> Dict[str, Dict]:
        status = {}
        for url, health in self._api_health.items():
            status[url] = {
                **health,
                'failed': url in self._failed_endpoints
            }
        return status
    
    def get_failed_endpoints_detail(self) -> List[Dict[str, Any]]:
        failed_details = []
        for url in self._failed_endpoints:
            health = self._api_health.get(url, {})
            failed_details.append({
                'url': url,
                'last_check': health.get('last_check'),
                'error': health.get('error'),
                'failed': True
            })
        return failed_details

    def clear_request_cache(self):
        self._request_cache.clear()
        logger.info("[GeweAPI] 请求缓存已清空")

    async def get_personal_info(self, app_id: str = None) -> dict:
        if not app_id:
            logger.error("[GeweAPI] app_id 未配置")
            return None
        response = await self._post(PERSONAL_INFO_API, {"appId": app_id})
        return response

    async def send_text_message(self, app_id: str, to_wxid: str, content: str, ats: str = None) -> dict:
        if not app_id or not to_wxid or not content:
            return None
        data = {"appId": app_id, "toWxid": to_wxid, "content": content}
        if ats:
            data["ats"] = ats
        response = await self._post(SEND_TEXT_API, data)
        if response and response.get("ret") == 200:
            return response.get("data", {})
        logger.warning(f"[GeweAPI] 发送文字消息失败")
        return None

    async def send_image_message(self, app_id: str, to_wxid: str, img_url: str) -> dict:
        if not app_id or not to_wxid or not img_url:
            return None
        response = await self._post(SEND_IMAGE_API, {"appId": app_id, "toWxid": to_wxid, "imgUrl": img_url})
        if response and response.get("ret") == 200:
            return response.get("data", {})
        logger.warning(f"[GeweAPI] 发送图片消息失败")
        return None

    async def send_file_message(self, app_id: str, to_wxid: str, file_url: str, file_name: str) -> dict:
        if not app_id or not to_wxid or not file_url or not file_name:
            return None
        response = await self._post(SEND_FILE_API, {
            "appId": app_id,
            "toWxid": to_wxid,
            "fileUrl": file_url,
            "fileName": file_name,
        })
        if response and response.get("ret") == 200:
            return response.get("data", {})
        logger.warning(f"[GeweAPI] 发送文件消息失败")
        return None

    async def delete_contact(self, app_id: str, wx_id: str) -> bool:
        if not app_id or not wx_id:
            logger.error("[GeweAPI] 删除联系人失败:参数无效")
            return False
        response = await self._post(DELETE_CONTACT_API, {"appId": app_id, "wxid": wx_id})
        if response and response.get("ret") == 200:
            logger.info(f"[GeweAPI] 删除联系人成功")
            return True
        logger.warning(f"[GeweAPI] 删除联系人失败")
        return False

    async def update_remark(self, app_id: str, wx_id: str, remark: str) -> bool:
        if not app_id or not wx_id:
            logger.error("[GeweAPI] 修改备注失败:参数无效")
            return False
        response = await self._post(UPDATE_REMARK_API, {"appId": app_id, "wxid": wx_id, "remark": remark})
        if response and response.get("ret") == 200:
            logger.info(f"[GeweAPI] 修改备注成功")
            return True
        logger.warning(f"[GeweAPI] 修改备注失败")
        return False


gewe_api_service = GeweApiService()