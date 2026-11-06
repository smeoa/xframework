import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
  rules: {
    // Vue 3 支持多根节点，页面组件按区块拆分布局，故关闭该 Vue 2 规则
    'vue/no-multiple-template-root': 'off'
  }
})
