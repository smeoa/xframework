class ApiError(Exception):
    """API 调用错误"""
    def __init__(self, message: str, status: int = 502):
        self.status = status
        super().__init__(f"[{status}] {message}")


def extract_response(result: dict) -> dict:
    """从 ``process_request`` 返回值提取响应数据"""
    if "error" in result:
        err = result["error"]
        raise ApiError(
            message=err.get("message", "AI 服务调用失败"),
            status=err.get("status", 502),
        )
    if "response" not in result:
        raise ApiError("无效的响应格式", status=502)
    return result["response"]


def get_content(response: dict) -> str:
    """提取聊天补全的首条文本内容"""
    msg = (response.get("choices") or [{}])[0].get("message", {})
    return msg.get("content", "")


def get_reasoning(response: dict) -> str:
    """提取 reasoning 内容"""
    msg = (response.get("choices") or [{}])[0].get("message", {})
    return msg.get("reasoning", "")


def get_tool_calls(response: dict) -> list:
    """提取工具调用列表"""
    msg = (response.get("choices") or [{}])[0].get("message", {})
    return msg.get("tool_calls", [])


def get_usage(response: dict) -> dict:
    """提取用量统计"""
    return response.get("usage", {})
