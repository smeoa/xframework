<template>
  <el-card class="filter-panel" shadow="never">
    <template #header>
      <!-- 组间逻辑关系 -->
      <div class="groups-logic">
        <span>组间关系：</span>
        <el-select v-model="localGroupsLogic" class="groups-logic-select">
          <el-option label="并且" value="and" />
          <el-option label="或者" value="or" />
        </el-select>
        <el-button type="primary" @click="addFilterGroup">
          <el-icon><Plus /></el-icon>添加组
        </el-button>
      </div>
    </template>
    <el-scrollbar class="filter-panel-scrollbar">
      <div v-for="(group, gi) in localFilterGroups" :key="gi" class="filter-group">
        <el-divider v-if="gi > 0" content-position="center">{{ group.groupLogic === 'and' ? '并且' : '或者' }}</el-divider>
        <el-card class="filter-card">
          <template #header>
            <div class="card-header">
              <el-select v-model="group.conditionLogic" class="condition-logic-select">
                <el-option label="所有" value="and" />
                <el-option label="任意" value="or" />
              </el-select>
              <div class="header-actions">
                <el-button type="primary" @click="addCondToGroup(gi)">
                  <el-icon><Plus /></el-icon>添加条件
                </el-button>
                <el-button type="danger" @click="removeFilterGroup(gi)" v-if="localFilterGroups.length > 1 && gi > 0">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          <div v-for="(cond, ci) in group.conditions" :key="ci" class="filter-cond">
            <el-select v-model="cond.field" class="field-select" filterable @change="handleFieldChange(cond)">
              <el-option-group v-for="groupItem in filterFieldGroups" :key="groupItem.label" :label="groupItem.label">
                <el-option v-for="field in groupItem.fields" :key="field.value" :label="field.label" :value="field.value" />
              </el-option-group>
            </el-select>
            <!-- 选项字段（来源站点 / 产品标签 / 平台状态 / 处理进度）取值固定为「包含任一」，另支持为空 / 不为空 -->
            <el-select v-model="cond.operator" class="operator-select">
              <template v-if="hasFieldOptions(cond.field)">
                <el-option label="包含任一" value="in" />
                <el-option label="为空" value="is_null" />
                <el-option label="不为空" value="is_not_null" />
              </template>
              <template v-else>
                <el-option label="等于" value="eq" />
                <el-option label="不等于" value="ne" />
                <el-option label="包含" value="contains" />
                <el-option label="不包含" value="not_contains" />
                <el-option label="大于" value="gt" />
                <el-option label="小于" value="lt" />
                <el-option label="大于等于" value="gte" />
                <el-option label="小于等于" value="lte" />
                <el-option label="为空" value="is_null" />
                <el-option label="不为空" value="is_not_null" />
              </template>
            </el-select>
            <!-- 「为空 / 不为空」不需要填写值 -->
            <template v-if="cond.operator !== 'is_null' && cond.operator !== 'is_not_null'">
              <el-select v-if="hasFieldOptions(cond.field)" v-model="cond.value" multiple collapse-tags clearable
                placeholder="请选择" class="value-input">
                <el-option v-for="opt in fieldOptionsOf(cond.field)" :key="opt.value" :label="opt.label"
                  :value="opt.value" />
              </el-select>
              <el-input v-else v-model="cond.value" placeholder="请输入值" class="value-input" />
            </template>
            <el-button type="danger" @click="removeCondFromGroup(gi, ci)" class="delete-btn">
              <el-icon><Delete /></el-icon>删除
            </el-button>
            <el-divider v-if="ci < group.conditions.length - 1" class="cond-divider" />
          </div>
        </el-card>
      </div>
      <div class="spacer"></div>
    </el-scrollbar>
    <template #footer>
      <div class="filter-actions">
        <el-button type="primary" @click="emit('apply')" class="apply-btn">筛选</el-button>
        <el-button @click="resetFilter" class="reset-btn">清空</el-button>
        <el-button @click="handleSaveAs" class="save-as-btn">另存为</el-button>
        <el-button type="primary" @click="handleSave" class="save-btn">保存</el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  filterGroups: { type: Array, default: () => [{ groupLogic: 'and', conditionLogic: 'and', conditions: [] }] },
  groupsLogic: { type: String, default: 'and' },
  // 列表页签：origin / dhgate / voghion，筛选项 = 主表 x_product_detail_origin 全字段 + 该页签专属分组
  platform: { type: String, default: 'dhgate' },
  // 自定义字段分组：非空时优先于 platform 内置分组（订单等模块复用本组件时传入自己的字段分组）
  fieldGroups: { type: Array, default: () => [] },
  // 按字段声明的选项：如 { source_site: [{label,value}], tags: [{label,value}] }，
  // 声明了选项的字段渲染为多选下拉（原始产品页签保留站点/标签下拉）
  fieldOptions: { type: Object, default: () => ({}) },
  // 当前生效的已保存方案名，空串表示未选中任何方案（保存按钮据此判断新建还是覆盖更新）
  currentPresetName: { type: String, default: '' },
  // 当前页签已保存的方案名列表，用于新建 / 保存 / 另存为时的前端查重
  presetNames: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:filterGroups', 'update:groupsLogic', 'apply', 'reset', 'save', 'save-as'])

