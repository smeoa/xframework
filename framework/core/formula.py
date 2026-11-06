"""公式解析与计算引擎模块

为「运费公式（代码公式）」与「定价公式模板」提供统一的公式解析与安全求值能力：

- 占位符：`${变量名}` 为待填变量，解析后得到变量 key；`${变量名:默认值}` 可指定默认值，
  未传该变量时按默认值参与计算；
- 提示注释：`//变量=说明` 单独成行时，为同名变量提供 hint 提示文字；
- 多行公式：`var 变量 = 表达式` 逐行赋值，最后一行表达式（或最后一个赋值变量）为输出；
- 三元表达式：兼容 `条件 ? 值1 : 值2` 写法（内部转换为 Python 三元表达式）；
- 安全求值：基于 ast 白名单节点手工求值，**不使用 eval / exec**，仅支持
  `+ - * / % **`、一元正负、比较运算、`and/or`、括号与三元表达式；
- 内置函数：`IF(条件, 值1, 值2)`、`MAX(a, b, ...)`、`MIN(a, b, ...)`、
  `ROUND(值, 位数)`（函数名大小写不敏感）。

典型用法：
    >>> validate_formula("var 总价 = ${成本价} * 1.3\n总价 + 5")
    {'valid': True, 'variables': [{'key': '成本价', ...}], 'output_expr': '总价 + 5', ...}
    >>> evaluate_formula("${重量} <= 0.1 ? 5 : 5 + (${重量} - 0.1) * 90", {"重量": 0.2})["result"]
    14.0
"""

import ast
import keyword
import re
from decimal import Decimal, DecimalException, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

# ${变量名} / ${变量名:默认值} 占位符
PLACEHOLDER_PATTERN = re.compile(r"\$\{([^}\n]+)\}")
# 整行提示注释：//变量=说明
HINT_LINE_PATTERN = re.compile(r"^//\s*(.*)$")
# 赋值语句：var 变量 = 表达式（var 可省略；排除 == / >= / <= / != 等比较运算）
ASSIGN_PATTERN = re.compile(r"^(?:var\s+)?([^\s=<>!+\-*/%()]+)\s*=(?!=)\s*(.+)$")
# 金额保留位数
MONEY_QUANT = Decimal("0.01")
# 内置函数白名单：名称（大写）→ (最少参数个数, 最多参数个数；None 表示不限)
FUNCTION_ARITY: Dict[str, Tuple[int, Optional[int]]] = {
    "IF": (3, 3),
    "MAX": (1, None),
    "MIN": (1, None),
    "ROUND": (1, 2),
}
# ROUND 允许的位数范围（含），超出会被 Decimal 拒绝
ROUND_DIGIT_LIMIT = 10
# 求值不支持的 AST 节点类型（解析阶段即拦截，避免被误判为「公式合法」）
UNSUPPORTED_NODE_TYPES = (
    ast.Subscript,
    ast.Attribute,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.Lambda,
    ast.Starred,
    ast.Await,
    ast.Slice,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.NamedExpr,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)
# 内置函数调用（用于统一大小写：`if` 是 Python 关键字，不统一会在解析阶段直接语法报错）
FUNCTION_CALL_PATTERN = re.compile(r"\b(if|max|min|round)\s*(?=\()", re.IGNORECASE)
# Python 语法错误信息 → 可读中文提示
SYNTAX_MESSAGE_MAP = {
    "invalid syntax": "表达式不完整或含非法字符",
    "unexpected EOF while parsing": "表达式不完整",
    "unterminated string literal": "字符串未闭合",
    "invalid decimal literal": "数字格式不正确",
    "invalid character": "包含非法字符",
    "leading zeros in decimal integer literals are not permitted": "数字不能以 0 开头",
    "cannot assign to expression here": "此处不能赋值，请写成「var 变量 = 表达式」",
    "cannot assign to literal here": "不能给常量赋值",
    "cannot assign to operator": "赋值号左侧必须是变量名",
}


class FormulaError(Exception):
    """公式解析/求值异常

    Attributes:
        message: 错误说明
        line: 出错行号（1 起，未知时为 None）
    """

    def __init__(self, message: str, line: Optional[int] = None) -> None:
        self.message = message
        self.line = line
        super().__init__(message)

    def to_text(self) -> str:
        """转为可直接展示给用户的错误文案

        Returns:
            含行号的错误文案，如「第 2 行：变量「成本价」未赋值」
        """
        if self.line:
            return f"第 {self.line} 行：{self.message}"
        return self.message


