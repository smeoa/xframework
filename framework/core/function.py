"""
通用工具函数
核心功能：提供通用的工具函数
"""


# -------------------------- 树形结构处理函数 --------------------------


from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from urllib.parse import quote


def build_content_disposition(filename: str) -> str:
    """构造兼容中文文件名的 Content-Disposition（RFC 5987）

    中文名放在 filename* 中做 UTF-8 百分号编码，并保留纯 ASCII 的 filename 兜底，
    否则响应头无法用 latin-1 编码会直接报错。
    """
    ascii_name = filename.encode("ascii", "ignore").decode().lstrip("._") or "export.xlsx"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def build_export_filename(label: str, ext: str = ".xlsx") -> str:
    """生成导出文件名：业务名称_时间戳（替代 UUID，便于用户识别）

    Args:
        label: 业务名称，如 "用户列表"
        ext: 文件扩展名，默认 ".xlsx"

    Returns:
        形如 "用户列表_20260918171600.xlsx"
    """
    return f"{label}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"


def build_tree(
    items: List[Dict[str, Any]],
    pid: Optional[Any] = None,
    processed_ids: Optional[Set[Any]] = None,
    parent_field: str = "pid",
    id_field: str = "id",
) -> List[Dict[str, Any]]:
    """构建树形结构

    Args:
        items: 扁平数据列表
        pid: 父ID，默认为None
        processed_ids: 已处理的ID集合，默认为None
        parent_field: 父ID字段名，默认为"pid"
        id_field: ID字段名，默认为"id"

    Returns:
        树形结构数据
    """
    # 初始化已处理ID集合
    if processed_ids is None:
        processed_ids = set()

    tree = []
    for item in items:
        item_id = item.get(id_field)
        item_pid = item.get(parent_field)

        # 防止循环引用导致的无限递归
        if item_id in processed_ids:
            continue

        # 同时处理 pid 为 0 和 None 的情况
        if item_pid == pid or (pid is None and (item_pid is None or item_pid == 0)):
            # 将当前ID添加到已处理集合
            current_processed = processed_ids.copy()
            current_processed.add(item_id)

            # 递归获取子部门
            children = build_tree(items, item_id, current_processed, parent_field, id_field)
            if children:
                item["children"] = children
            tree.append(item)
    return tree
