/**
 * 文件工具函数
 *
 * 提供统一的文件处理功能：
 * - URL 编码/解码处理
 * - 文件类型判断
 * - URL 验证
 * - 文件名提取
 */

import { ElMessage } from "element-plus";
import request from "@/utils/request";

/**
 * 图片格式列表
 */
export const IMAGE_EXTENSIONS = [
  ".jpg",
  ".jpeg",
  ".png",
  ".gif",
  ".bmp",
  ".webp",
  ".svg",
  ".ico",
];

/**
 * 视频格式列表
 */
export const VIDEO_EXTENSIONS = [
  ".mp4",
  ".webm",
  ".ogg",
  ".mov",
  ".avi",
  ".wmv",
  ".flv",
  ".mkv",
];

/**
 * 音频格式列表
 */
export const AUDIO_EXTENSIONS = [
  ".mp3",
  ".wav",
  ".ogg",
  ".aac",
  ".flac",
  ".m4a",
  ".wma",
];

/**
 * PDF格式列表
 */
export const PDF_EXTENSIONS = [".pdf"];

/**
 * Office文档格式列表
 */
export const OFFICE_EXTENSIONS = [
  ".doc",
  ".docx",
  ".xls",
  ".xlsx",
  ".ppt",
  ".pptx",
  "txt",
  "csv",
];

/**
 * 获取文件扩展名
 * @param {string} filename - 文件名或URL
 * @returns {string} 扩展名（不含点号）
 */
export const getFileExtension = (filename) => {
  if (!filename) return "";

  let name = filename;

  // 如果是 URL，先提取路径部分（去掉查询参数）
  if (filename.startsWith("http://") || filename.startsWith("https://")) {
    try {
      const urlObj = new URL(filename);
      name = urlObj.pathname;
    } catch {
      // 如果 URL 解析失败，手动去掉查询参数
      const qIndex = filename.indexOf("?");
      if (qIndex !== -1) {
        name = filename.substring(0, qIndex);
      }
    }
  } else {
    // 普通文件名，去掉查询参数
    const qIndex = filename.indexOf("?");
    if (qIndex !== -1) {
      name = filename.substring(0, qIndex);
    }
  }

  const lastDot = name.lastIndexOf(".");
  if (lastDot === -1) return "";
  return name.substring(lastDot + 1).toLowerCase();
};

/**
 * 判断是否为图片文件
 * @param {string} filename - 文件名或URL
 * @returns {boolean}
 */
export const isImage = (filename) => {
  if (!filename) return false;
  const ext = getFileExtension(filename);
  return IMAGE_EXTENSIONS.includes(`.${ext}`);
};

/**
 * 判断是否为视频文件
 * @param {string} filename - 文件名或URL
 * @returns {boolean}
 */
export const isVideo = (filename) => {
  if (!filename) return false;
  const ext = getFileExtension(filename);
  return VIDEO_EXTENSIONS.includes(`.${ext}`);
};

/**
 * 判断是否为音频文件
 * @param {string} filename - 文件名或URL
 * @returns {boolean}
 */
export const isAudio = (filename) => {
  if (!filename) return false;
  const ext = getFileExtension(filename);
  return AUDIO_EXTENSIONS.includes(`.${ext}`);
};

/**
 * 判断是否为PDF文件
 * @param {string} filename - 文件名或URL
 * @returns {boolean}
 */
export const isPdf = (filename) => {
  if (!filename) return false;
  const ext = getFileExtension(filename);
  return PDF_EXTENSIONS.includes(`.${ext}`);
};

/**
 * 判断是否为Office文档
 * @param {string} filename - 文件名或URL
 * @returns {boolean}
 */
export const isOffice = (filename) => {
  if (!filename) return false;
  const ext = getFileExtension(filename);
  return OFFICE_EXTENSIONS.includes(`.${ext}`);
};

/**
 * 从URL中提取文件名
 * @param {string} url - 文件URL
 * @returns {string} 文件名
 */
