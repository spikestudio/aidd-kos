# シークレット管理方針

## ローカル開発

1. `.env.example` をコピーして `.env` を作成する

   ```bash
   cp .env.example .env
   ```

2. `.env` に実際の値を設定する
   - `OPENAI_API_KEY`: [OpenAI API キー](https://platform.openai.com/api-keys) から取得
   - `LIGHTRAG_API_KEY`: LightRAG サーバーを外部公開する場合のみ設定（ローカル開発は空欄可）
   - その他の変数は `.env.example` のコメントを参照

## CI/CD

- シークレットは GitHub Actions の **Repository Secrets**（Settings → Secrets and variables → Actions）で管理する
- 環境変数名は `.env.example` の定義に従う
- 現在 CI で必要なシークレット: `OPENAI_API_KEY`（テストが LightRAG を呼び出す場合）

## 禁止事項

- シークレット値をコードやコミットメッセージに含めない
- `.env` ファイルをコミットしない（`.gitignore` で除外済み）
- API キーをログに出力しない（NFR §セキュリティ参照）
- LightRAG API を外部公開する場合は TLS を必須とし、`LIGHTRAG_API_KEY` を設定する
