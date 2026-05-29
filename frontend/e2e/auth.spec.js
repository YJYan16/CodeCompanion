import { test, expect } from '@playwright/test'

test.describe('码途智伴 E2E', () => {
  test('学生登录并进入主页', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('学号').fill('2024001')
    await page.getByPlaceholder('密码').fill('123456')
    await page.getByRole('button', { name: '登 录' }).click()
    await expect(page).toHaveURL('/')
    await expect(page.getByText('码途智伴')).toBeVisible()
  })

  test('教师登录并进入管理后台', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('学号').fill('admin')
    await page.getByPlaceholder('密码').fill('admin123')
    await page.getByRole('button', { name: '登 录' }).click()
    await expect(page).toHaveURL(/\/admin/)
    await expect(page.getByText('教师管理平台')).toBeVisible()
  })

  test('错误密码无法登录', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('学号').fill('2024001')
    await page.getByPlaceholder('密码').fill('wrong')
    page.on('dialog', (dialog) => dialog.accept())
    await page.getByRole('button', { name: '登 录' }).click()
    await expect(page).toHaveURL('/login')
  })
})