def _is_identifier(name: str) -> bool:
    """判断文本是否为合法标识符（可含中文）

    Args:
        name: 待判断文本

    Returns:
        是否为合法且非关键字的标识符
    """
    if not name:
        return False
    try:
        return name.isidentifier() and not keyword.iskeyword(name)
    except (TypeError, ValueError):
        return False


def _parse_default(text: str) -> Any:
    """解析占位符默认值文本

    Args:
        text: `${变量名:默认值}` 中 `:` 之后的文本

    Returns:
        整数优先、其次浮点数，无法转数值时按原字符串返回；空文本返回 None
    """
    value = (text or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _strip_inline_comment(line: str) -> str:
    """去除行内 `//` 注释

    占位符与提示注释已在此之前处理，剩余的 `//` 一律视为注释起点。

    Args:
        line: 原始行文本

    Returns:
        去掉行内注释后的文本
    """
    if "//" not in line:
        return line
    return line.split("//", 1)[0].strip()


def _preprocess(
    code: str,
) -> Tuple[List[Tuple[int, str]], Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, Any]]:
    """预处理公式代码：剥离注释、替换 ${变量名} / ${变量名:默认值} 占位符

    Args:
        code: 原始公式代码

    Returns:
        (语句列表, 占位符 label→内部标识, 内部标识→label, 提示文字 label→hint, label→默认值)
        语句列表每项为 (行号, 已规范化表达式文本)

    Raises:
        FormulaError: 公式为空时
    """
    lines = (code or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    hints: Dict[str, str] = {}
    defaults: Dict[str, Any] = {}
    label_to_name: Dict[str, str] = {}
    name_to_label: Dict[str, str] = {}
    statements: List[Tuple[int, str]] = []

    def replace_placeholder(match: re.Match) -> str:
        """把单个 ${变量名} / ${变量名:默认值} 占位符替换为内部标识符"""
        raw = match.group(1).strip()
        if not raw:
            return match.group(0)
        label, _sep, default_text = raw.partition(":")
        label = label.strip()
        if not label:
            return match.group(0)
        if default_text.strip():
            defaults[label] = _parse_default(default_text)
        if label in label_to_name:
            return label_to_name[label]
        if _is_identifier(label):
            name = label
        else:
            name = f"__v{len(label_to_name) + 1}"
        label_to_name[label] = name
        name_to_label[name] = label
        return name

    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        hint_match = HINT_LINE_PATTERN.match(line)
        if hint_match:
            body = hint_match.group(1).strip()
            if "=" in body:
                key, hint = body.split("=", 1)
                key = key.strip()
                if key:
                    hints[key] = hint.strip()
            continue

        line = _strip_inline_comment(line)
        if not line:
            continue

        line = PLACEHOLDER_PATTERN.sub(replace_placeholder, line)
        statements.append((index, line))

    if not statements:
        raise FormulaError("公式不能为空")

    return statements, label_to_name, name_to_label, hints, defaults


def _convert_ternary(expr: str) -> str:
    """把 `条件 ? 值1 : 值2` 转换为 Python 三元表达式 `值1 if 条件 else 值2`

    支持嵌套与括号包裹，仅在顶层（括号深度 0）定位 `?` 与配对的 `:`。

    Args:
        expr: 表达式文本

    Returns:
        转换后的表达式文本
    """
    depth = 0
    question_index = -1
    for index, char in enumerate(expr):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "?" and depth == 0:
            question_index = index
            break
    if question_index < 0:
        return expr

    depth = 0
    nested = 0
    colon_index = -1
    for index in range(question_index + 1, len(expr)):
        char = expr[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and char == "?":
            nested += 1
        elif depth == 0 and char == ":":
            if nested == 0:
                colon_index = index
                break
            nested -= 1
    if colon_index < 0:
        return expr

    condition = expr[:question_index]
    then_part = expr[question_index + 1:colon_index]
    else_part = expr[colon_index + 1:]
    return (
        f"({_convert_ternary(then_part)} if {_convert_ternary(condition)} "
        f"else {_convert_ternary(else_part)})"
    )


def _describe_syntax_error(error: SyntaxError) -> str:
    """把 Python 语法错误信息转成可读的中文提示

    Args:
        error: ast.parse 抛出的语法错误

    Returns:
        面向用户的中文错误说明
    """
    raw = (error.msg or "").strip()
    if raw in SYNTAX_MESSAGE_MAP:
        return SYNTAX_MESSAGE_MAP[raw]
    if "never closed" in raw or "unmatched" in raw:
        return "括号不匹配"
    if "expected ':'" in raw:
        return "三元表达式需写成：条件 ? 值1 : 值2"
    if raw.startswith("expected"):
        return f"语法不完整（{raw}）"
    return f"语法错误（{raw}）" if raw else "语法错误"


def _check_call(node: ast.Call, line: Optional[int]) -> None:
    """校验函数调用是否为白名单内的内置函数且参数个数合法

    Args:
        node: ast.Call 节点
        line: 行号

    Raises:
        FormulaError: 非内置函数、含关键字/展开参数、参数个数不合法时
    """
    if not isinstance(node.func, ast.Name):
        raise FormulaError("仅支持内置函数：IF / MAX / MIN / ROUND", line)
    name = node.func.id
    arity = FUNCTION_ARITY.get(name.upper())
    if arity is None:
        raise FormulaError(f"不支持的函数：{name}（仅支持 IF / MAX / MIN / ROUND）", line)
    if node.keywords:
        raise FormulaError(f"函数 {name} 不支持关键字参数", line)
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        raise FormulaError(f"函数 {name} 不支持展开参数", line)

    low, high = arity
    count = len(node.args)
    if count < low or (high is not None and count > high):
        if high is None:
            expect = f"至少 {low} 个"
        elif low == high:
            expect = f"{low} 个"
        else:
            expect = f"{low}~{high} 个"
        raise FormulaError(f"函数 {name} 需要{expect}参数，当前 {count} 个", line)


def _check_supported(tree: ast.AST, line: Optional[int]) -> None:
    """校验 AST 仅使用受支持的节点语法（供解析阶段提前报错）

    与 _eval_node 的支持范围保持一致：这里拦下的语法无需等到试算才暴露。

    Args:
        tree: 表达式 AST
        line: 行号

    Raises:
        FormulaError: 命中不支持的节点、非数值常量、not 或非法函数调用时
    """
    for node in ast.walk(tree):
        if isinstance(node, UNSUPPORTED_NODE_TYPES):
            raise FormulaError(f"不支持的语法：{type(node).__name__}", line)
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or value is None or isinstance(value, str):
                raise FormulaError("公式仅支持数值运算", line)
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, (ast.UAdd, ast.USub)):
            raise FormulaError("不支持的运算符（如需逻辑取反请用 1 - x 或三元表达式）", line)
        if isinstance(node, ast.BinOp) and not isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)
        ):
            raise FormulaError("不支持的运算符", line)
        if isinstance(node, ast.BoolOp) and not isinstance(node.op, (ast.And, ast.Or)):
            raise FormulaError("不支持的运算符", line)
        if isinstance(node, ast.Call):
            _check_call(node, line)


