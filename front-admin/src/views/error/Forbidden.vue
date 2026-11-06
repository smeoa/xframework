<template>
  <div class="forbidden-container">
    <el-result icon="warning" title="403" sub-title="很抱歉，你没有访问该页面的权限">
      <template #extra>
        <el-button type="primary" @click="goBack">返回上一页</el-button>
        <el-button @click="goHome">回到首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { resolveHomePath } from "@/utils/homePath";

const router = useRouter();

const goHome = async () => {
  const path = await resolveHomePath(router);
  if (!path || path === router.currentRoute.value.path) {
    ElMessage.warning("当前账号没有可访问的页面");
    return;
  }
  router.replace(path);
};

const goBack = async () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  await goHome();
};
</script>

<style scoped>
.forbidden-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
