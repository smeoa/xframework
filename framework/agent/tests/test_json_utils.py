"""JSON 工具模块单元测试"""
import pytest
from framework.agent.json_utils import (
    parse_json_safely,
    extract_json_from_text,
    is_valid_json,
)


class TestParseJsonSafely:
    """测试 parse_json_safely 函数"""

    def test_pure_json_object(self):
        """测试纯 JSON 对象"""
        content = '{"name": "test", "value": 123}'
        result = parse_json_safely(content)
        assert result == {"name": "test", "value": 123}

    def test_pure_json_array(self):
        """测试纯 JSON 数组"""
        content = '[1, 2, 3, "test"]'
        result = parse_json_safely(content)
        assert result == [1, 2, 3, "test"]

    def test_markdown_json_block(self):
        """测试 markdown 包裹的 JSON"""
        content = '```json\n{"name": "test"}\n```'
        result = parse_json_safely(content)
        assert result == {"name": "test"}

    def test_markdown_plain_block(self):
        """测试无标记的 markdown 代码块"""
        content = '```\n{"name": "test"}\n```'
        result = parse_json_safely(content)
        assert result == {"name": "test"}

    def test_json_embedded_in_text(self):
        """测试嵌入在文本中的 JSON"""
        content = '这是结果：{"name": "test", "value": 42} 请参考。'
        result = parse_json_safely(content)
        assert result == {"name": "test", "value": 42}

    def test_json_with_newlines(self):
        """测试多行 JSON"""
        content = """{
            "name": "test",
            "values": [1, 2, 3],
            "nested": {
                "key": "value"
            }
        }"""
        result = parse_json_safely(content)
        assert result is not None
        assert result["name"] == "test"
        assert result["values"] == [1, 2, 3]
        assert result["nested"]["key"] == "value"

    def test_empty_content(self):
        """测试空内容"""
        assert parse_json_safely("") is None
        assert parse_json_safely("   ") is None
        assert parse_json_safely(None) is None

    def test_invalid_content(self):
        """测试无效内容"""
        assert parse_json_safely("not a json") is None
        assert parse_json_safely("{name: test}") is None  # 缺少引号

    def test_nested_json(self):
        """测试嵌套 JSON"""
        content = '{"outer": {"inner": {"deep": "value"}}, "list": [{"a": 1}, {"b": 2}]}'
        result = parse_json_safely(content)
        assert result is not None
        assert result["outer"]["inner"]["deep"] == "value"
        assert result["list"][1]["b"] == 2


class TestExtractJsonFromText:
    """测试 extract_json_from_text 函数"""

    def test_extract_object(self):
        """测试提取 JSON 对象"""
        content = '前缀 {"key": "value"} 后缀'
        result = extract_json_from_text(content)
        assert result == {"key": "value"}

    def test_extract_array(self):
        """测试提取 JSON 数组"""
        content = '前缀 [1, 2, 3] 后缀'
        result = extract_json_from_text(content)
        assert result == [1, 2, 3]

    def test_extract_markdown_block(self):
        """测试从 markdown 块提取"""
        content = '说明：\n```json\n{"a": 1}\n```\n结束'
        result = extract_json_from_text(content)
        assert result == {"a": 1}

    def test_extract_complex_object(self):
        """测试提取复杂 JSON"""
        content = '结果：{"a": [1, 2], "b": {"c": "test"}} 结束'
        result = extract_json_from_text(content)
        assert result == {"a": [1, 2], "b": {"c": "test"}}

    def test_no_json_found(self):
        """测试无 JSON 内容"""
        content = '这里没有 JSON 内容'
        result = extract_json_from_text(content)
        assert result is None

    def test_string_with_braces(self):
        """测试字符串中含花括号"""
        content = '{"name": "obj{ect}value", "count": 1}'
        result = extract_json_from_text(content)
        # 这个测试关注是否能处理字符串中的花括号
        assert result is not None


class TestIsValidJson:
    """测试 is_valid_json 函数"""

    def test_valid(self):
        """测试有效 JSON"""
        assert is_valid_json('{"a": 1}') is True
        assert is_valid_json('[1, 2, 3]') is True

    def test_invalid(self):
        """测试无效 JSON"""
        assert is_valid_json('not json') is False
        assert is_valid_json('') is False
        assert is_valid_json('{"a": }') is False


class TestJsonEdgeCases:
    """测试 JSON 边界场景"""

    def test_json_with_unicode(self):
        """测试包含中文的 JSON"""
        content = '{"姓名": "张三", "年龄": 30, "城市": "北京"}'
        result = parse_json_safely(content)
        assert result is not None
        assert result["姓名"] == "张三"
        assert result["年龄"] == 30

    def test_json_with_emoji(self):
        """测试包含 emoji 的 JSON"""
        content = '{"message": "你好！🎉", "status": "ok"}'
        result = parse_json_safely(content)
        assert result is not None
        assert "🎉" in result["message"]

    def test_json_with_escaped_quotes(self):
        """测试包含转义引号的 JSON"""
        content = '{"text": "他说：\\"你好\\""}'
        result = parse_json_safely(content)
        assert result is not None
        assert "你好" in result["text"]

    def test_json_with_special_chars(self):
        """测试特殊字符"""
        content = '{"path": "C:\\\\Users\\\\test", "url": "https://example.com"}'
        result = parse_json_safely(content)
        assert result is not None
        assert "Users" in result["path"]

    def test_json_with_null(self):
        """测试 null 值"""
        content = '{"a": null, "b": "value"}'
        result = parse_json_safely(content)
        assert result == {"a": None, "b": "value"}

    def test_json_with_boolean(self):
        """测试布尔值"""
        content = '{"active": true, "deleted": false}'
        result = parse_json_safely(content)
        assert result == {"active": True, "deleted": False}

    def test_json_with_numbers(self):
        """测试数字"""
        content = '{"int": 42, "float": 3.14, "negative": -1, "zero": 0}'
        result = parse_json_safely(content)
        assert result == {"int": 42, "float": 3.14, "negative": -1, "zero": 0}


class TestRealLLMOutputScenarios:
    """测试真实 LLM 输出场景"""

    def test_llm_with_preamble(self):
        """测试带前言的 LLM 输出"""
        content = '好的，我理解了。以下是结果：\n{"result": "完成"}'
        result = parse_json_safely(content)
        assert result == {"result": "完成"}

    def test_llm_with_explanation(self):
        """测试带解释的 LLM 输出"""
        content = '执行结果如下：\n```json\n{\n  "status": "success",\n  "data": [1, 2, 3]\n}\n```\n请查收。'
        result = parse_json_safely(content)
        assert result == {"status": "success", "data": [1, 2, 3]}

    def test_llm_with_markdown_text(self):
        """测试 LLM 在 markdown 中输出 JSON"""
        content = '''# 分析报告

## 数据结果
```json
{
  "total": 100,
  "details": {
    "completed": 80,
    "pending": 20
  }
}
```

## 总结
完成度 80%'''
        result = parse_json_safely(content)
        assert result is not None
        assert result["total"] == 100
        assert result["details"]["completed"] == 80

    def test_llm_chinese_response(self):
        """测试 LLM 中文回复"""
        content = '{"任务": "完成", "状态": "成功", "耗时": 1.5}'
        result = parse_json_safely(content)
        assert result == {"任务": "完成", "状态": "成功", "耗时": 1.5}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