// 说明：request.js 只做「键名」camelCase → snake_case 转换，不转换字符串值，
// 而 filter.conditions[].field 会被后端直接拼进 SQL，因此这里的 value 必须使用数据库列名（snake_case）。
// 后端按列归属补表别名：主表已有列 → main.<field>；仅平台表存在的列 → plat.<field>；
// 两表同名列（id / data_id / create_by / update_by / create_time / update_time /
// is_deleted / delete_time / delete_by）在平台表侧统一用 plat_ 前缀指定。

// 主表 x_product_detail_origin 可筛字段（JSONB 列不参与筛选）
const ORIGIN_FIELD_GROUPS = [
  {
    label: '原始产品-基础信息',
    fields: [
      { label: '商品ID', value: 'id' },
      { label: '平台商品ID', value: 'source_goods_id' },
      { label: '商品标题', value: 'subject' },
      { label: '采集来源站点', value: 'source_site' },
      { label: '来源平台', value: 'source_platform' },
      { label: '采集来源链接', value: 'source_url' },
      { label: '类目ID', value: 'category_id' },
      { label: '类目名称', value: 'category_name' },
      { label: '单位', value: 'unit' },
      { label: '视频地址', value: 'video' },
      { label: '描述文本', value: 'text' },
      { label: '描述HTML', value: 'html' },
      { label: '创建时间', value: 'create_time' },
      { label: '更新时间', value: 'update_time' },
    ],
  },
  {
    label: '原始产品-价格库存',
    fields: [
      { label: '价格', value: 'price' },
      { label: '库存', value: 'stocks' },
      { label: '重量(kg)', value: 'weight' },
      { label: '包裹长度', value: 'cube_l' },
      { label: '包裹宽度', value: 'cube_w' },
      { label: '包裹高度', value: 'cube_h' },
    ],
  },
]

// 原始产品页签专属：产品标签（JSONB 标签ID，后端按「命中任一标签」匹配）
const ORIGIN_TAG_GROUP = {
  label: '原始产品-标签',
  fields: [{ label: '产品标签', value: 'tags' }],
}

