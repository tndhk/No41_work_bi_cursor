# E2Eテスト実行手順

## 前提条件

1. **ネットワーク接続**: npmレジストリにアクセスできること
2. **バックエンドサーバー**: ローカルで起動していること（ポート8000）
3. **DynamoDB/S3**: ローカル環境が起動していること

## セットアップ手順

### 1. Playwrightのインストール

```bash
cd frontend
npm install
npx playwright install --with-deps chromium
```

### 2. バックエンドのテストセットアップを有効化

バックエンドを起動する前に、環境変数を設定：

```bash
export ALLOW_TEST_SETUP=true
```

または `.env` ファイルに追加：

```
ALLOW_TEST_SETUP=true
```

### 3. バックエンドサーバーの起動

```bash
cd backend
# 環境変数を設定してから
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. E2Eテストの実行

別のターミナルで：

```bash
cd frontend
npm run test:e2e
```

Playwrightの設定により、フロントエンドサーバーは自動的に起動されます。

## トラブルシューティング

### ネットワークエラーの場合

npmレジストリに接続できない場合は、プロキシ設定を確認：

```bash
npm config get proxy
npm config get https-proxy
```

### バックエンドが起動していない場合

テストセットアップエンドポイントが403エラーを返す場合は、`ALLOW_TEST_SETUP=true`が設定されているか確認してください。

### ブラウザがインストールされていない場合

```bash
npx playwright install chromium
```

## テスト内容

`e2e/critical-path.spec.ts` が実行され、以下をテストします：

1. ログイン
2. ダッシュボード一覧表示
3. ダッシュボード詳細表示
4. フィルタ変更とカード更新
