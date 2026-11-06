"""Flow DAG工作流引擎集成测试"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from framework.agent.flow import Flow


class TestExecutionModeParsing:
    """执行模式解析测试"""

    def test_parallel_keywords(self):
        """测试并行关键字识别"""
        flow = Flow()
        keywords = ["全并行", "部分并行", "混合并行", "支持并行", "并行执行"]
        for keyword in keywords:
            plan = {"global_execution_flow": {"execution_mode": keyword}, "task_details": []}
            result = flow._plan_to_flow(plan)
            assert result["parallel"] is True, f"'{keyword}' should be parallel"

    def test_serial_keywords(self):
        """测试串行关键字识别"""
        flow = Flow()
        keywords = ["全串行", "顺序执行", "依次执行", "串行执行"]
        for keyword in keywords:
            plan = {"global_execution_flow": {"execution_mode": keyword}, "task_details": []}
            result = flow._plan_to_flow(plan)
            assert result["parallel"] is False, f"'{keyword}' should be serial"

    def test_empty_execution_mode(self):
        """测试空执行模式默认为串行"""
        flow = Flow()
        plan = {"global_execution_flow": {}, "task_details": []}
        result = flow._plan_to_flow(plan)
        assert result["parallel"] is False


class TestDependencyHandling:
    """依赖关系处理测试"""

    def test_no_dependency(self):
        """测试无依赖"""
        flow = Flow()
        plan = {"task_details": [{"task_id": "T001", "task_goal": "目标", "dependency": []}]}
        result = flow._plan_to_flow(plan)
        assert result["nodes"][0]["depends_on"] == []

    def test_single_dependency(self):
        """测试单依赖"""
        flow = Flow()
        plan = {
            "task_details": [
                {"task_id": "T001", "task_goal": "目标1", "dependency": []},
                {"task_id": "T002", "task_goal": "目标2", "dependency": ["T001"]}
            ]
        }
        result = flow._plan_to_flow(plan)
        assert result["nodes"][1]["depends_on"] == ["T001"]

    def test_multiple_dependencies(self):
        """测试多依赖"""
        flow = Flow()
        plan = {
            "task_details": [
                {"task_id": "T001", "task_goal": "目标1", "dependency": []},
                {"task_id": "T002", "task_goal": "目标2", "dependency": []},
                {"task_id": "T003", "task_goal": "目标3", "dependency": ["T001", "T002"]}
            ]
        }
        result = flow._plan_to_flow(plan)
        assert result["nodes"][2]["depends_on"] == ["T001", "T002"]


class TestFlowConversion:
    """Flow 转换测试"""

    def test_plan_to_flow_structure(self):
        """测试计划转 DAG 结构"""
        flow = Flow()
        plan = {
            "global_execution_flow": {"execution_mode": "全串行"},
            "task_details": [
                {"task_id": "T001", "task_name": "任务", "task_goal": "目标", "dependency": []}
            ]
        }
        result = flow._plan_to_flow(plan)

        assert "nodes" in result
        assert "parallel" in result
        assert len(result["nodes"]) == 1

    def test_plan_to_flow_parallel_structure(self):
        """测试并行计划转 DAG 结构"""
        flow = Flow()
        plan = {
            "global_execution_flow": {"execution_mode": "全并行"},
            "task_details": [
                {"task_id": "T001", "task_name": "任务1", "task_goal": "目标1", "dependency": []},
                {"task_id": "T002", "task_name": "任务2", "task_goal": "目标2", "dependency": []}
            ]
        }
        result = flow._plan_to_flow(plan)

        assert result["parallel"] is True
        assert len(result["nodes"]) == 2

    def test_node_fields_complete(self):
        """测试节点字段完整性"""
        flow = Flow()
        plan = {
            "task_details": [
                {
                    "task_id": "T001",
                    "task_name": "测试任务",
                    "task_goal": "测试目标",
                    "dependency": []
                }
            ]
        }
        result = flow._plan_to_flow(plan)
        node = result["nodes"][0]

        assert node["step_id"] == "T001"
        assert node["schema_unique_id"] == "T001_schema"
        assert "测试目标" in node["sys_prompt"]
        assert "严格输出要求" in node["sys_prompt"]
        assert node["output_fields"]["result"][0] == "str"
        assert node["temp"] == 0.0
        assert node["retries"] == 2
        assert "{raw_text}" in node["input_template"]
        assert "{knowledge}" in node["input_template"]


class TestCircularDependency:
    """循环依赖检测测试"""

    @pytest.mark.asyncio
    async def test_circular_dependency_detected(self):
        """测试循环依赖被检测"""
        flow = Flow()

        flow_config = [
            {"step_id": "T001", "schema_unique_id": "S1", "sys_prompt": "A", "depends_on": ["T002"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""},
            {"step_id": "T002", "schema_unique_id": "S2", "sys_prompt": "B", "depends_on": ["T001"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""}
        ]

        result = await flow.execute("test", flow_config)
        assert result["success"] is False
        assert result["code"] == "CIRCULAR_DEPENDENCY"

    @pytest.mark.asyncio
    async def test_complex_circular_dependency(self):
        """测试复杂循环依赖 A→B→C→A"""
        flow = Flow()

        flow_config = [
            {"step_id": "A", "schema_unique_id": "SA", "sys_prompt": "A", "depends_on": ["C"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""},
            {"step_id": "B", "schema_unique_id": "SB", "sys_prompt": "B", "depends_on": ["A"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""},
            {"step_id": "C", "schema_unique_id": "SC", "sys_prompt": "C", "depends_on": ["B"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""}
        ]

        result = await flow.execute("test", flow_config)
        assert result["success"] is False
        assert result["code"] == "CIRCULAR_DEPENDENCY"


class TestValidDAG:
    """有效 DAG 测试"""

    @pytest.mark.asyncio
    async def test_linear_chain(self):
        """测试线性链 A→B→C"""
        flow = Flow()

        flow_config = [
            {"step_id": "A", "schema_unique_id": "SA", "sys_prompt": "A", "depends_on": [],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""},
            {"step_id": "B", "schema_unique_id": "SB", "sys_prompt": "B", "depends_on": ["A"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""},
            {"step_id": "C", "schema_unique_id": "SC", "sys_prompt": "C", "depends_on": ["B"],
             "output_fields": {"r": ["str", {}]}, "temp": 0.0, "retries": 1, "input_template": ""}
        ]

        # 不 mock，直接测试结构有效性
        flow_data = flow._plan_to_flow({
            "global_execution_flow": {"execution_mode": "全串行"},
            "task_details": [
                {"task_id": "A", "task_goal": "A", "dependency": []},
                {"task_id": "B", "task_goal": "B", "dependency": ["A"]},
                {"task_id": "C", "task_goal": "C", "dependency": ["B"]}
            ]
        })
        assert flow_data["parallel"] is False

    @pytest.mark.asyncio
    async def test_fan_out(self):
        """测试扇出 A→B, A→C"""
        flow = Flow()

        flow_data = flow._plan_to_flow({
            "global_execution_flow": {"execution_mode": "部分并行"},
            "task_details": [
                {"task_id": "A", "task_goal": "A", "dependency": []},
                {"task_id": "B", "task_goal": "B", "dependency": ["A"]},
                {"task_id": "C", "task_goal": "C", "dependency": ["A"]}
            ]
        })
        assert flow_data["parallel"] is True

    @pytest.mark.asyncio
    async def test_fan_in(self):
        """测试扇入 A→C, B→C"""
        flow = Flow()

        flow_data = flow._plan_to_flow({
            "global_execution_flow": {"execution_mode": "全串行"},
            "task_details": [
                {"task_id": "A", "task_goal": "A", "dependency": []},
                {"task_id": "B", "task_goal": "B", "dependency": []},
                {"task_id": "C", "task_goal": "C", "dependency": ["A", "B"]}
            ]
        })
        assert flow_data["parallel"] is False


class TestExecuteInputParsing:
    """execute() 输入解析测试"""

    @pytest.mark.asyncio
    async def test_execute_string_input(self):
        """测试字符串输入"""
        flow = Flow()
        result = await flow.execute("test")
        assert result["success"] is True
        assert result["text"] == "test"

    @pytest.mark.asyncio
    async def test_execute_dict_input(self):
        """测试字典输入"""
        flow = Flow()
        result = await flow.execute({"text": "test", "knowledge": None})
        assert result["success"] is True
        assert result["text"] == "test"

    @pytest.mark.asyncio
    async def test_execute_dict_with_knowledge(self):
        """测试带知识库的字典输入"""
        flow = Flow()
        result = await flow.execute({
            "text": "test",
            "knowledge": [{"id": "1", "content": "doc"}]
        })
        assert result["success"] is True
        assert result["knowledge"] == '[{"id": "1", "content": "doc"}]'


class TestPlanGenerationModes:
    """计划生成模式测试"""

    @pytest.mark.asyncio
    async def test_serial_mode_detection(self):
        """测试串行模式检测"""
        flow = Flow()

        with patch.object(flow, "_generate_plan", new_callable=AsyncMock) as mock_plan:
            mock_plan.return_value = {
                "task_overview": {"total_tasks": 2, "priority_order": ["T1", "T2"]},
                "task_details": [
                    {"task_id": "T1", "task_goal": "目标1", "dependency": []},
                    {"task_id": "T2", "task_goal": "目标2", "dependency": ["T1"]}
                ],
                "global_execution_flow": {"execution_mode": "全串行"}
            }

            result = await flow.plan({"角色": "测试", "人设": "测试", "任务描述": "串行任务"})
            flow_data = flow._plan_to_flow(result["result"])
            assert flow_data["parallel"] is False

    @pytest.mark.asyncio
    async def test_parallel_mode_detection(self):
        """测试并行模式检测"""
        flow = Flow()

        with patch.object(flow, "_generate_plan", new_callable=AsyncMock) as mock_plan:
            mock_plan.return_value = {
                "task_overview": {"total_tasks": 3},
                "task_details": [
                    {"task_id": "T1", "task_goal": "目标1", "dependency": []},
                    {"task_id": "T2", "task_goal": "目标2", "dependency": []},
                    {"task_id": "T3", "task_goal": "目标3", "dependency": []}
                ],
                "global_execution_flow": {"execution_mode": "全并行"}
            }

            result = await flow.plan({"角色": "测试", "人设": "测试", "任务描述": "并行任务"})
            flow_data = flow._plan_to_flow(result["result"])
            assert flow_data["parallel"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
