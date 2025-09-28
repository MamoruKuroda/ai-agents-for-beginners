<!--
CO_OP_TRANSLATOR_METADATA:
{
  "original_hash": "e4e06d3b5d6207459a019c05fee5eb4b",
  "translation_date": "2025-08-22T00:00:00+00:00",
  "source_file": "07-planning-design/README.md",
  "language_code": "ja",
  "translator": "human-reviewed"
}
-->
[![プランニングデザインパターン](../../../07-planning-design/images/lesson-7-thumbnail.png)](https://youtu.be/kPfJ2BrBCMY?si=9pYpPXp0sSbK91Dr)

> （上の画像をクリックすると本レッスンの動画に移動します）

# プランニングデザイン（Planning Design）

## はじめに

このレッスンでは以下を扱います。

* 複雑なタスクを明確な全体ゴールに落とし込み、扱いやすいサブタスクへ分解する方法
* 構造化された出力（例: JSON）を活用し、機械可読性と信頼性を高める方法
* イベント駆動的なアプローチを用いて動的タスクや予期しない入力へ対応する方法

## 学習ゴール

完了後、次の点を理解できます。

* AIエージェントに明確で測定可能な全体ゴールを設定し、達成すべき対象を定義する
* 複雑なタスクを論理的な系列に並ぶサブタスクへ分解する
* 適切なツール（検索 / データ分析 など）を与え、いつ・どのように使うか、想定外事象のハンドリングを設計する
* サブタスク結果を評価し、パフォーマンスを測定しながら最終アウトプット改善へ反復する

## 全体ゴールの定義とタスク分解

![ゴールとタスクの定義](../../../07-planning-design/images/defining-goals-tasks.png)

現実世界の多くの課題は1ステップで完了できません。エージェントには行動指針となる簡潔で具体的な目的が必要です。例として次のゴールを考えます。

```
3日間の旅行行程を作成する
```

一見単純でも、「フライト候補」「宿泊案」「アクティビティ提案」など具体度を高める必要があります。ゴールを明確化するほど、エージェント（および人間の共同作業者）は正しい成果物へ集中できます。

### タスク分解（Task Decomposition）

大きく入り組んだタスクは、目的指向の小さなサブタスクに分けると扱いやすくなります。旅行行程の例では次のように分けられます。

* フライト手配（Flight Booking）
* ホテル手配（Hotel Booking）
* レンタカー手配（Car Rental）
* パーソナライゼーション（Personalization / アクティビティ提案 等）

サブタスクごとに専門エージェントや専用プロセスを割り当てられます。最終的には統合エージェント（オーケストレーター / 下流エージェント）が結果を集約し、一貫した旅程をユーザーへ返します。段階的な拡張も容易になり、たとえば「食事の推薦」「現地アクティビティ」専門エージェントを後から追加できます。

### 構造化出力（Structured Output）

LLMは構造化された出力（JSONなど）を生成でき、後続のエージェントやサービスがパースしやすくなります。マルチエージェント構成では、プラン結果を受けた後に各タスクを実行可能です。概要は次のブログが参考になります: <a href="https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/structured-output-agent.html" target="_blank">Structured Output Agent</a>

以下は単純なプランニングエージェントがゴールをサブタスクに分解し、構造化プランを生成する最小の Python スニペット例です（名前は英語ですがコメントで役割を示します）。

```python
from pydantic import BaseModel
from enum import Enum
from typing import List

# 利用可能な「専門エージェント」の種類を列挙
# それぞれが特定の責務（フライト検索 / 宿泊検索 など）を持つ前提
class AgentEnum(str, Enum):  # ★重要: 取りうるエージェント名を列挙 → 以降のバリデーション/ディスパッチの安定性確保
  FlightBooking = "flight_booking"          # フライトの検索・手配
  HotelBooking = "hotel_booking"            # ホテルの検索・予約
  CarRental = "car_rental"                  # レンタカー手配
  ActivitiesBooking = "activities_booking"  # アクティビティ/現地体験の検索・予約
  DestinationInfo = "destination_info"      # 目的地情報（気候/移動/注意点 等）の提供

# 1つのサブタスク（エージェントに渡す具体的指示）
class TravelSubTask(BaseModel):  # ★重要: サブタスクの原子単位（後でルーティング対象になる）
  task_details: str          # 例: "往復航空券を最安で検索"
  assigned_agent: AgentEnum  # 担当させたいエージェント種別

# 全体プラン（メインタスク + サブタスク配列）
class TravelPlan(BaseModel):  # ★重要: LLM 出力をこの形に収めるよう定義（スキーマ駆動設計）
  main_task: str             # 例: "家族旅行の3日間行程を作成"
  subtasks: List[TravelSubTask]
  is_greeting: bool          # 挨拶メッセージかどうか（挨拶なら分解不要などの分岐用）
```

<a id="extended-full-example"></a>
### 拡張例: サブタスク分解 + JSON応答検証

英語版 README のより長いサンプルと対応する形で、実際に JSON を生成し Pydantic で検証・表示する例です。
この例は「構造化出力を厳密に強制 → 受信後ただちに Pydantic で検証 → 失敗なら即座に例外」という信頼性向上フローを示します。
最小スニペットとの差分は、応答制約（JSONキー固定）とエラーハンドリング/検証ステップを明示して再利用性・堅牢性を高めている点です。
*注: 本スニペットは `code_samples/` ディレクトリの独立ノートブックとしてはまだ用意していません。必要に応じてこのコードをコピーし、新規ノートブックに貼り付けて実行してみてください。*

```python
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
import json, os
from pprint import pprint
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential

class AgentEnum(str, Enum):  # ★エージェント種別: LLM 出力を限定し綴り揺れ防止
  FlightBooking = "flight_booking"
  HotelBooking = "hotel_booking"
  CarRental = "car_rental"
  ActivitiesBooking = "activities_booking"
  DestinationInfo = "destination_info"
  DefaultAgent = "default_agent"
  GroupChatManager = "group_chat_manager"  # オプション

class TravelSubTask(BaseModel):  # ★サブタスク要素: task_details + 担当者
  task_details: str
  assigned_agent: AgentEnum

class TravelPlan(BaseModel):  # ★全体スキーマ: main_task / subtasks / is_greeting のみ許容
  main_task: str
  subtasks: List[TravelSubTask]
  is_greeting: bool

token = os.getenv("GITHUB_TOKEN")  # ★資格情報: 推論API呼び出しに必要。環境変数で注入しコード直書きを避ける
if not token:
  raise RuntimeError("GITHUB_TOKEN を環境変数に設定してください")

client = AzureAIChatCompletionClient(  # ★クライアント初期化: GitHub Models / Azure AI Inference 経由
  model="gpt-4o-mini",
  endpoint="https://models.inference.ai.azure.com",
  credential=AzureKeyCredential(token),
  model_info={"json_output": False, "function_calling": True, "vision": True, "family": "unknown"},
)

messages = [  # ★プロンプト構成: System(役割+出力制約) + User(要求)
  SystemMessage(content=(
    # 元英語: You are a planner agent. Decide which agents to run based on the user's request.
    # Provide ONLY JSON with keys: main_task, subtasks, is_greeting.
    # Agents: flight_booking, hotel_booking, car_rental, activities_booking, destination_info, default_agent.
    "あなたはプランナーエージェントです。ユーザーのリクエスト内容に基づきどのエージェントを走らせるか判断してください。\n"
    "出力は JSON のみで、キーは main_task, subtasks, is_greeting のみを含めてください。\n"
    "利用可能エージェント: flight_booking, hotel_booking, car_rental, activities_booking, destination_info, default_agent"
  ), source="system"),
  UserMessage(content="シンガポール発、子ども2人を含む家族向けのメルボルン旅行プランを作成してください", source="user"),
]

response = await client.create(  # ★構造化出力指示: SDK に JSON オブジェクト生成を強制
  messages=messages,
  extra_create_args={"response_format": 'json_object'}
)
raw_content: Optional[str] = response.content if isinstance(response.content, str) else None  # ★ガード: 文字列以外(ツール呼び出し等)を除外
if raw_content is None:
  raise ValueError("応答が文字列JSONではありません")

data = json.loads(raw_content)
pprint(data)
plan = TravelPlan.model_validate(data)  # ★Pydantic検証: スキーマ逸脱で即例外 → 早期失敗
print("\n=== サブタスク一覧 ===")
for st in plan.subtasks:
  print(f"- {st.assigned_agent}: {st.task_details}")
```

## マルチエージェント連携を伴うプランニング

（この節は前半の「タスク分解」「構造化出力」「拡張フル例」で学んだ“単一プラン生成＋検証”を踏まえ、生成されたプランを複数専門エージェントへどうオーケストレーション/ルーティングするかという“実運用統合”観点を示します。違いは、計画そのものよりもエージェント間配分と流れ制御に主眼がある点です。）

初心者向け補足: ここでいう Semantic Router（セマンティック ルーター）エージェントは「ユーザー入力の“意味”を理解して、どの専門エージェント/ツールに渡すかを決める係」です。単なるキーワードマッチではなく埋め込み（ベクトル類似度）や LLM 判断で “フライト関連か / ホテルか / どれでもないのでデフォルトか” を選びます。Planner が「何をやるか（サブタスク列）を作る」のに対し、Semantic Router は「次にどこへ送るか」を即時判断する分岐点。Orchestrator（全体制御）より粒度が小さく、誤判定時は fallback（default_agent など）に戻す安全策を入れます。

具体的には Semantic Router（ルーティング）エージェントがユーザー入力を受け取り、システムプロンプトに基づき構造化プランを生成し、適切な各専門エージェントへ振り分けます。今回のゴール`3日間の旅行行程を作成する`場合の流れ:

1. プラン生成: ユーザー要求と利用可能エージェント一覧をもとに JSON プラン生成
2. エージェント/ツール一覧: レジストリ（カタログ）で機能と責務を明示
3. ルーティング: サブタスク数に応じ単一エージェント直送 or グループマネージャ経由
4. 要約: 中間結果をまとめユーザー向けサマリを生成

### マルチエージェント向けプラン生成コード スニペット（Azure OpenAI SDK のコード例）

```python
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
import json, os
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

class AgentEnum(str, Enum):  # ★列挙: 追加/削除時はここだけ変更し他ロジック最小変更
  FlightBooking = "flight_booking"
  HotelBooking = "hotel_booking"
  CarRental = "car_rental"
  ActivitiesBooking = "activities_booking"
  DestinationInfo = "destination_info"
  DefaultAgent = "default_agent"
  GroupChatManager = "group_chat_manager"

class TravelSubTask(BaseModel):  # ★ルーティング単位
  task_details: str
  assigned_agent: AgentEnum

class TravelPlan(BaseModel):  # ★LLM の期待最終 JSON 形
  main_task: str
  subtasks: List[TravelSubTask]
  is_greeting: bool

client = AzureOpenAIChatCompletionClient(  # ★Azure OpenAI 用クライアント
  azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
  model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
  api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
  azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

messages = [  # ★System: 選択指示 / User: 具体的要求
  SystemMessage(content=(
    # 元英語: You are a planner agent. Decide which agents to run based on the user's request.
    # Agents: flight_booking, hotel_booking, car_rental, activities_booking, destination_info, default_agent.
    "あなたはプランナーエージェントです。ユーザー要求に基づいて適切なエージェントを選択してください。\n"
    "利用可能エージェント: flight_booking, hotel_booking, car_rental, activities_booking, destination_info, default_agent"
  ), source="system"),
  UserMessage(content="シンガポール発で子ども2人を含む家族向けのメルボルン旅行プランを作成してください", source="user"),
]

resp = await client.create(  # ★response_format に Pydantic モデルを直接指定 → 自動整形
  messages=messages,
  extra_create_args={"response_format": TravelPlan}
)
raw = resp.content if isinstance(resp.content, str) else None
if raw is None:
  raise ValueError("JSON応答を取得できませんでした")
obj = json.loads(raw)
plan = TravelPlan.model_validate(obj)  # ★構造検証
for st in plan.subtasks:
  print(st.assigned_agent, st.task_details)
```

### サンプル JSON 出力

```json
{
  "is_greeting": false,
  "main_task": "シンガポール発メルボルンへの家族旅行プランを作成する。",
  "subtasks": [
  { "assigned_agent": "flight_booking", "task_details": "シンガポール〜メルボルン往復航空券を手配" },
  { "assigned_agent": "hotel_booking", "task_details": "家族向けの宿泊施設をメルボルンで検索" },
  { "assigned_agent": "car_rental", "task_details": "4人家族に適したレンタカーをメルボルンで手配" },
  { "assigned_agent": "activities_booking", "task_details": "子どもも楽しめる現地アクティビティを列挙" },
  { "assigned_agent": "destination_info", "task_details": "メルボルンの目的地情報（概要・移動・注意点）を提供" }
  ]
}
```
<a id="iterative-planning-example"></a>
## 反復的プランニング（Iterative Planning）

（この節は「初期プラン生成」（タスク分解）と「オーケストレーション」（マルチエージェント連携）を踏まえ、実行中のフィードバック/失敗/ユーザー新要求に応じ “何を再計画すべきか・再計画すべきでないか” の判断基準と軽量な再プラン手順を学ぶのが目的です。静的な一括計画との差分は、状態変化トリガーに基づく選択的・最小差分更新を重視する点です。）

サブタスクの結果やユーザーフィードバックを受け再計画（Re-plan）が必要になる場合があります。例えばフライトのデータ形式が想定外だった、ユーザーが「もっと早い便に変更したい」と指示した等です。動的・反復的な再計画が最終品質を高めます。

Magentic One のような高度なマルチエージェントシステムでは、オーケストレーターがタスク進捗を追跡し、必要に応じ自動で計画を更新します。参考: <a href="https://www.microsoft.com/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks" target="_blank">Magentic One Blogpost</a>

### 再プラン（Re-plan）コード例

```python
from autogen_core.models import UserMessage, SystemMessage, AssistantMessage

messages = [  # ★再プラン判定: 旧プランを明示し差分思考を誘導
  SystemMessage(content=(
    # 元英語: You are a planner agent. Re-plan only if user intent changed or constraints invalidated previous plan.
    "あなたはプランナーエージェントです。ユーザー意図が変化した、あるいは制約により既存プランが無効になった場合のみ再計画してください。"
  ), source="system"),
  UserMessage(content="シンガポール発で子ども2人を含む家族向けのメルボルン旅行プランを作成してください", source="user"),
  # 以前のプランを文字列化して差分判断材料を提供
  AssistantMessage(content=f"前回の旅行プラン - {plan.model_dump_json()}", source="assistant"),  # ★旧状態: LLM に“再計画が必要か”を評価させる材料
]

replan_resp = await client.create(  # ★再プラン要求も JSON 指定でフォーマット一貫
  messages=messages,
  extra_create_args={"response_format": 'json_object'}
)
new_raw = replan_resp.content if isinstance(replan_resp.content, str) else None
if new_raw:
  import json
  new_obj = json.loads(new_raw)
  new_plan = TravelPlan.model_validate(new_obj)
  print("旧→新 サブタスク数:", len(plan.subtasks), '->', len(new_plan.subtasks))
```

## まとめ

本レッスンは「ゴール定義 → サブタスク分解 → 構造化出力 → ルーティング → 差分再計画」という一連の計画ライフサイクルを、スキーマ駆動と検証ファーストの観点で体系化しました。特に `code_samples` 内 3 つのノートブックは、すべて「(1) 先に JSON/Pydantic スキーマを固定し、(2) LLM 出力をその契約に合わせて制約し、(3) 即時バリデーションで逸脱を早期検知する」という共通方針を段階的に深めています。

| ノートブック | 目的/レイヤー | 主な特徴 | リスク低減要素 |
|--------------|---------------|----------|----------------|
| 07-azure-openai | 最小経路 (API 直接呼び出し) | `response_format` による JSON 強制 | 余計な自由度を排し構文失敗を抑制 |
| 07-autogen | フレームワーク抽象 | メッセージ/モデルクライアント差し替え・再試行ロジック | API 変更吸収, 再試行/例外パターン標準化 |
| 07-semantic-kernel | 関数化・再利用性 | ChatCompletion + 関数スタイル + Artifact 可視化 | 再利用/監査性向上, 技術的負債の局所化 |

### ビジネス視点での要約
1. スキーマ駆動 (Schema-First) は再現性とコンプライアンス適合性 (監査・データ境界) を高め、後工程 (ルーティング/実行) の不確実性コストを前倒しで削減します。  
2. 逐次的段階 (Minimal → Abstraction → Reusable Function) により、導入初期は TTV (Time To Value) を最短化しつつ、後から運用要件 (監視, 回帰テスト, A/B, バージョニング) を乗せる拡張余地を確保します。  
3. JSON Validation (Pydantic) による「即時失敗」は、曖昧な自然文後処理より失敗領域を明示化し SLO/SLA 設計 (成功率/再試行閾値) を数字で管理しやすくします。  
4. エージェント列挙型 (Enum) による責務境界の固定は、誤ルーティング/権限過剰行使の抑止 (最小権限原則) と内部統制 (Who can do what) の基盤になります。  
5. 差分再計画 (Selective Re-plan) は “全面再生成” に比べ計算コスト・待機時間・偶発的劣化 (Regression) を低減し、ユーザー体験 (局所修正の即応) を改善します。  
6. 検証結果/再試行統計/スキーマ違反ログは、品質改善 (Prompt 設計の PDCA) とコスト最適化 (再試行閾値調整/キャッシュ導入) のための計測レイヤーとして必須です。  
7. コード化されたプロンプト (関数化) と Artifact フラグは「いつ・何が・どこまで正常か」を定性的説明から定量モニタリングへ移行させ、インシデント MTTR 短縮に寄与します。  

### 技術的ハイライト再整理
- Generate-to-Schema パターン: モデル自由度を初期から拘束 → 逸脱時は即例外。  
- Enumerated Agents: 実行対象範囲を列挙型で契約化 → 新規エージェント追加時の影響範囲を局所化。  
- response_format / 明示 JSON 制約: “自然文→正規化” の曖昧工程削減。  
- Retry + Prompt Mutation: 軽量な再提示 (例: `#retry` 付与) で短期的回復率向上。  
- ChatHistory / SystemMessage 制御: 意図/制約/差分トリガーを履歴へ構造的に残し監査可能性確保。  
- Validation Telemetry: 成功/失敗/再試行をメトリクス化し SLA, コスト, 品質を三点同時最適。  

### 運用・ガバナンス観点の推奨アクション
- 観測: 成功率, 平均再試行回数, スキーマ違反種別 (Missing Key / Enum Drift / JSON Parse) をダッシュボード化。  
- 品質: 代表 / 境界 / 逆例 (悪意/無関係入力) テストケースを固定し回帰テスト自動化。  
- セキュリティ: 実行エージェントごとに資格情報スコープを分離 (最小権限)。  
- コスト: 再計画頻度と LLM トークン使用量を相関分析し不要な再プラン閾値を調整。  
- 継続改善: プロンプト差分と品質指標 (成功率/タスク完了時間) を週次レビューし Prompt バージョン管理。  

### 次の具体ステップ
- “再計画要否” 判定を独立エンドポイント化し、不要なフル再生成を削減。  
- サブタスク実行結果に信頼度/コスト/レイテンシを付帯しルーティング最適化 (Cost-Aware Scheduling)。  
- 代表入力 + ノイズ入力セットを用いた Prompt Regression Suite の整備。  
- 生成 JSON にバージョン (schema_version) 付与し後方互換・移行戦略を明確化。  
- キャッシュ (Plan ハッシュ) と TTL 管理で重複要求の計算コスト/レイテンシを削減。  

段階的にこれらを導入することで、POC レベルのプランナーを、監査性・可観測性・コスト効率・変更容易性を備えた実運用クラスのオーケストレーション層へ発展させることが可能です。

## 追加リソース

* AutoGen Magentic One: 複雑タスクに対するジェネラリスト型マルチエージェントシステム。<a href="https://github.com/microsoft/autogen/tree/main/python/packages/autogen-magentic-one" target="_blank">autogen-magentic-one</a>

## 前のレッスン

[信頼できるAIエージェントの構築](../06-building-trustworthy-agents/README.md)

## 次のレッスン

[マルチエージェントデザインパターン](../08-multi-agent/README.md)

### 推奨される Code Sample の実行順序

1. `code_samples/07-azure-openai.ipynb`（または同等の最小 Azure Inference 例）  
  単一プロンプト → JSON スキーマ検証の最小パス。依存関係と資格情報設定が最も少なく、接続性と response_format の挙動確認に最適。
2. `code_samples/07-autogen.ipynb`  
  AutoGen 抽象化を加えた構造化出力。基礎が動くことを確認後に、フレームワーク層（メッセージオブジェクト/モデルクライアント差し替え）へ理解を拡張。
3. `code_samples/07-semantic-kernel.ipynb`  
  プロンプトを“関数化”しプランナーコンポーネントとして再利用する設計。Semantic Kernel のプラグイン/関数呼び出しモデルを通じてオーケストレーションへの接続点を把握。
4. 本 README の [拡張フル例](#extended-full-example) を Jupyter Notebook として実行  
  追加のエラーハンドリング・列挙型・詳細 SystemMessage を統合した “運用寄り” スキーマ駆動パターン。前段 3 ステップ後に読むことで差分（堅牢化戦略）が把握しやすい。
5. README 内の [再プラン（Iterative Planning）](#iterative-planning-example)  を Jupyter Notebook として実行
  既存プランを入力に含め差分思考させる応用。初期プラン生成挙動を観察済みでないと再計画条件の効果比較が難しいため最後。

この順序は “最小実行パス → フレームワーク抽象 → 再利用関数化 → 運用強化 → 動的再計画” の学習曲線を意図し、学習コスト/デバッグ複雑性/概念密度が段階的に上がるよう最適化しています。

---
**免責事項**: 本ドキュメントは原文を基に人による確認を加えた翻訳です。法的または正確性が厳密に要求される用途では原文を参照してください。