// 组织模块的 mock 数据
export default [
  {
    url: "/admin/organization/get-dept-tree",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: [
          {
            id: 1,
            name: "总部",
            children: [
              {
                id: 2,
                name: "技术部",
                children: [
                  { id: 3, name: "前端组" },
                  { id: 4, name: "后端组" },
                  { id: 5, name: "测试组" },
                ],
              },
              {
                id: 6,
                name: "产品部",
              },
              {
                id: 7,
                name: "市场部",
              },
            ],
          },
        ],
      };
    },
  },
  {
    url: "/admin/organization/get-user-list",
    method: "post",
    response: (req) => {
      const { page = 1, limit = 20, keyword = "" } = req.body.data || {};
      return {
        code: 200,
        message: "success",
        data: {
          items: [
            {
              id: 1,
              username: "admin",
              name: "管理员",
              phone: "13800138000",
              email: "admin@example.com",
              deptName: "技术部",
              status: 1,
              createdTime: "2024-01-01 00:00:00",
              updatedTime: "2024-01-01 00:00:00",
            },
            {
              id: 2,
              username: "user1",
              name: "用户1",
              phone: "13800138001",
              email: "user1@example.com",
              deptName: "产品部",
              status: 1,
              createdTime: "2024-01-01 00:00:00",
              updatedTime: "2024-01-01 00:00:00",
            },
          ],
          total: 2,
        },
      };
    },
  },
  {
    url: "/admin/organization/delete-user",
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
    url: "/admin/organization/update-user",
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
    url: "/admin/organization/create-user",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          id: 3,
          username: "newuser",
          name: "新用户",
          phone: "13800138003",
          email: "newuser@example.com",
          deptId: 2,
          status: 1,
        },
      };
    },
  },
  {
    url: "/admin/organization/get-role-tree",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: [
          {
            id: 1,
            name: "超级管理员",
            children: [
              { id: 2, name: "管理员" },
              { id: 3, name: "普通用户" },
            ],
          },
        ],
      };
    },
  },
  {
    url: "/admin/organization/get-members",
    method: "post",
    response: (req) => {
      const { role_id, page = 1, limit = 20, keyword = "" } = req.body || {};
      return {
        code: 200,
        message: "success",
        data: {
          items: [
            {
              id: 1,
              username: "admin",
              name: "管理员",
            },
            {
              id: 2,
              username: "user1",
              name: "用户1",
            },
          ],
          total: 2,
        },
      };
    },
  },
  {
    url: "/admin/organization/create-role",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          id: 4,
          name: "新角色",
          status: 1,
          pid: 1,
        },
      };
    },
  },
  {
    url: "/admin/organization/update-role",
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
    url: "/admin/organization/add-members",
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
    url: "/admin/organization/remove-member",
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
    url: "/admin/organization/remove-members-batch",
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
    url: "/admin/organization/import-roles",
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
    url: "/admin/organization/export-roles",
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
    url: "/admin/organization/import-users",
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
    url: "/admin/organization/export-users",
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
    url: "/admin/organization/delete-users-batch",
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
    url: "/admin/organization/export-users-selected",
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
    url: "/admin/organization/delete-users-selected",
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
    url: "/admin/organization/update-users-batch",
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
    url: "/admin/organization/create-dept",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          id: 8,
          name: "新部门",
          pid: 1,
        },
      };
    },
  },
  {
    url: "/admin/organization/update-dept",
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
    url: "/admin/organization/get-available-users",
    method: "post",
    response: (req) => {
      const { role_id, page = 1, limit = 20 } = req.body.data || {};
      return {
        code: 200,
        message: "success",
        data: {
          items: [
            {
              id: 3,
              username: "user3",
              name: "用户3",
            },
          ],
          total: 1,
        },
      };
    },
  },
];
