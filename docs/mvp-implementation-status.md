# MVP実装状況マッピング

## 概要

MVP要件定義書（`docs/requirements.md`）に基づき、各機能の実装状況をマッピングしたドキュメント。

**最終更新**: 2026-02-04

---

## MVP要件一覧

### FR-1: Dataset取り込み

#### FR-1.1 Local CSV Import
- **要件**: UIでファイル選択/ドラッグ&ドロップ、プレビュー表示、取り込み設定、Dataset保存
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/datasets` (`backend/app/api/routes/datasets.py`)
  - Service: `dataset_service.create_dataset_from_upload()` (`backend/app/services/dataset_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `DatasetImport.tsx` (`frontend/src/components/dataset/DatasetImport.tsx`)
  - Page: `DatasetListPage.tsx` (`frontend/src/pages/DatasetListPage.tsx`)
- **状態**: ✅ MVP要件達成

#### FR-1.2 S3 CSV Import
- **要件**: 接続設定、バケット/プレフィックス/ファイル選択、手動実行で取り込み
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/datasets/s3-import` (`backend/app/api/routes/datasets.py`)
  - Service: `dataset_service.create_dataset_from_s3()` (`backend/app/services/dataset_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `DatasetImport.tsx` にS3インポート機能含む
- **状態**: ✅ MVP要件達成

