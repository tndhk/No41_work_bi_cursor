# 社内BI MVP 実装TODO

## 現在の実装状況

### 完了済み
- [x] プロジェクト構造作成
- [x] バックエンド基本構造（FastAPI + 設定管理）
- [x] フロントエンド基本構造（React + TypeScript + Vite）
- [x] docker-compose開発環境
- [x] DynamoDB接続層
- [x] S3接続層
- [x] 認証基盤（JWT + パスワードハッシュ）
- [x] ミドルウェア・エラーハンドリング
- [x] Users API基本構造

---

## 次にやるべきこと

### 優先度: 高

#### 1. 認証APIの完全実装
- [ ] `POST /api/auth/login` - ユーザ認証処理
- [ ] `GET /api/auth/me` - 現在のユーザ情報取得
- [ ] ユーザ登録エンドポイント（必要に応じて）

#### 2. Groups API
- [ ] `backend/app/models/group.py` - Groupモデル定義
- [ ] `backend/app/services/group_service.py` - Groupサービス
- [ ] `backend/app/api/routes/groups.py` - Groupルート
  - [ ] `GET /api/groups` - グループ一覧取得
  - [ ] `POST /api/groups` - グループ作成
  - [ ] `GET /api/groups/{groupId}` - グループ詳細取得
  - [ ] `PUT /api/groups/{groupId}` - グループ更新
  - [ ] `DELETE /api/groups/{groupId}` - グループ削除
  - [ ] `POST /api/groups/{groupId}/members` - メンバー追加
  - [ ] `DELETE /api/groups/{groupId}/members/{userId}` - メンバー削除

#### 3. Datasets API
- [ ] `backend/app/models/dataset.py` - Datasetモデル定義
- [ ] `backend/app/services/dataset_service.py` - Datasetサービス
  - [ ] CSV取り込み（Local）
  - [ ] CSV取り込み（S3）
  - [ ] Parquet変換・保存
  - [ ] プレビュー生成
  - [ ] 再取り込み
  - [ ] スキーマ変更検知
- [ ] `backend/app/api/routes/datasets.py` - Datasetルート
  - [ ] `GET /api/datasets` - Dataset一覧取得
  - [ ] `POST /api/datasets` - Dataset作成（Local CSV）
  - [ ] `POST /api/datasets/s3-import` - S3 CSV取り込み
  - [ ] `GET /api/datasets/{datasetId}` - Dataset詳細取得
  - [ ] `PUT /api/datasets/{datasetId}` - Dataset更新
  - [ ] `DELETE /api/datasets/{datasetId}` - Dataset削除
  - [ ] `POST /api/datasets/{datasetId}/import` - 再取り込み
  - [ ] `GET /api/datasets/{datasetId}/preview` - プレビュー取得

### 優先度: 中

#### 4. Transforms API
- [ ] `backend/app/models/transform.py` - Transformモデル定義
- [ ] `backend/app/services/transform_service.py` - Transformサービス
- [ ] `backend/app/api/routes/transforms.py` - Transformルート
  - [ ] CRUD操作
  - [ ] 手動実行
  - [ ] スケジュール設定
  - [ ] 実行履歴取得

#### 5. Cards API
- [ ] `backend/app/models/card.py` - Cardモデル定義
- [ ] `backend/app/services/card_service.py` - Cardサービス
- [ ] `backend/app/api/routes/cards.py` - Cardルート
  - [ ] CRUD操作
  - [ ] プレビュー実行
  - [ ] カード実行（Dashboard用）

#### 6. Dashboards API
- [ ] `backend/app/models/dashboard.py` - Dashboardモデル定義
- [ ] `backend/app/services/dashboard_service.py` - Dashboardサービス
- [ ] `backend/app/api/routes/dashboards.py` - Dashboardルート
  - [ ] CRUD操作
  - [ ] 複製
  - [ ] 参照Dataset一覧取得

#### 7. Dashboard Shares API
- [ ] 共有追加/更新/削除
- [ ] 権限チェック（Owner/Editor/Viewer）

#### 8. FilterViews API
- [ ] `backend/app/models/filter_view.py` - FilterViewモデル定義
- [ ] `backend/app/services/filter_view_service.py` - FilterViewサービス
- [ ] `backend/app/api/routes/filter_views.py` - FilterViewルート

