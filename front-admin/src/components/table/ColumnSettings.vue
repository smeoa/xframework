<template>
  <el-dialog header="字段设置" v-model="dialogVisible" width="800px" class="field-settings-dialog" :show-close="false">
    <template #header>
      字段设置
      <div class="close-btn">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-form class="field-settings-form">
      <el-scrollbar height="400px">
        <div class="width-order-container">
          <div class="field-list-header">
            <div class="field-cell index-cell">序号</div>
            <div class="field-cell name-cell">字段名</div>
            <div class="field-cell visible-cell">显示</div>
            <div class="field-cell width-cell">宽度(px)</div>
            <div class="field-cell fixed-cell">固定</div>
            <div class="field-cell action-cell">操作</div>
          </div>
          <div class="field-list-body" ref="fieldListBody">
            <div v-for="(row, index) in sortedFieldList" :key="row.value" class="field-list-item">
              <div class="field-cell index-cell">{{ index + 1 }}</div>
              <div class="field-cell name-cell">{{ row.label }}</div>
              <div class="field-cell visible-cell">
                <el-switch v-model="row.visible" size="small" />
              </div>
              <div class="field-cell width-cell">
                <el-input-number v-model="row.width" :min="50" :max="500" :step="10" controls-position="right"
                  style="width: 120px" />
              </div>
              <div class="field-cell fixed-cell">
                <el-select v-model="row.fixed" placeholder="不固定" style="width: 120px">
                  <el-option label="不固定" value="" />
                  <el-option label="左固定" value="left" />
                  <el-option label="右固定" value="right" />
                </el-select>
              </div>
              <div class="field-cell action-cell">
                <el-button type="primary" link size="small" :disabled="index === 0" @click="moveField(index, -1)" title="上移">
                  <el-icon>
                    <ArrowUp />
                  </el-icon>
                </el-button>
                <el-button type="primary" link size="small" :disabled="index === sortedFieldList.length - 1"
                  @click="moveField(index, 1)" title="下移">
                  <el-icon>
                    <ArrowDown />
                  </el-icon>
                </el-button>
                <div class="sortable-handle" style="
                    margin-left: 4px;
                    color: var(--td-text-color-placeholder);
                    cursor: move;
                    display: inline-block;
                  ">
                  <i class="iconfont x-tuodong2"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleReset">重置默认配置</el-button>
        <el-button type="primary" @click="handleSave" size="default">保存设置</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowUp, ArrowDown, Close } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'

const props = defineProps({
  visible: { type: Boolean, default: false },
  // 当前可见列（value 数组）
  fields: { type: Array, default: () => [] },
  // 当前列配置（用于取用户已保存的宽度 / 固定）
  fieldConfig: { type: Array, default: () => [] },
  // 全量列目录（当前页签适用列，含 value/label/width/fixed）
  catalog: { type: Array, default: () => [] },
  // localStorage 持久化键（按页签隔离）
  storageKey: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'save'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

const sortedFieldList = ref([])

let sortableInstance = null
const fieldListBody = ref(null)

// 初始化字段列表：优先按已保存顺序还原，label / 默认宽度以列目录为准
const initSortedFieldList = () => {
  const catalog = props.catalog || []
  const byValue = new Map(catalog.map((item) => [item.value, item]))
  let saved = null
  if (props.storageKey) {
    try {
      const raw = localStorage.getItem(props.storageKey)
      const parsed = raw ? JSON.parse(raw) : null
      if (Array.isArray(parsed) && parsed.length) saved = parsed
    } catch (e) {
      console.error('解析保存的字段配置失败:', e)
    }
  }

  if (saved) {
    const list = []
    saved.forEach((savedItem) => {
      const base = byValue.get(savedItem.value)
      if (!base) return
      list.push({
        value: base.value,
        label: base.label,
        width: savedItem.width ?? base.width ?? 100,
        fixed: savedItem.fixed ?? base.fixed ?? '',
        visible: savedItem.visible ?? props.fields.includes(base.value),
      })
    })
    // 列目录新增但历史配置缺失的列，追加到末尾并默认可见
    catalog.forEach((base) => {
      if (!list.some((item) => item.value === base.value)) {
        list.push({
          value: base.value,
          label: base.label,
          width: base.width ?? 100,
          fixed: base.fixed ?? '',
          visible: props.fields.includes(base.value),
        })
      }
    })
    sortedFieldList.value = list
    return
  }

  sortedFieldList.value = catalog.map((base) => {
    const savedItem = props.fieldConfig.find((item) => item.value === base.value)
    return {
      value: base.value,
      label: base.label,
      width: savedItem?.width ?? base.width ?? 100,
      fixed: savedItem?.fixed ?? base.fixed ?? '',
      visible: props.fields.includes(base.value),
    }
  })
}

const moveField = (index, direction) => {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= sortedFieldList.value.length) return
  const movedItem = sortedFieldList.value[index]
  sortedFieldList.value.splice(index, 1)
  sortedFieldList.value.splice(newIndex, 0, movedItem)
}

const initSortable = () => {
  if (fieldListBody.value && !sortableInstance) {
    sortableInstance = new Sortable(fieldListBody.value, {
      handle: '.sortable-handle',
      animation: 150,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      forceFallback: true,
      fallbackOnBody: true,
      swapThreshold: 0.65,
      onEnd: function (evt) {
        if (evt.oldIndex !== evt.newIndex && evt.oldIndex !== null && evt.newIndex !== null) {
          const newList = [...sortedFieldList.value]
          const movedItem = newList.splice(evt.oldIndex, 1)[0]
          newList.splice(evt.newIndex, 0, movedItem)
          sortedFieldList.value = newList
        }
      },
    })
  }
}

const destroySortable = () => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
}

