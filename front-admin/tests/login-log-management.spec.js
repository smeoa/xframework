// @ts-check
import { test, expect } from '@playwright/test';

// 登录记录页依赖登录态，统一在 beforeEach 中完成登录
async function login(page) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}

// 个人设置 -> 登录记录页签
async function gotoLoginLogs(page) {
  await page.goto('/profile');
  await page.locator('.profile-menu .el-menu-item', { hasText: '登录记录' }).click();
  await expect(page.locator('.login-logs-table')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(800);
}

// 表头单元格精确匹配（列头标签统一渲染在 .col-header-label 内，列操作图标为同级兄弟节点）
const headerCell = (page, text) =>
  page.locator(`.login-logs-table .el-table__header-wrapper th .col-header-label:text-is("${text}")`);

// 列头「列操作」触发区（悬停表头才出现操作图标，触发区始终存在）
const headerTrigger = (page, text) =>
  page
    .locator('.login-logs-table .el-table__header-wrapper th')
    .filter({ has: page.locator(`.col-header-label:text-is("${text}")`) })
    .first()
    .locator('.col-header-menu-trigger');

// 卡片工具栏（列头菜单里的「筛选」按钮非工具栏按钮，需限定作用域）
const toolbarBtn = (page, text) =>
  page.locator('.login-logs-card .card-header button', { hasText: text }).first();

test.describe('Login Logs Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    // 清理本页本地配置（字段设置 / 排序规则），保证用例互不影响
    await page.evaluate(() => {
      localStorage.removeItem('loginLogColumnSettingsV1');
      localStorage.removeItem('loginLogSortRulesV1');
    });
  });

  test('should load login logs page with core elements', async ({ page }) => {
    await gotoLoginLogs(page);
    // 工具栏
    await expect(toolbarBtn(page, '排序')).toBeVisible();
    await expect(toolbarBtn(page, '筛选')).toBeVisible();
    // 旧的日期范围选择器已移除，统一并入筛选面板
    await expect(page.locator('.login-logs-card .card-header .el-date-editor')).toHaveCount(0);
    // 动态数据列（保持原有 7 列）
    await expect(headerCell(page, '登录时间')).toBeVisible();
    await expect(headerCell(page, '登录IP')).toBeVisible();
    await expect(headerCell(page, '登录设备')).toBeVisible();
    await expect(headerCell(page, '登录状态')).toBeVisible();
    await expect(headerCell(page, '错误信息')).toBeVisible();
  });

  test('列操作：有 DB 列的列头菜单提供 升/降序、冻结、隐藏、筛选', async ({ page }) => {
    await gotoLoginLogs(page);
    await headerTrigger(page, '登录时间').click();
    const menu = page.locator('.col-header-menu-popper:visible').first();
    await expect(menu).toBeVisible();
    for (const label of ['升序', '降序', '冻结列', '隐藏此列', '筛选']) {
      await expect(menu.getByText(label, { exact: true }).first()).toBeVisible();
    }
  });

  test('列操作：无 DB 列的列头菜单仅提供 冻结 / 隐藏', async ({ page }) => {
    await gotoLoginLogs(page);
    await headerTrigger(page, '登录设备').click();
    const menu = page.locator('.col-header-menu-popper:visible').first();
    await expect(menu).toBeVisible();
    await expect(menu.getByText('冻结列', { exact: true }).first()).toBeVisible();
    await expect(menu.getByText('隐藏此列', { exact: true }).first()).toBeVisible();
    // 该列后端无对应字段，不提供排序与筛选
    await expect(menu.getByText('升序', { exact: true })).toHaveCount(0);
    await expect(menu.getByText('筛选', { exact: true })).toHaveCount(0);
  });

  // 登录时间默认即为降序，排序 / 冻结用例改用无默认排序的登录IP列
  test('列头排序：点击降序后列头显示排序状态', async ({ page }) => {
    await gotoLoginLogs(page);
    await headerTrigger(page, '登录IP').click();
    await page
      .locator('.col-header-menu-popper:visible')
      .first()
      .getByText('降序', { exact: true })
      .first()
      .click();
    // 列头出现排序状态标记
    await expect(headerTrigger(page, '登录IP')).toHaveClass(/has-state/);
    // 重新打开列头菜单，「降序」项为选中态
    await headerTrigger(page, '登录IP').click();
    await expect(
      page.locator('.col-header-menu-popper:visible .col-header-menu-item.is-checked').first(),
    ).toContainText('降序');
  });

  test('列头冻结：冻结登录IP列后状态标记为已冻结', async ({ page }) => {
    await gotoLoginLogs(page);
    await headerTrigger(page, '登录IP').click();
    await page
      .locator('.col-header-menu-popper:visible')
      .first()
      .getByText('冻结列', { exact: true })
      .first()
      .click();
    await expect(page.locator('.el-message').first()).toContainText('已冻结该列');
    // 再次打开列头菜单，「冻结列」处于选中态
    await headerTrigger(page, '登录IP').click();
    await expect(
      page
        .locator('.col-header-menu-popper:visible .col-header-menu-item', { hasText: '冻结列' })
        .first(),
    ).toHaveClass(/is-checked/);
  });

  test('列头隐藏：隐藏错误信息列后该列消失', async ({ page }) => {
    await gotoLoginLogs(page);
    await expect(headerCell(page, '错误信息')).toBeVisible();
    await headerTrigger(page, '错误信息').click();
    await page
      .locator('.col-header-menu-popper:visible')
      .first()
      .getByText('隐藏此列', { exact: true })
      .first()
      .click();
    await expect(page.locator('.el-message').first()).toContainText('已隐藏该列');
    await expect(headerCell(page, '错误信息')).toHaveCount(0);
  });

  test('字段设置：可通过字段设置恢复隐藏列', async ({ page }) => {
    await gotoLoginLogs(page);
    // 先隐藏「错误信息」列
    await headerTrigger(page, '错误信息').click();
    await page
      .locator('.col-header-menu-popper:visible')
      .first()
      .getByText('隐藏此列', { exact: true })
      .first()
      .click();
    await expect(headerCell(page, '错误信息')).toHaveCount(0);
    // 打开字段设置并重新开启该列
    await page.locator('.login-logs-card .header-actions > button').last().click();
    const dialog = page.locator('.field-settings-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('.field-list-header')).toContainText('字段名');
    const row = dialog.locator('.field-list-item').filter({ hasText: '错误信息' }).first();
    await row.locator('.visible-cell .el-switch').click();
    await dialog.locator('button', { hasText: '保存设置' }).click();
    await expect(page.locator('.el-message', { hasText: '字段设置已保存' })).toBeVisible();
    await expect(headerCell(page, '错误信息')).toBeVisible();
  });

  test('筛选：打开筛选面板显示组间关系与保存方案按钮', async ({ page }) => {
    await gotoLoginLogs(page);
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
    const presetName = `登录记录测试方案${Date.now()}`;
    await gotoLoginLogs(page);
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
    await page.locator('.login-logs-card .filter-split-more').click();
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
