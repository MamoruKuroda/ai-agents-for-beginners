<!--
CO_OP_TRANSLATOR_METADATA:
{
  "original_hash": "76945069b52a49cd0432ae3e0b0ba22e",
  "translation_date": "2025-06-17T08:35:56+00:00",
  "source_file": "00-course-setup/README.md",
  "language_code": "ja"
}
-->
## 目的
このドキュメントでは、コースのサンプルを実行できる状態にするために必要な環境変数の設定手順と、GitHub トークンや Azure 側の各種値の取得方法を順序立てて説明します。最初に GitHub トークンを用いた最小構成を準備し、そのあと Azure AI Foundry / Azure OpenAI / Azure Cognitive Search を利用する拡張設定へ進みます。

---
## GitHub モデル (GitHub Inference) 利用のためのセットアップ

### Step 1: GitHub にサインインしてトークンを作成します
1. GitHub にログインします。
2. 左側メニュー (またはプロフィールメニュー) から 「Fine-grained tokens」 を開きます。
3. 「Generate new token」 を選択します。
4. 次の項目を入力・選択します。
  - Name: 任意 (例: `ai-agents-course`)
  - Expiration: 30 日程度を推奨します。
  - Repository access / Scopes: Public Repositories（公開リポジトリのみで足りる場合）
  - 追加権限: Permissions → Models → GitHub Models へのアクセスを許可します。
5. 発行後、表示されたトークン文字列を必ずコピーします（後から再表示できないため安全な場所へ一時保存してください）。

![Generate Token](../../../00-course-setup/images/generate-token.png)

### Step 2: `.env` ファイルを作成してトークンを設定します
以下のコマンドでサンプルの雛形を複製します。

```bash
cp .env.example .env
```

エディタで `.env` を開き、`GITHUB_TOKEN=` の行にコピーしたトークンを貼り付けて保存してください。ここまでで GitHub モデルを用いる最小構成が整います。動作確認として後続レッスンの簡単なサンプルを実行できるはずです。

---
## Azure AI Foundry / Azure AI Agent Service 利用設定

### Step 1: Azure プロジェクトのエンドポイントを取得します
まだ Azure AI Foundry プロジェクトを作成していない場合は次の公式ドキュメントを参照してプロジェクトを作成してください。

- プロジェクトの概念と種類: [What is Azure AI Foundry? – Work in a project](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry#work-in-an-azure-ai-foundry-project)
- プロジェクト作成手順: [Create a project for Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects)
- エンドポイント確認を含むクイックスタート: [Quickstart: Get started with Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code#set-up-your-environment)

プロジェクトを作成したら Azure AI Foundry ポータルで対象プロジェクトを開き、**Overview** ページ右上付近に表示される Project endpoint（例: `https://<resource>.services.ai.azure.com/api/projects/<project>`）をコピーしてください。この値を後続の `PROJECT_ENDPOINT` に設定します。

> 注意: 「Hub」ベースの旧来プロジェクトでは同じ形式のエンドポイントが表示されません。もし表示されない場合は上記ドキュメントの「Types of projects」節を参照し、Foundry プロジェクトへ切り替えてください。

![Project Connection String](../../../00-course-setup/images/project-endpoint.png)

### Step 2: `.env` にプロジェクト関連の値を追加します
先ほど作成した `.env` を開き、以下のキーに値を記入してください。

| 変数 | 設定する内容 | 補足 |
|------|--------------|------|
| PROJECT_ENDPOINT | プロジェクトの services.ai.azure.com ベースのエンドポイント URL | 末尾の `/api/projects/<name>` を含む URL です。|
| AZURE_AI_PROJECT_NAME | プロジェクト名 | Overview 上部に表示されます。|
| MODEL_DEPLOYMENT_NAME | 利用したいモデルのデプロイ名 | 例: `gpt-4o-mini`。未指定時はサンプル内既定を用いる場合があります。|

### Step 3: Azure へサインインします
API キーを直接埋め込む代わりに、Microsoft Entra ID を用いたキーレス接続を推奨します。まず OS に合わせて [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) をインストールしてください。インストール後、以下を実行します。

```bash
az login --use-device-code
```

ブラウザで認証を完了したら、必要に応じて `az account set --subscription <SUBSCRIPTION_ID>` で利用するサブスクリプションを選択してください。以降、DefaultAzureCredential などを用いたコードから認証が自動的に行われます。

> 参考: キーレス認証の考え方は [Keyless authentication](https://learn.microsoft.com/azure/developer/ai/keyless-connections) を参照してください。

---
## 追加の環境変数 (Azure Search / Azure OpenAI を使うサンプル用)
Lesson 5 (Agentic RAG) など一部のサンプルでは Azure Cognitive Search や Azure OpenAI の追加設定が必要になります。必要になった段階で段階的に追加してください。以下は取得元ごとの整理です。

### (A) プロジェクト Overview ページで確認する値
- `AZURE_SUBSCRIPTION_ID` : Project details セクションを参照してください。
- `AZURE_AI_PROJECT_NAME` : ページ上部に表示されています (既に設定済みの場合は再入力不要です)。

### (B) Management Center / Project properties
- `AZURE_OPENAI_RESOURCE_GROUP` : Project properties で確認できます。

### (C) Models + Endpoints ページ
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` : Embedding モデル (例: `text-embedding-3-small`) の Deployment name。
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` : チャット用モデル (例: `gpt-4o-mini`) の Deployment name。

### (D) Azure ポータル (AI Services リソース)
- `AZURE_OPENAI_ENDPOINT` : Keys and Endpoint 画面で表示される Language APIs 用エンドポイント。
- `AZURE_OPENAI_API_KEY` : 同じ画面の KEY1 または KEY2。
- `AZURE_SEARCH_SERVICE_ENDPOINT` : Azure AI Search リソース Overview。
- `AZURE_SEARCH_API_KEY` : Search リソースの Keys 画面で Primary または Secondary 管理キー。

### (E) 公式 API バージョン情報ページ
- `AZURE_OPENAI_API_VERSION` : [API version lifecycle](https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation#latest-ga-api-release) の Latest GA API release を参照してください。

### (F) キーレス認証をコードで利用するサンプル
資格情報を直接ハードコーディングせず、`DefaultAzureCredential` などをインポートして利用します。例:

```python
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
```

---
## トラブルシューティング
セットアップでつまずいた場合は、以下を順に確認してください。
1. `.env` が作業ディレクトリ直下にあり、必要な値が空欄のままになっていないか確認してください。
2. `az login` 済みで正しいサブスクリプションが選択されているか確認してください。
3. モデル/デプロイ名のスペルが Azure ポータル上の表記と一致しているか確認してください。
4. Search のインデックス作成サンプルで 401/403 が出る場合は API キーとエンドポイントの組み合わせを再確認してください。
5. それでも解決しない場合は Issue 登録や学習用コミュニティ（Chat / Discussion）へ質問してください。

---
## 次のレッスンへ進みます
これでコースのコードサンプルを実行するための基本準備が完了しています。続いて AI エージェントの概要と代表的な活用例を学ぶレッスンへ進んでください。

[AI エージェントの紹介とエージェントのユースケース](../01-intro-to-ai-agents/README.md)

**免責事項**：  
本書類は AI 翻訳サービス「[Co-op Translator](https://github.com/Azure/co-op-translator)」を利用して生成した訳文を基に人手で校正しています。可能な限り正確さを保つよう努めていますが、自動翻訳特有の不正確さが残る場合があります。重要な判断に用いる際は原文と専門家による確認を行ってください。本翻訳利用に伴う不利益については責任を負いかねます。