export const getFileNameFromUrl = (url) => {
  if (!url) return "";
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const filename = pathname.split("/").pop() || "";
    // 去掉查询参数（如果 URL 对象没有自动去掉）
    const queryIndex = filename.indexOf("?");
    const cleanFilename =
      queryIndex !== -1 ? filename.substring(0, queryIndex) : filename;
    return decodeURIComponent(cleanFilename) || "";
  } catch {
    // 如果不是有效URL，尝试从字符串中提取
    const lastSlash = url.lastIndexOf("/");
    const lastQM = url.lastIndexOf("?");
    if (lastSlash !== -1) {
      const filename =
        lastQM !== -1 && lastQM > lastSlash
          ? url.substring(lastSlash + 1, lastQM)
          : url.substring(lastSlash + 1);
      try {
        return decodeURIComponent(filename);
      } catch {
        return filename;
      }
    }
    // 去掉查询参数
    const queryIndex = url.indexOf("?");
    return queryIndex !== -1 ? url.substring(0, queryIndex) : url;
  }
};

/**
 * 清理URL，处理编码问题
 * 主要用于处理七牛云等对象存储的URL
 *
 * @param {string} url - 原始URL
 * @returns {string} 清理后的URL
 */
export const cleanUrl = (url) => {
  if (!url) return "";

  // 如果不是 HTTP/HTTPS URL，直接返回
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    return url;
  }

  try {
    // 尝试提取 URL 中的路径部分并清理
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split("/");

      // 对每个路径部分进行编码/解码处理
      const processedPathParts = pathParts.map((part) => {
        try {
          return decodeURIComponent(part);
        } catch {
          return part;
        }
      });

      // 重新组装路径
      urlObj.pathname = processedPathParts.join("/");

      return urlObj.toString();
    } catch {
      // 如果 URL 解析失败，尝试直接解码和重新编码
      try {
        const decoded = decodeURIComponent(url);
        return encodeURI(decoded);
      } catch {
        return url;
      }
    }
  } catch (e) {
    return url;
  }
};

/**
 * 处理文件预览URL
 * 自动判断文件类型并处理URL编码
 *
 * @param {string} url - 文件URL
 * @param {string} filename - 文件名（可选）
 * @returns {object} 包含 url, type, name 的对象
 */
export const processFilePreview = (url, filename = "") => {
  return {
    url: cleanUrl(url),
    type: getFileExtension(filename || url),
    name: filename || getFileNameFromUrl(url),
  };
};

/**
 * 格式化文件大小
 * @param {number|string} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return "";
  const sizeNum = typeof bytes === "string" ? parseInt(bytes) : bytes;
  if (sizeNum === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(sizeNum) / Math.log(k));
  return parseFloat((sizeNum / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

/**
 * 下载文件
 * @param {string} url - 文件URL
 * @param {string} filename - 下载时的文件名（可选）
 */
export const downloadFile = (url, filename = "") => {
  if (!url) {
    console.warn("文件链接不存在");
    return;
  }

  const link = document.createElement("a");
  link.href = cleanUrl(url);
  link.target = "_blank";

  if (filename) {
    link.download = filename;
  } else {
    try {
      const name = getFileNameFromUrl(url);
      link.download = name || "download";
    } catch {
      link.download = "download";
    }
  }

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * 携带登录 token 下载后端受保护的文件（Blob 方式）
 *
 * 直链下载（a 标签 / window.open）无法携带 Authorization 请求头，会被后端
 * 鉴权拦截，因此改为通过 request 发起带 token 的请求，拿到二进制流后
 * 在前端触发保存。
 *
 * @param {string} url - 后端下载接口地址
 * @param {string} fallbackFilename - 响应头未携带文件名时使用的默认文件名
 * @returns {Promise<boolean>} 是否下载成功
 */
export const downloadFileWithToken = async (
  url,
  fallbackFilename = "download",
) => {
  if (!url) {
    ElMessage.warning("文件链接不存在");
    return false;
  }

  try {
    ElMessage({
      message: "下载开始，正在处理...",
      type: "info",
      duration: 3000,
    });

    // responseType=blob 时 request 拦截器原样返回完整 response；
    // 出错时拦截器会把响应体降级为空对象，因此需校验 data 类型。
    // 导出文件可能较大，关闭默认 10s 超时避免下载被中断
    const response = await request.get(url, {
      responseType: "blob",
      timeout: 0,
    });
    if (!response || !(response.data instanceof Blob)) {
      throw new Error("文件不存在或已过期");
    }

    // 后端异常时可能以 JSON 响应体返回错误说明，需识别出来按失败处理
    if (response.data.type.includes("application/json")) {
      const payload = JSON.parse(await response.data.text());
      throw new Error(payload.message || payload.detail || "下载失败");
    }

    // 解析响应头中的文件名：优先取 RFC 5987 的 filename*（中文名在此，需解码），
    // 其次回退到普通 filename（兼容带引号与不带引号两种写法）
    let filename = fallbackFilename;
    const disposition = response.headers["content-disposition"];
    if (disposition) {
      const utf8Matched = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      const plainMatched = disposition.match(/filename="?([^";]+)"?/i);
      if (utf8Matched) {
        filename = decodeURIComponent(utf8Matched[1].trim());
      } else if (plainMatched) {
        filename = plainMatched[1].trim();
      }
    }

    const blobUrl = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(blobUrl);

    ElMessage({
      message: "下载完成",
      type: "success",
      duration: 2000,
    });
    return true;
  } catch (error) {
    console.error("下载失败:", error);
    ElMessage({
      message: error.message || "下载失败，请稍后重试",
      type: "error",
      duration: 3000,
    });
    return false;
  }
};