// 平台表 x_product_detail_dhgate 可筛字段（普通列按列名筛选；平台状态 / 处理进度为 JSONB 虚拟字段）
// 分组标签与参考页（敦煌刊登-产品编辑）18 分组导航完全一致，顺序同参考页。
// 产品属性 / 产品特性 / 站外推广图 / 产品规格 / 货源信息 / 定制商品 六组字段全为 JSONB，无法参与筛选，故不出现在下拉中。
const DHGATE_FIELD_GROUPS = [
  {
    // plat.state 为 JSONB 对象，后端按状态名（state ->> 'name'）匹配
    label: '平台状态',
    fields: [{ label: '平台状态', value: 'state_name' }],
  },
  {
    // plat.sync 为 JSONB 数组，单个字段多选「环节 + 环节状态」（如 ai_enhance:0），后端按组合匹配
    label: '处理进度',
    fields: [{ label: '处理进度', value: 'sync_step' }],
  },
  {
    label: '状态',
    fields: [
      { label: '状态码', value: 'status_code' },
      { label: '信息', value: 'status_message' },
      { label: '状态解决方案', value: 'status_solution' },
    ],
  },
  {
    label: '类目',
    fields: [
      { label: '类目路径', value: 'category_path' },
      { label: '公共类目ID', value: 'cate_pub_id' },
    ],
  },
  {
    label: '基本信息',
    fields: [
      { label: '商品标题', value: 'item_name' },
      { label: '商品编码', value: 'item_code' },
      { label: '商品分组ID', value: 'item_group_id' },
      { label: '简短描述', value: 'short_desc' },
      { label: '详情富文本', value: 'html_content' },
      { label: '是否成人用品', value: 'is_sample' },
      { label: '是否敦煌优化', value: 'is_dh_optimized' },
      { label: '有效天数', value: 'vaild_day' },
      { label: '有效期', value: 'expire_date' },
      { label: '操作时间', value: 'operate_date' },
      { label: '供应商ID', value: 'supplier_id' },
      { label: '站点ID', value: 'site_id' },
    ],
  },
  {
    label: '产品关键词',
    fields: [
      { label: '关键词1', value: 'keyword1' },
      { label: '关键词2', value: 'keyword2' },
      { label: '关键词3', value: 'keyword3' },
    ],
  },
  {
    label: '视频',
    fields: [
      { label: '视频地址', value: 'video_url' },
    ],
  },
  {
    label: '主图',
    fields: [
      { label: '主图', value: 'pic' },
    ],
  },
  {
    label: '价格 USD',
    fields: [
      { label: '价格配置类型', value: 'price_config_type' },
    ],
  },
  {
    label: '销售方案',
    fields: [
      { label: '销售计量单位', value: 'measure_id' },
      { label: '一次最大购买数量', value: 'max_sale_qty' },
      { label: '备货期', value: 'leading_time' },
      { label: '满立减（最低批发量）', value: 'min_wholesale_qty' },
    ],
  },
  {
    label: '服务',
    fields: [
      { label: '运费模板ID', value: 'shipping_model_id' },
      { label: '售后服务模板ID', value: 'after_sale_template_id' },
      { label: '尺码模板ID', value: 'size_template_id' },
    ],
  },
  {
    label: '重量',
    fields: [
      { label: '包装后重量（毛重）', value: 'gross_weight' },
    ],
  },
  {
    label: '包装',
    fields: [
      { label: '长（CM）', value: 'pkg_length' },
      { label: '宽（CM）', value: 'pkg_width' },
      { label: '高（CM）', value: 'pkg_height' },
      { label: '包装数量', value: 'packing_quantity' },
    ],
  },
  {
    label: '系统信息',
    fields: [
      { label: '平台商品ID', value: 'pid' },
      { label: '数据ID', value: 'data_id' },
      { label: '库存所在地', value: 'inventory_location' },
      { label: '库存状态', value: 'inventory_status' },
      { label: '原始库存量', value: 'inventory_ori_qty' },
      { label: '库存量', value: 'inventory_qty' },
      { label: '店铺ID', value: 'shop_id' },
      { label: '店铺别名', value: 'shop_alias' },
      { label: '商品ID(平台表)', value: 'prod_id' },
      { label: '平台表ID', value: 'plat_id' },
      { label: '平台表创建时间', value: 'plat_create_time' },
      { label: '平台表更新时间', value: 'plat_update_time' },
    ],
  },
]

// 平台表 x_product_detail_voghion 可筛字段（JSONB 列不参与筛选）
const VOGHION_FIELD_GROUPS = [
  {
    label: 'Voghion-商品标识',
    fields: [
      { label: '商品ID(平台表)', value: 'prod_id' },
      { label: '线上产品ID', value: 'opid' },
      { label: '平台商品ID', value: 'pid' },
      { label: '主图', value: 'pic' },
      { label: '用户ID', value: 'uid' },
      { label: '数据ID', value: 'data_id' },
    ],
  },
  {
    label: 'Voghion-系统信息',
    fields: [
      { label: '类目ID', value: 'system_cid' },
      { label: '创建时间', value: 'system_create' },
      { label: '是否删除', value: 'system_deleted' },
      { label: '最大价格', value: 'system_max_price' },
      { label: '最小价格', value: 'system_min_price' },
      { label: '线上产品ID', value: 'system_opid' },
      { label: '产品详情ID', value: 'system_pdid' },
      { label: '平台', value: 'system_platform' },
      { label: '私有分组ID', value: 'system_private_gid' },
      { label: '公共分组ID', value: 'system_public_gid' },
      { label: '发布状态', value: 'system_publish' },
      { label: '是否已发布', value: 'system_published' },
      { label: '店铺别名', value: 'shop_alias' },
      { label: '系统产品编码(平台表)', value: 'plat_system_sku' },
      { label: '员工ID', value: 'system_staff_id' },
      { label: '状态', value: 'system_status' },
      { label: '产品标题', value: 'system_subject' },
      { label: '同步标记', value: 'system_sync' },
      { label: '用户ID', value: 'system_uid' },
      { label: '更新时间', value: 'system_update' },
      { label: '数据ID', value: 'system_data_id' },
    ],
  },
  {
    label: 'Voghion-平台表同步',
    fields: [
      { label: '平台表ID', value: 'plat_id' },
      { label: '平台表创建时间', value: 'plat_create_time' },
      { label: '平台表更新时间', value: 'plat_update_time' },
      { label: '平台表同步状态', value: 'plat_sync_status' },
      { label: '平台表同步失败信息', value: 'plat_sync_msg' },
      { label: '平台表最近同步时间', value: 'plat_sync_time' },
      { label: '平台表原始报文', value: 'plat_raw_response' },
    ],
  },
]

