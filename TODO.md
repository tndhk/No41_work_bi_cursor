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
- [x] 認証API完全実装（login, me）
- [x] Groups API（CRUD + メンバー管理）
- [x] Datasets API（CRUD + CSV取り込み + プレビュー + 再取り込み）
- [x] Cards API（CRUD + プレビュー実行）
- [x] Dashboards API（CRUD + 複製 + 参照Dataset）
- [x] Dashboard Shares API（権限管理）
- [x] FilterViews API（CRUD）
- [x] Transforms API（CRUD + 手動実行 + スケジュール設定 + 実行履歴取得）
- [x] Executor基本実装（sandbox, runner）
- [x] Executor完成（リソース制限、importフック、実行キュー/バックプレッシャ）
- [x] フロントエンド認証UI（LoginPage）
- [x] フロントエンド共通レイアウト（Layout, Header, Sidebar）
- [x] フロントエンドDashboard一覧・閲覧画面
- [x] フロントエンドDashboard編集画面（レイアウト編集・自動保存）
- [x] React Router + 保護ルート
- [x] テストスイート安定化（84テストパス）
- [x] Dataset管理UI（一覧・詳細・取り込み・プレビュー）
- [x] Transform管理UI（一覧・編集・Monaco Editor統合）
- [x] Card管理UI（一覧・編集・Monaco Editor統合・プレビュー）

---

## 次にやるべきこと

### 優先度: 高

#### 1. Transforms API
- [x] `backend/app/models/transform.py` - Transformモデル定義
- [x] `backend/app/services/transform_service.py` - Transformサービス
- [x] `backend/app/api/routes/transforms.py` - Transformルート
  - [x] CRUD操作
  - [x] 手動実行（NotImplementedError - Phase 6で実装予定）
  - [x] スケジュール設定
  - [x] 実行履歴取得

#### 2. Executor完成
- [x] リソース制限（CPU/メモリ/タイムアウト）の厳格化
- [x] importフック（ホワイトリストチェック）
- [x] 実行キュー管理
  - [x] 同時実行数制限
  - [x] バックプレッシャ（503返却）

### 優先度: 中

#### 3. フロントエンドDashboard編集
- [x] `frontend/src/pages/DashboardEditPage.tsx` - 編集画面
- [x] `frontend/src/components/dashboard/DashboardEditor.tsx`
- [x] `frontend/src/components/dashboard/DashboardViewer.tsx`

#### 4. Dataset管理UI
- [x] `frontend/src/pages/DatasetListPage.tsx`
- [x] `frontend/src/pages/DatasetDetailPage.tsx`
- [x] `frontend/src/components/dataset/DatasetList.tsx`
- [x] `frontend/src/components/dataset/DatasetImport.tsx`
- [x] `frontend/src/components/dataset/DatasetPreview.tsx`

#### 5. Transform管理UI
- [x] `frontend/src/pages/TransformListPage.tsx`
- [x] `frontend/src/components/transform/TransformList.tsx`
- [x] `frontend/src/components/transform/TransformEditor.tsx`（Monaco Editor統合済み）

#### 6. Card管理UI
- [x] `frontend/src/pages/CardListPage.tsx`
- [x] `frontend/src/components/card/CardList.tsx`
- [x] `frontend/src/components/card/CardEditor.tsx`（Monaco Editor統合済み）
- [x] `frontend/src/components/card/CardPreview.tsx`

### 優先度: 低（統合機能）

#### 7. Chatbot API
- [x] `backend/app/services/chatbot_service.py` - Vertex AI連携
- [x] Datasetサマリ生成
- [x] レート制限

#### 8. Chatbot UI
- [x] `frontend/src/components/chatbot/ChatbotPanel.tsx`
- [x] 会話履歴表示

#### 9. 監査ログ
- [ ] AuditLogsテーブル操作
- [ ] ログ記録サービス
- [ ] 検索API

#### 10. カード実行キャッシュ
- [ ] フィルタ値をキーにHTMLキャッシュ
- [ ] TTL: 1時間

#### 11. E2Eテスト
- [x] Playwrightセットアップ
- [x] クリティカルパス（ログイン→Dashboard閲覧→フィルタ変更）

---

## 推奨実装順序

1. ~~**Transforms API**~~ → 完了
2. ~~**Executor完成**~~ → 完了
3. ~~**フロントエンドDashboard編集**~~ → 完了
4. ~~**Dataset/Card管理UI**~~ → 完了
5. **次のステップ**:
   - ~~Chatbot機能（新機能追加）~~ → 完了
   - 監査ログ機能（セキュリティ要件）
   - カード実行キャッシュ（性能改善）
   - 技術的負債の解消

---

## 技術的負債・改善点

- [x] DynamoDB操作をaioboto3のコンテキストマネージャで適切に管理
- [ ] GSI（グローバルセカンダリインデックス）を使用したクエリ最適化
- [ ] 認証のリフレッシュトークン対応
- [ ] OpenAPI仕様の自動生成と検証
- [ ] テストカバレッジ80%達成
- [ ] Pydantic v2の警告解消（.dict() → .model_dump()）
