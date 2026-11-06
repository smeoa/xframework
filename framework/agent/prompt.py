"""框架内所有提示词的统一管理"""

from typing import Dict


class SystemPrompts:
    DOCUMENT_SUMMARY = "你是一个专业的文档总结助手，擅长分析和总结各种类型的文档内容。"

    MESSAGE_COMPRESSION = (
        "请将以下对话历史压缩为一段简洁的摘要，保留关键信息。"
        "只输出摘要内容，不要加任何前缀或解释。\n\n{text}\n\n摘要："
    )

    DOC_SUMMARY_BRIEF = """请对以下文档内容进行简要总结，输出不超过200字：

{content}

---
总结："""

    DOC_SUMMARY_DETAILED = """请对以下文档内容进行详细总结，包括主要内容、关键要点和结论：

{content}

---
详细总结："""

    DOC_SUMMARY_KEY_POINTS = """请提取以下文档内容的关键要点，用列表形式输出：

{content}

---
关键要点："""

    DOC_SUMMARY_TYPES = {
        "brief": DOC_SUMMARY_BRIEF,
        "detailed": DOC_SUMMARY_DETAILED,
        "key_points": DOC_SUMMARY_KEY_POINTS,
    }


class UserPrompts:
    IMAGE_ANALYSIS = """请对图片进行全面分析，按照以下三个维度输出：

【文字识别】：识别图片中所有可见文字，包括中文、英文、数字、符号等，保持原有格式和排版。如果没有文字，请说明"图片中未发现文字"。

【内容描述】：详细描述图片的视觉内容，包括场景、主体、颜色、构图、氛围等。

【重点标记】：识别图片中的重点元素、标记、注释、高亮区域、图表数据等关键信息。

请用自然语言清晰描述，每个维度用标题分隔。"""

    IMAGE_TEXT_OCR = """你是电商商品图片合规检查助手，只负责提取图片中出现的文字原文。要求：

1. 只输出图片中真实出现的文字，中文 / 英文 / 数字 / 符号一律原样保留，逐字提取；
2. 不要翻译、不要改写、不要补充解释，不要描述图片内容；
3. 图片中没有文字时，text 输出空字符串；
4. 只输出一行 JSON，格式为 {"text": "识别到的全部文字原文"}，不要输出任何多余字符或代码块标记。"""


class TaskPrompts:
    @staticmethod
    def task_planner(
        role: str = "",
        persona: str = "",
        task_description: str = "",
        tools_desc: str = "",
        skills_desc: str = "",
        knowledge_desc: str = "",
    ) -> str:
        """任务拆解引擎提示词"""
        return f"""你是专业的Agent任务拆解引擎。输出JSON格式的任务行动方案：

角色: {role}
人设: {persona}
任务描述: {task_description}
工具: {tools_desc or '无'}
技能: {skills_desc or '无'}
知识库摘要:
{knowledge_desc or '无'}
输出JSON（仅输出JSON，无其他内容）：
{{
  "task_overview": {{"total_tasks": N, "priority_order": ["T001",...], "global_dependency": null}},
  "task_details": [
    {{
      "task_id": "T001",
      "task_name": "...",
      "task_goal": "...",
      "dependency": []
    }}
  ],
  "global_execution_flow": {{"execution_mode": "全串行", "parallel_tasks": [], "data_flow": []}}
}}
"""

    @staticmethod
    def task_executor(task_name: str, task_goal: str) -> str:
        """任务执行提示词"""
        return f"""你正在执行任务: {task_name}
任务目标: {task_goal}

【严格输出要求】
- 仅输出 JSON 内容，不要包含任何解释、前言、markdown 标记
- 输出必须能被 json.loads() 解析
- 字段名必须严格匹配下方定义
"""


PROMPTS: Dict[str, str] = {
    "document_summary": SystemPrompts.DOCUMENT_SUMMARY,
    "message_compression": SystemPrompts.MESSAGE_COMPRESSION,
    "image_analysis": UserPrompts.IMAGE_ANALYSIS,
    "doc_summary_brief": SystemPrompts.DOC_SUMMARY_BRIEF,
    "doc_summary_detailed": SystemPrompts.DOC_SUMMARY_DETAILED,
    "doc_summary_key_points": SystemPrompts.DOC_SUMMARY_KEY_POINTS,
}
