<!--
CO_OP_TRANSLATOR_METADATA:
{
  "original_hash": "c4be907703b836d1a1c360db20da4de9",
  "translation_date": "2025-06-11T04:49:56+00:00",
  "source_file": "11-mcp/code_samples/github-mcp/MCP_SETUP.md",
  "language_code": "ja"
}
-->
# MCPサーバー統合ガイド

## 前提条件
- Node.js 18 以上（推奨）
- npm または pnpm
- Python 3.10+ 仮想環境と `requirements.txt` の依存インストール済み
- 有効な GitHub Personal Access Token（公開リポ参照のみなら read 権限で可）
- Azure OpenAI (Chat) の Deployment（例: gpt-4o-mini）と API キー

## セットアップ手順

本サンプルは `app.py` 内で `npx @modelcontextprotocol/server-github` を自動起動します。手動で起動するのは事前検証したい場合のみ任意です。

1. **依存インストール (Python)**
   ```bash
   pip install -r requirements.txt
   ```
2. **(任意) MCP サーバーを手動テスト起動**
   ```bash
   npx @modelcontextprotocol/server-github
   ```
   正常なら起動ログが表示されます。自動起動に任せる場合この手順は不要です。
3. **Chainlit / サンプル起動**
   ```bash
   chainlit run translations/ja/11-mcp/code_samples/github-mcp/app.py -w
   ```
4. **接続の確認 (自動起動シナリオ)**
   - ログに「GitHub MCP サーバー接続確立」「GitHub プラグイン初期化成功」
   - 以降は起動したブラウザのチャットで GitHub 関連指示が利用可能

## トラブルシューティング

### 401 (Azure OpenAI 認証失敗) 詳細
発生条件: エンドポイント/キー不一致, Deployment 名誤り, API バージョン未対応, OS 環境変数との競合。

確認順序:
1. 初期化ログの `endpoint_host` が期待する `<your-resource>.openai.azure.com` になっているか
2. Deployment 名がポータルの “Deployment name” と一致
3. API バージョンを一時的に安定版 (`2024-08-01-preview` など) に変更して再試行
4. キーを再生成し `.env` を更新（漏えい懸念時は直ちにローテーション）
5. `.env` の再読込は `load_dotenv(override=True)` で行われ、OS 既存値を上書きする設計

### よくある問題

1. **ポート競合 (EADDRINUSE)**  別プロセスが使用中。`--port` で変更可能。
2. **GitHub 認証失敗**  PAT の権限不足 / 期限切れ。新しい Token を発行し `.env` 更新。
3. **MCP 接続無し**  起動ログに “接続確立” が無ければ npx 失敗（Node 未インストール / ネットワーク遮断）を確認。
4. **検索結果が常に空**  Azure Search キー/エンドポイント不一致かインデックス未作成。

## MCP 接続確認

正常接続の指標:
1. ログ: 「GitHub MCP サーバー接続確立」→「GitHub プラグイン初期化成功」
2. チャットでリポジトリ参照要求がエラー無く応答

## 環境変数

重要: `.env` は Git 管理対象外にし、漏えい時は速やかにローテーションしてください。Azure OpenAI と Foundry の変数が混在しますが、本サンプルは Azure OpenAI の値のみ使用します。

必須例:
```
GITHUB_TOKEN=your_github_token
AZURE_OPENAI_ENDPOINT=...openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_SEARCH_SERVICE_ENDPOINT=...
AZURE_SEARCH_API_KEY=...
```

## 接続テスト / 利用例

最初の動作確認メッセージ:
```
Show me the repositories for username: <GitHub Username>
```

追加例 (英語/日本語):
```
List repositories for user <GitHub Username>
Analyze the language breakdown for user <GitHub Username>
<GitHub ユーザー名> の主要なプログラミング言語を分析してください
<GitHub ユーザー名> の公開リポジトリからAIエージェント向けの提案を作って
```

期待される応答: リポジトリ一覧 / 言語集計 / 推奨案（マルチエージェントの場合は段階的ストリーム）。

### Search / RAG 連携
起動時に `event-descriptions.md` が Azure Search インデックスへ投入され、イベント関連質問では回答内に `Event:` や `Live Event:` 行が混在します。表示されない場合はインデックス作成や API キーを再確認してください。

### Foundry 変数について
`.env` に `PROJECT_ENDPOINT` など Foundry 用変数がありますが、このサンプルでは未使用です。将来的に Agent Service 統合を行う拡張余地として残しています。

**免責事項**:  
本書類はAI翻訳サービス「[Co-op Translator](https://github.com/Azure/co-op-translator)」を使用して翻訳されました。正確性を期していますが、自動翻訳には誤りや不正確な箇所が含まれる可能性があることをご了承ください。原文の言語によるオリジナル文書が正式な情報源とみなされます。重要な情報については、専門の人間による翻訳を推奨します。本翻訳の使用により生じた誤解や誤訳について、一切の責任を負いかねます。