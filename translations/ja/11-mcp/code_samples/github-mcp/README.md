<!--
CO_OP_TRANSLATOR_METADATA:
{
  "original_hash": "9bf0395cbc541ce8db2a9699c8678dfc",
  "translation_date": "2025-06-11T04:50:54+00:00",
  "source_file": "11-mcp/code_samples/github-mcp/README.md",
  "language_code": "ja"
}
-->
# Github MCPサーバーの例

## 説明

これはMicrosoft Reactor主催のAI Agentsハッカソン向けに作成されたデモです。

このツールは、ユーザーのGithubリポジトリに基づいてハッカソンプロジェクトを推薦します。具体的には以下のように行います：

1. **Github Agent** - Github MCPサーバーを使ってリポジトリやその情報を取得します。
2. **Hackathon Agent** - Github Agentから得たデータをもとに、ユーザーのプロジェクトや使用言語、AI Agentsハッカソンのプロジェクトトラックに基づいた創造的なハッカソンプロジェクトのアイデアを考案します。
3. **Events Agent** - Hackathon Agentの提案をもとに、AI Agentハッカソンシリーズの関連イベントを推薦します。

## コードの実行

### 環境変数

このデモではAzure Open AI Service、Semantic Kernel、Github MCPサーバー、Azure AI Searchを使用しています。

これらのツールを利用するために、適切な環境変数が設定されていることを確認してください：

```python
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=""
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_API_VERSION=""
AZURE_SEARCH_SERVICE_ENDPOINT=""
AZURE_SEARCH_API_KEY=""
GITHUB_TOKEN=""  # または GITHUB_PERSONAL_ACCESS_TOKEN (どちらか一方、もしくは両方定義可)
GITHUB_PERSONAL_ACCESS_TOKEN=""  # 上と同じ値で冗長定義しても問題なし
``` 

## Chainlitサーバーの起動

MCPサーバーに接続するため、このデモではChainlitをチャットインターフェースとして使用しています。

サーバーを起動するには、ターミナルで以下のコマンドを実行してください：

```bash
chainlit run app.py -w
```

これで Chainlit サーバーが `http://localhost:8000` で起動し、同時に `event-descriptions.md` の内容が Azure AI Search インデックスに登録されます。

## MCPサーバーへの接続

Github MCPサーバーに接続するには、「Type your message here..」チャットボックスの下にある「プラグ」アイコンを選択してください：

![MCP Connect](../../../../../11-mcp/code_samples/github-mcp/images/mcp-chainlit-1.png)

次に、「Connect an MCP」をクリックしてGithub MCPサーバーへの接続コマンドを追加します：

```bash
npx -y @modelcontextprotocol/server-github --env GITHUB_PERSONAL_ACCESS_TOKEN=[YOUR PERSONAL ACCESS TOKEN]
```

"[YOUR PERSONAL ACCESS TOKEN]" は実際のパーソナルアクセストークンに置き換えてください。

接続が完了すると、プラグアイコンの横に(1)が表示されて接続が確認できます。表示されない場合は、`chainlit run app.py -w`でChainlitサーバーを再起動してみてください。
> **注意**: `chainlit run app.py -w`を実行しているターミナルで、Github のプラグインへの接続確立が表示されるケースもあります。ターミナルが出力している場合、UI上確認できなくても問題はありません。

## デモの使い方

ハッカソンプロジェクトの推薦ワークフローを開始するには、例えば以下のように入力します：

"ハッカソン向けのプロジェクト案を GitHubユーザー koreyspace の活動から提案してください"

Router Agentがリクエストを解析し、どのエージェント（Github、Hackathon、Events）の組み合わせが最適か判断します。エージェントは連携して、Githubリポジトリの分析、プロジェクトのアイデア出し、関連技術イベントの推薦を総合的に提供します。

## マルチエージェント・オーケストレーション戦略の補足

### 代表的パターン（MS Learn の5分類）

| パターン | 概要 (用途) | 強み | 留意点 |
|----------|-------------|------|--------|
| シーケンシャル・オーケストレーション | 固定順序でエージェントを直列実行します。 | 追跡とデバッグが容易でコスト管理もしやすいです。 | 動的な分岐や同時実行による高速化ができにくいです。 |
| コンカレント・オーケストレーション | 複数エージェントを並列に実行し結果を比較または統合します。 | 待ち時間短縮と多様性確保に役立ちます。 | 結果統合と重複コストが課題になります。 |
| グループ チャット オーケストレーション | 複数エージェントが共有コンテキストで発話を順番に追加します。 | 協調的に知識を積み上げやすいです。 | 発話の暴走や冗長化を抑制する制御が必要です。 |
| ハンドオフ オーケストレーション | 条件を満たした時点で次のエージェントに明示的に引き渡します。 | 責務境界が明確で中間成果物品質を保ちやすいです。 | 引き渡し条件設計が複雑になるおそれがあります。 |
| マジェンティック・オーケストレーション | 複数専門エージェントをタスク分解と再統合で調整します。 | 複雑な問題を多視点で解決しやすいです。 | 設計と観測が高度になりオーバーヘッドも増えます。 |

フレームワーク対応の概要: Semantic Kernel はシーケンシャルとグループ チャットを標準機能として備えており、他パターンも制御ロジックの追加で再現できます。AutoGen は並列とグループ型の対話を比較的容易に構築でき、ハンドオフや分解も拡張で対応できます。Magentic-One はタスク分解と再統合を核としており、マジェンティック指向の構成を第一級で扱います。

### 今回 Sequential を選ぶ理由
1. GitHub 解析 → アイデア生成 → アイデア語によるイベント検索という段階的依存が明確です。
2. エージェントが三つだけで並列化による待ち時間短縮効果が小さいです。
3. 上流が失敗または空なら下流を実行せずに済み、無駄なコストを避けられます。
4. まず直列(段階的依存)の構成で測定可能な実装を行い、原因の切り分けを容易にするため、適応的分岐やメタ制御は後回しにしています。(学習目的)
5. 学習用途として段階ごとの中間成果物を確認しやすく、失敗箇所を特定しやすい形を優先しています。

参考: Microsoft Learn - AI Agent Design Patterns  
https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns


**免責事項**：  
本書類はAI翻訳サービス[Co-op Translator](https://github.com/Azure/co-op-translator)を使用して翻訳されました。正確性を期しておりますが、自動翻訳には誤りや不正確な箇所が含まれる可能性があることをご承知おきください。原文はその言語における正式な情報源とみなされるべきです。重要な情報については、専門の人間による翻訳を推奨します。本翻訳の利用により生じたいかなる誤解や誤訳についても、当方は責任を負いかねます。