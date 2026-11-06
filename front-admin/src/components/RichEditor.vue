<template>
  <div class="rich-editor">
    <Toolbar class="rich-editor-toolbar" :editor="editorRef" :default-config="toolbarConfig" mode="default" />
    <Editor v-model="html" class="rich-editor-body" :default-config="editorConfig" mode="default" :style="{ height }"
      @on-created="handleCreated" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import '@wangeditor/editor/dist/css/style.css'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import request from '@/utils/request'

const UPLOAD_API = '/admin/attachment/upload-attachment'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '请输入内容' },
  height: { type: String, default: '320px' },
  readonly: { type: Boolean, default: false },
  module: { type: String, default: 'product' },
})

const emit = defineEmits(['update:modelValue'])

// 编辑器 HTML 内容（与父级 v-model 双向同步）
const html = ref(props.modelValue || '')

// 编辑器实例用浅响应持有，避免 wangEditor 内部结构被 Vue 代理
const editorRef = shallowRef(null)

// 全屏按钮会把编辑区脱离弹窗层级，排除
const toolbarConfig = { excludeKeys: ['fullScreen'] }

const editorConfig = {
  placeholder: props.placeholder,
  readOnly: props.readonly,
  MENU_CONF: {
    uploadImage: {
      // 改用项目统一附件接口，默认上传地址不可用
      async customUpload(file, insertFn) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('module', props.module)
        try {
          const res = await request.post(UPLOAD_API, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000,
          })
          if (res.code !== 200) {
            ElMessage.error(res.message || '图片上传失败')
            return
          }
          const url = res.data?.storagePath || res.data?.url || ''
          if (!url) {
            ElMessage.error('图片上传失败：未返回图片地址')
            return
          }
          insertFn(url, res.data?.filename || file.name, url)
        } catch (error) {
          ElMessage.error(error.message || '图片上传失败')
        }
      },
    },
  },
}

const handleCreated = (editor) => {
  editorRef.value = editor
}

watch(
  () => props.modelValue,
  (value) => {
    if (value !== html.value) html.value = value || ''
  },
)

watch(html, (value) => {
  if (value !== props.modelValue) emit('update:modelValue', value)
})

onBeforeUnmount(() => {
  const editor = editorRef.value
  if (editor) editor.destroy()
  editorRef.value = null
})
</script>

<style scoped>
.rich-editor {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.rich-editor-toolbar {
  border-bottom: 1px solid #dcdfe6;
}

.rich-editor-body {
  overflow-y: hidden;
}
</style>
