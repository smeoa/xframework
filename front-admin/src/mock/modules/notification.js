// 消息通知模块的 mock 数据
export default [
  {
    url: "/admin/notification/get-message-list",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          list: [
            {
              id: 1,
              type: "info",
              title: "系统通知",
              content: "欢迎使用管理系统",
              status: 0,
              created_at: "2024-01-01 10:00:00",
            },
            {
              id: 2,
              type: "warning",
              title: "提醒",
              content: "您有新的任务需要处理",
              status: 0,
              created_at: "2024-01-02 10:00:00",
            },
          ],
          total: 2,
        },
      };
    },
  },
  {
    url: "/admin/notification/read",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: null,
      };
    },
  },
  {
    url: "/admin/notification/read-all",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: null,
      };
    },
  },
];
