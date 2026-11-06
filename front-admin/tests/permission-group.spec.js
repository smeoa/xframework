// @ts-check
import { test, expect } from '@playwright/test';

// 权限组管理页与「权限组配置」抽屉均依赖登录态，统一在 beforeEach 中完成登录
async function login(page) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}

async function gotoPermissionGroup(page) {
  await page.goto('/permission-group');
  await expect(page.locator('.permission-group-card .el-table')).toBeVisible({ timeout: 15000 });
  await expect(listRows(page).first()).toBeVisible({ timeout: 15000 });
}

// 列表页表格行
const listRows = (page) => page.locator('.permission-group-card .el-table__body-wrapper tbody tr');
// 表头单元格精确匹配（避免「数据范围」命中抽屉 Tab 等同名文本）
const headerCell = (page, text) =>
  page.locator(`.permission-group-card .el-table__header-wrapper th .cell:text-is("${text}")`);
// 顶部筛选下拉：0=所属菜单 1=业务模块 2=状态
const filterSelect = (page, index) => page.locator('.header-filters .el-select').nth(index);
// 下拉选项：Element Plus 选项为 <li role="option"><span>文本</span></li>，
// :text-is 只会命中最深层的 <span>，故改用 role 精确匹配（仅可见的浮层生效）
const dropdownOption = (page, text) =>
  page.locator('.el-select-dropdown:visible').getByRole('option', { name: text, exact: true });

// 抽屉元素
const drawer = (page) => page.locator('.permission-group-drawer');
const drawerPane = (page, index) => drawer(page).locator('.el-tab-pane').nth(index);
const paneRows = (page, index) =>
  drawerPane(page, index).locator('.el-table__body-wrapper tbody tr');
// 抽屉内的 Tab 标题
const tabItem = (page, label) =>
  drawer(page).locator(`.el-tabs__item:text-is("${label}")`);

// 打开「权限组配置」抽屉（入口在页面顶栏标题右侧）
async function openDrawer(page, path) {
  await page.goto(path);
  const entry = page.locator('button[title="权限组配置"]');
  await expect(entry).toBeVisible({ timeout: 15000 });
  await entry.click();
  await expect(drawer(page)).toBeVisible({ timeout: 15000 });
  // 抽屉内容就绪：工具栏按钮 + 5 个配置 Tab
  await expect(drawer(page).locator('.dialog-toolbar button:has-text("新建权限组")')).toBeVisible({
    timeout: 15000,
  });
  await expect(drawer(page).locator('.el-tabs__item')).toHaveCount(5, { timeout: 15000 });
}

