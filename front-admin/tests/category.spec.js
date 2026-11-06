// @ts-check
import { test, expect } from '@playwright/test';

// 类目管理页面依赖登录态
async function login(page) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}

async function gotoCategory(page) {
  await page.goto('/category');
  await expect(page.locator('.category-body')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.category-platform-tabs')).toBeVisible({ timeout: 15000 });
}

// 主体工作区左右两栏
const leftCol = (page) => page.locator('.category-body > .el-col').first();
const rightCol = (page) => page.locator('.category-body > .el-col').last();

test.describe.serial('Category Module Layout', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should render two columns: left category info, right attribute info', async ({ page }) => {
    await gotoCategory(page);

    // 主体工作区恰好两栏
    await expect(page.locator('.category-body > .el-col')).toHaveCount(2);

    // 左栏：类目浏览区（面包屑根节点「全部类目」）
    await expect(leftCol(page).locator('.panel-breadcrumb')).toBeVisible();
    await expect(leftCol(page).locator('.panel-breadcrumb')).toContainText('全部类目');

    // 右栏：卡片头部显示类目完整路径，卡片主体为属性信息表格
    await expect(rightCol(page).locator('.panel-header')).toContainText('完整路径：');
    await expect(rightCol(page).locator('.el-table')).toBeVisible();

    // 两栏并排：左栏在右栏左侧且纵向重叠
    const leftBox = await leftCol(page).boundingBox();
    const rightBox = await rightCol(page).boundingBox();
    expect(leftBox).not.toBeNull();
    expect(rightBox).not.toBeNull();
    expect(leftBox.x + leftBox.width).toBeLessThanOrEqual(rightBox.x + 1);
    expect(leftBox.y).toBeLessThan(rightBox.y + rightBox.height);
  });

  test('should not render the brand list panel', async ({ page }) => {
    await gotoCategory(page);

    // 品牌列表入口（标题 / 搜索框 / 品牌ID 列）已全部移除
    await expect(page.getByText('品牌列表', { exact: true })).toHaveCount(0);
    await expect(page.locator('input[placeholder="品牌名称"]')).toHaveCount(0);
    await expect(page.locator('.category-body')).not.toContainText('品牌ID');
    await expect(page.locator('.brand-pagination')).toHaveCount(0);
  });

  test('should remove query-category button and keep only search button in search bar', async ({
    page,
  }) => {
    await gotoCategory(page);

    // 「查询类目」已删除
    await expect(page.locator('button:has-text("查询类目")')).toHaveCount(0);

    // 关键词搜索栏仅保留「搜索类目」按钮（「强制刷新」已移除）
    const searchBar = page.locator('.search-bar').first();
    const buttons = searchBar.locator('button');
    await expect(buttons).toHaveCount(1);
    await expect(buttons.nth(0)).toContainText('搜索类目');

    // DHgate 下筛选栏（站点/初始化信息）整体隐藏
    await expect(page.locator('.filter-bar')).toHaveCount(0);
  });

  test('should show recent categories on the left for Voghion', async ({ page }) => {
    await gotoCategory(page);

    // 切到 Voghion
    await page.locator('.category-platform-tabs .el-tabs__item:has-text("Voghion")').click();
    await expect(leftCol(page).getByText('最近使用类目', { exact: true })).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByText('类目预测', { exact: true })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('品牌列表', { exact: true })).toHaveCount(0);
  });

  test('should fill category info and attribute info after selecting a searched category', async ({
    page,
  }) => {
    await gotoCategory(page);

    // 关键词找类目
    await page.fill('.search-input input', '服装');
    await page.locator('button:has-text("搜索类目")').click();

    // 搜索态：左栏切换为搜索结果，类目浏览（面包屑）隐藏
    await expect(leftCol(page).getByText('关键词搜索结果', { exact: true })).toBeVisible({
      timeout: 30000,
    });
    await expect(leftCol(page).locator('.panel-breadcrumb')).toHaveCount(0);

    const rows = leftCol(page).locator('.el-table__body-wrapper tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 30000 });

    const firstCid = (await rows.first().locator('td').nth(0).innerText()).trim();
    const firstName = (await rows.first().locator('td').nth(1).innerText()).trim();
    await rows.first().locator('button:has-text("选中")').click();

    // 右栏卡片头部回填所选类目的完整路径与类目ID（仅显示ID数字，不带「类目ID：」标签）
    await expect(rightCol(page).locator('.panel-header')).toContainText(firstName, {
      timeout: 15000,
    });
    await expect(rightCol(page).locator('.panel-header')).toContainText(firstCid);
    await expect(rightCol(page).locator('.panel-header')).not.toContainText('类目ID：');

    // 右栏「属性信息」：选中类目后自动加载属性模板，不应报错
    await expect(page.locator('.el-message--error')).toHaveCount(0);

    // 清空搜索框：退出搜索态，左栏恢复类目浏览（面包屑）
    await page.fill('.search-input input', '');
    await expect(leftCol(page).locator('.panel-breadcrumb')).toBeVisible();
    await expect(leftCol(page).locator('.panel-breadcrumb')).toContainText('全部类目');
    await expect(leftCol(page).getByText('关键词搜索结果', { exact: true })).toHaveCount(0);
  });

  test('should keep platform tabs left aligned after visiting product list', async ({ page }) => {
    // 先进商品列表：该页全局引入 product.css，其中 .platform-tabs 为 space-between
    await page.goto('/product');
    await expect(page.locator('.platform-tabs')).toBeVisible({ timeout: 15000 });

    await gotoCategory(page);

    // 平台页签应靠左：左边界与卡片主体内容左边界对齐
    const headerBox = await page.locator('.category-platform-tabs .el-tabs__header').boundingBox();
    const bodyEl = page.locator('.filter-card > .el-card__body');
    const bodyBox = await bodyEl.boundingBox();
    const bodyPaddingLeft = await bodyEl.evaluate((el) => parseFloat(getComputedStyle(el).paddingLeft));
    expect(Math.abs(headerBox.x - (bodyBox.x + bodyPaddingLeft))).toBeLessThanOrEqual(2);
  });
});