/**
 * 在新标签页打开文件
 * @param {string} url - 文件URL
 */
export const openInNewTab = (url) => {
  if (!url) {
    console.warn("文件链接不存在");
    return;
  }
  window.open(cleanUrl(url), "_blank");
};

/**
 * 获取文件图标类型
 * @param {string} filename - 文件名或URL
 * @returns {string} 图标类型：'image', 'video', 'audio', 'pdf', 'office', 'file'
 */
export const getFileIconType = (filename) => {
  if (isImage(filename)) return "image";
  if (isVideo(filename)) return "video";
  if (isAudio(filename)) return "audio";
  if (isPdf(filename)) return "pdf";
  if (isOffice(filename)) return "office";
  return "file";
};

/**
 * 验证URL是否有效
 * @param {string} url - URL字符串
 * @returns {boolean}
 */
export const isValidUrl = (url) => {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * 从文件名中移除 UUID 部分
 * 支持格式：
 * - 文件名_uuid.扩展名（如：图片_abc123def456.jpg）
 * - uuid_文件名.扩展名（如：abc123def456_图片.jpg）
 * - uuid.扩展名（如：abc123def456.jpg）
 * - URL 查询参数（如：文件名.jpg?e=xxx&token=xxx）
 *
 * @param {string} filename - 文件名
 * @returns {string} 去掉UUID后的文件名
 */
export const removeUuidFromFilename = (filename) => {
  if (!filename) return "";

  let result = filename;

  // 第一步：去掉 URL 查询参数（如 ?e=xxx&token=xxx）
  const questionMarkIndex = result.indexOf("?");
  if (questionMarkIndex !== -1) {
    result = result.substring(0, questionMarkIndex);
  }

  // 第二步：去掉 UUID 部分
  // UUID 正则表达式：
  // 1. 带连字符的标准格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  // 2. 纯32位字符格式：a4e429185d8c4937b3a0e72617e0aa9d

  // 模式1：标准 UUID 格式（带连字符）
  const standardUuidPattern =
    /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
  let matches = result.match(standardUuidPattern);
  if (matches) {
    for (const uuid of matches) {
      const escapedUuid = uuid.replace(/-/g, "[_-]?");
      const uuidRegex = new RegExp(`[_-]?${escapedUuid}[_-]?`, "gi");
      result = result.replace(uuidRegex, "_");
    }
  }

  // 模式2：32位连续字符格式（无连字符）
  // 匹配32个连续十六进制字符，前面可能有分隔符
  const uuid32Pattern = /[_-]?([0-9a-f]{32})[_-]?/gi;
  matches = result.match(uuid32Pattern);
  if (matches) {
    for (const match of matches) {
      // 提取UUID部分（去掉前后分隔符）
      const uuid32Regex = /[_-]?([0-9a-f]{32})[_-]?/i;
      const uuidMatch = match.match(uuid32Regex);
      if (uuidMatch) {
        const uuid = uuidMatch[1];
        // 替换整个匹配（包括前后分隔符）为单个下划线
        const fullRegex = new RegExp(`[_-]?${uuid}[_-]?`, "gi");
        result = result.replace(fullRegex, "_");
      }
    }
  }

  // 第三步：清理多余的下划线
  result = result.replace(/_+/g, "_");

  // 检查文件名是否以扩展名结尾，如果是则去掉前导下划线
  const hasExtension = /\.[a-zA-Z0-9]+$/.test(result);
  if (hasExtension && result.startsWith("_")) {
    result = result.substring(1);
  }

  return result;
};