def _normalize_function_names(expr: str) -> str:
    """把内置函数名统一为大写，实现函数名大小写不敏感

    Args:
        expr: 表达式文本

    Returns:
        函数名已归一为大写的表达式文本
    """
    return FUNCTION_CALL_PATTERN.sub(lambda match: match.group(1).upper(), expr)


def _parse_expression(expr: str, line: Optional[int]) -> ast.Expression:
    """解析表达式为 AST（含三元表达式转换）

    Args:
        expr: 表达式文本
        line: 所属行号（用于错误定位）

    Returns:
        AST 表达式节点

    Raises:
        FormulaError: 语法错误时
    """
    if not expr or not expr.strip():
        raise FormulaError("表达式不能为空", line)
    try:
        tree = ast.parse(_convert_ternary(_normalize_function_names(expr)), mode="eval")
    except SyntaxError as e:
        # 含 ? 但缺 : 的写法无法转成 Python 三元，给出针对性提示
        if "?" in expr and ":" not in expr:
            raise FormulaError("三元表达式需写成：条件 ? 值1 : 值2", line)
        raise FormulaError(_describe_syntax_error(e), line)
    _check_supported(tree, line)
    return tree


def _split_statement(lineno: int, text: str) -> Tuple[Optional[str], str]:
    """拆分「赋值语句」与「输出表达式」

    Args:
        lineno: 行号
        text: 规范化后的行文本

    Returns:
        (赋值变量名或 None, 表达式文本)
    """
    match = ASSIGN_PATTERN.match(text)
    if match:
        name = match.group(1).strip()
        expr = match.group(2).strip()
        if _is_identifier(name):
            return name, expr
    return None, text


