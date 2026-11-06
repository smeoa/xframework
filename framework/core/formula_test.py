"""公式引擎内置函数（IF / MAX / MIN / ROUND）单元测试

覆盖白名单函数的正常计算、嵌套与变量参与、大小写不敏感，以及解析阶段即拦截的
非法用法（不支持的函数、参数个数错误、not 逻辑取反、非数值参数），并验证函数名
不会被误当作待填变量。

运行：pytest framework/core/formula_test.py
"""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from framework.core.formula import (  # noqa: E402
    FormulaError,
    evaluate_formula,
    extract_variables,
    validate_formula,
)


def _result(code, inputs=None):
    """执行公式并返回保留 2 位小数的结果"""
    return evaluate_formula(code, inputs or {})["result"]


# ---------------------------------------------------------------- IF


def test_if_true_branch():
    assert _result("IF(1 > 0, 10, 20)") == 10.0


def test_if_false_branch():
    assert _result("IF(0 > 1, 10, 20)") == 20.0


def test_function_case_insensitive():
    assert _result("if(1 < 2, 7, 9)") == 7.0
    assert _result("if (1 < 2, 7, 9)") == 7.0
    assert _result("max(1, 2)") == 2.0
    assert _result("Min(1, 2)") == 1.0
    assert _result("round(1.6)") == 2.0


def test_if_with_variables():
    code = "IF(${成本价} > 100, ${成本价} * 1.2, ${成本价} * 1.5)"
    assert _result(code, {"成本价": 200}) == 240.0
    assert _result(code, {"成本价": 80}) == 120.0


# ---------------------------------------------------------------- MAX / MIN


def test_max_and_min_basic():
    assert _result("MAX(1, 2)") == 2.0
    assert _result("MIN(1, 2)") == 1.0
    assert _result("MAX(1, 5, 3, 9, 2)") == 9.0
    assert _result("MIN(8, 3, 6)") == 3.0


def test_max_min_with_variables():
    code = "MAX(${成本价} - ${参考价}, 0)"
    assert _result(code, {"成本价": 100, "参考价": 60}) == 40.0
    assert _result(code, {"成本价": 50, "参考价": 60}) == 0.0


# ---------------------------------------------------------------- ROUND


def test_round_basic():
    assert _result("ROUND(1.234, 1)") == 1.2
    assert _result("ROUND(1.235, 2)") == 1.24
    assert _result("ROUND(2.5)") == 3.0
    assert _result("ROUND(1234, -2)") == 1200.0


# ---------------------------------------------------------------- 组合与嵌套


def test_nested_functions():
    assert _result("MAX(1, IF(1 > 0, 5, 9))") == 5.0
    assert _result("MIN(ROUND(2.34, 1), 2)") == 2.0


def test_functions_with_ternary():
    code = "${成本价} > 100 ? MAX(${成本价} * 1.2, 150) : MIN(${成本价} * 1.5, 200)"
    assert _result(code, {"成本价": 200}) == 240.0
    assert _result(code, {"成本价": 80}) == 120.0


def test_function_in_multiline_assignment():
    code = "var 差价 = MAX(${成本价} - ${参考价}, 0)\n差价 + 5"
    assert _result(code, {"成本价": 100, "参考价": 60}) == 45.0


# ---------------------------------------------------------------- 变量解析


def test_function_names_are_not_variables():
    variables = extract_variables("MAX(${成本价}, 100)")
    assert [item["key"] for item in variables] == ["成本价"]


def test_validate_recognizes_function_formula():
    result = validate_formula("IF(1 > 0, 10, 20)")
    assert result["valid"] is True
    assert result["variables"] == []


# ---------------------------------------------------------------- 非法用法


@pytest.mark.parametrize(
    "code, fragment",
    [
        ("SUM(1, 2)", "不支持的函数：SUM"),
        ("ABS(1)", "不支持的函数：ABS"),
        ("IF(1, 2)", "需要3 个参数"),
        ("IF(1, 2, 3, 4)", "需要3 个参数"),
        ("MAX()", "至少 1 个"),
        ("ROUND(1, 2, 3)", "需要1~2 个"),
        ("not (1 > 0)", "不支持的运算符"),
    ],
)
def test_invalid_function_rejected_at_parse(code, fragment):
    """解析阶段（校验）即拦截的非法写法"""
    result = validate_formula(code)
    assert result["valid"] is False
    assert fragment in result["error"]


@pytest.mark.parametrize(
    "code, fragment",
    [
        ("ROUND(1.2, 1.5)", "必须是整数"),
        ("ROUND(1.2, 99)", "位数需在"),
        ("MAX(1 > 0, 2)", "必须是数值"),
    ],
)
def test_invalid_function_rejected_at_evaluate(code, fragment):
    """语法通过校验，但取值时被判非法的写法"""
    assert validate_formula(code)["valid"] is True
    with pytest.raises(FormulaError) as error:
        evaluate_formula(code)
    assert fragment in error.value.message


def test_unsupported_function_raises_on_evaluate():
    with pytest.raises(FormulaError) as error:
        evaluate_formula("SUM(1, 2)")
    assert "不支持的函数：SUM" in error.value.message


def test_boolean_result_still_rejected():
    result = validate_formula("1 < 2 and 3 > 2")
    # 比较/逻辑运算本身合法，但输出布尔值不被接受
    assert result["valid"] is True
    with pytest.raises(FormulaError) as error:
        evaluate_formula("1 < 2 and 3 > 2")
    assert "公式输出必须是数值" in error.value.message
