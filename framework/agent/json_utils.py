"""JSON 解析与提取工具模块

提供 LLM 输出 JSON 内容的鲁棒解析能力：
- 自动去除 markdown 标记
- 从混合文本中提取 JSON
- 修复常见的 JSON 格式问题
"""

import json
import re
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


def parse_json_safely(content: str) -> Optional[Any]:
    """安全解析 JSON 字符串

    Args:
        content: 待解析的字符串

    Returns:
        解析后的对象，失败返回 None
    """
    if not content or not isinstance(content, str):
        return None

    content = content.strip()
    if not content:
        return None

    # 1. 直接尝试解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. 尝试去除 markdown 代码块标记
    cleaned = _strip_markdown(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. 尝试从文本中提取 JSON 片段
    extracted = extract_json_from_text(content)
    if extracted is not None:
        return extracted

    return None


def _strip_markdown(content: str) -> str:
    """去除 markdown 代码块标记"""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def extract_json_from_text(content: str) -> Optional[Any]:
    """从混合文本中提取 JSON 内容

    支持提取以下格式：
    - 纯 JSON 对象/数组
    - markdown 包裹的 JSON
    - 文本中嵌入的 JSON
    - 单引号 JSON（修复为双引号）

    Args:
        content: 包含 JSON 的文本

    Returns:
        解析后的对象，未找到返回 None
    """
    if not content or not isinstance(content, str):
        return None

    # 1. 处理 markdown 代码块
    md_match = re.search(
        r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL
    )
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. 寻找最外层的 JSON 对象
    obj_match = _find_balanced_json(content, start_char="{", end_char="}")
    if obj_match is not None:
        try:
            return json.loads(obj_match)
        except json.JSONDecodeError:
            pass

    # 3. 寻找最外层的 JSON 数组
    arr_match = _find_balanced_json(content, start_char="[", end_char="]")
    if arr_match is not None:
        try:
            return json.loads(arr_match)
        except json.JSONDecodeError:
            pass

    # 4. 尝试修复单引号 JSON
    fixed = _fix_single_quotes(content)
    if fixed != content:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    return None


def _find_balanced_json(content: str, start_char: str, end_char: str) -> Optional[str]:
    """从文本中查找平衡的 JSON 块

    Args:
        content: 文本内容
        start_char: 起始字符（'{' 或 '['）
        end_char: 结束字符（'}' 或 ']'）

    Returns:
        找到的 JSON 字符串，未找到返回 None
    """
    start_idx = content.find(start_char)
    if start_idx == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    string_char = None

    for i in range(start_idx, len(content)):
        ch = content[i]

        if escape_next:
            escape_next = False
            continue

        if in_string:
            if ch == "\\":
                escape_next = True
            elif ch == string_char:
                in_string = False
            continue

        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            continue

        if ch == start_char:
            depth += 1
        elif ch == end_char:
            depth -= 1
            if depth == 0:
                return content[start_idx : i + 1]

    return None


def _fix_single_quotes(content: str) -> str:
    """将内容中的单引号替换为双引号（用于修复非标准 JSON）

    仅在看起来像 JSON 但使用单引号时进行替换。
    """
    # 仅当内容看起来是 JSON 时才尝试修复
    stripped = content.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return content

    # 简单替换：在 {、[、,、: 之后的单引号转为双引号
    # 这里采用保守策略，只对最外层进行替换
    result = []
    in_string = False
    string_char = None
    prev_char = ""

    for ch in content:
        if not in_string and ch == "'":
            # 字符串外的单引号不应出现，跳过
            result.append('"')
            in_string = True
            string_char = '"'
            continue
        elif in_string and ch == "'" and string_char == '"':
            # 字符串内遇到的单引号，视为字符串结束
            result.append('"')
            in_string = False
            continue
        elif in_string and ch == '"' and string_char == '"':
            # 字符串内的双引号需要转义
            result.append('\\"')
            continue

        result.append(ch)
        prev_char = ch

    return "".join(result)


def is_valid_json(content: str) -> bool:
    """检查字符串是否为合法 JSON"""
    return parse_json_safely(content) is not None