def _referenced_names(expr: str, line: Optional[int]) -> List[str]:
    """提取表达式引用的变量名（按出现顺序去重）

    Args:
        expr: 表达式文本
        line: 行号

    Returns:
        变量名列表
    """
    tree = _parse_expression(expr, line)
    # 函数调用名（如 IF / MAX）不是待填变量，需排除
    function_names = {
        id(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    positioned: List[Tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and id(node) not in function_names:
            positioned.append((node.lineno, node.col_offset, node.id))
    positioned.sort(key=lambda item: (item[0], item[1]))

    names: List[str] = []
    for _lineno, _offset, name in positioned:
        if name not in names:
            names.append(name)
    return names


def _parse_plan(code: str) -> Dict[str, Any]:
    """解析公式为执行计划

    Args:
        code: 公式代码

    Returns:
        {
          "steps": [{line, name, expr}],   赋值步骤（按顺序）
          "output_expr": str,              输出表达式
          "output_var": str|None,          输出表达式对应的变量名（末行为赋值时）
          "input_names": [str],            待填变量（内部标识）
          "name_to_label": {name: label},
          "label_to_name": {label: name},
          "hints": {label: hint},
          "defaults": {label: default},
        }

    Raises:
        FormulaError: 语法非法时
    """
    statements, label_to_name, name_to_label, hints, defaults = _preprocess(code)

    steps: List[Dict[str, Any]] = []
    input_names: List[str] = []
    assigned: set = set()

    def collect_inputs(expr: str, line: int) -> None:
        """收集表达式中的待填变量"""
        for name in _referenced_names(expr, line):
            if name not in assigned and name not in input_names:
                input_names.append(name)

    last_index = len(statements) - 1
    output_expr = ""
    output_var: Optional[str] = None

    for position, (lineno, text) in enumerate(statements):
        name, expr = _split_statement(lineno, text)
        _parse_expression(expr, lineno)

        if position == last_index:
            if name is not None:
                collect_inputs(expr, lineno)
                steps.append({"line": lineno, "name": name, "expr": expr})
                assigned.add(name)
                output_var = name
                output_expr = expr
            else:
                collect_inputs(expr, lineno)
                output_expr = expr
            break

        if name is None:
            collect_inputs(expr, lineno)
            continue

        collect_inputs(expr, lineno)
        steps.append({"line": lineno, "name": name, "expr": expr})
        assigned.add(name)

    if not output_expr:
        raise FormulaError("公式缺少输出表达式", statements[-1][0])

    return {
        "steps": steps,
        "output_expr": output_expr,
        "output_var": output_var,
        "input_names": input_names,
        "name_to_label": name_to_label,
        "label_to_name": label_to_name,
        "hints": hints,
        "defaults": defaults,
    }


def extract_variables(code: str) -> List[Dict[str, Any]]:
    """解析公式中的待填变量清单

    Args:
        code: 公式代码

    Returns:
        变量列表：[{key, label, hint, default, required}]
        key/label 为 `${变量名}` 中的原始文本；hint 来自 `//变量=说明`；
        default 来自 `${变量名:默认值}`，有默认值的变量 required 为 False

    Raises:
        FormulaError: 公式非法时
    """
    plan = _parse_plan(code)
    variables: List[Dict[str, Any]] = []
    for name in plan["input_names"]:
        label = plan["name_to_label"].get(name, name)
        default = plan["defaults"].get(label)
        variables.append(
            {
                "key": label,
                "label": label,
                "hint": plan["hints"].get(label) or plan["hints"].get(name) or "",
                "default": default,
                "required": default is None,
            }
        )
    return variables


def validate_formula(code: str) -> Dict[str, Any]:
    """校验公式并返回变量清单与输出信息

    Args:
        code: 公式代码

    Returns:
        {
          "valid": bool,
          "variables": [...],
          "output_expr": str|None,
          "output_var": str|None,
          "error": str|None,
          "error_line": int|None,
        }
    """
    try:
        plan = _parse_plan(code)
    except FormulaError as e:
        return {
            "valid": False,
            "variables": [],
            "output_expr": None,
            "output_var": None,
            "error": e.message,
            "error_line": e.line,
        }
    except Exception as e:  # pragma: no cover - 兜底，避免异常直接抛给接口
        return {
            "valid": False,
            "variables": [],
            "output_expr": None,
            "output_var": None,
            "error": str(e),
            "error_line": None,
        }

    return {
        "valid": True,
        "variables": extract_variables(code),
        "output_expr": plan["output_expr"],
        "output_var": plan["output_var"],
        "error": None,
        "error_line": None,
    }


def _to_decimal(value: Any, line: Optional[int] = None, name: Optional[str] = None) -> Decimal:
    """把输入值转换为 Decimal

    Args:
        value: 原始值
        line: 行号（错误定位）
        name: 变量名（错误定位）

    Returns:
        Decimal 数值

    Raises:
        FormulaError: 值不是合法数值时
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise FormulaError(f"变量「{name or ''}」的值不是数值", line)
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            raise FormulaError(f"变量「{name or ''}」的值为空", line)
        try:
            return Decimal(text)
        except (DecimalException, ValueError):
            raise FormulaError(f"变量「{name or ''}」的值不是合法数值：{value}", line)
    raise FormulaError(f"变量「{name or ''}」的值不是合法数值", line)


def _eval_node(node: ast.AST, env: Dict[str, Decimal], line: Optional[int]) -> Any:
    """递归求值 AST 节点（白名单节点）

    Args:
        node: AST 节点
        env: 变量环境（内部标识 → Decimal）
        line: 行号（错误定位）

    Returns:
        计算结果（数值或布尔）

    Raises:
        FormulaError: 命中不支持的语法、未赋值变量或除零时
    """
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, env, line)

    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool) or value is None or isinstance(value, str):
            raise FormulaError("公式仅支持数值运算", line)
        return Decimal(str(value))

    if isinstance(node, ast.Name):
        if node.id not in env:
            raise FormulaError(f"变量「{node.id}」未赋值", line)
        return env[node.id]

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, env, line)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return operand
        raise FormulaError("不支持的运算符", line)

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, env, line)
        right = _eval_node(node.right, env, line)
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                return left ** right
        except DecimalException:
            raise FormulaError("计算失败：请检查是否出现除零或数值溢出", line)
        raise FormulaError("不支持的运算符", line)

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, env, line)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, env, line)
            if isinstance(op, ast.Lt):
                result = left < right
            elif isinstance(op, ast.LtE):
                result = left <= right
            elif isinstance(op, ast.Gt):
                result = left > right
            elif isinstance(op, ast.GtE):
                result = left >= right
            elif isinstance(op, ast.Eq):
                result = left == right
            elif isinstance(op, ast.NotEq):
                result = left != right
            else:
                raise FormulaError("不支持的比较运算", line)
            if not result:
                return False
            left = right
        return True

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = _eval_node(value, env, line)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = _eval_node(value, env, line)
            if result:
                return result
        return result

    if isinstance(node, ast.IfExp):
        condition = _eval_node(node.test, env, line)
        if condition:
            return _eval_node(node.body, env, line)
        return _eval_node(node.orelse, env, line)

    if isinstance(node, ast.Call):
        return _eval_call(node, env, line)

    raise FormulaError(f"不支持的语法：{type(node).__name__}", line)


def _as_decimal(value: Any, func: str, line: Optional[int]) -> Decimal:
    """把函数入参转为 Decimal（布尔/非数值入参直接报错）

    Args:
        value: 入参求值结果
        func: 函数名（用于错误文案）
        line: 行号

    Returns:
        Decimal 数值

    Raises:
        FormulaError: 入参不是数值时
    """
    if isinstance(value, bool):
        raise FormulaError(f"函数 {func} 的参数必须是数值", line)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (DecimalException, ValueError):
        raise FormulaError(f"函数 {func} 的参数必须是数值", line)


def _eval_call(node: ast.Call, env: Dict[str, Decimal], line: Optional[int]) -> Any:
    """求值白名单内置函数（IF / MAX / MIN / ROUND）

    函数名与参数个数已在解析阶段（_check_call）校验，此处只做取值与计算。

    Args:
        node: ast.Call 节点
        env: 变量环境
        line: 行号

    Returns:
        计算结果（Decimal，IF 返回命中的分支值）

    Raises:
        FormulaError: 位数非整数、超出范围或计算失败时
    """
    name = node.func.id.upper()
    args = [_eval_node(arg, env, line) for arg in node.args]

    if name == "IF":
        return args[1] if args[0] else args[2]

    if name == "MAX":
        return max(_as_decimal(value, name, line) for value in args)

    if name == "MIN":
        return min(_as_decimal(value, name, line) for value in args)

    # ROUND(值, 位数)：位数缺省为 0
    value = _as_decimal(args[0], name, line)
    digits = _as_decimal(args[1], name, line) if len(args) > 1 else Decimal(0)
    if digits != digits.to_integral_value():
        raise FormulaError("函数 ROUND 的位数必须是整数", line)
    count = int(digits)
    if not -ROUND_DIGIT_LIMIT <= count <= ROUND_DIGIT_LIMIT:
        raise FormulaError(f"函数 ROUND 的位数需在 -{ROUND_DIGIT_LIMIT} ~ {ROUND_DIGIT_LIMIT} 之间", line)
    try:
        return value.quantize(Decimal(1).scaleb(-count), rounding=ROUND_HALF_UP)
    except DecimalException:
        raise FormulaError("函数 ROUND 计算失败：位数超出可表示范围", line)


def evaluate_formula(code: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """按公式代码与变量取值计算结果

    Args:
        code: 公式代码
        inputs: 变量取值字典，键为 `${变量名}` 中的原始文本（也兼容内部标识符）；
            未传且公式中用 `${变量名:默认值}` 指定了默认值的变量按默认值计算

    Returns:
        {
          "result": float|None,            最终结果（保留 2 位小数）
          "raw_result": float,             未取整的原始结果
          "output_var": str|None,          输出变量名
          "output_expr": str,              输出表达式
          "output_label": str,             输出变量的原始文本
          "variables": [{key,label,hint,default,required}],
          "steps": [{key,label,expr,value}], 中间变量（按赋值顺序）
        }

    Raises:
        FormulaError: 缺少必填变量、语法非法、除零或类型错误时
    """
    plan = _parse_plan(code)
    provided = inputs if isinstance(inputs, dict) else {}

    env: Dict[str, Decimal] = {}
    variables = extract_variables(code)
    missing: List[str] = []

    for variable in variables:
        label = variable["key"]
        if label in provided and provided[label] is not None and provided[label] != "":
            raw_value = provided[label]
        elif variable.get("label") in provided and provided[variable["label"]] not in (None, ""):
            raw_value = provided[variable["label"]]
        elif variable.get("default") is not None:
            raw_value = variable["default"]
        else:
            missing.append(label)
            continue
        env[plan["label_to_name"].get(label, label)] = _to_decimal(raw_value, None, label)

    if missing:
        raise FormulaError(f"缺少必填变量：{'、'.join(missing)}")

    steps: List[Dict[str, Any]] = []
    for step in plan["steps"]:
        tree = _parse_expression(step["expr"], step["line"])
        try:
            value = _eval_node(tree, env, step["line"])
        except FormulaError:
            raise
        except DecimalException:
            raise FormulaError("计算失败：请检查是否出现除零或数值溢出", step["line"])
        env[step["name"]] = value
        steps.append(
            {
                "key": plan["name_to_label"].get(step["name"], step["name"]),
                "label": plan["name_to_label"].get(step["name"], step["name"]),
                "expr": step["expr"],
                "value": round_money(value),
            }
        )

    tree = _parse_expression(plan["output_expr"], None)
    try:
        result = _eval_node(tree, env, None)
    except FormulaError:
        raise
    except DecimalException:
        raise FormulaError("计算失败：请检查是否出现除零或数值溢出")

    if isinstance(result, bool):
        raise FormulaError("公式输出必须是数值")

    output_label = plan["name_to_label"].get(plan["output_var"] or "", plan["output_var"] or plan["output_expr"])

    return {
        "result": round_money(result),
        "raw_result": float(result),
        "output_var": plan["output_var"],
        "output_expr": plan["output_expr"],
        "output_label": output_label,
        "variables": variables,
        "steps": steps,
    }


def round_money(value: Any) -> Optional[float]:
    """金额四舍五入保留 2 位小数

    Args:
        value: 数值（Decimal/int/float/str）

    Returns:
        保留 2 位小数的浮点数；value 为空时返回 None
    """
    if value is None or value == "":
        return None
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        return float(decimal_value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP))
    except (DecimalException, ValueError, TypeError):
        return None
