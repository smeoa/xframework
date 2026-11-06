import { h } from "vue";
import { ElButton, ElNotification, ElMessage } from "element-plus";
import { downloadFileWithToken } from "@/utils/fileUtils";
import { deepCamelToSnake, snakeToCamel } from "@/utils/request";

class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageHandlers = [];
    this.reconnectTimeout = null;
    // 自动连接
    this.connect();
  }

  // 连接 WebSocket（幂等：已有连接时复用，不会重复建连）
  connect() {
    // 连接中或已连接时直接复用，避免同一客户端重复建连
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)
    ) {
      if (this.ws.readyState === WebSocket.OPEN) {
        // 连接已就绪但可能尚未注册（如登录后重新进入布局），补发注册消息
        this.register();
      }
      return;
    }

    // 旧连接已失效，解除其监听，避免其关闭时再触发一次重连
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log("WebSocket 连接已建立");
        this.connected = true;
        this.reconnectAttempts = 0;
        // 延迟发送注册消息，确保连接完全建立
        setTimeout(() => {
          this.register();
        }, 100);
      };

      this.ws.onmessage = (event) => {
        try {
          // 与 request.js 同一套转换：后端推送的 snake_case 键名统一转为 camelCase
          const message = snakeToCamel(JSON.parse(event.data));
          this.handleMessage(message);
        } catch (error) {
          console.error("解析 WebSocket 消息失败:", error);
        }
      };

      this.ws.onclose = () => {
        console.log("WebSocket 连接已关闭");
        this.connected = false;
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket 错误:", error);
      };
    } catch (error) {
      console.error("WebSocket 连接失败:", error);
      this.attemptReconnect();
    }
  }

  // 注册用户
  register(user_id) {
    const targetUserId = user_id || this.getCurrentUserId();
    if (targetUserId === null || targetUserId === undefined || targetUserId === "") {
      // 未登录（无用户ID）时不注册，避免后端按错误ID路由
      return;
    }
    if (this.connected && this.ws && this.ws.readyState === 1) {
      this.send({
        type: "register",
        userId: targetUserId,
      });
    } else {
      // 连接尚未完全建立，延迟发送注册消息
      setTimeout(() => {
        this.register(targetUserId);
      }, 100);
    }
  }

  // 读取当前登录用户ID（用于后端按用户定向推送消息）
  getCurrentUserId() {
    try {
      const raw = localStorage.getItem("user");
      const user = raw ? JSON.parse(raw) : null;
      return user && user.id != null ? user.id : null;
    } catch (error) {
      return null;
    }
  }

  // 断开连接
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected = false;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  // 尝试重连
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `尝试重连 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
      );

      this.reconnectTimeout = setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error("WebSocket 重连失败，已达到最大尝试次数");
    }
  }

  // 发送消息（与 request.js 同一套转换：camelCase → snake_case）
  send(message) {
    if (this.connected && this.ws && this.ws.readyState === 1) {
      try {
        this.ws.send(JSON.stringify(deepCamelToSnake(message)));
        return true;
      } catch (error) {
        console.error("发送 WebSocket 消息失败:", error);
        return false;
      }
    } else {
      console.error("WebSocket 未连接或连接尚未完全建立，无法发送消息");
      return false;
    }
  }

  // 处理接收到的消息
  handleMessage(message) {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error("处理 WebSocket 消息失败:", error);
      }
    });
  }

  // 添加消息处理器
  onMessage(handler) {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
    };
  }

  // 监听导出完成消息
  onExportComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "export_complete") {
        callback(message);
      }
    });
  }

  // 监听导出错误消息
  onExportError(callback) {
    return this.onMessage((message) => {
      if (message.type === "export_error") {
        callback(message);
      }
    });
  }

  // 监听 AI 打标完成消息
  onAiTagComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "ai_tag_complete") {
        callback(message);
      }
    });
  }

  // 监听 AI 打标失败消息
  onAiTagError(callback) {
    return this.onMessage((message) => {
      if (message.type === "ai_tag_error") {
        callback(message);
      }
    });
  }

  // 监听 AI 完善（类目匹配 + 属性完善）完成消息
  onAiEnhanceComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "ai_enhance_complete") {
        callback(message);
      }
    });
  }

  // 监听 AI 完善失败消息
  onAiEnhanceError(callback) {
    return this.onMessage((message) => {
      if (message.type === "ai_enhance_error") {
        callback(message);
      }
    });
  }

  // 监听平台产品扩展功能任务消息（定价规则 / 图片处理 / SKU 优化 / 发布检查）
  onTaskMessage(subtype, callback) {
    return this.onMessage((message) => {
      if (message.type === `${subtype}_complete` || message.type === `${subtype}_error`) {
        callback(message);
      }
    });
  }

  // 监听定价规则完成消息
  onPricingRuleComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "pricing_rule_complete") {
        callback(message);
      }
    });
  }

  // 监听定价规则失败消息
  onPricingRuleError(callback) {
    return this.onMessage((message) => {
      if (message.type === "pricing_rule_error") {
        callback(message);
      }
    });
  }

  // 监听内容加工（图片处理 / SKU优化 / SEO优化）完成消息
  onContentProcessComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "content_process_complete") {
        callback(message);
      }
    });
  }

  // 监听内容加工排队位次消息（前方任务开始执行时推送最新位次）
  onContentProcessQueued(callback) {
    return this.onMessage((message) => {
      if (message.type === "content_process_queued") {
        callback(message);
      }
    });
  }

  // 监听内容加工失败消息
  onContentProcessError(callback) {
    return this.onMessage((message) => {
      if (message.type === "content_process_error") {
        callback(message);
      }
    });
  }

  // 监听发布完成消息
  onPublishComplete(callback) {
    return this.onMessage((message) => {
      if (message.type === "publish_complete") {
        callback(message);
      }
    });
  }

  // 监听发布失败消息
  onPublishError(callback) {
    return this.onMessage((message) => {
      if (message.type === "publish_error") {
        callback(message);
      }
    });
  }

  // 监听后台任务批次进度消息（type = {subtype}_progress），用于渲染任务进度条
  onTaskProgress(callback) {
    return this.onMessage((message) => {
      if (typeof message?.type === "string" && message.type.endsWith("_progress")) {
        callback(message);
      }
    });
  }

  // 监听任务结束消息（type = {subtype}_complete / {subtype}_error），用于清理任务进度条
  onTaskSettled(callback) {
    return this.onMessage((message) => {
      if (typeof message?.type === "string" && /_(complete|error)$/.test(message.type)) {
        callback(message);
      }
    });
  }

  // 检查连接状态
  isConnected() {
    return this.connected;
  }

  // 启用默认的导出通知
  enableExportNotifications() {
    this.onExportComplete((message) => {
      ElNotification({
        title: "导出文件准备完成",
        // 用按钮替代直链：直链无法携带 token，会被后端鉴权拦截
        message: h("div", null, [
          h("div", null, "导出文件已准备完成。文件下载链接将于24小时后失效"),
          h(
            ElButton,
            {
              type: "primary",
              size: "small",
              style: { marginTop: "8px" },
              onClick: () => downloadFileWithToken(message.fileUrl, "导出文件.xlsx"),
            },
            () => "立即下载",
          ),
        ]),
        type: "success",
        duration: 0, // 不自动关闭
        showClose: true,
        customClass: "download-notification",
        offset: 80,
      });
    });

    this.onExportError((message) => {
      ElMessage.error(message.message);
    });
  }
}

// 创建单例实例
// 使用同源地址：dev 由 vite proxy(/ws/) 转发，生产由 Nginx 反向代理转发；
// 若写死 ws://localhost:8000，反代部署后浏览器会误连用户本机导致连接失败
const clientId = "client_" + Math.random().toString(36).substr(2, 9);
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsManager = new WebSocketManager(`${wsProtocol}//${window.location.host}/ws/${clientId}`);

export default wsManager;