// 每个页签 = 主表全字段 + 该页签专属分组
const PLATFORM_FIELD_GROUPS = {
  origin: [...ORIGIN_FIELD_GROUPS, ORIGIN_TAG_GROUP],
  dhgate: [...ORIGIN_FIELD_GROUPS, ...DHGATE_FIELD_GROUPS],
  voghion: [...ORIGIN_FIELD_GROUPS, ...VOGHION_FIELD_GROUPS],
}

// 处理进度环节（key 与后端 product_step_service.SYNC_GROUPS 一致）
const SYNC_STEPS = [
  { key: 'ai_enhance', name: 'AI完善' },
  { key: 'content_process', name: '内容加工' },
  { key: 'pricing_rule', name: '定价应用' },
  { key: 'publish', name: '发布' },
]

// 环节状态码（与后端 CODE_TEXT 一致：0 待处理 / 1 已完成 / 2 失败）
const SYNC_CODE_TEXT = { 0: '待处理', 1: '已完成', 2: '失败' }

// 处理进度选项：4 个环节 × 3 种状态合并为一个多选列表
// 值 = 「环节key:状态码」，分隔符与后端 product_model.SYNC_VALUE_SEPARATOR 一致
const SYNC_STEP_OPTIONS = SYNC_STEPS.flatMap((step) =>
  Object.entries(SYNC_CODE_TEXT).map(([code, text]) => ({
    label: `${step.name} · ${text}`,
    value: `${step.key}:${code}`,
  })),
)

// DHgate 页签内置选项（Product.vue 对非 origin 页签不传 fieldOptions，故在组件内兜底）
// 平台状态按状态名多选；处理进度按「环节 + 环节状态」组合多选
const DHGATE_BUILTIN_FIELD_OPTIONS = {
  state_name: [
    { label: '未上架', value: '未上架' },
    { label: '已上架', value: '已上架' },
    { label: '已下架', value: '已下架' },
    { label: '未定义', value: '未定义' },
    { label: '待审核', value: '待审核' },
    { label: '审核未通过', value: '审核未通过' },
    { label: '品牌商投诉', value: '品牌商投诉' },
    { label: '疑似侵权', value: '疑似侵权' },
    { label: '内容违规', value: '内容违规' },
  ],
  sync_step: SYNC_STEP_OPTIONS,
}

const PLATFORM_BUILTIN_FIELD_OPTIONS = {
  dhgate: DHGATE_BUILTIN_FIELD_OPTIONS,
}

const filterFieldGroups = computed(
  () =>
    (props.fieldGroups && props.fieldGroups.length ? props.fieldGroups : null) ||
    PLATFORM_FIELD_GROUPS[props.platform] ||
    PLATFORM_FIELD_GROUPS.dhgate,
)

// 传入自定义字段分组（订单等模块）时不套用页签内置选项
const builtinFieldOptions = computed(() =>
  (props.fieldGroups && props.fieldGroups.length
    ? {}
    : PLATFORM_BUILTIN_FIELD_OPTIONS[props.platform] || {}),
)

// 声明了选项的字段（渲染为多选下拉，操作符固定为 in）：传入选项优先，其次页签内置选项
const fieldOptionsOf = (field) => {
  const declared = props.fieldOptions?.[field]
  if (declared && declared.length) return declared
  return builtinFieldOptions.value[field] || []
}
const hasFieldOptions = (field) => fieldOptionsOf(field).length > 0