### 優先度: 中（Python実行基盤）

#### 9. Executor実装
- [ ] `executor/app/sandbox.py` - サンドボックス実装
  - [ ] リソース制限（CPU/メモリ/タイムアウト）
  - [ ] importフック（ホワイトリストチェック）
- [ ] `executor/app/runner.py` - 実行エンジン
  - [ ] Card実行（render関数呼び出し）
  - [ ] Transform実行（transform関数呼び出し）
- [ ] 実行キュー管理
  - [ ] 同時実行数制限
  - [ ] バックプレッシャ（503返却）

### 優先度: 中（フロントエンド）

#### 10. 認証UI
- [ ] `frontend/src/pages/LoginPage.tsx` - ログイン画面
- [ ] 認証状態管理の完成
- [ ] 保護ルート実装

#### 11. 共通レイアウト
- [ ] `frontend/src/components/common/Layout.tsx`
- [ ] `frontend/src/components/common/Header.tsx`
- [ ] `frontend/src/components/common/Sidebar.tsx`
- [ ] React Router設定

#### 12. Dashboard機能
- [ ] `frontend/src/pages/DashboardListPage.tsx` - 一覧画面
- [ ] `frontend/src/pages/DashboardViewPage.tsx` - 閲覧画面
- [ ] `frontend/src/pages/DashboardEditPage.tsx` - 編集画面
- [ ] `frontend/src/components/dashboard/DashboardViewer.tsx`
- [ ] `frontend/src/components/dashboard/DashboardEditor.tsx`
- [ ] `frontend/src/components/dashboard/FilterBar.tsx`
- [ ] `frontend/src/components/dashboard/CardContainer.tsx`（iframe表示）

#### 13. Dataset管理
- [ ] `frontend/src/pages/DatasetListPage.tsx`
- [ ] `frontend/src/components/dataset/DatasetList.tsx`
- [ ] `frontend/src/components/dataset/DatasetImport.tsx`
- [ ] `frontend/src/components/dataset/DatasetPreview.tsx`

#### 14. Transform管理
- [ ] `frontend/src/pages/TransformListPage.tsx`
- [ ] `frontend/src/components/transform/TransformList.tsx`
- [ ] `frontend/src/components/transform/TransformEditor.tsx`（Monaco Editor）

#### 15. Card管理
- [ ] `frontend/src/pages/CardListPage.tsx`
- [ ] `frontend/src/components/card/CardList.tsx`
- [ ] `frontend/src/components/card/CardEditor.tsx`（Monaco Editor）
- [ ] `frontend/src/components/card/CardPreview.tsx`

### 優先度: 低（統合機能）

#### 16. Chatbot API
- [ ] `backend/app/services/chatbot_service.py` - Vertex AI連携
- [ ] Datasetサマリ生成
- [ ] レート制限

#### 17. Chatbot UI
- [ ] `frontend/src/components/chatbot/ChatbotPanel.tsx`
- [ ] 会話履歴表示

#### 18. 監査ログ
- [ ] AuditLogsテーブル操作
- [ ] ログ記録サービス
- [ ] 検索API

#### 19. カード実行キャッシュ
- [ ] フィルタ値をキーにHTMLキャッシュ
- [ ] TTL: 1時間

#### 20. E2Eテスト
- [ ] Playwrightセットアップ
- [ ] クリティカルパス（ログイン→Dashboard閲覧→フィルタ変更）

---

## 推奨実装順序

1. **認証API完全実装** → ログインできないと他の機能テストが困難
2. **Datasets API** → データがないとCard/Transformが動作しない
3. **Cards API** → Dashboardの核となる機能
4. **Dashboards API** → ユーザ向けの主要機能
5. **Executor実装** → Card/Transform実行に必要
6. **フロントエンド認証UI** → バックエンドと連携テスト
7. **フロントエンドDashboard機能** → ユーザ向け画面
8. **残りの機能**

---

## 技術的負債・改善点

- [ ] DynamoDB操作をaioboto3のコンテキストマネージャで適切に管理
- [ ] GSI（グローバルセカンダリインデックス）を使用したクエリ最適化
- [ ] 認証のリフレッシュトークン対応
- [ ] OpenAPI仕様の自動生成と検証
- [ ] テストカバレッジ80%達成