onMounted(() => {
  initSortedFieldList()
})

onUnmounted(() => {
  destroySortable()
})

watch(dialogVisible, (visible) => {
  if (visible) {
    initSortedFieldList()
    requestAnimationFrame(() => {
      destroySortable()
      initSortable()
    })
  } else {
    destroySortable()
  }
})

watch(
  () => sortedFieldList.value.length,
  () => {
    if (dialogVisible.value) {
      requestAnimationFrame(() => {
        destroySortable()
        initSortable()
      })
    }
  },
)

const handleCancel = () => {
  dialogVisible.value = false
  destroySortable()
}

const handleReset = () => {
  sortedFieldList.value = (props.catalog || []).map((base) => ({
    value: base.value,
    label: base.label,
    width: base.width ?? 100,
    fixed: base.fixed ?? '',
    visible: props.fields.includes(base.value),
  }))
  ElMessage.success('已重置为默认配置')
}

const handleSave = () => {
  // 完整配置（含隐藏列）持久化到 localStorage，供下次打开还原顺序 / 宽度
  const allFieldsConfig = sortedFieldList.value.map((item) => ({
    value: item.value,
    label: item.label,
    width: item.width,
    fixed: item.fixed,
    visible: item.visible,
  }))
  if (props.storageKey) {
    localStorage.setItem(props.storageKey, JSON.stringify(allFieldsConfig))
  }

  const sortedVisibleFields = sortedFieldList.value
    .filter((item) => item.visible)
    .map((item) => ({
      value: item.value,
      label: item.label,
      width: item.width,
      fixed: item.fixed,
    }))
  emit('save', sortedVisibleFields)
  dialogVisible.value = false
  destroySortable()
}
</script>

<style scoped>
.field-settings-dialog .close-btn {
  float: right;
}

.width-order-container {
  width: 100%;
  box-sizing: border-box;
}

.field-list-header {
  display: flex;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px 4px 0 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.field-settings-form {
  width: 100%;
  padding: 0;
  overflow: visible;
}

.field-list-body {
  border-bottom: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
}

.field-list-item {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  background-color: #fff;
}

.field-list-item:last-child {
  border-bottom: none;
}

.field-cell {
  padding: 12px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-cell {
  width: 60px;
  text-align: center;
}

.name-cell {
  flex: 1;
  min-width: 120px;
  justify-content: flex-start;
}

.width-cell {
  width: 140px;
}

.visible-cell {
  width: 80px;
}

.fixed-cell {
  width: 120px;
}

.action-cell {
  width: 160px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.sortable-ghost {
  opacity: 0.5;
  background: #ecf5ff;
  border: 2px dashed var(--brand-color);
}

.sortable-chosen {
  background: #ecf5ff;
  border-color: var(--brand-color);
}

.sortable-drag {
  opacity: 0.8;
  box-shadow: 0 4px 12px rgba(var(--brand-color-rgb), 0.3);
}

.sortable-handle {
  transition: color 0.2s;
}

.sortable-handle:hover {
  color: var(--td-text-color-brand);
}
</style>
