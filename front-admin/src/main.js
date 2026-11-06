import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";
import "./style/global.css";
import App from "./App.vue";
import router from "./router";
import { bindRouter } from "./utils/pageSubtitle";
import permission from "./directives/permission";

const app = createApp(App);
const pinia = createPinia();

// 注入路由实例，供页面 header 副标题按当前菜单分别存取（详见 utils/pageSubtitle.js）
bindRouter(router);

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.directive("permission", permission);

app.use(pinia);
app.use(router);
app.use(ElementPlus, {
  locale: zhCn,
});

app.mount("#app");