test.describe('Permission Group Management Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should load list page with core elements', async ({ page }) => {
    await gotoPermissionGroup(page);
    // 顶部操作按钮
    await expect(page.locator('.permission-group-card button:has-text("刷新")')).toBeVisible();
    await expect(page.locator('.permission-group-card button:has-text("搜索")')).toBeVisible();
    // 关键字搜索框
    await expect(page.locator('input[placeholder="搜索名称或编码"]')).toBeVisible();
    // 三个筛选下拉
    await expect(page.locator('.header-filters .el-select')).toHaveCount(3);
    // 分页
    await expect(page.locator('.permission-group-card .el-pagination')).toBeVisible();
  });

  test('should display table with 数据范围 column', async ({ page }) => {
    await gotoPermissionGroup(page);
    const expectedHeaders = [
      'ID', '权限组名称', '所属菜单',
      '操作权限', '字段权限', '数据范围', '绑定主体',
      '排序', '状态', '描述', '操作',
    ];
    for (const title of expectedHeaders) {
      await expect(headerCell(page, title)).toBeVisible();
    }
    // 编码 / 业务模块 为自动维护字段，不在列表展示
    for (const title of ['编码', '业务模块']) {
      await expect(headerCell(page, title)).toHaveCount(0);
    }
  });

  test('should show numeric counts in every statistic column', async ({ page }) => {
    await gotoPermissionGroup(page);
    const rows = listRows(page);
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    // 操作权限(3) / 字段权限(4) / 数据范围(5) / 绑定主体(6) 均为数字
    for (let i = 0; i < Math.min(rowCount, 5); i += 1) {
      for (const columnIndex of [3, 4, 5, 6]) {
        const text = (await rows.nth(i).locator('td').nth(columnIndex).innerText()).trim();
        expect(text).toMatch(/^\d+$/);
      }
    }
  });

  test('should provide row actions for each permission group', async ({ page }) => {
    await gotoPermissionGroup(page);
    // 操作列由 6 个图标链接组成：操作权限 / 字段权限 / 数据权限 / 绑定主体 / 编辑 / 删除
    const actions = listRows(page).first().locator('td').last().locator('.cell-actions .el-link');
    await expect(actions).toHaveCount(6);
    await expect(actions.first().locator('.el-icon')).toBeVisible();
    // 前 5 个为主色链接，最后 1 个（删除）为危险色链接
    await expect(actions.nth(4)).toHaveClass(/el-link--primary/);
    await expect(actions.nth(5)).toHaveClass(/el-link--danger/);
  });

  test('should filter list by 业务模块', async ({ page }) => {
    await gotoPermissionGroup(page);
    const totalBefore = await listRows(page).count();
    expect(totalBefore).toBeGreaterThan(1);

    await filterSelect(page, 1).click();
    await dropdownOption(page, 'product').click();

    // 等待筛选结果
    await expect.poll(async () => listRows(page).count()).toBeLessThan(totalBefore);

    // 业务模块列已不展示（自动维护字段），校验筛选后结果非空即可
    const rows = listRows(page);
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('should filter list by 状态', async ({ page }) => {
    await gotoPermissionGroup(page);
    await filterSelect(page, 2).click();
    await dropdownOption(page, '启用').click();

    await expect(listRows(page).first()).toBeVisible();
    const rows = listRows(page);
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    for (let i = 0; i < rowCount; i += 1) {
      await expect(rows.nth(i).locator('td').nth(8)).toContainText('启用');
    }
  });

  test('should search permission groups by keyword', async ({ page }) => {
    await gotoPermissionGroup(page);
    const totalBefore = await listRows(page).count();

    await page.fill('input[placeholder="搜索名称或编码"]', '店铺');
    await page.locator('.permission-group-card button:has-text("搜索")').click();

    await expect.poll(async () => listRows(page).count()).toBeLessThan(totalBefore);

    const rows = listRows(page);
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    for (let i = 0; i < rowCount; i += 1) {
      const name = await rows.nth(i).locator('td').nth(1).innerText();
      expect(name).toContain('店铺');
    }
  });

  test('should prefill form dialog when editing', async ({ page }) => {
    await gotoPermissionGroup(page);
    const firstRow = listRows(page).first();
    const rowTitle = (await firstRow.locator('td').nth(1).innerText()).trim();

    // 操作列第 5 个图标链接为「编辑」
    await firstRow.locator('.cell-actions .el-link').nth(4).click();

    const dialog = page.locator('.el-dialog:visible');
    await expect(dialog.locator('.el-dialog__title')).toHaveText('编辑权限组');
    await expect(
      dialog.locator('.el-form-item:has(.el-form-item__label:text-is("权限组名称")) input'),
    ).toHaveValue(rowTitle);
    // 编辑态编码只读（编码不在列表展示，仅校验已回填且不可编辑）
    const codeInput = dialog.locator(
      '.el-form-item:has(.el-form-item__label:text-is("权限组编码")) input',
    );
    await expect(codeInput).toBeDisabled();
    expect((await codeInput.inputValue()).trim().length).toBeGreaterThan(0);

    await dialog.locator('button:has-text("取消")').click();
    await expect(page.locator('.el-dialog:visible')).toHaveCount(0);
  });

  test('should ask for confirmation before deleting and keep data on cancel', async ({ page }) => {
    await gotoPermissionGroup(page);
    const rowCountBefore = await listRows(page).count();
    const firstRow = listRows(page).first();
    const rowTitle = (await firstRow.locator('td').nth(1).innerText()).trim();

    // 操作列第 6 个图标链接为「删除」
    await firstRow.locator('.cell-actions .el-link').nth(5).click();

    const messageBox = page.locator('.el-message-box');
    await expect(messageBox).toBeVisible();
    await expect(messageBox).toContainText(rowTitle);
    await messageBox.locator('button:has-text("取消")').click();
    await expect(page.locator('.el-message-box')).toHaveCount(0);

    // 取消后数据保持不变
    await expect(listRows(page)).toHaveCount(rowCountBefore);
  });
});

