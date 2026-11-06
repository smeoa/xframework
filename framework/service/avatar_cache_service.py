"""头像缓存服务模块

提供好友和群聊头像的缓存管理，缓存未命中时自动从API获取。

缓存策略：
- 私聊(好友): 优先从好友缓存获取，未命中时从 getBriefInfo API 获取
- 群聊成员: 优先从群成员缓存获取，未命中时从 getChatroomMemberList API 获取
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from threading import Lock

from framework.core.config import config

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    nickname: str
    avatar: str
    timestamp: float

    def is_expired(self, ttl: int) -> bool:
        return time.time() - self.timestamp > ttl


class FriendAvatarCache:
    """好友头像缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._max_size = max_size
        self._ttl = ttl
        self._hit_count = 0
        self._miss_count = 0

    async def get(self, wx_id: str) -> Optional[Tuple[str, str]]:
        """获取缓存的好友信息"""
        with self._lock:
            entry = self._cache.get(wx_id)
            if entry and not entry.is_expired(self._ttl):
                self._hit_count += 1
                return (entry.nickname, entry.avatar)
            self._miss_count += 1
            return None

    async def set(self, wx_id: str, nickname: str, avatar: str):
        """设置缓存的好友信息"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                del self._cache[oldest_key]
            self._cache[wx_id] = CacheEntry(nickname, avatar, time.time())

    async def delete(self, wx_id: str):
        """删除缓存"""
        with self._lock:
            if wx_id in self._cache:
                del self._cache[wx_id]

    async def clear(self, confirm: str = "") -> bool:
        """清空缓存"""
        if confirm != "CONFIRM":
            return False
        with self._lock:
            self._cache.clear()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.2f}%",
        }


class GroupAvatarCache:
    """群聊头像缓存"""

    def __init__(self, max_size: int = 500, ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._max_size = max_size
        self._ttl = ttl
        self._hit_count = 0
        self._miss_count = 0

    async def get(self, group_id: str) -> Optional[Tuple[str, str]]:
        """获取缓存的群聊信息"""
        with self._lock:
            entry = self._cache.get(group_id)
            if entry and not entry.is_expired(self._ttl):
                self._hit_count += 1
                return (entry.nickname, entry.avatar)
            self._miss_count += 1
            return None

    async def set(self, group_id: str, nickname: str, avatar: str):
        """设置缓存的群聊信息"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                del self._cache[oldest_key]
            self._cache[group_id] = CacheEntry(nickname, avatar, time.time())

    async def delete(self, group_id: str):
        """删除缓存"""
        with self._lock:
            if group_id in self._cache:
                del self._cache[group_id]

    async def clear(self, confirm: str = "") -> bool:
        """清空缓存"""
        if confirm != "CONFIRM":
            return False
        with self._lock:
            self._cache.clear()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.2f}%",
        }


class GroupMemberCache:
    """群成员缓存"""

    def __init__(self, max_size: int = 200, ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._member_cache: Dict[str, Dict[str, Tuple[str, str]]] = {}
        self._lock = Lock()
        self._member_lock = asyncio.Lock()
        self._max_size = max_size
        self._ttl = ttl
        self._member_hit_count = 0
        self._member_miss_count = 0

    async def get_members(self, group_id: str) -> Optional[Dict[str, Tuple[str, str]]]:
        """获取缓存的群成员信息"""
        async with self._member_lock:
            entry = self._cache.get(group_id)
            if entry and not entry.is_expired(self._ttl):
                self._member_hit_count += 1
                return self._member_cache.get(group_id)
            self._member_miss_count += 1
            return None

    async def set_members(self, group_id: str, members: Dict[str, Tuple[str, str]]):
        """设置缓存的群成员信息"""
        async with self._member_lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                del self._cache[oldest_key]
                if oldest_key in self._member_cache:
                    del self._member_cache[oldest_key]
            self._cache[group_id] = CacheEntry("", "", time.time())
            self._member_cache[group_id] = members

    async def update_member_info(self, group_id: str, member_wxid: str, nickname: str, avatar: str):
        """更新单个成员信息"""
        async with self._member_lock:
            if group_id in self._member_cache:
                self._member_cache[group_id][member_wxid] = (nickname, avatar)

    async def batch_get_member_info(self, group_id: str, member_wxids: List[str]) -> Dict[str, Tuple[str, str]]:
        """批量获取成员信息"""
        result = {}
        members = await self.get_members(group_id)
        if members:
            for wxid in member_wxids:
                if wxid in members:
                    result[wxid] = members[wxid]
        return result

    async def delete_members(self, group_id: str):
        """删除群成员缓存"""
        async with self._member_lock:
            if group_id in self._cache:
                del self._cache[group_id]
            if group_id in self._member_cache:
                del self._member_cache[group_id]

    async def clear(self, confirm: str = "") -> bool:
        """清空缓存"""
        if confirm != "CONFIRM":
            return False
        async with self._member_lock:
            self._cache.clear()
            self._member_cache.clear()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._member_hit_count + self._member_miss_count
        hit_rate = (self._member_hit_count / total * 100) if total > 0 else 0
        total_members = sum(len(members) for members in self._member_cache.values())
        return {
            "cache_name": "GroupMemberCache",
            "cache_size": len(self._member_cache),
            "total_members": total_members,
            "max_size": self._max_size,
            "hit_count": self._member_hit_count,
            "miss_count": self._member_miss_count,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.2f}%",
        }

    async def cleanup_expired(self):
        """清理过期的群成员缓存"""
        async with self._member_lock:
            expired_groups = []
            for group_id, entry in self._cache.items():
                if entry.is_expired(self._ttl):
                    expired_groups.append(group_id)
            for group_id in expired_groups:
                del self._cache[group_id]
                if group_id in self._member_cache:
                    del self._member_cache[group_id]
            if expired_groups:
                logger.info(f"[缓存] GroupMember 清理过期缓存, 共 {len(expired_groups)} 个群")


