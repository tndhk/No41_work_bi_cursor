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
- Python 3.11（ローカル開発時）
- Node.js 20.x（ローカル開発時）

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

詳細は [docs/](docs/) を参照してください。
