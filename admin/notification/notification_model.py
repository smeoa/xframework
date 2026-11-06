from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from framework.core.model import Model


class NotificationModel(Model):
    """消息通知模型"""

    def __init__(self):
        """初始化模型"""
        super().__init__("notification")

    # create
    async def create_message(self, **kwargs) -> int:
        """创建消息

        Args:
            **kwargs: 消息内容

        Returns:
            消息ID
        """
        try:
            # 构建插入数据
            data = kwargs.copy()
            data["read"] = False  # 初始状态为未读

            # 执行插入操作
            message_id = await self.create(data)
            return message_id
        except Exception as e:
            print(f"创建消息失败: {str(e)}")
            raise

    # read
    async def get_message_list(self, type: str = "all", only_unread: bool = False) -> List[Dict[str, Any]]:
        """获取消息列表

        Args:
            type: 消息类型，all表示所有类型
            only_unread: 是否只获取未读消息

        Returns:
            消息列表
        """
        try:
            filter = []

            # 按类型过滤
            if type != "all":
                filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "type", "operator": "eq", "value": type}],
                    }
                )

            # 按未读状态过滤
            if only_unread:
                filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "read", "operator": "eq", "value": False}],
                    }
                )

            # 按时间倒序排序
            sort_rules = [{"field": "timestamp", "direction": "desc"}]

            # 查询数据
            result = await self.get_list(filter=filter, sort_rules=sort_rules)

            # 确保返回的是列表
            if isinstance(result, dict) and "items" in result:
                messages = result["items"]
            else:
                messages = result

            return messages
        except Exception as e:
            print(f"获取消息列表失败: {str(e)}")
            raise

    async def mark_all_as_read(self) -> bool:
        """标记所有消息为已读

        Returns:
            是否操作成功
        """
        try:
            # 构建更新数据
            data = {"read": True}

            # 构建过滤条件（所有消息）
            filter = []

            # 执行更新
            await self.update(data, filter)
            return True
        except Exception as e:
            print(f"标记所有消息为已读失败: {str(e)}")
            return False

    async def mark_messages_as_read(self, message_ids: List[int]) -> bool:
        """标记指定消息为已读

        Args:
            message_ids: 消息ID列表

        Returns:
            是否操作成功
        """
        try:
            # 构建更新数据
            data = {"read": True}

            # 构建过滤条件
            filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "id", "operator": "in", "value": message_ids}],
                }
            ]

            # 执行更新
            await self.update(data, filter)
            return True
        except Exception as e:
            print(f"标记指定消息为已读失败: {str(e)}")
            return False

    async def create_table(self):
        """创建消息通知表"""
        try:
            # 检查表是否存在
            check_table_sql = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = '{self.table_name}'
            """
            result = await self.db.fetch_one(check_table_sql)

            if not result:
                # 创建表
                create_table_sql = f"""
                CREATE TABLE {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    subtype VARCHAR(50),
                    download_url VARCHAR(255),
                    read BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                await self.db.execute(create_table_sql)

                # 创建索引
                create_index_sqls = [
                    f"CREATE INDEX idx_{self.table_name}_type ON {self.table_name}(type)",
                    f"CREATE INDEX idx_{self.table_name}_read ON {self.table_name}(read)",
                    f"CREATE INDEX idx_{self.table_name}_timestamp ON {self.table_name}(timestamp)",
                ]
                for sql in create_index_sqls:
                    await self.db.execute(sql)

                # 插入测试数据
                insert_data_sql = f"""
                INSERT INTO {self.table_name} (title, content, type, subtype, download_url, read, timestamp)
                VALUES
                    ('系统通知', 'WebSocket 连接已建立', 'system', 'system', NULL, FALSE, NOW() - INTERVAL '1 hour'),
                    ('下载通知', '成本核对：导出文件已准备完成。文件下载链接将于24小时后失效，请尽快下载。', 'download', 'download', 'https://example.com/download/test.xlsx', FALSE, NOW() - INTERVAL '2 hours'),
                    ('异常提醒', '应用使用的「经营看板-销售」仪表盘中，「未完全分析」的数据触发预警，恶性流失。', 'warning', 'warning', NULL, TRUE, NOW() - INTERVAL '3 hours'),
                    ('系统通知', '系统将于今晚23:00进行维护，预计持续1小时', 'system', 'system', NULL, TRUE, NOW() - INTERVAL '4 hours'),
                    ('下载通知', '用户数据导出：导出文件已准备完成。文件下载链接将于24小时后失效，请尽快下载。', 'download', 'download', 'https://example.com/download/users.xlsx', FALSE, NOW() - INTERVAL '5 hours')
                """
                await self.db.execute(insert_data_sql)

                print("消息通知表创建成功并插入测试数据")
            else:
                print("消息通知表已存在")
        except Exception as e:
            print(f"创建消息通知表失败: {str(e)}")
            raise
