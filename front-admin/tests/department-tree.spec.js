// @ts-check
import { test, expect } from '@playwright/test';

// 部门树依赖登录态，统一在 beforeEach 中完成登录
async function login(page) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[placeholder="请输入密码"]', 'admin123');
  await page.click('button:has-text("登录")');
  await page.waitForURL('**/dashboard', { timeout: 15000 });
}

async function gotoOrganization(page) {
  await page.goto('/organization');
  await expect(page.locator('.organization-aside .el-tree')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(800);
}

// 根级部门名称（el-tree 直接子节点）
const rootNameLocator = (page) =>
  page.locator(
    '.organization-aside .el-tree > .el-tree-node > .el-tree-node__content .tree-node-content > div:first-child'
  );

const rootNames = async (page) => rootNameLocator(page).allInnerTexts();

// 按显示文本定位树节点内容行（子节点渲染在 __content 之外，不会误命中父节点）
const nodeContent = (page, name) =>
  page.locator('.organization-aside .el-tree-node__content').filter({ hasText: name });

// HTML5 拖拽：鼠标按下后移动到目标节点上沿（<25% 高度，触发 dropType = before）
async function dragBefore(page, source, target) {
  await source.scrollIntoViewIfNeeded();
  const s = await source.boundingBox();
  const t = await target.boundingBox();
  expect(s && t).toBeTruthy();

  await page.mouse.move(s.x + s.width / 2, s.y + s.height / 2);
  await page.mouse.down();
  // 先小幅移动越过拖拽阈值，触发 dragstart
  await page.mouse.move(s.x + s.width / 2 + 12, s.y + s.height / 2 + 2, { steps: 4 });
  // 再移动到目标节点上沿
  await page.mouse.move(t.x + 40, t.y + 3, { steps: 10 });
  await page.waitForTimeout(300);
  await page.mouse.up();
}

test.describe('Department Tree Drag Sort', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('同级拖拽排序应落库并在刷新后保持', async ({ page, request }) => {
    await gotoOrganization(page);

    const token = await page.evaluate(() => localStorage.getItem('token'));
    const apiPost = async (url, data) => {
      const res = await request.post(url, {
        headers: { Authorization: `Bearer ${token}` },
        // 后端统一从 body.data 取业务参数（与 request.js 一致）
        data: { data },
      });
      const body = await res.json();
      expect(body.code, `${url} -> ${JSON.stringify(body)}`).toBe(200);
      return body.data;
    };
    const fetchTree = () => apiPost('/admin/organization/get-dept-tree', {});
    const childrenOf = (tree, pid) => {
      const node = tree.find((item) => item.id === pid);
      return node?.children || [];
    };

    // 1. 页面渲染的根级顺序应与真实后端一致（排除 mock 数据 总部/产品部）
    const tree0 = await fetchTree();
    const apiRootNames = tree0.map((item) => item.name);
    const domRootNames = await rootNames(page);
    expect(domRootNames).toEqual(apiRootNames);
    expect(domRootNames).not.toContain('总部');

    // 2. 造两个同级临时部门，作为可识别的拖拽对象
    const stamp = Date.now();
    const nameA = `E2E排序A_${stamp}`;
    const nameB = `E2E排序B_${stamp}`;
    // 挂到无子节点的根部门下，拖拽只影响这两个临时部门，避免改动既有数据
    const parentId = tree0.find((item) => !item.children)?.id;
    expect(parentId).toBeTruthy();
    const created = [];
    try {
      for (const [name, sort] of [
        [nameA, 900],
        [nameB, 910],
      ]) {
        const dept = await apiPost('/admin/organization/create-dept', {
          name,
          code: `e2e_sort_${stamp}_${sort}`,
          pid: parentId,
          sort,
        });
        created.push(dept.id);
      }

      await page.reload();
      await expect(page.locator('.organization-aside .el-tree')).toBeVisible({ timeout: 15000 });
      await page.waitForTimeout(800);

      const boxA0 = await nodeContent(page, nameA).boundingBox();
      const boxB0 = await nodeContent(page, nameB).boundingBox();
      expect(boxB0.y).toBeGreaterThan(boxA0.y);

      // 3. 把 B 拖到 A 之前
      await dragBefore(page, nodeContent(page, nameB), nodeContent(page, nameA));
      await expect(page.locator('.el-message--success').last()).toContainText('调整成功', {
        timeout: 15000,
      });
      await page.waitForTimeout(1200);

      // 4. 界面顺序已交换
      const boxA1 = await nodeContent(page, nameA).boundingBox();
      const boxB1 = await nodeContent(page, nameB).boundingBox();
      expect(boxB1.y).toBeLessThan(boxA1.y);

      // 5. 已落库：B 排在 A 之前，且同级 sort 按位置递增
      const children = childrenOf(await fetchTree(), parentId);
      const ids = children.map((item) => item.id);
      expect(ids.indexOf(created[1])).toBeLessThan(ids.indexOf(created[0]));
      expect(children.map((item) => item.sort)).toEqual(
        children.map((_, index) => (index + 1) * 10)
      );

      // 6. 刷新后顺序保持
      await page.reload();
      await expect(page.locator('.organization-aside .el-tree')).toBeVisible({ timeout: 15000 });
      await page.waitForTimeout(800);
      const boxA2 = await nodeContent(page, nameA).boundingBox();
      const boxB2 = await nodeContent(page, nameB).boundingBox();
      expect(boxB2.y).toBeLessThan(boxA2.y);
    } finally {
      // 清理临时部门，避免污染数据
      for (const id of created.reverse()) {
        await apiPost('/admin/organization/delete-dept', { id });
      }
    }
  });
});