const defaultField = computed(() => filterFieldGroups.value[0]?.fields[0]?.value || 'id')

const localFilterGroups = ref(JSON.parse(JSON.stringify(props.filterGroups)))
const localGroupsLogic = ref(props.groupsLogic)

watch(() => props.filterGroups, (v) => {
  localFilterGroups.value = JSON.parse(JSON.stringify(v))
}, { deep: true })

watch(localFilterGroups, (v) => {
  const currentPropsJson = JSON.stringify(props.filterGroups)
  const newGroupsJson = JSON.stringify(v)
  if (currentPropsJson !== newGroupsJson) {
    emit('update:filterGroups', JSON.parse(JSON.stringify(v)))
  }
}, { deep: true })

watch(localGroupsLogic, (v) => {
  if (v !== props.groupsLogic) {
    emit('update:groupsLogic', v)
  }
})

const addFilterGroup = () => {
  localFilterGroups.value.push({
    groupLogic: localGroupsLogic.value,
    conditionLogic: localGroupsLogic.value,
    conditions: [],
  })
}

const removeFilterGroup = (gi) => {
  if (localFilterGroups.value.length > 1) {
    localFilterGroups.value.splice(gi, 1)
  }
}

const addCondToGroup = (gi) => {
  const field = defaultField.value
  localFilterGroups.value[gi].conditions.push(
    hasFieldOptions(field)
      ? { field, operator: 'in', value: [] }
      : { field, operator: 'eq', value: '' },
  )
}

// 切换字段时归一取值：选项字段固定 in + 数组，其余字段恢复单值
const handleFieldChange = (cond) => {
  if (hasFieldOptions(cond.field)) {
    cond.operator = 'in'
    // 切换字段后旧取值已失效，选项字段一律清空重选
    cond.value = []
  } else if (Array.isArray(cond.value)) {
    cond.value = ''
    if (!cond.operator || cond.operator === 'in' || cond.operator === 'not_in') {
      cond.operator = 'eq'
    }
  }
}

const removeCondFromGroup = (gi, ci) => {
  localFilterGroups.value[gi].conditions.splice(ci, 1)
}

const resetFilter = () => {
  localFilterGroups.value = [{ groupLogic: 'and', conditionLogic: 'and', conditions: [] }]
  localGroupsLogic.value = 'and'
  emit('reset')
}

// 是否存在有效筛选条件（任一条件已选择字段即视为非空）
const hasCondition = computed(() =>
  localFilterGroups.value.some((group) =>
    (group.conditions || []).some((cond) => cond.field),
  ),
)

// 方案名称最大长度，与后端 MAX_NAME_LENGTH / 数据库列定义保持一致
const MAX_PRESET_NAME_LENGTH = 64

/**
 * 弹出名称输入框收集方案名称
 *
 * @param {string} title 弹框标题
 * @param {string} excludeName 查重时排除的名称（保存已有方案时传原名称，允许名称不变）
 * @returns {Promise<string>} 确认返回名称；取消或校验失败返回空串
 */
const promptPresetName = async (title, excludeName = '') => {
  try {
    const { value } = await ElMessageBox.prompt('请输入筛选条件名称', title, {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      // 保存已有方案时预填原名称，直接确认即名称不变
      inputValue: excludeName,
      inputValidator: (text) => {
        const name = (text || '').trim()
        if (!name) return '名称不能为空'
        if (name.length > MAX_PRESET_NAME_LENGTH) {
          return `名称长度不能超过 ${MAX_PRESET_NAME_LENGTH} 字符`
        }
        if (name !== excludeName && props.presetNames.includes(name)) {
          return '方案名称已存在'
        }
        return true
      },
    })
    return value.trim()
  } catch (error) {
    // 取消输入不做处理
    return ''
  }
}

// 保存条件：已选中方案时预填原名称（可改名，改名即重命名并覆盖更新条件）；未选中方案时新建
const handleSave = async () => {
  if (!hasCondition.value) {
    ElMessage.warning('请先添加筛选条件')
    return
  }
  const name = await promptPresetName(
    props.currentPresetName ? '保存筛选条件（修改名称即重命名）' : '保存筛选条件',
    props.currentPresetName,
  )
  if (name) emit('save', name)
}

