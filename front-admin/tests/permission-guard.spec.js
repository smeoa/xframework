// @ts-check
import { test, expect } from '@playwright/test';

/**
 * 路由级权限守卫 E2E
 *
 * 覆盖 router/index.js 的 beforeEach：
 *  1. 未登录访问受保护菜单 → 跳转 /login
 *  2. 已登录访问 /login → 回到该账号首个可访问菜单
 *  3. 无 meta.permission 授权 → 跳转 /403
 *  4. 管理员（全量权限）可进入所有受保护菜单
 *  5. 进入菜单前 alignGroupForMenu 对齐激活组，使操作权限自愈（dashboard:view 取数 200）
 */

// admin：is_admin=True 全量权限；deptuser：普通用户，仅有部分菜单权限
const ADMIN = { username: 'admin', password: 'admin123' };
const DEPT_USER = { username: 'deptuser', password: '123456' };

async function login(page, { username, password }) {
  await page.goto('/login');
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', username);
  await page.fill('input[placeholder="请输入密码"]', password);
  await page.click('button:has-text("登录")');
  // 登录后进入该账号第一个可访问菜单，离开 /login 即视为登录成功
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15000 });
}

const forbiddenResult = (page) => page.locator('.forbidden-container');

test.describe('Route permission guard', () => {
  test('should redirect unauthenticated visitor to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible();
  });

  test('should redirect logged-in user away from login page', async ({ page }) => {
    await login(page, DEPT_USER);
    await page.goto('/login');
    await expect(page).not.toHaveURL(/\/login$/);
  });

  test('should allow admin to open protected menus', async ({ page }) => {
    await login(page, ADMIN);
    for (const path of ['/dashboard', '/permission-group', '/menu', '/organization']) {
      await page.goto(path);
      await expect(page).not.toHaveURL(/\/403$/);
      await expect(page.locator('.layout-container')).toBeVisible({ timeout: 15000 });
    }
  });

  test('should block menus without permission for non-admin user', async ({ page }) => {
    await login(page, DEPT_USER);
    // deptuser 无 nav:permission-group / nav:menu / nav:organization 权限
    for (const path of ['/permission-group', '/menu', '/organization']) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/403$/);
      await expect(forbiddenResult(page)).toBeVisible();
      await expect(forbiddenResult(page)).toContainText('403');
    }
  });

  test('should render dashboard for non-admin user by aligning active group', async ({ page }) => {
    await login(page, DEPT_USER);
    // 仪表盘取数依赖操作权限 dashboard:view（仅来自激活组），验证自愈后接口返回 200
    const summaryResponse = page.waitForResponse(
      (res) =>
        res.url().includes('/admin/dashboard/summary') && res.request().method() === 'POST',
      { timeout: 20000 },
    );
    await page.goto('/dashboard');
    await expect(page).not.toHaveURL(/\/403$/);
    await expect(page.locator('.dashboard-main')).toBeVisible({ timeout: 15000 });
    const resp = await summaryResponse;
    expect(resp.status()).toBe(200);
  });

  test('should provide back and home actions on 403 page', async ({ page }) => {
    await login(page, DEPT_USER);
    await page.goto('/menu');
    await expect(forbiddenResult(page)).toBeVisible();
    await expect(page.locator('button:has-text("返回上一页")')).toBeVisible();
    const homeButton = page.locator('button:has-text("回到首页")');
    await expect(homeButton).toBeVisible();
    // 回到首页：跳转到该账号可访问的菜单，离开 /403
    await homeButton.click();
    await expect(page).not.toHaveURL(/\/403$/);
  });
});
