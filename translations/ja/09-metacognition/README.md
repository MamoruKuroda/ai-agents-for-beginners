<!--
CO_OP_TRANSLATOR_METADATA:
{
  "original_hash": "8cbf460468c802c7994aa62e0e0779c9",
  "translation_date": "2025-06-11T04:46:43+00:00",
  "source_file": "09-metacognition/README.md",
  "language_code": "ja"
}
-->
[![Multi-Agent Design](../../../09-metacognition/images/lesson-9-thumbnail.png)](https://youtu.be/His9R6gw6Ec?si=3_RMb8VprNvdLRhX)

> _(上の画像をクリックするとこのレッスンの動画が視聴できます)_

# AIエージェントにおけるメタ認知

<!-- UPDATE_NOTE: 下記 code_samples 日本語版 09-semantic-kernel.ipynb を追加。英語版セル構成を踏襲し、コメントで要点補足。 -->

## はじめに
AIエージェントのメタ認知に関するレッスンへようこそ！この章は、自分自身の思考プロセスについてAIエージェントがどのように考えるかに興味を持つ初心者向けに設計されています。このレッスンを終える頃には、重要な概念を理解し、メタ認知をAIエージェント設計に応用するための実践的な例を身につけることができます。

## 学習目標

このレッスンを修了すると、以下ができるようになります：

1. エージェント定義における推論ループの意味を理解する。
2. 自己修正型エージェントを支援するための計画と評価技術を使う。
3. タスクを達成するためにコードを操作できるエージェントを作成する。

### 全体の位置づけ（学習層の流れ）
本レッスンは次の層が積み重なる中で「より自律的で説明可能なエージェント」へ至る流れのうち、メタ認知層を中心に扱います。

| 層 | 主目的 | 観察対象 | 主な更新対象 | 評価粒度 | 代表ループ |
|----|--------|----------|--------------|----------|------------|
| 計画 | 目標をステップ列へ分解します | 目標/進行状況 | ステップ列 | 成否(粗) | plan→act |
| 自己修正型RAG | 応答不足や誤りを補います | 回答品質/取得結果 | 追加取得条件/再プロンプト | 根拠有無/充足率 | retrieve→generate→evaluate |
| 環境モデル | 継続参照する内部状態を保持します | preferences / avoid / change_log など | 状態フィールド | 一貫性/再利用率 | update→query |
| SQL等構造化取得 | 条件単位で精緻にデータ取得します | 行数/重複/カバレッジ | WHERE/JOIN/投影列 | 行数適正/重複率/コスト | refine→run→log |
| コード生成 | 戦略変更を再利用資産にします | 差分/テスト結果 | 関数/クエリ/評価コード | テスト合格率/改善率 | propose→patch→test |
| メタ認知 | 戦略と内部状態を再評価し次サイクル方針を更新します | 戦略/状態/失敗傾向 | 嗜好/評価指標/回避条件 | 指標トレンド/失敗分類 | observe→reflect→revise |

要点: 計画で行動列を作り、自己修正型RAGで応答を改善し、環境モデルに状態を保持し、SQLで取得条件を明確化し、コード生成で変更を資産化し、メタ認知で方針全体を再評価する循環で精度と説明可能性を段階的に高めます。

補足:
- 環境モデルは一時的推論結果と次サイクル改善判断を橋渡しします。これが無いと嗜好や失敗パターンが断片的になり再質問や無駄取得が増えます。
- 自己修正型RAGは「応答」を改善し、メタ認知は「改善方針」を改善します。
- コード生成はメタ認知で得た抽象判断を具体コードへ固定し差分検証を可能にします。
- SQLは取得条件を明示し再現性と条件単位の改善検証を支えます。

## メタ認知の紹介

メタ認知とは、自分自身の思考について考える高次の認知プロセスを指します。AIエージェントにおいては、自己認識や過去の経験に基づいて自分の行動を評価・調整できる能力を意味します。メタ認知、つまり「思考についての思考」は、エージェント型AIシステムの開発において重要な概念です。これはAIシステムが自身の内部プロセスを認識し、それに基づいて行動を監視、制御、適応できることを含みます。私たちが場の空気を読むときや問題を見つめるときと似ています。

この自己認識は、AIシステムがより良い意思決定を行い、エラーを特定し、時間をかけてパフォーマンスを向上させるのに役立ちます。これはチューリングテストやAIが人間を超えるかどうかの議論にも関連しています。

エージェント型AIシステムの文脈では、メタ認知は以下のような課題に対処する助けとなります：

- 透明性：AIシステムが自身の推論や意思決定を説明できることを保証する。
- 推論：情報を統合し、適切な判断を下す能力を強化する。
- 適応性：新しい環境や変化する条件に適応できるようにする。
- 知覚：環境からのデータ認識や解釈の精度を向上させる。

### メタ認知とは何か？

メタ認知は「思考についての思考」とも呼ばれ、自分の認知プロセスに対する自己認識と自己制御を伴う高次の認知プロセスです。AIの領域では、メタ認知によりエージェントは自身の戦略や行動を評価し、適応させることが可能となり、問題解決や意思決定能力が向上します。

メタ認知を理解することで、より知的で適応性が高く効率的なAIエージェントを設計できます。

真のメタ認知では、AIが自分の推論について明示的に考えます。

例：「安いフライトを優先したけど…直行便を見逃しているかもしれないから、再確認しよう。」

どのルートを選んだか、なぜそうしたかを追跡します。

- 前回のユーザーの好みに過度に依存してミスをしたことに気づき、最終的な推薦だけでなく意思決定戦略自体を修正する。
- 「ユーザーが『混雑しすぎ』と言ったときは、単に特定の観光地を外すだけでなく、人気順で『トップアトラクション』を選ぶ方法自体が問題だと反省する」といったパターンを診断する。

### AIエージェントにおけるメタ認知の重要性

メタ認知はAIエージェント設計において以下の理由で重要な役割を果たします：

![Importance of Metacognition](../../../09-metacognition/images/importance-of-metacognition.png)

- 自己反省(Self-Reflection)：エージェントが自分のパフォーマンスを評価し、改善点を見つけることができる。
- 適応性(Adaptability)：過去の経験や変化する環境に基づいて戦略を修正できる。
- エラー修正(Error Correction)：自律的にエラーを検出し修正できるため、より正確な結果が得られる。
- 資源管理(Resource Management)：時間や計算資源などの使用を最適化するために行動を計画・評価できる。

## AIエージェントの構成要素

メタ認知プロセスに入る前に、AIエージェントの基本的な構成要素を理解することが重要です。AIエージェントは通常以下で構成されます：

- ペルソナ：ユーザーとのやり取りの仕方を定義する性格や特徴。
- ツール：エージェントが実行できる機能や能力。
- スキル：エージェントが持つ知識や専門性。

これらの要素が連携して、特定のタスクを実行できる「専門ユニット」を形成します。

**例**：旅行代理店を考えてみましょう。単に旅行を計画するだけでなく、リアルタイムデータや過去の顧客の旅の経験に基づいてプランを調整するサービスです。

### 例：旅行代理店サービスにおけるメタ認知

AIによって動く旅行代理店サービスを設計するとします。このエージェント「Travel Agent」はユーザーの休暇計画を支援します。メタ認知を組み込むには、自己認識や過去の経験に基づいて行動を評価・調整する必要があります。

> 注: ここで列挙しているタスク分解やステップは「人間（設計者）が例示したもの」であり、この段階ではまだエージェント自身が動的に計画を生成しているわけではありません。後続の「計画」セクションで、メタ認知に基づくエージェント主体の計画（状態→評価→次行動選択）について説明しています。

メタ認知が果たす役割の例：

#### 現在のタスク

ユーザーのパリ旅行計画を手伝うこと。

#### タスクを完了するステップ

1. **ユーザーの好みを収集**：旅行日程、予算、興味（例：美術館、料理、ショッピング）、特別な要望を尋ねる。
2. **情報を取得**：ユーザーの好みに合ったフライト、宿泊施設、観光地、レストランを検索。
3. **提案を作成**：フライト情報、ホテル予約、アクティビティの提案を含むパーソナライズされた旅程を提供。
4. **フィードバックに基づき調整**：ユーザーからの意見を聞き、必要に応じて調整。

#### 必要なリソース

- フライトやホテル予約のデータベースへのアクセス。
- パリの観光地やレストランの情報。
- 過去のユーザーフィードバックデータ。

#### 経験と自己反省

Travel Agentはメタ認知を活用してパフォーマンスを評価し、過去の経験から学習します。例えば：

1. **ユーザーフィードバックの分析**：どの提案が好評で、どれがそうでなかったかを見直し、今後の提案に反映させる。
2. **適応性**：ユーザーが混雑を嫌うと言った場合、今後はピーク時間の人気スポットを避けるようにする。
3. **エラー修正**：過去に満室のホテルを提案してしまった場合、今後は予約状況をより厳密に確認するよう学習する。

#### 開発者向け実用例

Travel Agentのコードにメタ認知を組み込んだ簡単な例：

```python
class Travel_Agent:
    def __init__(self):
        # user_preferences: ユーザー嗜好を保持 (メタ認知=自己状態の明示保持)
        # experience_data: フィードバック履歴 (振り返り/再評価用ログ)
        self.user_preferences = {}
        self.experience_data = []

    def gather_preferences(self, preferences):
        # 初期嗜好の収集。
        self.user_preferences = preferences

    def retrieve_information(self):
        # メタ認知: 失敗回数やレスポンス品質スコアを内部に記録し再検索戦略を動的に変更
        flights = search_flights(self.user_preferences)
        hotels = search_hotels(self.user_preferences)
        attractions = search_attractions(self.user_preferences)
        return flights, hotels, attractions

    def generate_recommendations(self):
        # 推論チェーン: 取得 → 統合 (create_itinerary)。
        flights, hotels, attractions = self.retrieve_information()
        itinerary = create_itinerary(flights, hotels, attractions)
        return itinerary

    def adjust_based_on_feedback(self, feedback):
        # フィードバックを経験データに蓄積 (学習ログとして使用)。
        self.experience_data.append(feedback)
        # adjust_preferences は純関数的に user_preferences を更新する想定で実装。
        self.user_preferences = adjust_preferences(self.user_preferences, feedback)

# 例: 使用方法 (Example usage)
travel_agent = Travel_Agent()
preferences = {
    "destination": "Paris",  # 目的地
    "dates": "2025-04-01 to 2025-04-10",  # 旅行期間 (開始〜終了)
    "budget": "moderate",  # 予算帯 (例: low / moderate / high)
    "interests": ["museums", "cuisine"]  # 興味カテゴリ (メタ認知: 推薦理由の根拠データ)
}
travel_agent.gather_preferences(preferences)
itinerary = travel_agent.generate_recommendations()
print("提案旅程:", itinerary)
feedback = {"liked": ["Louvre Museum"], "disliked": ["Eiffel Tower (too crowded)"]}
travel_agent.adjust_based_on_feedback(feedback)
```

#### メタ認知が重要な理由

単一のLLMは基本的に「入力→一度きりの出力」の即時生成で内部の評価プロセスや継続的記憶が露出しませんが、メタ認知エージェントは目標・状態・評価結果を明示的に保持し (計画→実行→自己評価→調整) という反復ループを回すことで、説明可能性・自己修正精度・リソース効率を段階的に高められます。

- **自己反省**：エージェントは自身のパフォーマンスを分析し、改善点を見つけることができる。
- **適応性**：フィードバックや変化する条件に基づき戦略を修正できる。
- **エラー修正**：誤りを自律的に検出・修正できる。
- **資源管理**：時間や計算リソースの使用を最適化できる。

メタ認知を取り入れることで、Travel Agentはよりパーソナライズされ正確な旅行提案を提供し、ユーザー体験を向上させることができます。

---

## 計画（メタ認知をもとに行動を計画する）

ここでは前半で説明したメタ認知（自己状態の把握と評価）を、タスク達成の具体的なステップ作成つまり「計画」を行います。メタ認知が内省なら、計画はその結果を次の行動へ橋渡しする実行指針です。
計画はAIエージェントの行動において重要な要素です。目標達成のために必要なステップを、現在の状況や資源、障害を考慮しながら整理します。

### 計画の要素

- **現在のタスク**：タスクを明確に定義する。
- **タスク完了までのステップ**：タスクを実行可能なステップに分解する。
- **必要なリソース**：必要な資源を特定する。
- **経験**：過去の経験を活用して計画を立てる。

**例**：Travel Agentがユーザーの旅行計画を効果的に支援するために取るべきステップは以下の通りです。

### Travel Agentのステップ

1. **ユーザーの好みを収集**

- 旅行日程、予算、興味、特別な要望を尋ねる。
- 例：「いつ旅行を予定していますか？」「予算はどのくらいですか？」「旅行中にどんなアクティビティを楽しみたいですか？」

2. **情報を取得**

- ユーザーの好みに基づいて関連する旅行オプションを検索。
- **フライト**：予算と希望の日程内で利用可能なフライトを探す。
- **宿泊施設**：場所、価格、設備の好みに合ったホテルやレンタル物件を探す。
- **観光地・レストラン**：ユーザーの興味に合う人気の観光スポットや飲食店を特定する。

3. **提案を作成**

- 取得した情報を基にパーソナライズされた旅程をまとめる。
- フライト、ホテル予約、推奨アクティビティの詳細を提供し、ユーザーの好みに合わせて調整する。

4. **旅程をユーザーに提示**

- 提案した旅程をユーザーに共有し、確認してもらう。
- 例：「パリ旅行のおすすめ旅程です。フライト情報、ホテル予約、推奨アクティビティとレストランのリストを含んでいます。ご意見をお聞かせください。」

5. **フィードバックを収集**

- 提案に対するユーザーの意見を尋ねる。
- 例：「フライトの選択は気に入りましたか？」「ホテルはご希望に合っていますか？」「追加や削除したいアクティビティはありますか？」

6. **フィードバックに基づき調整**

- ユーザーの意見を反映して旅程を修正。
- フライト、宿泊、アクティビティの提案をより好みに合わせて変更。

7. **最終確認**

- 更新した旅程をユーザーに提示し、最終確認を得る。
- 例：「ご意見を反映して調整しました。こちらが最新の旅程です。ご確認ください。」

8. **予約と確認**

- ユーザーの承認後、フライトや宿泊、事前計画されたアクティビティの予約を進める。
- 確認情報をユーザーに送信。

9. **継続的なサポート**

- 旅行前や旅行中に変更や追加の要望に対応できるようサポートを継続。
- 例：「旅行中に何かお手伝いが必要な場合は、いつでもご連絡ください！」

### 開発者向け実用例

```python
"""短縮版: plan -> act -> reflect -> revise の最小要素
前半との違いは大きく3つ: (1) 明示 plan 生成 (2) フィードバックで再計算 (3) journal ログ
余計な挿入ロジックは省き概念理解を最優先。
"""
from typing import Dict, Any, List

def search_flights(prefs):
    return [{"id": "F-001", "price": 520}]

def search_hotels(prefs):
    return [{"name": "Central Hotel", "score": 7.1}]

def search_attractions(prefs):
    return ["Louvre", "Seine Walk"]

def create_itinerary(flights, hotels, attractions):
    return {"flights": flights, "hotels": hotels, "attractions": attractions}

def adjust(prefs, feedback):
    if feedback.get("disliked"):
        prefs.setdefault("avoid", []).extend(feedback["disliked"])
    if feedback.get("liked"):
        prefs.setdefault("favorites", []).extend(feedback["liked"])
    return prefs

class MiniPlanningAgent:
    def __init__(self):
        self.prefs: Dict[str, Any] = {}
        self.plan: List[str] = []
        self.journal: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {}

    def gather_preferences(self, p):
        self.prefs = p

    def generate_plan(self):
    # 計画生成(中枢): サブタスク列をここで定義
        self.plan = [
            "retrieve",      # 情報取得
            "compose",       # 旅程組立
            "feedback",      # フィードバック取得 (模擬)
            "revise"         # 調整
        ]
        self._log("plan_created", {"plan": self.plan})

    def run(self, feedback=None):
    # 実行ループ(中枢): plan を順に実行し内省/再計算を適用
        for step in self.plan:
            if step == "retrieve":
                self.state["flights"] = search_flights(self.prefs)
                self.state["hotels"] = search_hotels(self.prefs)
                self.state["attractions"] = search_attractions(self.prefs)
            elif step == "compose":
                self.state["itinerary"] = create_itinerary(
                    self.state["flights"], self.state["hotels"], self.state["attractions"]
                )
            elif step == "feedback":
                self.state["feedback"] = feedback or {"liked": ["Louvre"], "disliked": []}
            elif step == "revise":
                adjust(self.prefs, self.state.get("feedback", {}))
                # 再計算 (簡略: ホテルスコア + liked 数 *0.5 - disliked 数 *0.5)
                base = self.state["hotels"][0]["score"]
                fb = self.state.get("feedback", {})
                score = base + 0.5*len(fb.get("liked", [])) - 0.5*len(fb.get("disliked", []))
                self.state["score"] = round(score, 2)
            self._log("step", {"name": step})
        return self.state

    def _log(self, event, detail):
        self.journal.append({"event": event, "detail": detail})

# 使用例
agent = MiniPlanningAgent()
agent.gather_preferences({
    "destination": "Paris",  # 目的地
    "dates": "2025-04-01 to 2025-04-10",  # 旅行期間 (開始〜終了)
    "budget": "moderate",  # 予算帯 (例: low / moderate / high)
    "interests": ["museums", "cuisine"]  # 興味カテゴリ
})
agent.generate_plan()
result = agent.run(feedback={"liked": ["Louvre"], "disliked": ["Central Hotel (too noisy)"]})
print("スコア:", result["score"])
print("旅程キー一覧:", list(result["itinerary"].keys()))
print("ログイベント:", [e["event"] for e in agent.journal])
```

## 自己修正型RAGシステム

> 用語統一: 本レッスンでは「自己修正型RAG」を使用します (英: Corrective / Self-Refining RAG)。RAGにフィードバック/評価ループを組み込み、取得・生成結果の誤りや不足を段階的に検出・改善する手法を指します。

まずはRAGツールと先取りコンテキストロードの違いを理解しましょう。

![RAG vs Context Loading](../../../09-metacognition/images/rag-vs-context.png)

### Retrieval-Augmented Generation (RAG)

RAGは検索システムと生成モデルを組み合わせたものです。クエリが発せられると、検索システムが外部ソースから関連文書やデータを取得し、その情報を生成モデルへの入力に加えます。これにより、より正確で文脈に沿った応答が可能になります。

RAGシステムでは、エージェントが知識ベースから関連情報を取得し、それを使って適切な応答や行動を生成します。

### 自己修正型RAGアプローチ

自己修正型RAGアプローチは、RAG技術に自己評価ループを組み合わせ、取得/生成過程での誤り・不足・曖昧さを段階的に検出し再取得や再プロンプトで改善していくことに焦点を当てています。これには以下が含まれます：

1. **プロンプト技術**：エージェントが関連情報を取得するための特定のプロンプトを使用する。
2. **ツール**：取得情報の関連性を評価し、正確な応答を生成するアルゴリズムや仕組みを実装する。
3. **評価**：エージェントのパフォーマンスを継続的に評価し、精度と効率を改善するための調整を行う。

### 自己修正型RAGの代表例

自己修正型RAGは「取得→生成」一回で終わらず、評価/フィードバックで不足や誤差を検知し再取得・再生成を繰り返す枠組みです。代表的な適用シナリオを二つにまとめて示します。

1. 検索エージェント: Web から根拠を取得し回答を生成。
    - プロンプト技術: 質問を検索しやすいクエリに分解・拡張する。
    - ツール: 検索結果をランキング/フィルタし重複を除去、引用用に整形する。
    - 評価: 引用不足や矛盾があれば再取得・再生成する。
2. 旅行プランニング（本例）: 嗜好と複数カテゴリ(フライト/ホテル/アクティビティ)を統合し旅程を反復改善。
    - プロンプト技術: 目的地・期間・予算・興味タグをクエリ条件へマッピングする。
    - ツール: カテゴリ別に候補を取得し旅程へ統合、基本制約(予算/時間)をチェックする。
    - 評価: 満足度や興味カバレッジ、ユーザーフィードバック(liked/avoid)を反映して再検索・調整する。

以下では上記の Travel Agent ケースを使って実装ステップを具体化します。

> 計画セクションとの主な違い: ここでは「静的に立てた手順」ではなく、ユーザーフィードバック/評価指標を入力として再取得・再統合を行う反復(自己修正)ループに焦点を当てます。重要点は (1) 外部取得と内部状態の分離 (2) フィードバックを再検索条件へ即座に還元 (3) 再生成前に簡易評価を挟む ことです。

#### 実装ステップ（Travel Agent例）  
1. **初期ユーザーインタラクション**  
- 旅行代理店は目的地、旅行日程、予算、興味などユーザーの初期希望を収集する。  
```python
     preferences = {
         "destination": "Paris",
         "dates": "2025-04-01 to 2025-04-10",
         "budget": "moderate",
         "interests": ["museums", "cuisine"]
     }
```  
2. **情報の取得**  
- 旅行代理店はユーザーの希望に基づいてフライト、宿泊施設、観光地、レストランの情報を取得する。  
```python
     flights = search_flights(preferences)
     hotels = search_hotels(preferences)
     attractions = search_attractions(preferences)
```  
3. **初期推奨の生成**  
- 旅行代理店は取得した情報を使ってパーソナライズされた旅程を生成する。  
```python
     itinerary = create_itinerary(flights, hotels, attractions)
     print("Suggested Itinerary:", itinerary)
```  
4. **ユーザーフィードバックの収集**  
- 旅行代理店は初期推奨に対するユーザーのフィードバックを求める。  
```python
     feedback = {
         "liked": ["Louvre Museum"],
         "disliked": ["Eiffel Tower (too crowded)"]
     }
```  
5. **自己修正型RAGプロセス**  
- **プロンプト技術**：旅行代理店はユーザーフィードバックに基づいて新たな検索クエリを作成する。  
```python
       if "disliked" in feedback:
           preferences["avoid"] = feedback["disliked"]
```  
- **ツール**：旅行代理店はユーザーフィードバックに基づいて新しい検索結果をランキング・フィルタリングするアルゴリズムを使用する。  
```python
       new_attractions = search_attractions(preferences)
       new_itinerary = create_itinerary(flights, hotels, new_attractions)
       print("Updated Itinerary:", new_itinerary)
```  
- **評価**：旅行代理店はユーザーフィードバックを分析し、推奨の関連性と正確性を継続的に評価し、必要な調整を行う。  
```python
       def adjust_preferences(preferences, feedback):
           if "liked" in feedback:
               preferences["favorites"] = feedback["liked"]
           if "disliked" in feedback:
               preferences["avoid"] = feedback["disliked"]
           return preferences

       preferences = adjust_preferences(preferences, feedback)
```  

#### 実践例  
以下は自己修正型RAGの最小ループ (plan/act/feedback/revise + 簡易評価) を明示した Travel Agent の実装です。計画セクションとの差異はフィードバックを再検索条件へ即時反映し再生成前後でスコア評価を行う点です。  
```python
from typing import Dict, Any

"""フェーズ対応表 (自己修正型RAG 最小ループ)
plan    : SelfCorrectingTravelAgent.__init__ 内 self.plan 定義
act     : run_once 内 retrieve / compose ステップ (外部取得と統合)
feedback: run_once 内 feedback ステップ (ユーザ/模擬フィードバック受理)
revise  : run_once 内 revise ステップ (prefs 更新 + 評価呼出)
evaluate: _evaluate メソッド (興味カバレッジ + ホテルスコア) と revise からの呼び出し
loop    : improve_until (閾値/最大反復制御による反復自己修正)
状態伝播: prefs -> 検索関数(search_hotels/search_attractions) で avoid/favorites を反映し次反復に影響
"""

def search_flights(p):
    return [{"id": "F1", "price": 500}]

def search_hotels(p):
    base = [{"name": "Central Hotel", "score": 7.2}]
    # avoid が含まれる場合は簡易フィルタ (再取得例)
    if p.get("avoid"):
        return [h for h in base if all(a not in h["name"] for a in p["avoid"]) ] or base
    return base

def search_attractions(p):
    data = ["Louvre Museum", "Seine Walk", "Eiffel Tower"]
    if p.get("avoid"):
        data = [d for d in data if all(a not in d for a in p["avoid"])]
    return data[:2]

def create_itinerary(flights, hotels, attractions):
    return {"flights": flights, "hotels": hotels, "attractions": attractions}

class SelfCorrectingTravelAgent:
    def __init__(self):
        self.prefs: Dict[str, Any] = {}              # 内部状態(ユーザ嗜好)
        self.plan = ["retrieve", "compose", "feedback", "revise"]  # plan: 明示的なサブタスク列
        self.state: Dict[str, Any] = {}
        self.score_history = []                      # 評価履歴 (自己修正の推移確認)

    def set_preferences(self, p):
        self.prefs = p

    def _evaluate(self):
        # evaluate: 興味タグ一致数 + ホテルスコア で簡易スコア化 (説明可能な軽量指標)
        interests = self.prefs.get("interests", [])
        attractions = self.state.get("attractions", [])
        cover = sum(1 for i in interests if any(i.lower().split()[0] in a.lower() for a in attractions))
        hotel_score = self.state.get("hotels", [{}])[0].get("score", 0)
        score = round(hotel_score + cover, 2)
        self.state["score"] = score
        self.score_history.append(score)

    def run_once(self, feedback=None):
        for step in self.plan:
            if step == "retrieve":
                # act/retrieve: 外部情報取得 (次反復で avoid/favorites が影響)
                self.state["flights"] = search_flights(self.prefs)
                self.state["hotels"] = search_hotels(self.prefs)
                self.state["attractions"] = search_attractions(self.prefs)
            elif step == "compose":
                # act/compose: 取得情報を統合し旅程構造化
                self.state["itinerary"] = create_itinerary(
                    self.state["flights"], self.state["hotels"], self.state["attractions"]
                )
            elif step == "feedback":
                # feedback: ユーザ or 模擬フィードバックを状態に取り込む
                self.state["feedback"] = feedback or {"liked": ["Louvre Museum"], "disliked": ["Eiffel Tower"]}
            elif step == "revise":
                # revise: フィードバックで prefs を更新し再取得条件を変化させる + 評価実施
                fb = self.state.get("feedback", {})
                # liked を favorites に、disliked を avoid に反映 (次回取得条件変化)
                if fb.get("liked"): self.prefs.setdefault("favorites", []).extend(fb["liked"])
                if fb.get("disliked"): self.prefs.setdefault("avoid", []).extend(fb["disliked"])
                self._evaluate()
        return self.state

    def improve_until(self, threshold=8.0, max_iters=3):
    # loop: しきい値到達または最大反復まで自己修正サイクルを回す
    for _ in range(max_iters):
            self.run_once()
            if self.state.get("score", 0) >= threshold:
                break
        return self.state

# 使用例
agent = SelfCorrectingTravelAgent()
agent.set_preferences({
    "destination": "Paris",
    "dates": "2025-04-01 to 2025-04-10",
    "budget": "moderate",
    "interests": ["museums", "cuisine"]
})
final_state = agent.improve_until(threshold=8.5)
print("最終スコア:", final_state.get("score"))
print("score履歴:", agent.score_history)
print("avoid:", agent.prefs.get("avoid"))
```

### 先取りコンテキストロード (Pre-emptive Context Load)
「先に関連知識を読み込んでおき、その後の個別クエリでは追加取得を最小化する」戦略です。RAGとの違いは「逐次必要な断片を取りに行く」か「最初に土台コンテキストを敷く」かのタイミング差です。

**利点**: 応答遅延の一貫性 / キャッシュヒット率向上 / 繰り返し質問での再取得削減  
**欠点**: 初期ロードが冗長化しやすい / 不要データ混入によるトークン浪費 / 動的差分取得が遅れる  

#### 簡易例
```python
class PreloadedTravelAgent:
    def __init__(self):
        # 代表的な都市情報を先読み（本番運用ではサイズ/鮮度/更新ポリシー管理が必要）
        self.context = {
            "Paris": {
                "country": "フランス",
                "language": "フランス語",
                "attractions": ["エッフェル塔", "ルーヴル美術館"]
            },
            "Tokyo": {
                "country": "日本",
                "language": "日本語",
                "attractions": ["浅草寺", "渋谷スクランブル交差点"]
            }
        }

    def get_destination_info(self, name: str):
        # 未登録の場合は空の辞書を返す
        return self.context.get(name, {})
```

### 目標ブートストラップ (Bootstrapping the Plan with a Goal)
反復に入る前に「達成したい評価基準/制約」を初期明示し、各ステップがゴール指標をどれだけ改善したかを観察できる形にします。

```python
class GoalBootstrappedPlanner:
    def __init__(self, candidates):
        self.candidates = candidates  # [{name, cost, activity}...]

    def bootstrap(self, prefs, budget):
        plan, total = [], 0
        for c in self.candidates:
            if total + c['cost'] <= budget and all(c.get(k) == v for k, v in prefs.items()):
                plan.append(c); total += c['cost']
        return plan

    def iterate(self, plan, prefs, budget):
        # 単純: 置換を一巡試行し改善 (コスト+嗜好一致) を優先
        for i, _ in enumerate(plan):
            for c in self.candidates:
                if c not in plan and all(c.get(k) == v for k, v in prefs.items()):
                    new_cost = sum(x['cost'] for x in plan) - plan[i]['cost'] + c['cost']
                    if new_cost <= budget:
                        plan[i] = c
                        break
        return plan
```

### LLMによるリランキングとスコアリング活用 (Re-ranking & Scoring)
まず検索で広く候補（安価なベクトル/キーワード検索）を集め、その後 LLM がユーザー意図や嗜好を踏まえて精密に再スコアし上位だけを残す二段構成です。 
これにより取りこぼしを避けつつノイズとトークンコストを削減し、スコア理由をログ化できるため精度・効率・説明可能性を同時に満たします。 
全体スコアが低い場合は「再検索/クエリ再生成」を発火させる品質ゲートとしても使えます。

#### Azure OpenAI を用いた簡易なプロンプト例
```python
def build_prompt(prefs, destinations):
    lines = ["ユーザー嗜好:"] + [f"- {k}: {v}" for k, v in prefs.items()]
    lines.append("\n候補:")
    for d in destinations:
        lines.append(f"- {d['name']}: {d['desc']}")
    lines.append("\n各候補を嗜好適合度(0-5)で評価し JSON 配列で返してください。")
    return "\n".join(lines)
```
> 実際のAPI呼び出し部分はエンドポイント/Keyの設定を行います。ここでは構造保持目的で省略しています。

#### Azure OpenAI を用いたRe-rankingの例
```python
import requests, json

class TravelAgentRerank:
    def __init__(self, destinations):
        self.destinations = destinations  # [{name, description}...]

    def generate_prompt(self, preferences):
        lines = ["Here are the travel destinations ranked and scored based on user preferences:"]
        for k, v in preferences.items():
            lines.append(f"{k}: {v}")
        lines.append("\nDestinations:")
        for d in self.destinations:
            lines.append(f"- {d['name']}: {d['description']}")
        return "\n".join(lines)

    def get_recommendations(self, preferences, api_key, endpoint):
        prompt = self.generate_prompt(preferences)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {"prompt": prompt, "max_tokens": 150, "temperature": 0.7}
        r = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        # 出力フォーマットの揺れ対策で行単位に分割
        lines = data.get('choices', [{}])[0].get('text', '').strip().split('\n')
        return [ln for ln in lines if ln.strip()]

# 利用例（endpoint / key は環境変数で保持するのが推奨）
destinations = [
    {"name": "Paris", "description": "芸術・ファッション・文化"},
    {"name": "Tokyo", "description": "近代性と伝統の融合"},
    {"name": "New York", "description": "多様性とランドマーク"},
    {"name": "Sydney", "description": "港とビーチ"},
]
preferences = {"activity": "sightseeing", "culture": "diverse"}  # culture=多様性志向
# agent = TravelAgentRerank(destinations)
# recs = agent.get_recommendations(preferences, api_key=..., endpoint=...)
# print(recs)  # LLM出力行をそのまま配列化した結果
```
> 注意: 本番では API キーを直接埋め込まず Key Vault / 環境変数で管理し、レート制限/エラーハンドリング(429/5xx再試行)を追加します。

### RAG: プロンプト技法 vs ツール化
最初はプロンプトを直接書き換えて「どの再書き換え・分割・要約・再ランキング観点が効くか」を素早く試し、その後に安定パターンを部品化してツールへ組み込みます。この段階的な移行で再現性と測定性を高めながら無駄な早期最適化を避けます。

**どちらを選ぶかの目安**
- ユーザー質問の種類や評価指標がまだ固まっていない段階ではプロンプト技法を使って試行回数を増やします。
- 同じ失敗分析（例: クエリ不足, 過剰取得）を繰り返している場合はその手順をツール内部の明示ステップへ昇格します。
- コストや応答時間を継続的に追跡したい場合はツール化して計測フック（ログ/指標）を標準化します。
- 出力品質の揺れを抑えチームで共有したい場合は頻出プロンプト断片をテンプレート化して埋め込みます。

**移行の流れ（例）**
1. 実験段階で入力プロンプト / 取得件数 / 回答 / 簡易指標（再現率, コスト）を記録します。
2. 10〜20回の試行で安定した再書き換え語彙や再ランキング観点を抽出します。
3. 抽出結果を `rewrite_query()`, `rerank(docs)`, `synthesize_answer()` など小さな関数に分離します。
4. 関数の入出力を JSON で記録し差分と回帰を後から追跡できるようにします。
5. 閾値（例: 再現率 < 0.6 または トークン当たりコスト > 許容量）を定義しガードを組み込みます。

**トレードオフ（簡潔まとめ）**
- プロンプト技法: 初期負担が低く高速に学習できますが、品質の揺れと属人化が起こりやすいです。
- ツール化: 実装初期コストは高いですが、再現性・監視性・拡張性を向上させます。

段階を *探索 → 抽象化 → インターフェース確立* と進めることで、早すぎる固定化と遅すぎる標準化の両方を避けられます。

#### 簡易コード対比
```python
# Prompting Technique
def search_museums_in_paris():
    q = "Find top museums in Paris"
    return web_search(q)

# Tool 化 (内部で embedding→retrieve→rerank を隠蔽)
class RAGTool:
    def retrieve_and_generate(self, user_input: str):
        docs = retrieve(user_input)
        return synthesize_answer(user_input, docs)
```

### 関連性評価 (Evaluating Relevancy)
ここでいう関連性は単一指標ではなく、(1) ユーザー意図に合っているか、(2) 記述が事実と矛盾しないか、(3) 必要な観点をどれだけ網羅しているか、(4) 余分な重複が抑えられているか、の複合観点で判断します。下の簡易 `relevance_score` は最小例であり、実運用では重み付けや減点（例: ノイズ語含有, 重複度）を追加します。

```python
def relevance_score(item, query):
    score = 0
    # 嗜好カテゴリ適合: 興味一覧に含まれるか
    if item.get('category') in query.get('interests', []):
        score += 1
    # 予算制約: 価格が最大許容以下か
    if item.get('price', 10**9) <= query.get('budget_max', 10**9):
        score += 1
    # 目的地一致: ロケーションが指定目的地か
    if item.get('location') == query.get('destination'):
        score += 1
    return score

def filter_and_rank(items, query):
    # スコア降順で上位10件を返します
    ranked = sorted(items, key=lambda x: relevance_score(x, query), reverse=True)
    return ranked[:10]
```

### 意図にもとづく検索 (Search with Intent)
この小節ではクエリの「意図」を簡易分類して、検索戦略（クエリ書き換えや検索対象）を切り替える最小構成の例を示します。単純な文字列検索だけでは目的の異なる要求（学びたい / 公式サイトへ行きたい / 予約したい）が同じ処理に流れ、不要な結果やコスト増につながるため、先に意図を推定して分岐します。

分類は次の三つを扱います。
1. Informational: 何かを理解したい・比較したい要求です（例: "best museums in Kyoto"）。広めの語を補強し要約性と網羅性を高めるクエリへ拡張します。
2. Navigational: 特定の既知サイトや公式リソースへ到達したい要求です（例: "kyoto city official website"）。過度な書き換えは避け、原文または最小限の正規化のみを行います。
3. Transactional: 予約・購入・申し込みなど行動完了を狙う要求です（例: "book kyoto ryokan"）。動詞（book, buy など）や時期情報を強調して実行可能な検索語を組み立てます。

以下は単純なキーワード判定による例です。実運用では以下を追加します。
- 形態素解析または埋め込み類似度による動詞・目的語抽出
- LLM への少量プロンプトでのラベル推定と信頼度しきい値
- 不確実ラベル (low_confidence) へのフォールバック処理

この段階で信頼度を付与しておくと、後段の再ランキングやメタ認知評価で「意図誤分類による失敗パターン」を切り分けやすくなります。

```python
def classify_intent(text: str):
    """非常に単純なヒューリスティック分類です。信頼度は未実装なので実運用では必ず補強します。"""
    lowered = text.lower()
    if any(k in lowered for k in ["book", "purchase", "reserve", "buy"]):
        return "transactional"
    if any(k in lowered for k in ["official", "website", "portal"]):
        return "navigational"
    return "informational"

def rewrite_query(query: str, intent: str, prefs):
    """意図に応じた検索語最適化を行います。最低限の例です。"""
    if intent == "informational":
        # 興味分野と地点を組み合わせ広めに探索します
        return f"best {prefs['interests'][0]} in {prefs['destination']}"
    if intent == "navigational":
        # 原文を尊重し過剰拡張を避けます
        return query
    # transactional: 予約・購入行為を明示します
    return f"book {prefs['destination']} {prefs['dates']}"

def search_with_intent(query: str, prefs):
    intent = classify_intent(query)
    rewritten = rewrite_query(query, intent, prefs)
    # 実際には intent と rewritten をログへ記録して後続のメタ認知評価に利用します
    return web_search(rewritten)
```



## ツールとしてのコード生成  
コード生成エージェントはAIモデルを使ってコードを書き、実行し、複雑な問題を解決したりタスクを自動化したりします。  

この節は直前まで扱ってきた「計画 → 実行 → 評価 → 改良」のメタ認知ループを、テキスト回答ではなく“検証可能なコード資産”に適用した拡張です。評価指標がテスト・型・静的解析・実行ログといった自動化可能なシグナルに置き換わる点が本質的な違いです。ここではその橋渡しとして、同じループ構造がどのようにコード生成に再利用されるかを最小構成で示します。  

### コード生成エージェント  
コード生成エージェントは生成AIモデルを用いてコードを生成・実行します。これにより複雑な問題を解決し、タスクを自動化し、多様なプログラミング言語でコードを生成・実行して有益な洞察を提供します。  

#### 実用的な応用例  
1. **自動コード生成**：データ分析、ウェブスクレイピング、機械学習など特定のタスク向けのコードスニペットを生成。  
2. **RAGとしてのSQL**：データベースからデータを取得・操作するためにSQLクエリを使用。  
3. **問題解決**：アルゴリズム最適化やデータ分析など特定の問題を解決するコードを作成・実行。  

#### 例：データ分析用コード生成エージェント  
コード生成エージェントを設計する場合の例：  
1. **タスク**：データセットを分析し、傾向やパターンを特定。  
2. **ステップ**：  
- データセットをデータ分析ツールに読み込む。  
- データをフィルタリング・集約するSQLクエリを生成。  
- クエリを実行し結果を取得。  
- 結果を使って可視化や洞察を生成。  
3. **必要リソース**：データセット、データ分析ツール、SQL機能へのアクセス。  
4. **経験**：過去の分析結果を利用し、将来の分析の精度と関連性を向上。  

### 例：Travel Agent用コード生成エージェント  
この例では、ユーザーの旅行計画を支援するためにコード生成エージェントTravel Agentを設計します。このエージェントは旅行オプションの取得、結果のフィルタリング、旅程の作成などを生成AIで行います。  

#### コード生成エージェントの概要  
1. **ユーザーの好み収集**：目的地、旅行日程、予算、興味などのユーザー入力を収集。  
2. **データ取得用コード生成**：フライト、ホテル、観光地に関するデータを取得するコードスニペットを生成。  
3. **生成コードの実行**：生成したコードを実行し、リアルタイム情報を取得。  
4. **旅程生成**：取得したデータをまとめてパーソナライズされた旅行プランを作成。  
5. **フィードバックに基づく調整**：ユーザーフィードバックを受け取り、必要に応じてコードを再生成し結果を改善。  

#### 実装ステップ  
1. **ユーザーの好み収集**  
```python
class Travel_Agent:
    def __init__(self):
        self.user_preferences = {}

    def gather_preferences(self, preferences):
        self.user_preferences = preferences
```
2. **データ取得用コード生成**  
```python
def generate_code_to_fetch_data(preferences):
    # フライト検索用コード文字列を生成
    code = f"""
def search_flights():
    import requests
    response = requests.get('https://api.example.com/flights', params={preferences})
    return response.json()
"""
    return code

def generate_code_to_fetch_hotels(preferences):
    # ホテル検索用コード文字列を生成
    code = f"""
def search_hotels():
    import requests
    response = requests.get('https://api.example.com/hotels', params={preferences})
    return response.json()
"""
    return code
```
3. **生成コードの実行**  
```python
def execute_code(code):
    # 生成したコードを実行
    exec(code, globals())
    return {k: v for k, v in globals().items() if k.startswith('search_')}

travel_agent = Travel_Agent()
preferences = {
    "destination": "Paris",
    "dates": "2025-04-01 to 2025-04-10",
    "budget": "moderate",
    "interests": ["museums", "cuisine"]
}
travel_agent.gather_preferences(preferences)

flight_code = generate_code_to_fetch_data(preferences)
hotel_code = generate_code_to_fetch_hotels(preferences)

exec_env_flights = execute_code(flight_code)
exec_env_hotels = execute_code(hotel_code)
print("生成されたフライト取得関数キー:", list(exec_env_flights.keys()))
print("生成されたホテル取得関数キー:", list(exec_env_hotels.keys()))
```
4. **旅程生成**  
```python
def generate_itinerary(flights, hotels, attractions):
    return {"flights": flights, "hotels": hotels, "attractions": attractions}

# ダミー呼び出し（実際は search_* 関数結果を使用）
flights = [{"id": "F100", "price": 480}]
hotels = [{"name": "Central Hotel", "price": 150}]
attractions = ["Louvre Museum", "Seine Walk"]
itinerary = generate_itinerary(flights, hotels, attractions)
print("提案旅程:", itinerary)
```
5. **フィードバックに基づく調整**  
```python
def adjust_based_on_feedback(feedback, preferences):
    if feedback.get("liked"):
        preferences["favorites"] = feedback["liked"]
    if feedback.get("disliked"):
        preferences["avoid"] = feedback["disliked"]
    return preferences

feedback = {"liked": ["Louvre Museum"], "disliked": ["Eiffel Tower (too crowded)"]}
updated_preferences = adjust_based_on_feedback(feedback, preferences)
print("更新後のユーザー嗜好:", updated_preferences)
```

### 環境認識と推論の活用  
テーブルのスキーマに基づくことで、環境認識と推論を活用したクエリ生成プロセスを強化できます。以下はその例です：  
1. **スキーマの理解**：システムがテーブルのスキーマを理解し、クエリ生成の基盤とする。  
2. **フィードバックに基づく調整**：フィードバックに基づきユーザーの好みを調整し、スキーマのどのフィールドを更新すべきか推論。  
3. **クエリの生成と実行**：調整された好みに基づき、更新されたフライト・ホテルデータを取得するクエリを生成・実行。  

以下はこれらの概念を組み込んだPythonコード例：
```python
def adjust_based_on_feedback(feedback, preferences, schema):
    # フィードバック内容に基づき嗜好を更新
    if "liked" in feedback:
        preferences["favorites"] = feedback["liked"]
    if "disliked" in feedback:
        preferences["avoid"] = feedback["disliked"]
    # スキーマに基づく推論で関連フィールドも調整
    for field in schema:
        if field in preferences:
            preferences[field] = adjust_based_on_environment(feedback, field, schema)
    return preferences

def adjust_based_on_environment(feedback, field, schema):
    # スキーマ＋フィードバックに基づくカスタム調整ロジック
    if field in feedback["liked"]:
        return schema[field]["positive_adjustment"]
    elif field in feedback["disliked"]:
        return schema[field]["negative_adjustment"]
    return schema[field]["default"]

def generate_code_to_fetch_data(preferences):
    # 更新後嗜好に基づきフライト取得コード（呼び出し文字列）を生成
    return f"fetch_flights(preferences={preferences})"

def generate_code_to_fetch_hotels(preferences):
    # 更新後嗜好に基づきホテル取得コード（呼び出し文字列）を生成
    return f"fetch_hotels(preferences={preferences})"

def execute_code(code):
    # コード実行をシミュレートしモックデータを返す
    return {"data": f"Executed: {code}"}

def generate_itinerary(flights, hotels, attractions):
    # フライト・ホテル・観光地を統合して旅程生成
    return {"flights": flights, "hotels": hotels, "attractions": attractions}

# スキーマ例
schema = {
    "favorites": {"positive_adjustment": "increase", "negative_adjustment": "decrease", "default": "neutral"},
    "avoid": {"positive_adjustment": "decrease", "negative_adjustment": "increase", "default": "neutral"}
}

# 利用例
preferences = {"favorites": "観光スポット巡り", "avoid": "混雑した場所"}
feedback = {"liked": ["ルーヴル美術館"], "disliked": ["エッフェル塔 (混雑しすぎ) "]}
updated_preferences = adjust_based_on_feedback(feedback, preferences, schema)

# 更新された嗜好に基づきコードを再生成・実行
updated_flight_code = generate_code_to_fetch_data(updated_preferences)
updated_hotel_code = generate_code_to_fetch_hotels(updated_preferences)

updated_flights = execute_code(updated_flight_code)
updated_hotels = execute_code(updated_hotel_code)

updated_itinerary = generate_itinerary(updated_flights, updated_hotels, feedback["liked"])
print("更新後旅程:", updated_itinerary)
```

#### 説明 - フィードバックに基づく予約  
1. **スキーマ認識**：`schema` はフィードバックにもとづき嗜好をどのように調整するかを定義する辞書で、`favorites` や `avoid` などのフィールドとその調整方針を持つ。  
2. **嗜好調整 (`adjust_based_on_feedback` メソッド)**：ユーザーフィードバックとスキーマ規則を参照し、該当する嗜好フィールドを更新する。  
3. **環境ベース調整 (`adjust_based_on_environment`)**：スキーマとフィードバックに基づいて関連フィールドの値を最適化。  
4. **クエリ生成と実行**：調整された好みに基づき、フライト・ホテルデータを取得するコードを生成し、クエリの実行をシミュレート。  
5. **旅程生成**：新しいフライト、ホテル、観光地データに基づいて更新された旅程を作成。  

環境認識とスキーマに基づく推論を活用することで、より正確で関連性の高いクエリを生成でき、より良い旅行推奨とパーソナライズされたユーザー体験が実現します。  

#### 失敗パターンと世界モデルによる対処一覧  
環境モデルを明示的に持たない場合に起こりやすい失敗と、それを抑えるためにどの状態フィールドを管理し何を更新するかを整理しました。表の文は簡潔にし、後工程の自動化（SQL条件最適化やコード生成）でそのまま利用しやすい形にしています。  

| 失敗パターン | 症状 | 関連状態 | 検出条件例 | 主な更新タイミング | 対処 | 改善後の状態 |
|--------------|------|----------|------------|----------------|------|----------------|
| 嗜好を再入力させてしまう | 毎回「静かなホテル」を聞き直します | `inferred_preferences` | 直近N発話で同義表現を複数検出 | ユーザー発話直後 | `ambience=quiet` を保存し検索条件へ追加します | 同じ希望を再質問しません |
| 禁止条件を反映しない | avoid:crowded を無視した案を提示します | `avoid`, `change_log` | 提示候補に禁止語が含まれます | 検索直前 | 最新 `avoid` 差分をフィルタへ再適用します | 禁止条件違反案が除外されます |
| 全体を無駄に再計算する | 1ホテル変更で旅程全再生成します | `change_log` | 変更要素=1 かつ 再計算範囲>50% | 差分検出時 | 影響範囲を特定し該当部分のみ再生成します | 無関係部分は保持されます |
| レート制限を連続発生 | API エラーが連続します | `resources.api_remaining` | 残回数 < 閾値 | 各API後 | キャッシュ/要約モードへ切り替えます | エラー頻度が低下します |
| 改善理由が説明できない | スコア変化の原因不明です | `evaluation_metrics`, `change_log` | スコア差>=閾値 且つ 原因未記録 | 評価後 | 指標→更新項目 の対応を記録します | ログに改善理由が残ります |
| 検索が過剰または不足 | 取得件数過多や0件です | `context_quality` | 重複率>30% または カバレッジ<閾値 | 取得直後 | 上限縮小 / クエリ語彙拡張を行います | 件数と重複率が許容内に収まります |
| 嗜好を再度質問する | 既知の予算を再質問します | `user_preferences` | 質問候補キーが既存です | 質問生成前 | 既存キーを質問候補から除外します | 不要な再質問が消えます |
| 予算制約が崩れる | 予算超過案を提示します | `user_preferences`, `change_log` | 案合計 > 予算値 | プラン生成直前 | 予算超過案を除外し代替を挿入します | 予算内案のみ提示されます |
| 過去回避を忘れる | 除外済み候補が再出現します | `change_log`, `avoid` | 候補ID が除外リストに存在 | 候補マージ時 | ブラックリスト照合で除外します | 再提示が発生しません |

最初は `user_preferences`, `inferred_preferences`, `avoid`, `resources`, `change_log` の5項目から始めます。必要になった段階で `evaluation_metrics` と `context_quality` を追加すると複雑さを抑えながら拡張できます。  

用語補足: 「除外候補ID」はユーザーが不要または避けたいと明示/暗示したホテルやフライト等の内部識別子です。会話メッセージIDではありません。再提示防止と「なぜ除外されたか」を説明する根拠として利用します。  

### RAG技術としてのSQLの活用  
（導入）メタ認知で得た「どの条件が失敗に寄与したか」を再現・検証するには構造化取得が有効です。SQL を加える主目的は以下の3点です。
1. 再現性: クエリそのものが実験条件の完全記録となり、後で同一条件比較が容易になります。
2. 条件単位評価: WHERE / JOIN / LIMIT 等ごとに行数・重複率・カバレッジ指標を記録し、過剰/不足/冗長を局所修正できます。
3. コスト最適化: 不要列除去やフィルタ順序変更を試行し、トークン消費・IO削減効果を数値で追跡できます。

SQL（構造化問い合わせ言語）はデータベース操作に強力なツールです。Retrieval-Augmented Generation（RAG）アプローチの一部として使用すると、SQLはデータベースから関連データを取得し、AIエージェントの応答や行動生成に役立ちます。Travel Agentの文脈でSQLをRAG技術として活用する方法を見てみましょう。  

#### 主要概念  
1. **データベースとのやり取り**：  
- SQLはデータベースにクエリを送り、関連情報を取得・操作する。  
- 例：旅行データベースからフライト詳細、ホテル情報、観光地を取得。  

2. **RAGとの統合**：  
- SQLクエリはユーザー入力や好みに基づいて生成される。  
- 取得したデータはパーソナライズされた推奨や行動生成に使用される。  

3. **動的クエリ生成**：  
- AIエージェントは文脈やユーザーのニーズに応じて動的にSQLクエリを生成。  
- 例：予算、日程、興味に基づいて結果を絞り込むSQLクエリのカスタマイズ。  

#### 応用例  
- **自動コード生成**：特定タスク向けコードスニペットの生成。  
- **RAGとしてのSQL**：データ操作にSQLクエリを使用。  
- **問題解決**：問題解決のためのコード生成・実行。  

#### 例：Travel AgentにおけるSQL活用  
1. **ユーザーの好み収集**  
```python
class Travel_Agent:
    def __init__(self):
        self.user_preferences = {}

    def gather_preferences(self, preferences):
        self.user_preferences = preferences
```
2. **SQLクエリ生成**  
```python
def generate_sql_query(table: str, preferences: dict) -> str:
    # 簡易: 文字列埋め込み（本番はパラメータバインドでSQLインジェクション対策）
    conditions = []
    for key, value in preferences.items():
        if isinstance(value, list):
            # リスト型は ANY 相当に単純化（実装学習目的の簡略版）
            joined = ",".join([str(v) for v in value])
            conditions.append(f"{key} IN ({joined})")
        else:
            conditions.append(f"{key} = '{value}'")
    where = " AND ".join(conditions) if conditions else "1=1"
    return f"SELECT * FROM {table} WHERE {where};"
```
3. **SQLクエリ実行**  
```python
import sqlite3
from contextlib import closing

def execute_sql_query(query: str, database: str = "travel.db"):
    with closing(sqlite3.connect(database)) as conn:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
    return rows
```
4. **推奨生成**  
```python
def generate_recommendations(preferences: dict):
    flight_query = generate_sql_query("flights", preferences)
    hotel_query = generate_sql_query("hotels", preferences)
    attraction_query = generate_sql_query("attractions", preferences)

    flights = execute_sql_query(flight_query)
    hotels = execute_sql_query(hotel_query)
    attractions = execute_sql_query(attraction_query)

    return {"flights": flights, "hotels": hotels, "attractions": attractions}

travel_agent = Travel_Agent()
preferences = {
    "destination": "Paris",
    "dates": "2025-04-01_to_2025-04-10",  # 例: フォーマットはDBスキーマ前提で調整
    "budget": "moderate",
    "interests": ["museums", "cuisine"]
}
travel_agent.gather_preferences(preferences)
itinerary = generate_recommendations(preferences)
print("生成された旅程:", itinerary)
```

SQLをRetrieval-Augmented Generation（RAG）技術の一部として活用することで、Travel AgentのようなAIエージェントは関連データを動的に取得・活用し、正確かつパーソナライズされた推奨を提供できます。  

#### SQLクエリ例 (Example SQL Queries)
英語版の例示クエリを対応する形で掲載します。

```sql
-- フライト
SELECT * FROM flights WHERE destination='Paris' AND dates='2025-04-01_to_2025-04-10' AND budget='moderate';

-- ホテル
SELECT * FROM hotels WHERE destination='Paris' AND budget='moderate';

-- 観光地 (interests は正規化テーブルであれば JOIN へ変換推奨)
SELECT * FROM attractions WHERE destination='Paris' AND interests='museums, cuisine';
```


### コード生成とメタ認知・SQLの統合
この小節ではメタ認知で得た「何をどの順で改善するか」という抽象的判断を、再利用できるコード生成ステップと SQL による測定基盤へ写像して継続的改善ループを確立します。目的は判断を一度きりの思いつきで終わらせず、(1) ログ化 → (2) 条件別指標抽出 → (3) 自動パッチ提案 → (4) 指標比較 → (5) 受け入れ/却下 の形に固定化して再現性と監視性を高めることです。下の表は自動化対象と入力・指標・発火条件を要約したものです。

| 目的 | 自動生成対象 | 主な入力 | 代表指標 | 典型トリガー |
|------|--------------|----------|----------|--------------|
| 取得精度向上 | 改訂SQLクエリ / 条件ビルダ | 失敗パターンログ, 条件別行数 | 重複率, 網羅性, 行数閾値 | 行数0/過多, 重複超過 |
| 戦略検証 | 評価スクリプト / 集計コード | 実行履歴(journal) | 改善率, 再現性 | 指標停滞/退行 |
| 応答品質改善 | プロンプト / テンプレ差分 | フィードバック要約 | 引用率, 嗜好反映率 | 引用欠落, 嗜好未反映 |
| 安全性向上 | サニタイズ / 検証関数 | 例外ログ | 失敗率, 型整合率 | 例外頻発, 型不一致 |


### メタ認知の例  
ここでは前段で定義した評価指標やログ化の仕組みをすでに読んでいることを前提に、抽象概念（振り返りループ）を具体的な動作手順へ写像する位置付けを採っています。評価指標と失敗パターンの説明を先に済ませることで例中の戦略切替理由が直感的に理解しやすくなります。  
メタ認知の実装例を示すため、問題解決中に*自身の意思決定プロセスを振り返る*単純なエージェントを作成します。  
この例では、エージェントがホテルの選択を最適化しようと試み、誤った選択や最適でない選択をした場合に自身の推論を評価し、戦略を調整します。基本例として、価格と品質の組み合わせでホテルを選択しつつ、決定を「振り返り」、必要に応じて調整します。  

#### メタ認知の説明  
1. **初期決定**：エージェントは品質の影響を理解せずに最も安いホテルを選択。  
2. **振り返りと評価**：初期選択後、ユーザーフィードバックを用いてそのホテルが「悪い」選択かをチェック。品質が低すぎる場合、自身の推論を振り返る。  
3. **戦略調整**：振り返りに基づき戦略を「最安値」から「最高品質」に切り替え、将来の意思決定を改善。  

例：
```python
# === 手法ラベル凡例 ===
# [計画] 戦略や手順を事前に定義/選択する部分
# [メタ認知] 自身の過去判断を評価し戦略切替を行う部分
# [自己修正型RAG] 取得→生成→評価→改良のループ要素（本例では取得/生成を簡略化）
# [環境認識] 過去状態や履歴を内部構造に保持/参照する部分
# [コード生成] 戦略分岐ロジックや改善アクションをコードとして組み立てる部分
# [SQL構造化] （本例には登場しないが）条件ごとの行数・指標取得を行う層

class HotelRecommendationAgent:
    def __init__(self):
        # [環境認識] 過去に選んだホテル（戦略, 候補）
        self.previous_choices = []
        # [環境認識] 戦略調整後に再評価された選択
        self.corrected_choices = []
        # [計画] 利用可能な推奨戦略（事前に定義した戦略空間）
        self.recommendation_strategies = ['cheapest', 'highest_quality']

    def recommend_hotel(self, hotels, strategy: str):
        """与えられた戦略（'cheapest' または 'highest_quality'）に基づき候補を1件選ぶ。 [計画][コード生成]
        （戦略に応じた評価関数を分岐させる“手続き”をコード化）"""
        if strategy == 'cheapest':
            recommended = min(hotels, key=lambda x: x['price'])
        elif strategy == 'highest_quality':
            recommended = max(hotels, key=lambda x: x['quality'])
        else:
            recommended = None
        # [環境認識] 戦略と結果を履歴に記録
        self.previous_choices.append((strategy, recommended))
        return recommended

    def reflect_on_choice(self):
        """直近の選択を振り返り不満足なら戦略を切り替える。 [メタ認知]
        （評価→判断→方針切替の小さいループ）"""
        if not self.previous_choices:
            return "まだ選択がありません。"

        last_choice_strategy, last_choice = self.previous_choices[-1]
        # [自己修正型RAG] 簡易フィードバック取得（実際はユーザー入力や外部評価に相当）
        user_feedback = self.get_user_feedback(last_choice)

        if user_feedback == "bad":
            # [メタ認知] 評価結果が不十分なら別の戦略へ切り替える（改善アクション選択）
            new_strategy = 'highest_quality' if last_choice_strategy == 'cheapest' else 'cheapest'
            # [環境認識] 修正履歴に保存（後続分析・再学習の基盤）
            self.corrected_choices.append((new_strategy, last_choice))
            return f"選択を振り返り、戦略を {new_strategy} に切り替えます。"
        else:
            return "前回の選択は良好です。戦略変更は不要です。"

    def get_user_feedback(self, hotel: dict):
    """ユーザーフィードバックを模倣する簡易ルールです。 [自己修正型RAG(簡略)]
    役割:
    - 取得 相当: すでに選択されたホテルの属性 (price, quality) を読むだけで外部検索は行っていません。
    - 評価 相当: 閾値を下回る品質や極端な低価格を "bad" として改善トリガにします。
    - 改良 相当: 実際の改良処理は reflect_on_choice 内で別の戦略へ切り替える処理として行われます。
    この最小例は RAG の構造 (retrieve→generate→evaluate→revise) を教育目的で圧縮した形です。実運用では:
    1. 外部データ源 / 検索 / ベクトルインデックスから候補取得（取得）
    2. LLM やルールで多次元スコアリング（評価）
    3. クエリ / プロンプト / 戦略関数を再生成（改良）
    4. 評価ログや指標を永続保存し次回意思決定へ利用（環境認識）
    へ拡張します。"""
        if hotel['price'] < 100 or hotel['quality'] < 7:
            return "bad"
        return "good"


# サンプル: 価格と品質を持つホテル候補リスト
hotels = [
    {'name': 'Budget Inn', 'price': 80, 'quality': 6},
    {'name': 'Comfort Suites', 'price': 120, 'quality': 8},
    {'name': 'Luxury Stay', 'price': 200, 'quality': 9}
]

# エージェント生成
agent = HotelRecommendationAgent()

# Step 1: 最初は最安戦略 [計画 初期方針設定]
recommended_hotel = agent.recommend_hotel(hotels, 'cheapest')
print(f"初回推奨(cheapest): {recommended_hotel['name']}")

# Step 2: 振り返りと必要に応じた戦略調整 [メタ認知 評価→方針再決定]
reflection_result = agent.reflect_on_choice()
print(reflection_result)

# Step 3: 調整後の戦略で再推奨 [自己修正型RAG 改良フェーズ再実行]
adjusted_recommendation = agent.recommend_hotel(hotels, 'highest_quality')
print(f"調整後推奨(highest_quality): {adjusted_recommendation['name']}")
```

#### エージェントのメタ認知能力  
ここまでの例は、過去の意思決定を整理して評価し、必要なら戦略を切り替えて次の結果を改善するための最小構成を示しています。目的は精緻な内省ではなく、効果の出る調整を再現可能な手順として固定することです。以下でその流れ（記録 → 評価 → 判断 → 改良 → 学習基盤化）を分解します。 

構造を分解すると次の流れになります。  
1. 記録: `previous_choices` が（戦略, 結果）ペアを保存します（環境認識）。  
2. 評価: `get_user_feedback` が閾値ルールで良否を返し改善トリガを生成します（自己修正型RAGの簡略評価）。  
3. 判断: `reflect_on_choice` が評価結果を読み取り方針を維持するか別の戦略へ切り替えるかを選びます（メタ認知）。  
4. 改良: 戦略を切り替えて再推薦し新しい結果を取得します（計画の再適用）。  
5. 学習基盤化: 修正結果を `corrected_choices` に追記して将来の分析や統計化に備えます。  

内部状態は次の二層に分かれます。  
- 短期状態: 直近の選択（前回戦略とホテル）。  
- 累積状態: すべての選択履歴と修正履歴。これにより「どの戦略が何回失敗し戦略変更に至ったか」といった頻度統計を後で算出できます。  

失敗検出（bad 判定）は現状では単純閾値ですが、実運用では以下へ拡張します。  
- 重み付き総合スコア: 多次元指標（価格 / 品質 / レビュー / 距離 など）を 0〜1 に正規化し、重要度を表す重みを掛けて足し合わせた合計値を用います（例: 総合 = 0.40*価格スコア + 0.35*品質 + 0.15*レビュー + 0.10*距離）。この方式を「重み付き合算」と呼び、指標間の重要度バランスを明示的に制御します。  
- ペアワイズ比較: LLM に 2 つの候補を同時に提示し「どちらが目的（例: 快適さと費用対効果）により適しているか。その理由は何か」を返させ、勝者を記録して相対順位を構築します。これを複数組み合わせると安定したランキングを得ます。  
- 戦略と結果のクロス集計: SQL で戦略と結果カテゴリ（例: good / bad や三段階満足度）の組み合わせ頻度を集計し、一定の不合格率や連続失敗回数が閾値を超えた際に「切り替え判定の基準値」（例: 連続失敗許容回数）を最近の実績に合わせて自動更新します。  

改善アクションも単純な二択の単純切り替えから次のように段階化できます。  
- 優先順位調整（例: 価格→品質→立地の重み配分を段階的に変更します）。  
- クエリや取得条件を一時的に緩めて、ジャンルや価格帯の異なる候補も取得し、同質な候補に偏って局所的最適に陥る状況を避けます（候補の多様性確保）。  
- 再ランキング基準の挿入（例: 快適度指標を追加して総合スコアを再計算します）。  

観測→評価→調整のループをコードとして明示化する利点は次の通りです。  
- 再現性: 同じ入力条件なら同じ改善手順を踏みます。  
- 監視容易性: どの判定が何回改善を引き起こしたかを履歴から追跡できます。  
- 拡張性: 評価器と戦略集合を差し替えてもフレームワーク部分を維持できます。  

次の成熟段階の例を示します。  
| 段階 | 評価手段 | 戦略集合 | 改善判定条件 | 追加で観測する指標 |
|------|----------|----------|----------------|------------------|
| 最小 (本例) | 閾値ルール | 二択 (最安 / 最高品質) | 不適判定 (bad) が発生 | 戦略変更回数 |
| 拡張1 | 多次元重み付き総合スコア | 3～5 戦略 | 総合スコア差が目標閾値を下回る | 戦略別成功率 |
| 拡張2 | LLM 二者比較 + ルール補助 | 動的生成（重み再最適化） | 改善率停滞が N 回連続 | 収束までの試行数 |
| 拡張3 | A/B 試験 + 統計検定 + SQL 集計 | 逐次探索最適化（バンディット手法） | 統計的有意差を確認 | p値 / 後悔指標 (累積 regret) |

※ 用語補足: 「多次元重み付き総合スコア」は各指標を 0〜1 に正規化し重みを掛けて合算した値です。  
※ 「LLM 二者比較」は二つの候補を同時提示してどちらが要求に適合し理由は何かを回答させ順位を構築します。  
※ 「逐次探索最適化（バンディット手法）」は試行ごとに学習しながら探索と活用の配分を調整して累積の後悔（本来得られた最良報酬との差）を最小化します。  
※ 「後悔指標」は理想的に常に最良戦略を選んだ場合との差分を累積し、改善速度を評価する指標です。  

このようにメタ認知は「高コストな完全内省」ではなく、小さく検証可能な改善手続きを積み上げる設計として具体化できます。  

## 結論  
本章で扱った要点は「観測→評価→判断→改良→記録」を明示し、改善ロジックを一度限りの試行錯誤で終わらせず再現可能な仕組みへ固定することです。メタ認知は抽象的な“内省”ではなく、測れる指標を用いて方針を継続的に調整する運用上の仕組みとして具体化します。  

導入時はまず戦略と結果の履歴を蓄積し、重複率・網羅性・戦略変更回数・連続失敗回数など基本指標を計算し、連続不適などの閾値を超えたら戦略や重みを切り替えて効果を同じ指標で検証します。 成熟は「単純閾値と手動確認」→「重み付き総合スコアと自動切替」→「二者比較や A/B と統計的有意差および後悔指標による探索と活用の最適化」という段階で進めます。 立ち上げでは履歴構造追加→失敗分類→切替条件コード化→前後比較の順で最小ループを固め、成功は不適率低下・網羅性向上・重複率と連続失敗の縮減・平均取得コスト削減など複数指標の改善で判断します。

これらを小さく回し、改善ロジック自体をコードとして資産化することで、安定性と適応性を同時に高められます。次章ではこれを本番運用へ拡張し、コスト・安全性・監視との統合を進めます。  
## 前のレッスン  
[マルチエージェントデザインパターン](../08-multi-agent/README.md)  
## 次のレッスン  
[AIエージェントの実運用](../10-ai-agents-production/README.md)

**免責事項**：  
本書類はAI翻訳サービス「[Co-op Translator](https://github.com/Azure/co-op-translator)」を使用して翻訳されました。正確性を期しておりますが、自動翻訳には誤りや不正確な部分が含まれる可能性があることをご了承ください。原文の言語で記載されたオリジナルの文書が正式な情報源とみなされます。重要な情報については、専門の人間による翻訳を推奨します。本翻訳の利用により生じたいかなる誤解や解釈違いについても、当方は一切の責任を負いかねます。