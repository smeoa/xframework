import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { readFileSync } from "fs";
import { resolve } from "path";
import { createRequire } from "module";

const __dirname = resolve(fileURLToPath(new URL(".", import.meta.url)));
const require = createRequire(import.meta.url);

// 加载 mock 配置和数据
async function loadMockConfig() {
  try {
    const mockModule = await import('./src/mock/index.js');
    const mockList = mockModule.default || [];
    
    console.log('[Mock] 模块配置已加载（从 src/mock/index.js）');
    return mockList;
  } catch (e) {
    console.error('[Mock] 无法读取配置:', e.message);
    return [];
  }
}

// 构建路由映射
function buildRouteMap(mockList) {
  const routeMap = new Map();

  for (const mock of mockList) {
    const key = `${mock.method.toUpperCase()}:${mock.url}`;
    if (!routeMap.has(key)) {
      routeMap.set(key, { mock, module: 'unknown' });
    }
  }

  return routeMap;
}

// 全局变量存储路由映射
let routeMap = new Map();

// 初始化 mock 配置
(async () => {
  const mockList = await loadMockConfig();
  routeMap = buildRouteMap(mockList);
  console.log(`[Mock] 总计注册 ${routeMap.size} 个接口`);
})();

// 解析请求体
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        resolve({});
      }
    });
    req.on('error', reject);
  });
}

// 创建 mock 中间件
function createMockMiddleware() {
  return async (req, res, next) => {
    const startTime = Date.now();
    const path = req.url.split('?')[0];
    const method = req.method.toUpperCase();
    const key = `${method}:${path}`;

    if (!path.startsWith('/admin/')) {
      next();
      return;
    }

    const entry = routeMap.get(key);
    if (!entry) {
      next();
      return;
    }

    // 跳过文件上传类请求（multipart），直接转发给后端
    const contentType = req.headers['content-type'] || '';
    if (contentType.includes('multipart/form-data')) {
      next();
      return;
    }

    const duration = Date.now() - startTime;

    try {
      const body = await parseBody(req);
      const response = typeof entry.mock.response === 'function'
        ? entry.mock.response({ body: body })
        : entry.mock.response;

      console.log(`[Mock] ✓ ${method} ${path} (${duration}ms)`);

      res.setHeader('Content-Type', 'application/json');
      res.statusCode = 200;
      res.end(JSON.stringify(response));
    } catch (e) {
      console.error(`[Mock] ✗ ${method} ${path}: ${e.message}`);
      res.statusCode = 500;
      res.end(JSON.stringify({ code: 500, message: e.message }));
    }
  };
}

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'vite-plugin-mock-module',
      configureServer(server) {
        server.middlewares.use(createMockMiddleware());
        console.log('[Mock] 中间件已注册（从 src/mock/modules/ 加载）');
      }
    }
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 3000,
    // 固定端口：3000 被占用时直接报错，而不是静默漂移到 3001
    // （Playwright baseURL 与后端代理约定都按 3000，漂移会导致「改了代码没生效」的错觉）
    strictPort: true,
    // 监听所有网卡，便于通过局域网 IP 访问开发服务器与 HMR
    host: true,
    proxy: {
      "/admin/": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true
      },
      "/api/": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true
      },
      // 素材文件由前台站点托管，代理后后台可直接预览 /images/** 相对地址
      "/images/": {
        target: "http://localhost:3011",
        changeOrigin: true
      },
      "/ws/": {
        target: "ws://localhost:8000",
        ws: true
      }
    },
    historyApiFallback: true
  },
});
