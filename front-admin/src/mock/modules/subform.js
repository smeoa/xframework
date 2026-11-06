/**
 * 子表单管理 Mock 数据
 */

export default [
  {
    url: "/admin/subform/list",
    method: "post",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          items: [],
          total: 0,
        },
      };
    },
  },
  {
    url: "/admin/subform/detail",
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
    url: "/admin/subform/create",
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
    url: "/admin/subform/update",
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
    url: "/admin/subform/delete",
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