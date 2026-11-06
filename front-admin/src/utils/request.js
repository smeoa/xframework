import axios from "axios";
import { ElMessage } from "element-plus";

// 辅助函数：camelCase 转 snake_case
function camelToSnake(str) {
  if (typeof str !== "string") {
    return str;
  }
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

// 平台专用产品信息容器（与 admin/platform/platform_constant.py 的平台一一对应）
// 容器下一级键是平台字段名，与数据库列名一一对应，仍需做驼峰↔下划线转换；
// 再往下是该 JSONB 列中保存的平台原始 JSON，键名必须原样保留，
// 否则会破坏平台侧语义（如区域价格 {"US":1.5} 会被改写成 {"_u_s":1.5}）
const PLATFORM_PAYLOAD_KEYS = new Set(["dhgate", "voghion"]);

// 平台容器内第 1 层键（= 数据库列名）参与转换，第 2 层及以后原样保留
const PLATFORM_RAW_DEPTH = 2;

// 辅助函数：深度转换对象键名。
// platformDepth 表示已进入平台容器的层级：0 = 未进入；1 = 容器本身；2 = 容器内部
function deepConvertKeys(obj, mapper, platformDepth = 0) {
  if (obj === null || typeof obj !== "object") {
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map((item) => deepConvertKeys(item, mapper, platformDepth));
  }
  const keepKey = platformDepth >= PLATFORM_RAW_DEPTH;
  const result = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      // 已进入容器内部：再往下的层级全部保持原样
      const nextDepth =
        platformDepth > 0
          ? PLATFORM_RAW_DEPTH
          : PLATFORM_PAYLOAD_KEYS.has(key)
            ? 1
            : 0;
      result[keepKey ? key : mapper(key)] = deepConvertKeys(
        obj[key],
        mapper,
        nextDepth,
      );
    }
  }
  return result;
}

// 辅助函数：深度转换 camelCase 对象为 snake_case
function deepCamelToSnake(obj) {
  return deepConvertKeys(obj, camelToSnake);
}

// 辅助函数：单个键名 snake_case 转 camelCase
function snakeToCamelKey(key) {
  if (typeof key !== "string") {
    return key;
  }
  return key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

// 辅助函数：snake_case 转 camelCase
function snakeToCamel(obj) {
  return deepConvertKeys(obj, snakeToCamelKey);
}

// 键名转换工具导出：WebSocket 消息、本地缓存的字段配置等复用同一套转换，
// 保证「请求体 / 响应体 / 推送消息 / 本地缓存」四处 camelCase 口径完全一致
export { camelToSnake, deepCamelToSnake, snakeToCamel, snakeToCamelKey };

const request = axios.create({
  baseURL: "", // 使用空字符串，请求发到当前服务器，由 MOCK 或代理处理
  timeout: 10000,
});

// 请求拦截器：注入 Authorization + camelCase → snake_case
request.interceptors.request.use((config) => {
  // 注入登录 token（FormData 请求同样需要）
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  // 跳过 FormData 对象的转换，因为它会破坏文件上传
  if (config.data && !(config.data instanceof FormData)) {
    config.data = deepCamelToSnake(config.data);
  }
  return config;
});

request.interceptors.response.use(
  (response) => {
    // 如果是二进制响应，直接返回response对象
    if (response.config.responseType === "blob") {
      return response;
    }
    // 否则返回转换后的数据（axios会将其放在 response.data 中）
    const transformedData = snakeToCamel(response.data);
    return transformedData;
  },
  (error) => {
    // 处理错误响应
    if (error.response) {
      // 401：清理本地登录态并按需跳转登录页
      if (error.response.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        const url = (error.config && error.config.url) || "";
        const isLoginRequest = url.includes("/admin/auth/login");
        const isLoginPage = window.location.pathname === "/login";
        if (!isLoginRequest && !isLoginPage) {
          window.location.href = "/login";
        }
      }
      // 403：已登录但缺少操作权限
      if (error.response.status === 403) {
        const detail = (error.response.data && error.response.data.detail) || "";
        ElMessage.error(detail || "没有执行该操作的权限");
      }
      // 如果有响应数据，转换后返回
      if (error.response.data) {
        const transformedData = snakeToCamel(error.response.data);
        return Promise.resolve(transformedData);
      }
    }
    ElMessage.error(error.message || "请求失败");
    return Promise.reject(error);
  },
);

export default request;
