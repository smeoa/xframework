import logging
from typing import Any, Dict, Optional

from .ws_route import manager

logger = logging.getLogger(__name__)


async def send_message_to_user(user_id: str, message: Dict) -> bool:
    """发送消息给指定用户（同一用户可能有多个连接同时在线，需全部推送）

    用户当前无在线连接时直接返回 False，不做广播兜底：消息均按用户定向，广播会把
    与其他人无关的内容推给全部在线客户端（越权可见），并触发对方无谓的消息列表刷新；
    业务侧通知已同步落库（x_notification），用户下次打开页面可正常看到。
    """
    client_ids = manager.get_client_ids_by_user_id(user_id)
    if not client_ids:
        return False
    for client_id in client_ids:
        await manager.send_personal_message(message, client_id)
    return True


async def broadcast_message(message: Dict):
    """广播消息给所有连接的客户端"""
    await manager.broadcast(message)


async def send_task_progress(
    user_id: str,
    task_id: str,
    subtype: str,
    title: str,
    processed: int,
    total: int,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """推送后台任务进度（type={subtype}_progress），供前端展示任务进度条

    每完成一个处理单元（单个产品/单批）调用一次，前端按 task_id 更新对应进度条，收到
    {subtype}_complete / {subtype}_error 后移除。进度推送失败不影响任务主流程，仅记录日志。

    Args:
        user_id: 提交任务的用户ID
        task_id: 任务ID
        subtype: 任务类型标识（ai_tag / ai_category / pricing_rule 等）
        title: 任务中文名（用于进度文案）
        processed: 已处理产品数（累计）
        total: 本次任务产品总数
        extra: 附加进度计数（如已更新数、新匹配类目数）
    """
    try:
        total = max(int(total or 0), 0)
        processed = max(int(processed or 0), 0)
        percent = min(int(processed * 100 / total), 100) if total else 0
        data: Dict[str, Any] = {
            "task_id": task_id,
            "processed": processed,
            "product_total": total,
            "percent": percent,
        }
        if extra:
            data.update(extra)
        await send_message_to_user(
            str(user_id),
            {
                "type": f"{subtype}_progress",
                "task_id": task_id,
                "message": f"{title}进行中：已处理 {processed}/{total}",
                "data": data,
            },
        )
    except Exception as e:
        logger.error(f"任务进度推送失败 {subtype} {task_id}: {e}")
