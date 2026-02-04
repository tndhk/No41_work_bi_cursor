import { test, expect, Page, Request } from '@playwright/test'
import { setupTestData } from './utils'

function waitForPreviewRequest(page: Page): Promise<Request> {
  return page.waitForRequest(
    (request) =>
      request.url().includes('/api/cards/') &&
      request.url().includes('/preview') &&
      request.method() === 'POST'
  )
}

function verifyFilterPayload(
  request: Request,
  filterName: string,
  expectedValue: string
): void {
  const requestData = request.postDataJSON()
  expect(requestData.filters).toBeDefined()
  expect(requestData.filters[filterName]).toBe(expectedValue)
}

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
    
    // フィルタ値を変更してリクエストを検証
    const requestPromise1 = waitForPreviewRequest(page)
    await filterInput.fill('B')
    const request1 = await requestPromise1
    verifyFilterPayload(request1, testData.filter_name, 'B')
    
    // カードコンテンツが更新されることを確認
    await expect(page.locator('.card-content')).toContainText('Filter: B')
    
    // フィルタ値を別の値に変更してリクエストを検証
    const requestPromise2 = waitForPreviewRequest(page)
    await filterInput.fill('C')
    const request2 = await requestPromise2
    verifyFilterPayload(request2, testData.filter_name, 'C')
    
    // カードコンテンツが再度更新されることを確認
    await expect(page.locator('.card-content')).toContainText('Filter: C')
  })
})
