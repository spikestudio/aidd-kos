# ADR-001: aidd-kos エラーコード体系の統一設計

| 項目 | 内容 |
|------|------|
| ステータス | 承認済み |
| 日付 | 2026-06-03 |
| 決定者 | sanojimaru |

## コンテキスト

Epic #2（MCP Aggregator）では `LIGHTRAG_UNAVAILABLE` が MCP ツールのエラーコードとして定義済み。
Epic #4（CLI & Install）では `MISE_NOT_FOUND`・`OPENAI_API_KEY_MISSING` 等が必要だが
コード体系が未定義のまま実装に入ろうとしていた。

将来 Epic が増えるたびに命名が揺れると、エラーコードを解析するスクリプト・ドキュメント・
AI Agent の動作が壊れる。後から変更すると全 docs/spec/ の修正と実装の変更が必要になるため、
今の段階で体系を確定する。

## 決定事項

**シンプル形式を採用する。命名規則: `{COMPONENT}_{ERROR_TYPE}`（大文字スネークケース）**

| コンポーネント | エラーコード例 |
|------------|-------------|
| `LIGHTRAG` | `LIGHTRAG_UNAVAILABLE` |
| `CODEGRAPH` | `CODEGRAPH_UNAVAILABLE` |
| `MISE` | `MISE_NOT_FOUND` |
| `OPENAI` | `OPENAI_API_KEY_MISSING` |
| `PORT` | `PORT_IN_USE` |

## 根拠

Epic #2 が `LIGHTRAG_UNAVAILABLE` を既に確定しており、プレフィックス形式に変更すると
全 docs/spec/ の修正と AI Agent への説明変更が必要になる。

aidd-kos はローカル実行ツールであり、エラーコードを外部 API として公開しない。
プレフィックスによる名前空間は過剰設計になる。
シンプル形式で十分な識別性があり、移行コストもゼロ。

## 代替案

### 代替案 A: シンプル形式 `{COMPONENT}_{ERROR_TYPE}`（**採用**）

- メリット: 短く読みやすい。Epic #2 で既採用のため変更不要。
- デメリット: 名前空間なし。将来他ツールのエラーコードと衝突する可能性（ローカルツールのため現実的リスクは低い）。

### 代替案 B: プレフィックス形式 `AIDD_KOS_{COMPONENT}_{ERROR_TYPE}`

- メリット: 名前空間あり。外部ライブラリのエラーコードと衝突しない。
- デメリット: Epic #2 の既存コードを全修正必要。冗長で読みにくい。

### 代替案 C: 現状維持（体系なし）

- メリット: 即時実装可能。
- デメリット: Epic が増えるたびに命名が揺れる。後から統一できなくなる。

## 影響・トレードオフ

- **影響を受けるコンポーネント:** MCP ツール（Epic #2）・CLI コマンド（Epic #4）・全後続 Epic
- **影響を受ける Epic / Phase:** Core MVP 全 Epic（#2・#3・#4）
- **Charter §10 採用方針との関係:** 該当なし（エラーコード命名は業界標準なし）
- **マスタドキュメントの更新:** docs/spec/mcp-aggregator.md・docs/spec/install.md のエラーコード記述がこの ADR に準拠することを確認
- **トレードオフ:** 名前空間なしのため、将来 aidd-kos を他システムと統合する際に衝突の可能性あり。その時点で `AIDD_KOS_` プレフィックスへの移行を検討する。
