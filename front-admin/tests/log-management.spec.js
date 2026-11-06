// @ts-check
import { test, expect } from '@playwright/test';

// 日志管理页依赖登录态，统一在 beforeEach 中完成登录
async function login(page) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}

async function gotoLog(page) {
  await page.goto('/log');
  await expect(page.locator('.log-table')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(800);
}

// 表头单元格精确匹配（列头标签统一渲染在 .col-header-label 内，列操作图标为同级兄弟节点）
const headerCell = (page, text) =>
  page.locator(`.log-table .el-table__header-wrapper th .col-header-label:text-is("${text}")`);

// 列头「列操作」触发区（悬停表头才出现操作图标，触发区始终存在）
const headerTrigger = (page, text) =>
  page
    .locator('.log-table .el-table__header-wrapper th')
    .filter({ has: page.locator(`.col-header-label:text-is("${text}")`) })
    .first()
    .locator('.col-header-menu-trigger');

// 列表工具栏（未选中时为 .card-header；列头菜单里的「筛选」按钮非工具栏按钮，需限定作用域）
const toolbarBtn = (page, text) => page.locator('.card-header button', { hasText: text }).first();

test.describe('Log Management Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    // 清理本页本地配置（字段设置 / 排序规则），保证用例互不影响
    await page.evaluate(() => {
      localStorage.removeItem('logColumnSettingsV1');
      localStorage.removeItem('logSortRulesV1');
    });
  });

  test('should load log list page with core elements', async ({ page }) => {
    await gotoLog(page);
    // 工具栏
    await expect(toolbarBtn(page, '清理历史日志')).toBeVisible();
    await expect(toolbarBtn(page, '搜索')).toBeVisible();
    await expect(toolbarBtn(page, '排序')).toBeVisible();
    await expect(toolbarBtn(page, '筛选')).toBeVisible();
    // 动态数据列
    await expect(headerCell(page, 'ID')).toBeVisible();
    await expect(headerCell(page, '级别')).toBeVisible();
    await expect(headerCell(page, '日志内容')).toBeVisible();
    await expect(headerCell(page, '创建时间')).toBeVisible();
    // 操作列表头「字段设置」入口
    await expect(page.locator('.log-table .el-table__header-wrapper [title="字段设置"]').first()).toBeVisible();
  });

  test('列操作：列头菜单提供 排序 / 冻结 / 隐藏 / 筛选', async ({ page }) => {
    await gotoLog(page);
    await headerTrigger(page, '级别').click();
    const menu = page.locator('.col-header-menu-popper:visible');
    await expect(menu).toBeVisible();
    for (const label of ['升序', '降序', '冻结列', '隐藏此列', '筛选']) {
      await expect(menu.getByText(label, { exact: true }).first()).toBeVisible();
    }
  });

  test('列头排序：点击降序后列头显示排序状态', async ({ page }) => {
    await gotoLog(page);
    await headerTrigger(page, '级别').click();
    await page.locator('.col-header-menu-popper:visible').getByText('降序', { exact: true }).first().click();
    // 列头出现排序状态标记
    await expect(headerTrigger(page, '级别')).toHaveClass(/has-state/);
    // 重新打开列头菜单，「降序」项为选中态
    await headerTrigger(page, '级别').click();
    await expect(
      page.locator('.col-header-menu-popper:visible .col-header-menu-item.is-checked').first(),
    ).toContainText('降序');
  });

  test('列头冻结：冻结级别列后状态标记为已冻结', async ({ page }) => {
    await gotoLog(page);
    await headerTrigger(page, '级别').click();
    await page.locator('.col-header-menu-popper:visible').getByText('冻结列', { exact: true }).first().click();
    await expect(page.locator('.el-message').first()).toContainText('已冻结该列');
    // 再次打开列头菜单，「冻结列」处于选中态
    await headerTrigger(page, '级别').click();
    await expect(
      page.locator('.col-header-menu-popper:visible .col-header-menu-item.is-checked').first(),
    ).toContainText('冻结列');
  });

  test('字段设置：可通过字段设置隐藏列', async ({ page }) => {
    await gotoLog(page);
    await expect(headerCell(page, '模块')).toBeVisible();
    await page.locator('.log-table .el-table__header-wrapper [title="字段设置"]').first().click();
    const dialog = page.locator('.field-settings-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('.field-list-header')).toContainText('字段名');
    // 关闭「模块」列的显示开关
    const moduleRow = dialog.locator('.field-list-item').filter({ hasText: '模块' }).first();
    await moduleRow.locator('.visible-cell .el-switch').click();
    await dialog.locator('button', { hasText: '保存设置' }).click();
    await expect(page.locator('.el-message', { hasText: '字段设置已保存' })).toBeVisible();
    await expect(headerCell(page, '模块')).toHaveCount(0);
  });

  test('筛选：打开筛选面板显示组间关系与保存方案按钮', async ({ page }) => {
    await gotoLog(page);
    await toolbarBtn(page, '筛选').click();
    const panel = page.locator('.advanced-search-aside .filter-panel');
    await expect(panel).toBeVisible();
    await expect(panel.locator('.groups-logic')).toContainText('组间关系');
    for (const label of ['筛选', '清空', '另存为', '保存']) {
      await expect(panel.locator('.filter-actions button', { hasText: label }).first()).toBeVisible();
    }
    // 关闭筛选面板
    await toolbarBtn(page, '收起').click();
    await expect(page.locator('.advanced-search-aside')).toHaveCount(0);
  });

  test('筛选方案：另存为保存后可套用并删除', async ({ page }) => {
    const presetName = `自动化测试方案${Date.now()}`;
    await gotoLog(page);
    await toolbarBtn(page, '筛选').click();
    const panel = page.locator('.advanced-search-aside .filter-panel');
    await expect(panel).toBeVisible();
    // 添加一个筛选条件（默认字段已选中，满足保存前置）
    await panel.locator('button', { hasText: '添加条件' }).first().click();
    // 另存为 -> 输入名称 -> 保存
    await panel.locator('.filter-actions button', { hasText: '另存为' }).click();
    const promptBox = page.locator('.el-message-box');
    await expect(promptBox).toBeVisible();
    await promptBox.locator('input').fill(presetName);
    await promptBox.locator('button', { hasText: '保存' }).click();
    await expect(page.locator('.el-message', { hasText: '保存成功' })).toBeVisible();
    // 方案下拉中出现该方案
    await page.locator('.filter-split-more').click();
    const presetItem = page.locator('.el-dropdown-menu .filter-preset-item', { hasText: presetName }).first();
    await expect(presetItem).toBeVisible();
    // 删除该方案（悬停显示删除图标）
    await presetItem.hover();
    await presetItem.locator('.filter-preset-item-delete').click();
    const confirmBox = page.locator('.el-message-box');
    await expect(confirmBox).toBeVisible();
    await confirmBox.locator('button', { hasText: '确定' }).click();
    await expect(page.locator('.el-message', { hasText: '删除成功' })).toBeVisible();
    await expect(page.locator('.el-dropdown-menu .filter-preset-item', { hasText: presetName })).toHaveCount(0);
  });
});