#### FR-1.3 Dataset再取り込み
- **要件**: 再取り込みボタン、成功/失敗結果、行数/列数/更新時刻/実行者、スキーマ変化検知と警告
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/datasets/{dataset_id}/import` (`backend/app/api/routes/datasets.py`)
  - Service: `dataset_service.reimport_dataset()` (`backend/app/services/dataset_service.py`)
- **フロントエンド**: ⚠️ 要確認（Dataset詳細画面の実装状況）
- **状態**: ⚠️ バックエンドは実装済み、フロントエンド要確認

---

### FR-2: Transform（PythonベースETL）

#### FR-2.1 Transform定義
- **要件**: Transform作成/編集画面、入力Dataset選択（複数可）、Pythonコード編集、規約エントリポイント
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/transforms`, `PUT /api/transforms/{transform_id}` (`backend/app/api/routes/transforms.py`)
  - Service: `transform_service.create_transform()`, `transform_service.update_transform()` (`backend/app/services/transform_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `TransformEditor.tsx` (`frontend/src/components/transform/TransformEditor.tsx`)
  - Page: `TransformListPage.tsx` (`frontend/src/pages/TransformListPage.tsx`)
- **状態**: ✅ MVP要件達成

#### FR-2.2 Transform実行
- **要件**: 手動実行（UI上の「実行」ボタン）、スケジュール実行（cron形式）、実行履歴表示
- **バックエンド**: ❌ **未実装（ブロッカー）**
  - Route: `POST /api/transforms/{transform_id}/execute` は存在するが、`NotImplementedError` を発生
  - Service: `transform_service.execute_transform()` (`backend/app/services/transform_service.py:307`)
  - **問題**: Executorサービス統合が未実装
- **フロントエンド**: ⚠️ 実行ボタンUIは存在するが、バックエンド未実装のため動作しない
- **状態**: ❌ **MVP要件未達成（UATブロッカー）**

#### FR-2.3 Transform実行制約
- **要件**: 外部ネットワーク遮断、CPU/メモリ/タイムアウト上限（5分）、ホワイトリストライブラリのみ許可
- **バックエンド**: ✅ Executorサービスで実装済み
  - Executor: `executor/app/sandbox.py`, `executor/app/resource_limiter.py`
  - タイムアウト: `executor/app/config.py` で設定可能（デフォルト300秒）
- **状態**: ✅ MVP要件達成（Executor実装済み）

---

### FR-3: Card（PythonベースHTMLカード）

#### FR-3.1 カード定義形式
- **要件**: Card作成/編集画面、Pythonコード編集、規約エントリポイント
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/cards`, `PUT /api/cards/{card_id}` (`backend/app/api/routes/cards.py`)
  - Service: `card_service.create_card()`, `card_service.update_card()` (`backend/app/services/card_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `CardEditor.tsx` (`frontend/src/components/card/CardEditor.tsx`)
  - Page: `CardListPage.tsx` (`frontend/src/pages/CardListPage.tsx`)
- **状態**: ✅ MVP要件達成

#### FR-3.2 フィルタ適用
- **要件**: プラットフォーム側でフィルタ適用、フィルタ適用済みデータをカードへ渡す
- **バックエンド**: ⚠️ プレビュー実行が未実装のため、フィルタ適用ロジックは未検証
  - Executor: `executor/app/runner.py:190` に `apply_filters()` 関数が実装済み
- **フロントエンド**: ✅ 実装済み
  - Component: `FilterBar.tsx` (`frontend/src/components/dashboard/FilterBar.tsx`)
  - Component: `CardContainer.tsx` (`frontend/src/components/card/CardContainer.tsx`)
- **状態**: ⚠️ Executor統合後に検証必要

#### FR-3.3 HTMLの安全な表示
- **要件**: iframe分離を原則、CSP適用、Plotly等の社内ホスト済み静的ライブラリのみ許可
- **フロントエンド**: ✅ 実装済み
  - Component: `CardContainer.tsx` でiframe分離実装
  - CSP設定は要確認（フロントエンド設定ファイル）
- **状態**: ✅ MVP要件達成（CSP設定要確認）

#### FR-3.4 カード実行制約
- **要件**: 外部ネットワーク遮断、CPU/メモリ/タイムアウト上限（10秒）、ホワイトリストライブラリのみ許可、実行ログ
- **バックエンド**: ❌ **未実装（ブロッカー）**
  - Route: `POST /api/cards/{card_id}/preview` は存在するが、`NotImplementedError` を発生
  - Service: `card_service.preview_card()` (`backend/app/services/card_service.py:323`)
  - **問題**: Executorサービス統合が未実装
- **Executor**: ✅ 実装済み（`executor/app/runner.py:29`）
- **フロントエンド**: ⚠️ プレビューUIは存在するが、バックエンド未実装のため動作しない
- **状態**: ❌ **MVP要件未達成（UATブロッカー）**

---

### FR-4: Dashboard（作成・配置・閲覧）

#### FR-4.1 Dashboard作成/編集
- **要件**: Dashboard作成、複製、削除、レイアウト編集（カード追加/削除、移動/リサイズ）、カード数上限20
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/dashboards`, `PUT /api/dashboards/{dashboard_id}`, `DELETE /api/dashboards/{dashboard_id}`, `POST /api/dashboards/{dashboard_id}/clone` (`backend/app/api/routes/dashboards.py`)
  - Service: `dashboard_service.create_dashboard()`, `dashboard_service.update_dashboard()` (`backend/app/services/dashboard_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `DashboardEditor.tsx` (`frontend/src/components/dashboard/DashboardEditor.tsx`)
  - Page: `DashboardEditPage.tsx` (`frontend/src/pages/DashboardEditPage.tsx`)
- **状態**: ✅ MVP要件達成

#### FR-4.2 Dashboard閲覧モード
- **要件**: カードのロード状態/エラー状態が視認できる、複数カード配置
- **バックエンド**: ✅ 実装済み（Dashboard取得API）
- **フロントエンド**: ✅ 実装済み
  - Component: `DashboardViewer.tsx` (`frontend/src/components/dashboard/DashboardViewer.tsx`)
  - Page: `DashboardViewPage.tsx` (`frontend/src/pages/DashboardViewPage.tsx`)
- **状態**: ✅ MVP要件達成（カード実行未実装のため、実際のロード状態は未検証）

---

### FR-5: ページフィルタ（カテゴリ、日付）

#### FR-5.1 フィルタ種別
- **要件**: カテゴリフィルタ（1選択/複数選択）、日付フィルタ（期間、カレンダーUI）
- **バックエンド**: ✅ 実装済み（フィルタ適用ロジックはExecutorに実装）
- **フロントエンド**: ✅ 実装済み
  - Component: `FilterBar.tsx` (`frontend/src/components/dashboard/FilterBar.tsx`)
- **状態**: ✅ MVP要件達成

#### FR-5.2 フィルタ適用ルール
- **要件**: Dashboardに設定されたページフィルタは対象カードへ一括適用、カード側は対応フィルタ項目を宣言可能
- **バックエンド**: ✅ 実装済み（Executor: `executor/app/runner.py:190`）
- **フロントエンド**: ✅ 実装済み（FilterBar → CardContainer）
- **状態**: ✅ MVP要件達成（Executor統合後に検証必要）

#### FR-5.3 フィルタUI
- **要件**: フィルタバー表示/非表示、フィルタ適用中の表示（カード上のアイコン等）
- **フロントエンド**: ✅ 実装済み
  - Component: `FilterBar.tsx`
- **状態**: ✅ MVP要件達成

---

### FR-6: FilterView（フィルタ状態の保存）

#### FR-6.1 FilterView操作
- **要件**: 現在のフィルタ状態を「名前付きビュー」として保存、保存済みビューの適用、ビューの更新/削除
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/dashboards/{dashboard_id}/filter-views`, `GET /api/dashboards/{dashboard_id}/filter-views`, `PUT /api/dashboards/{dashboard_id}/filter-views/{filter_view_id}`, `DELETE /api/dashboards/{dashboard_id}/filter-views/{filter_view_id}` (`backend/app/api/routes/filter_views.py`)
  - Service: `filter_view_service.create_filter_view()`, `filter_view_service.list_filter_views()` (`backend/app/services/filter_view_service.py`)
- **フロントエンド**: ❌ **未実装（ブロッカー）**
  - FilterView管理UIが見つからない
  - FilterBarに保存/適用機能がない
- **状態**: ❌ **MVP要件未達成（UATブロッカー）**

#### FR-6.2 FilterView共有
- **要件**: 個人用ビュー、Dashboard共有範囲内での共有ビュー、デフォルトビュー設定
- **バックエンド**: ✅ 実装済み（FilterViewモデルに `is_shared`, `is_default` フィールド）
- **フロントエンド**: ❌ **未実装（ブロッカー）**
  - FilterView管理UI自体が未実装のため、共有機能も未実装
- **状態**: ❌ **MVP要件未達成（UATブロッカー）**

---

### FR-7: 共有/権限（Dashboardのみ）

#### FR-7.1 Dashboard共有
- **要件**: Dashboardをユーザまたはグループへ共有、権限種別（Viewer/Editor/Owner）、共有ダイアログにDataset一覧表示
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/dashboards/{dashboard_id}/shares`, `GET /api/dashboards/{dashboard_id}/shares`, `PUT /api/dashboards/{dashboard_id}/shares/{share_id}`, `DELETE /api/dashboards/{dashboard_id}/shares/{share_id}` (`backend/app/api/routes/dashboard_shares.py`)
  - Service: `dashboard_share_service.create_share()`, `dashboard_share_service.list_shares()` (`backend/app/services/dashboard_share_service.py`)
  - Route: `GET /api/dashboards/{dashboard_id}/referenced-datasets` でDataset一覧取得可能
- **フロントエンド**: ❌ **未実装（ブロッカー）**
  - Dashboard共有管理UIが見つからない
  - DashboardEditor/DashboardViewerに共有ボタン/ダイアログがない
- **状態**: ❌ **MVP要件未達成（UATブロッカー）**

#### FR-7.2 権限チェック
- **要件**: Dashboard閲覧時に権限チェック、Dashboard編集時にEditor/Owner権限チェック、Dashboard共有時にOwner権限チェック
- **バックエンド**: ⚠️ **部分実装**
  - Service: `dashboard_share_service.check_dashboard_permission()` (`backend/app/services/dashboard_share_service.py:153`)
  - **問題**: Groupメンバーシップチェックが未実装（TODOコメント: `backend/app/services/dashboard_share_service.py:168`）
- **フロントエンド**: ✅ 実装済み（権限チェックは読み取り専用、編集/共有UIは未実装）
- **状態**: ⚠️ **Group共有時の権限チェックが不完全（UATブロッカー）**

---

### FR-8: Chatbot（データ質問）

#### FR-8.1 Chatbot機能
- **要件**: Dashboard画面にチャットパネル追加、Dashboardが参照するDatasetについてAIに質問、LLM: Vertex AI（Gemini）、質問＋Datasetサマリをプロンプトに含めてLLMへ送信
- **バックエンド**: ✅ 実装済み
  - Route: `POST /api/dashboards/{dashboard_id}/chat` (`backend/app/api/routes/chatbot.py`)
  - Service: `chatbot_service.chat_with_dashboard()` (`backend/app/services/chatbot_service.py`)
- **フロントエンド**: ✅ 実装済み
  - Component: `ChatbotPanel.tsx` (`frontend/src/components/chatbot/ChatbotPanel.tsx`)
  - Integration: DashboardViewerに統合済み
- **状態**: ✅ MVP要件達成

#### FR-8.2 Datasetサマリ生成
- **要件**: 大規模Datasetは全行送信不可、サマリ化またはサンプリングで対応
- **バックエンド**: ✅ 実装済み（`chatbot_service.py` でサマリ生成）
- **状態**: ✅ MVP要件達成

---

## 非機能要件

### NFR-1: 性能（暫定SLO）
- **要件**: Dashboard初回表示 p95 5秒以内、フィルタ変更後の再描画 p95 2.5秒以内、カード単体実行タイムアウト 10秒、Transform実行タイムアウト 5分
- **実装状況**: ⚠️ カード/Transform実行が未実装のため、性能検証不可
- **状態**: ⚠️ 実装後に検証必要

### NFR-2: 可用性
- **要件**: Python実行基盤のワーカーは水平スケール可能、実行キュー（同時実行数制限、バックプレッシャ）
- **実装状況**: ✅ Executorサービスで実装済み（`executor/app/queue.py`）
- **状態**: ✅ MVP要件達成

### NFR-3: セキュリティ
- **要件**: Python実行: ネットワーク遮断、権限分離、リソース制限、HTML表示: iframe分離＋CSP＋サニタイズ、監査ログ
- **実装状況**: ✅ Executorサービスで実装済み（`executor/app/sandbox.py`, `executor/app/resource_limiter.py`）
- **監査ログ**: ✅ 実装済み（`backend/app/api/routes/audit_logs.py`）
- **状態**: ✅ MVP要件達成

### NFR-4: 監査ログ
- **要件**: Dashboard共有変更、Dataset取り込み/Transform実行、カード実行失敗を記録
- **実装状況**: ✅ 実装済み（`backend/app/services/audit_log_service.py`）
- **状態**: ✅ MVP要件達成

---

## ブロッカー一覧（UAT開始前に解決必須）

### 1. Card Preview実行統合 ❌
- **場所**: `backend/app/services/card_service.py:323`
- **問題**: `NotImplementedError` を発生、Executorサービス統合が未実装
- **影響**: Cardプレビューが動作しない、Dashboard上でカードが表示されない

### 2. Transform実行統合 ❌
- **場所**: `backend/app/services/transform_service.py:307`
- **問題**: `NotImplementedError` を発生、Executorサービス統合が未実装
- **影響**: Transformが実行できない、ETL処理が動作しない

### 3. FilterView管理UI ❌
- **場所**: `frontend/src/components/dashboard/FilterBar.tsx` に機能なし
- **問題**: FilterView保存/適用/削除UIが未実装
- **影響**: フィルタ状態の保存・再利用ができない

### 4. Dashboard共有管理UI ❌
- **場所**: DashboardEditor/DashboardViewerにUIなし
- **問題**: Dashboard共有ダイアログ/管理画面が未実装
- **影響**: Dashboard共有機能が使えない

### 5. Groupメンバーシップチェック ⚠️
- **場所**: `backend/app/services/dashboard_share_service.py:168`
- **問題**: Group共有時のメンバーシップチェックが未実装（TODOコメント）
- **影響**: Group共有時の権限チェックが不完全

---

## 実装済み機能サマリ

### ✅ 完全実装済み
- Dataset取り込み（Local CSV / S3 CSV）
- Transform定義（作成/編集）
- Card定義（作成/編集）
- Dashboard作成/編集/閲覧
- ページフィルタ（カテゴリ/日付）
- Chatbot（データ質問）
- 認証（JWT）
- 監査ログ

### ⚠️ 部分実装
- Transform実行（定義は実装済み、実行統合が未実装）
- Card実行（定義は実装済み、プレビュー統合が未実装）
- 権限チェック（User共有は実装済み、Group共有時のチェックが未実装）

### ❌ 未実装
- FilterView管理UI
- Dashboard共有管理UI

---

## 次のステップ

1. **Executor統合**: Card preview + Transform実行のバックエンド統合
2. **Group権限チェック**: Groupメンバーシップチェックの実装
3. **FilterView UI**: FilterView保存/適用/削除UIの実装
4. **共有UI**: Dashboard共有ダイアログ/管理画面の実装
5. **UATチェックリスト作成**: MVP要件に基づくUATシナリオ定義
