# memory-palace

記憶宮殿（場所法）をデジタルに再現する間隔反復学習ツール。3D空間にアイテムを配置し、忘却曲線で最適復習タイミングを計算。

## 技術スタック
- Python/FastAPI: API + SM-2スケジューリング
- TypeScript/React + Three.js: 3Dルームエディタ
- PostgreSQL / GCP Cloud Run

## ルール
- TypeScript: `~/.claude/rules/typescript.md`
- Python: Ruff でフォーマット・リント

## コマンド
```
make check     # lint → test → build
make quality   # 品質ゲート
```

## 構造
```
backend/src/memory_palace/ api/ models/ schemas/ services/
frontend/src/ components/ hooks/ lib/ types/
```

## 環境変数
`.env.example` を参照
