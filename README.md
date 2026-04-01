# Memory Palace

記憶宮殿（場所法）をデジタルに再現し、3D空間内の「場所」に記憶対象を配置する間隔反復学習ツール。

## 特徴

- **3D 記憶宮殿**: Three.js による 3D 空間でルームを作成し、記憶アイテムを配置
- **個人適応型間隔反復**: SM-2 アルゴリズムベースの忘却曲線モデルで最適な復習タイミングを計算
- **学習分析**: 復習セッションの正答率トラッキングと忘却曲線の可視化

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | TypeScript / React + Three.js |
| バックエンド | Python / FastAPI |
| データベース | PostgreSQL |
| インフラ | GCP Cloud Run |

## セットアップ

### 前提条件

- Node.js >= 22.0.0
- Python >= 3.12
- PostgreSQL

### インストール

```bash
# リポジトリをクローン
git clone git@github.com:akaitigo/memory-palace.git
cd memory-palace

# フロントエンド
cd frontend
npm install

# バックエンド
cd ../backend
pip install -e ".[dev]"
```

### 環境変数

`.env.example` を `.env` にコピーして値を設定:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/memory_palace
CORS_ORIGINS=http://localhost:5173
```

### 開発サーバー起動

```bash
# フロントエンド（別ターミナル）
cd frontend && npm run dev

# バックエンド（別ターミナル）
cd backend && uvicorn memory_palace.main:app --reload
```

### テスト & リント

```bash
make check    # 全チェック（フォーマット + リント + 型チェック + テスト + ビルド）
make quality  # 品質ゲート
```

## アーキテクチャ

```
frontend/  — TypeScript + React + Three.js (3Dルームエディタ)
backend/   — Python + FastAPI (REST API + SM-2 スケジューリング)
           └── PostgreSQL (ユーザー・ルーム・記憶アイテム・復習履歴)
```

- フロントエンドは Three.js で3D記憶宮殿を描画し、ルーム内にアイテムを配置
- バックエンドは SM-2 アルゴリズムで個人適応型の復習スケジュールを計算
- 復習セッションの結果をもとに忘却曲線パラメータを自動調整

## 注意事項

> **MVP版では認証なし** — 全エンドポイントが認証不要でアクセスできます。
>
> **本番利用前に必要な対応:**
> - ユーザー認証の実装（JWT / OAuth）
> - HTTPS の設定
> - CSP ヘッダーの設定
> - レート制限の実装
> - データベースのバックアップ戦略

## ライセンス

[MIT](LICENSE)