test.describe('Permission Group Config Drawer', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should open drawer with toolbar and 5 tabs', async ({ page }) => {
    await openDrawer(page, '/shop');

    // 标题与工具栏
    await expect(drawer(page).locator('.el-drawer__title')).toContainText('权限组配置');
    await expect(drawer(page).locator('.dialog-toolbar button:has-text("新建权限组")')).toBeVisible();

    // 5 个 Tab
    const tabs = drawer(page).locator('.el-tabs__header .el-tabs__item');
    await expect(tabs).toHaveCount(5);
    for (const label of ['权限组', '操作权限', '字段权限', '数据范围', '主体绑定']) {
      await expect(tabItem(page, label)).toBeVisible();
    }
    // 默认停留在「权限组」Tab
    await expect(tabItem(page, '权限组')).toHaveClass(/is-active/);
    await expect(paneRows(page, 0).first()).toBeVisible();
  });

  test('should keep detail tab row counts consistent with 权限组 tab', async ({ page }) => {
    await openDrawer(page, '/shop');

    const groupRows = paneRows(page, 0);
    const groupCount = await groupRows.count();
    expect(groupCount).toBeGreaterThan(0);

    // 汇总「权限组」Tab 的操作权限(2) / 字段权限(3) / 数据范围(4) / 绑定主体(5) 列计数
    const sumColumn = async (index) => {
      let total = 0;
      for (let i = 0; i < groupCount; i += 1) {
        const text = (await groupRows.nth(i).locator('td').nth(index).innerText()).trim();
        total += Number(text);
      }
      return total;
    };
    const permissionTotal = await sumColumn(2);
    const fieldTotal = await sumColumn(3);
    const scopeTotal = await sumColumn(4);
    const subjectTotal = await sumColumn(5);
    expect(permissionTotal).toBeGreaterThan(0);

    // 操作权限 Tab 每组一行；字段 / 数据范围 / 主体绑定 Tab 行数 = 各组计数之和
    await tabItem(page, '操作权限').click();
    await expect(paneRows(page, 1)).toHaveCount(groupCount);
    await tabItem(page, '字段权限').click();
    await expect(paneRows(page, 2)).toHaveCount(fieldTotal);
    await tabItem(page, '数据范围').click();
    await expect(paneRows(page, 3)).toHaveCount(scopeTotal);
    await tabItem(page, '主体绑定').click();
    await expect(paneRows(page, 4)).toHaveCount(subjectTotal);
  });

  test('should switch to each detail tab and show its own columns', async ({ page }) => {
    await openDrawer(page, '/shop');

    const cases = [
      { index: 1, label: '操作权限', headers: ['权限组', '已授权权限点'] },
      { index: 2, label: '字段权限', headers: ['权限组', '模块', '字段', '可见', '可编辑'] },
      { index: 3, label: '数据范围', headers: ['权限组', '模块', '范围'] },
      { index: 4, label: '主体绑定', headers: ['权限组', '主体类型', '主体'] },
    ];

    for (const item of cases) {
      await tabItem(page, item.label).click();
      await expect(tabItem(page, item.label)).toHaveClass(/is-active/);
      await expect(paneRows(page, item.index).first()).toBeVisible();
      for (const header of item.headers) {
        await expect(
          drawerPane(page, item.index).locator(`.el-table__header-wrapper th .cell:text-is("${header}")`),
        ).toBeVisible();
      }
    }
  });

  test('should close drawer via footer button', async ({ page }) => {
    await openDrawer(page, '/shop');
    await drawer(page).locator('.el-drawer__footer button:has-text("关闭")').click();
    // el-drawer 关闭后节点仍保留在 DOM 中（v-show 隐藏），断言隐藏而非移除
    await expect(drawer(page)).toBeHidden();
  });

  test('should keep drawer entry working on another menu', async ({ page }) => {
    await openDrawer(page, '/product');
    await expect(drawer(page).locator('.el-drawer__title')).toContainText('权限组配置');
    await expect(drawer(page).locator('.el-tabs__item')).toHaveCount(5);
    // 商品菜单下的种子权限组
    await expect(paneRows(page, 0)).toHaveCount(2);
  });

  test('should create group from drawer with code/menu/module auto-maintained and hidden', async ({ page }) => {
    // 待采集列表页（nav:collect → collectqueue）作为入口
    await page.goto('/collect');
    const entry = page.locator('button[title="权限组配置"]');
    await expect(entry).toBeVisible({ timeout: 15000 });
    await entry.click();
    await expect(drawer(page)).toBeVisible({ timeout: 15000 });

    await drawer(page).locator('button:has-text("新建权限组")').click();

    const dialog = page.locator('.el-dialog:visible');
    await expect(dialog.locator('.el-dialog__title')).toHaveText('新建权限组');
    // 抽屉入口下：编码 / 所属菜单 / 业务模块 均不展示（自动维护）
    for (const label of ['权限组编码', '所属菜单', '业务模块']) {
      await expect(dialog.locator(`.el-form-item__label:text-is("${label}")`)).toHaveCount(0);
    }
    // 其余字段仍正常展示
    for (const label of ['权限组名称', '排序', '状态', '描述']) {
      await expect(dialog.locator(`.el-form-item__label:text-is("${label}")`)).toBeVisible();
    }

    const title = `抽屉自动编码_${Date.now()}`;
    await dialog.locator('.el-form-item:has(.el-form-item__label:text-is("权限组名称")) input').fill(title);
    await dialog.locator('button:has-text("确定")').click();
    await expect(dialog).toBeHidden({ timeout: 15000 });

    // 抽屉「权限组」表格同样不展示编码 / 业务模块（自动维护字段）
    for (const header of ['编码', '业务模块']) {
      await expect(
        drawerPane(page, 0).locator(`.el-table__header-wrapper th .cell:text-is("${header}")`),
      ).toHaveCount(0);
    }
    const newRow = paneRows(page, 0).filter({ hasText: title });
    await expect(newRow).toBeVisible({ timeout: 15000 });

    // 编码 / 业务模块仍在后端自动维护（pg:collectqueue:NNN + collectqueue）
    const token = await page.evaluate(() => localStorage.getItem('token'));
    const headers = { Authorization: `Bearer ${token}` };
    const listRes = await page.request.post('/admin/permission-group/get-group-list', {
      data: { data: { page: 1, limit: 200, menu_id: 3 } },
      headers,
    });
    const listBody = await listRes.json();
    const target = (listBody.data?.items || []).find((item) => item.title === title);
    expect(target).toBeTruthy();
    expect(target.code).toMatch(/^pg:collectqueue:\d{3}$/);
    expect(target.module).toBe('collectqueue');
    const delRes = await page.request.post('/admin/permission-group/delete-group', {
      data: { data: { id: target.id } },
      headers,
    });
    expect((await delRes.json()).code).toBe(200);
  });
});
