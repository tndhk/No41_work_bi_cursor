# テストガイド

## 概要

このドキュメントでは、実装したMVP機能をテストする手順を説明します。

## 前提条件

- Docker 24.x
- docker-compose 2.x
- ブラウザ（Chrome/Firefox推奨）

## 1. 環境セットアップ

### 1.1 環境変数ファイルの準備

```bash
# プロジェクトルートで実行
cp .env.example .env
```

`.env`ファイルは既にdocker-compose.ymlで設定されているため、基本的にはそのままで動作します。

### 1.2 サービス起動

```bash
# すべてのサービスを起動（バックグラウンド）
docker-compose up -d

# ログを確認したい場合
docker-compose up
```

起動するサービス:
- **api** (Backend API): http://localhost:8000
- **executor** (Python実行基盤): http://localhost:8080
- **frontend** (React SPA): http://localhost:3000
- **dynamodb-local** (DynamoDB Local): http://localhost:8001
- **minio** (S3互換ストレージ): http://localhost:9000 (API), http://localhost:9001 (Console)

### 1.3 サービスの起動確認

```bash
# すべてのサービスが起動しているか確認
docker-compose ps

# 各サービスのログを確認
docker-compose logs api
docker-compose logs executor
docker-compose logs frontend
```

### 1.4 データベース・ストレージの初期化

#### DynamoDBテーブルの作成

```bash
# APIコンテナ内でテーブル初期化スクリプトを実行
docker-compose exec api python scripts/init_tables.py
```

または、テストセットアップAPIを使用:

```bash
# テスト用のセットアップAPIを呼び出す（ALLOW_TEST_SETUP=trueの場合）
curl -X POST http://localhost:8000/api/test-setup
```

#### MinIOバケットの作成

```bash
# S3バケット初期化スクリプトを実行
bash scripts/init-s3.sh
```

または、MinIO Console (http://localhost:9001) にアクセスして手動で作成:
- ログイン: minioadmin / minioadmin
- バケット作成: `bi-datasets`, `bi-static`

## 2. バックエンドテスト

### 2.1 ユニットテスト実行

```bash
# すべてのテストを実行
docker compose run --rm api pytest tests/ -v

# 特定のテストファイルを実行
docker compose run --rm api pytest tests/test_cards.py -v

# カバレッジ付きで実行
docker compose run --rm api pytest tests/ --cov=app --cov-report=html
```

### 2.2 API動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# Executorヘルスチェック
curl http://localhost:8080/health

# APIドキュメント確認
# ブラウザで http://localhost:8000/docs にアクセス
```

## 3. フロントエンドテスト

### 3.1 ユニットテスト実行

```bash
cd frontend
npm install  # 初回のみ
npm run test
```

### 3.2 フロントエンド開発サーバー起動（オプション）

```bash
cd frontend
npm run dev
# http://localhost:5173 でアクセス可能（Viteのデフォルトポート）
```

## 4. 手動テスト（ブラウザ）

### 4.1 アプリケーションにアクセス

1. ブラウザで http://localhost:3000 にアクセス
2. ログインページが表示される

### 4.2 テストユーザーの作成

初回起動時はテストユーザーが存在しないため、API経由で作成する必要があります。

```bash
# テストユーザー作成（テストセットアップAPIを使用）
curl -X POST http://localhost:8000/api/test-setup

# または、手動でユーザー作成APIを呼び出す
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "name": "テストユーザー"
  }'
```

### 4.3 ログイン

1. http://localhost:3000 にアクセス
2. テストユーザーのメールアドレスとパスワードでログイン

### 4.4 MVP機能のテスト

#### 4.4.1 Dataset取り込み

1. **Local CSV Import**
   - Dataset一覧画面で「新規作成」→「Local CSV」を選択
   - CSVファイルをアップロード
   - プレビューが表示されることを確認
   - 「取り込み」をクリックしてDatasetが作成されることを確認

2. **S3 CSV Import**
   - Dataset一覧画面で「新規作成」→「S3 CSV」を選択
   - S3接続情報を入力（MinIOの場合: minioadmin/minioadmin）
   - バケット/ファイルを選択して取り込み

#### 4.4.2 Transform実行

1. Transform一覧画面で「新規作成」をクリック
2. Transform名、入力Dataset、Pythonコードを入力
3. 「実行」ボタンをクリック
4. 実行が完了し、出力Datasetが生成されることを確認

**テスト用Transformコード例:**
```python
def transform(inputs, params):
    # 入力Datasetを取得
    df = inputs[list(inputs.keys())[0]]
    # 簡単な変換を実行
    result = df.copy()
    return result
```

#### 4.4.3 Card作成・プレビュー

1. Card一覧画面で「新規作成」をクリック
2. Card名、Dataset、Pythonコードを入力
3. 「プレビュー」タブでフィルタを設定して「プレビュー実行」
4. HTMLが生成されることを確認

**テスト用Cardコード例:**
```python
def render(dataset, filters, params):
    return {
        "html": f"<div><h1>データ行数: {len(dataset)}</h1></div>",
        "used_columns": list(dataset.columns),
        "filter_applicable": []
    }
```

#### 4.4.4 Dashboard作成・編集

1. Dashboard一覧画面で「新規作成」をクリック
2. Dashboard名を入力
3. 編集画面でCardを追加・配置
4. レイアウトが保存されることを確認

#### 4.4.5 ページフィルタ

1. Dashboard閲覧画面でフィルタバーを表示
2. カテゴリフィルタまたは日付フィルタを設定
3. フィルタがカードに反映されることを確認

#### 4.4.6 FilterView管理

1. Dashboard閲覧画面でフィルタを設定
2. 「フィルタビュー」セクションで「保存」をクリック
3. ビュー名を入力して保存
4. 保存したビューを選択して適用
5. フィルタが復元されることを確認

#### 4.4.7 Dashboard共有

1. Dashboard閲覧画面で「共有」ボタンをクリック
2. 共有ダイアログでユーザーまたはグループを選択
3. 権限を設定して「共有」をクリック
4. 共有一覧に追加されることを確認

#### 4.4.8 Chatbot

1. Dashboard閲覧画面で「データを質問」ボタンをクリック
2. チャットパネルで質問を入力
3. AIが回答を返すことを確認

## 5. トラブルシューティング

### 5.1 サービスが起動しない

```bash
# ログを確認
docker-compose logs

# サービスを再起動
docker-compose restart

# 完全にクリーンアップして再起動
docker-compose down
docker-compose up -d
```

### 5.2 DynamoDBテーブルが存在しない

```bash
# テーブル初期化スクリプトを実行
docker-compose exec api python scripts/init_tables.py
```

### 5.3 S3バケットが存在しない

```bash
# S3バケット初期化スクリプトを実行
bash scripts/init-s3.sh
```

### 5.4 Executorサービスに接続できない

```bash
# Executorのログを確認
docker-compose logs executor

# Executorのヘルスチェック
curl http://localhost:8080/health
```

### 5.5 フロントエンドがAPIに接続できない

- `.env`ファイルまたは`docker-compose.yml`で`VITE_API_URL`が正しく設定されているか確認
- ブラウザの開発者ツール（F12）でネットワークエラーを確認
- CORSエラーの場合は、バックエンドのCORS設定を確認

## 6. テスト完了後のクリーンアップ

```bash
# すべてのサービスを停止
docker-compose down

# ボリュームも含めて完全に削除（データも削除される）
docker-compose down -v
```

## 7. 次のステップ

実装した機能の動作確認が完了したら、`docs/mvp-uat-checklist.md`に従ってUATを実施してください。
