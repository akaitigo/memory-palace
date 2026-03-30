# Memory Palace — アーキテクチャ概要

## 設計判断

### モノレポ構成
フロントエンド（TypeScript/React + Three.js）とバックエンド（Python/FastAPI）を1リポジトリで管理する。
理由: MVPフェーズでは開発速度を優先。サービス分離は将来必要に応じて実施。

### 3D レンダリング
Three.js を直接使用（React Three Fiber は導入しない）。
理由: 記憶宮殿の空間操作はカスタム性が高く、低レベル API への直接アクセスが必要。

### 間隔反復アルゴリズム
MVP では SM-2（SuperMemo 2）アルゴリズムをルールベースで実装。
ML モデルへの移行は十分なユーザーデータ蓄積後（Phase 2 以降）。

## 外部サービス連携
- **PostgreSQL**: ユーザー、ルーム、記憶アイテム、復習履歴の永続化
- **GCP Cloud Run**: コンテナデプロイ（将来）

## ADR
設計判断は `docs/adr/` に ADR として記録する。