class AvatarCacheService:
    """头像缓存服务

    提供好友和群聊头像的缓存管理，缓存未命中时自动从API获取。

    缓存策略：
    - 私聊(好友): 优先从好友缓存获取，未命中时从 getBriefInfo API 获取
    - 群聊成员: 优先从群成员缓存获取，未命中时从 getChatroomMemberList API 获取
    """

    def __init__(self):
        self.friend_cache = FriendAvatarCache()
        self.group_cache = GroupAvatarCache()
        self.group_member_cache = GroupMemberCache()

    async def get_friend_info(self, wx_id: str, msg_data: dict = None) -> Tuple[str, str]:
        """获取好友(私聊)信息

        优先从缓存获取，缓存未命中时从 /gewe/v2/api/contacts/getBriefInfo 获取。

        Args:
            wx_id: 好友微信ID
            msg_data: 消息数据(包含app_id等信息)

        Returns:
            (nickname, avatar)
        """
        cached = await self.friend_cache.get(wx_id)
        if cached:
            logger.debug(f"[缓存] 好友缓存命中 | wx_id={wx_id}")
            return cached

        logger.info(f"[缓存] 好友缓存未命中, 从API获取: {wx_id}")

        nickname, avatar = wx_id, ""

        if msg_data:
            app_id = config.get("GEWE_APP_ID", "")
            if app_id:
                try:
                    from framework.service.gewe_api_service import gewe_api_service
                    records = await gewe_api_service.get_brief_info(app_id, [wx_id])
                    if records and isinstance(records, list) and len(records) > 0:
                        info = records[0]
                        nickname = self._extract_nickname(info) or wx_id
                        avatar = self._extract_avatar(info)
                        logger.info(f"[缓存] 从getBriefInfo获取好友信息成功 | wx_id={wx_id}")
                except Exception as e:
                    logger.error(f"[缓存] 从getBriefInfo获取好友信息失败: {str(e)}")

        if nickname or avatar:
            await self.friend_cache.set(wx_id, nickname, avatar)

        return nickname, avatar

    async def get_group_info(self, group_id: str, msg_data: dict = None) -> Tuple[str, str]:
        """获取群聊信息"""
        cached = await self.group_cache.get(group_id)
        if cached:
            return cached

        logger.info(f"[缓存] 群聊头像缓存未命中, 从API获取: {group_id}")

        group_name, avatar = group_id, ""
        if msg_data:
            app_id = config.get("GEWE_APP_ID", "")
            if app_id:
                try:
                    from framework.service.gewe_api_service import gewe_api_service
                    group_name, avatar = await gewe_api_service.fetch_group_info(app_id, group_id)
                except Exception as e:
                    logger.error(f"[缓存] 获取群信息失败: {str(e)}")

        if group_name or avatar:
            await self.group_cache.set(group_id, group_name, avatar)
        return group_name, avatar

    async def refresh_friend_info(self, wx_id: str, msg_data: dict = None) -> Tuple[str, str]:
        """刷新好友信息(强制重新获取)"""
        await self.friend_cache.delete(wx_id)
        return await self.get_friend_info(wx_id, msg_data)

    async def refresh_group_info(self, group_id: str, msg_data: dict = None) -> Tuple[str, str]:
        """刷新群聊信息(强制重新获取)"""
        await self.group_cache.delete(group_id)
        return await self.get_group_info(group_id, msg_data)

    async def get_group_member_info(self, group_id: str, member_wxid: str) -> Tuple[str, str]:
        """获取群成员信息

        优先从缓存获取，缓存未命中时从 /gewe/v2/api/group/getChatroomMemberList 获取。

        Args:
            group_id: 群聊ID
            member_wxid: 群成员微信ID

        Returns:
            (nickname, avatar)
        """
        cached_members = await self.group_member_cache.get_members(group_id)
        if cached_members and member_wxid in cached_members:
            logger.debug(f"[缓存] 群成员缓存命中 | group_id={group_id} | member={member_wxid}")
            return cached_members[member_wxid]

        logger.info(f"[缓存] 群成员缓存未命中, 从API获取: group={group_id}, member={member_wxid}")

        app_id = config.get("GEWE_APP_ID", "")
        if not app_id or not group_id:
            logger.warning(f"[缓存] 群成员获取失败 | app_id或group_id为空 | app_id={app_id}, group_id={group_id}")
            return member_wxid, ""

        try:
            from framework.service.gewe_api_service import gewe_api_service
            members = await gewe_api_service.get_group_members(app_id, group_id)
            if members:
                member_dict = {}
                for member in members:
                    wx_id = member.get("wxid") or member.get("userName") or member.get("userId") or ""
                    if wx_id:
                        nickname = member.get("nickName") or member.get("nickname") or wx_id
                        avatar = member.get("bigHeadImgUrl") or member.get("smallHeadImgUrl") or member.get("headImgUrl") or ""
                        member_dict[wx_id] = (nickname, avatar)

                await self.group_member_cache.set_members(group_id, member_dict)
                logger.info(f"[缓存] 从getChatroomMemberList获取群成员成功 | group_id={group_id} | count={len(member_dict)}")

                if member_wxid in member_dict:
                    return member_dict[member_wxid]
        except Exception as e:
            logger.error(f"[缓存] 从getChatroomMemberList获取群成员失败: {str(e)}")

        return member_wxid, ""

    async def clear_all(self, confirm: str) -> bool:
        """清空所有缓存"""
        friend_ok = await self.friend_cache.clear(confirm)
        group_ok = await self.group_cache.clear(confirm)
        member_ok = await self.group_member_cache.clear(confirm)
        return friend_ok and group_ok and member_ok

    async def warm_up_from_db(self):
        """从数据库预热缓存"""
        try:
            from admin.models import ContactModel
            contact_model = ContactModel()
            result = await contact_model.get_list(
                filter=[{
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }],
                fields="wx_id, wx_nickname, wx_avatar",
            )
            contacts = result.get("items", []) if isinstance(result, dict) else (result or [])
            for c in contacts:
                if c.get("wx_id"):
                    await self.friend_cache.set(c["wx_id"], c.get("wx_nickname", ""), c.get("wx_avatar", ""))
            logger.info(f"[缓存预热] 联系人缓存完成, 共 {len(contacts)} 条")
        except Exception as e:
            logger.error(f"[缓存预热] 联系人缓存失败: {str(e)}")

        try:
            from admin.models import ConversationModel
            conv_model = ConversationModel()
            result = await conv_model.get_list(
                filter=[{
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "is_group", "operator": "eq", "value": 1},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }],
                fields="wx_id, wx_nickname, wx_avatar",
            )
            groups = result.get("items", []) if isinstance(result, dict) else (result or [])
            for g in groups:
                if g.get("wx_id"):
                    await self.group_cache.set(g["wx_id"], g.get("wx_nickname", ""), g.get("wx_avatar", ""))
            logger.info(f"[缓存预热] 群聊缓存完成, 共 {len(groups)} 条")
        except Exception as e:
            logger.error(f"[缓存预热] 群聊缓存失败: {str(e)}")

    async def batch_get_group_member_info(self, group_id: str, member_wxids: list) -> Dict[str, Tuple[str, str]]:
        """批量获取多个群成员信息"""
        return await self.group_member_cache.batch_get_member_info(group_id, member_wxids)

    async def set_group_members(self, group_id: str, members: Dict[str, Tuple[str, str]]):
        """设置群成员列表"""
        await self.group_member_cache.set_members(group_id, members)

    async def delete_group_members(self, group_id: str):
        """删除群成员缓存"""
        await self.group_member_cache.delete_members(group_id)

    async def cleanup_expired_caches(self):
        """清理所有过期缓存"""
        await self.group_member_cache.cleanup_expired()

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            "friend_cache": self.friend_cache.get_stats(),
            "group_cache": self.group_cache.get_stats(),
            "group_member_cache": self.group_member_cache.get_stats(),
        }

    def _extract_nickname(self, info: dict) -> str:
        """从信息中提取昵称"""
        return info.get("nickname") or info.get("wx_nickname") or info.get("userName") or info.get("displayName") or ""

    def _extract_group_name(self, info: dict) -> str:
        """从信息中提取群名"""
        return info.get("nickName") or info.get("groupName") or info.get("nickname") or info.get("wx_nickname") or ""

    def _extract_avatar(self, info: dict) -> str:
        """从信息中提取头像"""
        return info.get("bigHeadImgUrl") or info.get("smallHeadImgUrl") or info.get("headImgUrl") or info.get("avatar") or info.get("wx_avatar") or ""

    async def refresh_group_member_info(self, group_id: str, member_wxid: str) -> Tuple[str, str]:
        """强制刷新群成员信息"""
        logger.info(f"[缓存] 强制刷新群成员信息 | group_id={group_id} | member={member_wxid}")
        await self.group_member_cache.delete_members(group_id)
        return await self.get_group_member_info(group_id, member_wxid)


# 创建全局缓存服务实例
avatar_cache_service = AvatarCacheService()

# 保留原有的全局实例以便向后兼容
friend_avatar_cache = avatar_cache_service.friend_cache
group_avatar_cache = avatar_cache_service.group_cache
