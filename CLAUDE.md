# Memory Palace

## 概要
記憶宮殿（場所法）をデジタルに再現し、3D空間内の「場所」に記憶対象を配置する間隔反復学習ツール。忘却曲線モデルを個人の記憶力に適応させ、最適な復習タイミングを計算する。

## 技術スタック
- **フロントエンド**: TypeScript / React + Three.js（3D レンダリング）
- **バックエンド**: Python / FastAPI（API 層 + ML/データ処理）
- **データベース**: PostgreSQL
- **インフラ**: GCP Cloud Run
- **ビルドツール**: Vite（フロントエンド）、Ruff（Python リンター）

## コーディングルール
- TypeScript/React → `~/.claude/rules/typescript.md` のルールに従うこと
  - `any` 型の使用禁止。`unknown` + 型ガードまたはジェネリクスを使う
  - `as` 型アサーションは最小限に。型推論またはジェネリクスで解決
- Python → Ruff でフォーマット・リント

## ビルド & テスト

### フロントエンド
```bash
cd frontend
npm install          # 依存インストール
npm run dev          # 開発サーバー起動
npm run build        # プロダクションビルド
npm run lint         # リント実行
npm run typecheck    # 型チェック
npm run test         # テスト実行
```

### バックエンド
```bash
cd backend
pip install -e ".[dev]"  # 依存インストール
pytest                    # テスト実行
ruff check .              # リント
ruff format .             # フォーマット
```

### 全体
```bash
make check    # フォーマット + リント + テスト + ビルド（全体）
make quality  # 品質ゲート（LICENSE、秘匿情報、TODO 等）
```

## ディレクトリ構造
```
memory-palace/
├── frontend/            # React + Three.js SPA
│   ├── src/
│   │   ├── components/  # React コンポーネント
│   │   ├── hooks/       # カスタムフック
│   │   ├── lib/         # ユーティリティ・Three.js ヘルパー
│   │   └── types/       # TypeScript 型定義
│   ├── public/          # 静的アセット
│   ├── package.json
│   └── tsconfig.json
├── backend/             # Python/FastAPI API サーバー
│   ├── src/memory_palace/
│   └── tests/
├── test/e2e/            # E2E テスト（Playwright）
├── PRD.md               # プロダクト要件定義
├── CLAUDE.md            # このファイル
└── Makefile             # 共通コマンドインターフェース
```

## 環境変数
```bash
DATABASE_URL=           # PostgreSQL 接続文字列
JWT_SECRET=             # JWT 署名用シークレット
CORS_ORIGINS=           # CORS 許可オリジン（カンマ区切り）
```
