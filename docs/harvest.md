# Harvest: memory-palace

## 使えたもの
- [x] Makefile (make check / make quality)
- [x] lint設定 (ruff + oxlint + biome)
- [x] CI YAML
- [x] CLAUDE.md (27行、50行以下達成)
- [ ] ADR テンプレート (ADR未作成)
- [x] 品質チェックリスト (make quality)
- [x] E2Eテスト雛形 (test/e2e/smoke.spec.ts)
- [x] Hooks（PostToolUse ruff/oxlint）
- [x] lefthook
- [x] startup.sh

## 使えなかったもの（理由付き）
- ADR: 作成されなかった。idea-workスキルでADR作成を強制する仕組みがない

## テンプレート改善提案

| 対象ファイル | 変更内容 | 根拠 |
|-------------|---------|------|
| idea-work SKILL.md | model:opus Issue にADR作成を必須化 | 5PJ中ADR作成は2PJのみ |
| pyproject.toml テンプレート | TCH003除外を Pydantic プロジェクト向けに追加 | runtime型解決でテスト14件失敗 |
| biome.json テンプレート | v2スキーマに更新済み（v5.8で対応） | TS PJでスキーマ不一致 |

## メトリクス

| 項目 | 値 |
|------|-----|
| Issue (closed/total) | 5/5 |
| PR merged | 7 |
| テスト数 | 237 |
| CI失敗数 | 0 |
| ADR数 | 0 |
| テンプレート実装率 | 90% |
| CLAUDE.md行数 | 27 |

## 次のPJへの申し送り
- Pydantic v2 は TYPE_CHECKING ブロック内の型をランタイムで解決できない。Ruff TCH003 を schemas/ で除外する設定が必要
- Three.js プロジェクトでは @types/three のバージョンを固定すべき（Dependabot で major 更新が来ると壊れる可能性）
