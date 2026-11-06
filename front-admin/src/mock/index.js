// ========================================
// MOCK 模块配置
// ========================================
// URL 格式：/[前台/后台]/[模块名]/具体方法
// 例如：/admin/admin_user/list, /admin/product/detail
//
// 配置说明：
// true  = 该模块使用 MOCK 数据（拦截请求）
// false = 该模块使用真实后端（转发请求）
// ========================================

// 按模块配置是否使用 mock 数据
const mockModules = [
  ["user", false], // /admin/user/* -> 真实后端
  ["organization", false], // /admin/organization/* -> 真实后端
  ["menu", false], // /admin/menu/* -> 真实后端
  ["notification", false], // /admin/notification/* -> 真实后端
  ["subform", false], // /admin/subform/* -> 真实后端
];

export const mockEnable = Object.fromEntries(mockModules);

// 导入所有 mock 数据
import userMock from "./modules/user";
import organizationMock from "./modules/organization";
import menuMock from "./modules/menu";
import notificationMock from "./modules/notification";
import subformMock from "./modules/subform";

// 模块到 mock 数据的映射
const mockDataMap = {
  user: userMock,
  organization: organizationMock,
  menu: menuMock,
  notification: notificationMock,
  subform: subformMock,
};

// 生成 mock 列表
const mockList = mockModules
  .filter(([name]) => mockEnable[name])
  .flatMap(([name]) => mockDataMap[name] || []);

export default mockList;

// 导出启用的模块列表
export const enabledModules = mockModules
  .filter(([name]) => mockEnable[name])
  .map(([name]) => name);

// 统计信息
const totalModules = mockModules.length;
const enabledCount = enabledModules.length;

console.log("[Mock] 模块配置:");
mockModules.forEach(([name]) => {
  const status = mockEnable[name] ? "✓ MOCK" : "✗ 真实后端";
  console.log(`  ${name}: ${status}`);
});
console.log(`[Mock] 总计: ${enabledCount}/${totalModules} 个模块使用 MOCK`);
