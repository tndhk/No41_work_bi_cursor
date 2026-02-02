import { test, expect } from '@playwright/test'
import { setupTestData } from './utils'

test.describe('Critical Path E2E', () => {
  test('login → dashboard view → filter change', async ({ page, request }) => {
    // テストデータをセットアップ
    const testData = await setupTestData(request)
    
    // カードプレビューAPIをスタブ化
    await page.route('**/api/cards/*/preview', async (route) => {
      const requestData = route.request().postDataJSON()
      const filterValue = requestData?.filters?.[testData.filter_name] || 'A'
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            html: `<div>Filter: ${filterValue}</div><div>Value: 100</div>`,
            used_columns: ['category', 'value'],
            filter_applicable: ['category'],
          },
        }),
      })
    })
    
    // ログインページにアクセス
    await page.goto('/login')
    
    // ログインフォームに入力
    await page.getByLabel('メールアドレス').fill(testData.email)
    await page.getByLabel('パスワード').fill(testData.password)
    
    // ログインボタンをクリック
    await page.getByRole('button', { name: 'ログイン' }).click()
    
    // ダッシュボード一覧ページにリダイレクトされることを確認
    await expect(page).toHaveURL('/dashboards')
    
    // ダッシュボード一覧にテストダッシュボードが表示されることを確認
    await expect(page.getByRole('link', { name: testData.dashboard_name })).toBeVisible()
    
    // ダッシュボードをクリックして開く
    await page.getByRole('link', { name: testData.dashboard_name }).click()
    
    // ダッシュボード詳細ページに遷移することを確認
    await expect(page).toHaveURL(new RegExp(`/dashboards/${testData.dashboard_id}`))
    
    // ダッシュボード名が表示されることを確認
    await expect(page.getByRole('heading', { name: testData.dashboard_name })).toBeVisible()
    
    // フィルタ入力欄を取得
    const filterInput = page.getByLabel(testData.filter_name)
    await expect(filterInput).toBeVisible()
    
    // フィルタ値を変更
    await filterInput.fill('B')
    
    // カードコンテンツが更新されることを確認（スタブされたHTMLに新しいフィルタ値が含まれる）
    await expect(page.locator('.card-content')).toContainText('Filter: B')
    
    // フィルタ値を別の値に変更
    await filterInput.fill('C')
    
    // カードコンテンツが再度更新されることを確認
    await expect(page.locator('.card-content')).toContainText('Filter: C')
  })
})