// 另存为：无论当前是否选中方案，均按新名称保存成新方案
const handleSaveAs = async () => {
  if (!hasCondition.value) {
    ElMessage.warning('请先添加筛选条件')
    return
  }
  const name = await promptPresetName('另存为新的筛选条件')
  if (name) emit('save-as', name)
}
</script>

<style scoped>
.filter-panel {
  width: 320px;
  background-color: #fff;
  height: 100%;
  /* 描边由外层容器（aside）统一承担，卡片自身不重复描边；仅右侧两角随容器圆角 */
  border: 0 !important;
  border-radius: 0 var(--radius-card) var(--radius-card) 0;
}

/* body 只作为滚动区域的外壳，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒后触发横向滚动 */
.filter-panel > :deep(.el-card__body) {
  padding: 0;
}

/* 滚动容器铺满 body，内部内容用 8px 垂直 / 12px 水平内边距与 header 对齐 */
.filter-panel-scrollbar {
  height: 100%;
}

.filter-panel-scrollbar :deep(.el-scrollbar__view) {
  display: block;
  padding: 8px 12px;
}

/* header 垂直内边距与主卡片 header 一致，使两者高度与底部分隔线对齐；
   水平内边距 25px，使顶部内容与下方筛选组左右对齐 */
.filter-panel > :deep(.el-card__header) {
  padding: var(--td-comp-paddingTB-l) 25px;
}

/* 顶部区域已由 el-card header 承载，内边距由 header 提供 */
.groups-logic {
  display: flex;
  align-items: center;
  border-radius: 4px;
}

/* 标签固定宽度，避免被压缩导致右侧下拉框位置漂移 */
.groups-logic > span {
  width: 75px;
}

/* 添加组按钮靠右对齐 */
.groups-logic .el-button {
  margin-left: auto;
}

.groups-logic-select {
  width: 90px;
  margin-left: 8px;
  margin-right: 8px;
}

.groups-logic-select :deep(.el-select__wrapper) {
  width: 90px;
}

.filter-group {
}

.filter-card {
  max-width: 480px;
  width: 295px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* 占满 header 内容盒，使「添加条件」等操作按钮靠右贴齐卡片内边缘 */
  width: 100%;
}

.filter-card :deep(.el-card__header) {
  width: 295px;
  padding-left: 12px;
  padding-right: 12px;
}

.filter-card :deep(.el-card__body) {
  padding-left: 0;
  padding-right: 0;
  padding-bottom: 8px;
}

.condition-logic-select {
  width: 148px;
  margin-left: 0px;
}

.condition-logic-select :deep(.el-select__wrapper) {
  width: 85px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions :deep(.el-button--primary) {
  margin-left: 20px;
  padding-left: 12px;
}

.filter-cond {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 271px;
  margin: 0 auto;
}

.field-select {
  width: 148px;
  margin-bottom: 8px;
}

.field-select :deep(.el-select__wrapper) {
  width: 148px;
}

.value-input :deep(.el-input__wrapper) {
  width: 148px;
}

.operator-select {
  width: 97px;
  margin-bottom: 8px;
}

.operator-select :deep(.el-select__wrapper) {
  width: 96px;
}

.operator-select {
  margin-left: auto;
}

.value-select {
  width: 168px;
  margin-bottom: 8px;
}

.value-input {
  width: 148px;
  margin-bottom: 8px;
}

.delete-btn {
  width: 96px;
  line-height: 24px;
  margin-bottom: 8px;
  margin-left: auto;
}

.cond-divider {
  margin-bottom: 16px;
  margin-top: 8px;
}

.spacer {
  margin-bottom: 120px;
}

/* 操作栏已由 el-card 的 footer 承载：去掉原先 fixed 定位与自带内边距/描边，
   内边距与外框统一交给 footer，避免与 footer 的顶边框和圆角叠加 */
.filter-actions {
  width: 100%;
  display: flex;
  flex-direction: row;
  /* 全局 .filter-actions 带 align-items: center，会令子行收缩为内容宽度，此处显式拉伸 */
  align-items: stretch;
  padding: 0;
  border: 0;
  border-radius: 0;
  background-color: transparent;
  gap: 8px;
}

/* 四个按钮单行平分宽度：去掉 Element Plus 相邻按钮外边距，压缩内边距避免「保存条件」换行 */
.filter-actions .el-button {
  flex: 1;
  margin-left: 0;
  padding-left: 8px;
  padding-right: 8px;
}
</style>
