import { hasAnyPermission } from "@/utils/permission";

/**
 * 按钮级权限指令
 *
 * 用法：
 *   v-permission="'org:role:create'"          单个权限码
 *   v-permission="['org:role:update', 'org:role:grant']"  多码「或」关系
 *
 * 无权限时直接移除元素；管理员与不传权限码时不做限制。
 */
const permission = {
  mounted(el, binding) {
    const codes = binding.value;
    if (!codes || (Array.isArray(codes) && codes.length === 0)) {
      return;
    }
    if (!hasAnyPermission(codes)) {
      if (el.parentNode) {
        el.parentNode.removeChild(el);
      }
    }
  },
};

export default permission;
