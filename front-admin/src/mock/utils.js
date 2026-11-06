// Mock 工具函数

// 生成唯一 ID
let idCounter = 100;
const generateId = () => idCounter++;

// 模拟列表接口
export const mockList = (data) => (req, res) => {
  res.json({
    code: 200,
    data: data,
  });
};

// 模拟详情接口
export const mockDetail = (data) => (req, res) => {
  const { id } = req.params;
  const item = data.find((item) => item.id === parseInt(id));
  if (item) {
    res.json({
      code: 200,
      data: item,
    });
  } else {
    res.json({
      code: 404,
      message: "数据不存在",
    });
  }
};

// 模拟创建接口
export const mockCreate = (data) => (req, res) => {
  const newItem = {
    id: generateId(),
    ...req.body,
    create_time: new Date().toISOString().slice(0, 19).replace("T", " "),
    update_time: new Date().toISOString().slice(0, 19).replace("T", " "),
    create_by: 1,
    update_by: 1,
    status: 1,
  };
  data.push(newItem);
  res.json({
    code: 200,
    data: newItem,
  });
};

// 模拟更新接口
export const mockUpdate = (data) => (req, res) => {
  const { id } = req.params;
  const item = data.find((item) => item.id === parseInt(id));
  if (item) {
    Object.assign(item, req.body);
    item.update_time = new Date().toISOString().slice(0, 19).replace("T", " ");
    item.update_by = 1;
    res.json({
      code: 200,
      data: item,
    });
  } else {
    res.json({
      code: 404,
      message: "数据不存在",
    });
  }
};

// 模拟删除接口
export const mockDelete = (data) => (req, res) => {
  const { id } = req.params;
  const index = data.findIndex((item) => item.id === parseInt(id));
  if (index !== -1) {
    data.splice(index, 1);
    res.json({
      code: 200,
      message: "删除成功",
    });
  } else {
    res.json({
      code: 404,
      message: "数据不存在",
    });
  }
};

// 模拟状态更新接口
export const mockStatus = (data) => (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  const item = data.find((item) => item.id === parseInt(id));
  if (item) {
    item.status = status;
    item.update_time = new Date().toISOString().slice(0, 19).replace("T", " ");
    item.update_by = 1;
    res.json({
      code: 200,
      data: item,
    });
  } else {
    res.json({
      code: 404,
      message: "数据不存在",
    });
  }
};
