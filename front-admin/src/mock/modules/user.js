// 用户模块的 mock 数据
export default [
  {
    url: "/admin/user/list",
    method: "get",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          list: [
            {
              id: 1,
              username: "user1",
              name: "用户1",
              email: "user1@example.com",
              phone: "13800138001",
              status: 1,
            },
            {
              id: 2,
              username: "user2",
              name: "用户2",
              email: "user2@example.com",
              phone: "13800138002",
              status: 1,
            },
          ],
          total: 2,
        },
      };
    },
  },
];
