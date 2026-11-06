// 菜单模块的 mock 数据
export default [
  {
    url: "/admin/menu/get-menu-tree",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: [
          {
            id: 1,
            name: "系统管理",
            children: [
              { id: 2, name: "用户管理" },
              { id: 3, name: "角色管理" },
              { id: 4, name: "权限管理" },
            ],
          },
          {
            id: 5,
            name: "内容管理",
            children: [
              { id: 6, name: "文章管理" },
              { id: 7, name: "分类管理" },
            ],
          },
          {
            id: 8,
            name: "商品管理",
            children: [
              { id: 9, name: "商品列表" },
              { id: 10, name: "商品分类" },
            ],
          },
        ],
      };
    },
  },
  {
    url: "/admin/menu/get-menu-list",
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
              name: "系统管理",
              path: "/system",
              icon: "Setting",
              type: 1,
              status: 1,
              pid: null,
            },
            {
              id: 2,
              name: "用户管理",
              path: "/system/user",
              icon: "User",
              type: 2,
              status: 1,
              pid: 1,
            },
            {
              id: 3,
              name: "角色管理",
              path: "/system/role",
              icon: "UserFilled",
              type: 2,
              status: 1,
              pid: 1,
            },
            {
              id: 4,
              name: "权限管理",
              path: "/system/permission",
              icon: "Lock",
              type: 2,
              status: 1,
              pid: 1,
            },
            {
              id: 5,
              name: "内容管理",
              path: "/content",
              icon: "Document",
              type: 1,
              status: 1,
              pid: null,
            },
            {
              id: 6,
              name: "文章管理",
              path: "/content/article",
              icon: "Document",
              type: 2,
              status: 1,
              pid: 5,
            },
            {
              id: 7,
              name: "分类管理",
              path: "/content/category",
              icon: "Menu",
              type: 2,
              status: 1,
              pid: 5,
            },
            {
              id: 8,
              name: "商品管理",
              path: "/product",
              icon: "Goods",
              type: 1,
              status: 1,
              pid: null,
            },
            {
              id: 9,
              name: "商品列表",
              path: "/product/list",
              icon: "Goods",
              type: 2,
              status: 1,
              pid: 8,
            },
            {
              id: 10,
              name: "商品分类",
              path: "/product/category",
              icon: "Menu",
              type: 2,
              status: 1,
              pid: 8,
            },
          ],
          total: 10,
        },
      };
    },
  },
  {
    url: "/admin/menu/delete-menu",
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
    url: "/admin/menu/update-menu",
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
    url: "/admin/menu/create-menu",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          id: 11,
          name: "新菜单",
          path: "/new",
          icon: "Document",
          type: 1,
          status: 1,
          pid: null,
        },
      };
    },
  },
  {
    url: "/admin/menu/import",
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
    url: "/admin/menu/export",
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
    url: "/admin/menu/delete-menus-batch",
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
    url: "/admin/menu/export-selected",
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
    url: "/admin/menu/delete-menus-selected",
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
    url: "/admin/menu/update-menus-batch",
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
