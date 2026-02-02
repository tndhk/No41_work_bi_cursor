# 社内BI・Pythonカード

ローカルCSVおよびS3上のCSVを取り込み、PythonでHTMLカードを定義してダッシュボードに配置できる社内BIツール。

## プロジェクト構成

- `frontend/` - React SPA (TypeScript + Vite)
- `backend/` - FastAPI (Python 3.11)
- `executor/` - Python実行基盤（サンドボックス）
- `infra/` - Terraform（AWSインフラ）
- `docs/` - 要件・設計ドキュメント

## 開発環境セットアップ

### 前提条件

- Docker 24.x
- docker-compose 2.x

**重要**: このプロジェクトはDockerベースです。開発・テストは**必ずDocker Composeを使用**してください。ローカル環境で直接実行すると依存サービスが起動していないためエラーになります。

### 起動方法

```bash
# 環境変数ファイルをコピー
cp .env.example .env

# サービス起動
docker-compose up -d

# API: http://localhost:8000
# Frontend: http://localhost:3000
# MinIO Console: http://localhost:9001
```

### テスト実行

```bash
# バックエンドテスト（必ずDocker Composeを使用）
docker compose run --rm api pytest tests/ -v

# テスト完了後はDockerを停止
docker compose down

# フロントエンドテスト
cd frontend && npm run test
```

**⚠️ 注意:** ローカルで`pytest`を直接実行しないでください。DynamoDB LocalやMinIOなどの依存サービスが必要なため、必ずDocker Composeを使用してください。

詳細は [docs/CONTRIB.md](docs/CONTRIB.md) を参照してください。
