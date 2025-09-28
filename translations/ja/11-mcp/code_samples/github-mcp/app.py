"""学習 / 指導向け GitHub MCP マルチエージェント サンプル
===============================================================

本ファイルは Semantic Kernel + Chainlit + Model Context Protocol (MCP) +
簡易 RAG（検索拡張生成）を組み合わせた、現実的かつ最小構成の
マルチエージェント オーケストレーション パターンを示します。

重要タグ（コード内検索用）:
    [AGENT]               : 各エージェント（専門役割）の定義箇所
    [MCP PLUGIN]          : 外部 GitHub MCP サーバーをツール提供元として接続
    [RAG FUNCTION]        : LLM から呼ばれる検索拡張関数
    [GROUP ORCHESTRATION] : 複数エージェントを逐次協調実行する部分
    [ROUTING]             : 単一/複数エージェントを切り替える簡易キーワードルータ
    [FUNCTION CALL STREAM]: ストリーミング内での関数/ツール呼び出し可視化

高レベル実行フロー:
1. 環境変数読込 & ロギング初期化
2. Azure Cognitive Search の小規模インデックスを作成 / Markdown 取り込み
3. RAGPlugin の search_events を登録 (FunctionChoiceBehavior.Auto で LLM が自動利用可)
4. GitHub MCP プラグイン(Node) を stdio で起動しツール群を Kernel に追加
5. 3 つの専門エージェント: GitHub 解析 / ハッカソン案出し / イベント推薦
6. 複数領域要求時は順序 (GitHub → Hackathon → Events) で連鎖実行
7. 入力文をキーワード判定し単独ストリーミング or 連鎖
8. 関数呼び出し/結果を逐次表示し透明性を確保
9. セッション終了時に MCP 接続をクリーンにクローズ

学習用途のためコメントは冗長です。実運用では削除/要約してください。
"""

import os
import json
import logging
import re
from dotenv import load_dotenv
import requests

import chainlit as cl
from mcp import ClientSession

from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.agents.strategies import (
        SequentialSelectionStrategy,
        DefaultTerminationStrategy,
)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchFieldDataType,
        SearchableField,
)


###############################################################################
# 環境 & ロギング設定
###############################################################################
# override=True: ワークショップ等でローカル .env を確実に優先させるため
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


###############################################################################
# [RAG FUNCTION] 軽量検索拡張プラグイン
# search_events 関数 1 つのみ公開:
#   (a) 小規模 Azure Cognitive Search インデックス検索
#   (b) Devpost Hackathon API ライブ取得
# モデルはイベント情報が必要と判断したタイミングで自律的に呼び出せる。
###############################################################################
class RAGPlugin:
    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    @kernel_function(name="search_events", description="技術キーワードに基づきインデックス + ライブ API から関連イベントを取得します。")
    def search_events(self, query: str) -> str:
        """クエリに一致するインデックスイベント + ライブ Hackathon 情報を統合して返す。

        学習用に例外も文字列へ吸収。実運用ではログ区別・構造化を推奨。
        """
        context_parts: list[str] = []
        # Index lookup
        try:
            results = self.search_client.search(query, top=5)
            for r in results:
                if "content" in r:
                    context_parts.append(f"インデックスイベント: {r['content']}")
        except Exception as e:  # noqa: BLE001 – 教育用簡略化
            context_parts.append(f"[インデックス検索エラー] {e}")
        # Live API augmentation
        try:
            resp = requests.get(
                f"https://devpost.com/api/hackathons?search={query}", timeout=5
            )
            if resp.ok:
                data = resp.json()
                for event in data.get("hackathons", [])[:5]:
                    context_parts.append(
                        f"ライブイベント: {event.get('title')} - {event.get('url')}"
                    )
        except Exception as e:  # noqa: BLE001
            context_parts.append(f"[ライブ API エラー] {e}")
        return "\n\n".join(context_parts) if context_parts else "関連イベントは見つかりませんでした。"


###############################################################################
# Azure Cognitive Search (デモ用トイインデックス)
###############################################################################
search_service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "event-descriptions"

search_client = SearchClient(
    endpoint=search_service_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_api_key)
)

index_client = SearchIndexClient(
    endpoint=search_service_endpoint,
    credential=AzureKeyCredential(search_api_key)
)

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String)
]

index = SearchIndex(name=index_name, fields=fields)

try:  # 冪等なセットアップ (既存なら再利用)
    index_client.get_index(index_name)
    print(f"インデックス '{index_name}' は既に存在するため再利用します。")
except Exception:  # noqa: BLE001
    print(f"インデックス '{index_name}' を作成します…")
    index_client.create_index(index)

current_dir = os.path.dirname(os.path.abspath(__file__))
event_descriptions_path = os.path.join(current_dir, "event-descriptions.md")

try:
    with open(event_descriptions_path, "r", encoding='utf-8') as f:
        markdown_content = f.read()
except FileNotFoundError:
    logger.warning(f"Could not find {event_descriptions_path}")
    markdown_content = ""

event_descriptions = markdown_content.split("---")

documents = []
for i, description in enumerate(event_descriptions):
    description = description.strip()
    if description:
        documents.append({"id": str(i + 1), "content": description})

if documents:
    # 簡易リフレッシュ: 既存削除 (失敗は警告のみ) → 再アップロード
    try:
        search_client.delete_documents(documents=[{"id": d["id"]} for d in documents])
        print("既存ドキュメントを削除しました。")
    except Exception as e:  # noqa: BLE001
        print(f"警告: 削除失敗 (続行します): {e}")
    search_client.upload_documents(documents)
    print(f"{len(documents)} 件のドキュメントをアップロードしました。")

def flatten(xss):  # noqa: D401 – 現在未使用 (参考用)
    """二次元リストをフラット化 (学習用プレースホルダ)。"""
    return [x for xs in xss for x in xs]

###############################################################################
# [MCP PLUGIN] 接続確立時にツールメタデータを取得・キャッシュ。
# どのツール呼び出しがどの MCP セッションに属するか逆引きできるようにする。
###############################################################################
@cl.on_mcp_connect
async def on_mcp(connection, session: ClientSession):
    logger.info(f"MCP 接続確立: {connection.name}")
    result = await session.list_tools()
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in result.tools
    ]

    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)

    print(f"[MCP] 利用可能ツール ({connection.name}):")
    for tool in tools:
        print(f"  · {tool['name']}: {tool['description']}")

###############################################################################
# MCP ツール実行ステップ (Chainlit 上で可視化)
# モデルが MCP プラグイン経由ツールを呼び出した際に実行される。
###############################################################################
@cl.step(type="tool")
async def call_tool(tool_use):
    tool_name = tool_use.name
    tool_input = tool_use.input
    step = cl.context.current_step
    step.name = tool_name

    mcp_tools = cl.user_session.get("mcp_tools", {})
    target_conn = None
    for conn_name, tools in mcp_tools.items():
        if any(t.get("name") == tool_name for t in tools):
            target_conn = conn_name
            break
    if not target_conn:
        step.output = json.dumps({"error": f"ツール '{tool_name}' はどの MCP 接続にも存在しません"})
        return step.output

    mcp_session, _ = cl.context.session.mcp_sessions.get(target_conn)
    if not mcp_session:
        step.output = json.dumps({"error": f"MCP セッション '{target_conn}' が見つかりません"})
        return step.output

    try:
        step.output = await mcp_session.call_tool(tool_name, tool_input)
    except Exception as e:  # noqa: BLE001
        step.output = json.dumps({"error": f"ツール実行エラー: {e}"})
    return step.output

###############################################################################
# チャットセッション初期化
###############################################################################
@cl.on_chat_start
async def on_chat_start():
    # 1. Kernel と LLM サービス登録
    kernel = Kernel()
    service_id = "default-openai"
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
    # モデルが利用可能関数(プラグイン)を自動選択できるようにする
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # 2. RAG プラグイン登録
    rag_plugin = RAGPlugin(search_client)
    kernel.add_plugin(rag_plugin, plugin_name="RAG")

    # 3. MCP GitHub プラグイン (外部ツール提供元)
    try:
        logger.info("GitHub MCP プラグイン起動 (stdio)...")
        github_plugin = MCPStdioPlugin(
            name="GitHub",
            description="GitHub repository exploration tools",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
        )
        await github_plugin.connect()
        kernel.add_plugin(github_plugin)
        logger.info("GitHub MCP プラグイン接続 & 追加完了")
    except Exception as e:  # noqa: BLE001
        logger.error(f"GitHub MCP プラグイン初期化失敗: {e}")
        github_plugin = None

    # 4. エージェント指示 (日本語化)
    GITHUB_INSTRUCTIONS = (
        "あなたは GitHub リポジトリ解析の専門家です。必ずユーザーが指定した GitHub ユーザー名のみを使い、" \
        "推測や網羅的検索は行いません。取得対象: (a) リポジトリ所有者, (b) 主要言語, (c) README / ファイル上の顕著情報。" \
        "引用する各リポジトリには直接 URL を付けます。ユーザー名が無い場合は生成せず要求してください。"
    )

    HACKATHON_INSTRUCTIONS = (
        "あなたは AI エージェント系ハッカソン戦略アドバイザーです。ユーザーの GitHub 実績(リポジトリ/言語)" \
        "に厳密に基づき創造的な AI エージェント案を提示します。各案には: 短い名称 / 問題設定 / アーキテクチャ概要 / 推奨言語とツール / " \
        "該当し得る Microsoft AI Agent Hackathon 賞カテゴリと根拠 / 参照した具体的リポジトリ or 言語 を含めます。汎用的助言は避けます。"
    )

    EVENTS_INSTRUCTIONS = (
        "あなたは イベント推薦エージェントです。選ばれたプロジェクト案に含まれる技術語を使ってまず search_events 関数を呼び出し、" \
        "その返却結果に含まれるイベントのみ推薦します。各イベントがプロジェクトにどのように直接関連するか説明し、見つからなければ" \
        "代替検索キーワードを提案します (捏造禁止)。"
    )

    # 5. エージェント定義
    # [AGENT] GitHub 解析 (MCP GitHub ツール利用)
    github_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="GitHubAgent",
        instructions=GITHUB_INSTRUCTIONS,
        plugins=[github_plugin] if github_plugin else [],
    )
    # [AGENT] ハッカソン案出し
    hackathon_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="HackathonAgent",
        instructions=HACKATHON_INSTRUCTIONS,
    )
    # [AGENT] イベント推薦 (RAG 検索利用)
    events_agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="EventsAgent",
        instructions=EVENTS_INSTRUCTIONS,
        plugins=[rag_plugin],
    )

    # 6. マルチエージェント協調
    # [GROUP ORCHESTRATION]
    agent_group_chat = AgentGroupChat(
        agents=[github_agent, hackathon_agent, events_agent],
        selection_strategy=SequentialSelectionStrategy(initial_agent=github_agent),
        termination_strategy=DefaultTerminationStrategy(maximum_iterations=3),
    )

    # 7. ストリーミング用共有状態
    chat_history = ChatHistory()

    # セッションオブジェクト保存
    cl.user_session.set("kernel", kernel)
    cl.user_session.set("settings", settings)
    cl.user_session.set("chat_completion_service", AzureChatCompletion())
    cl.user_session.set("chat_history", chat_history)
    cl.user_session.set("mcp_tools", {})
    cl.user_session.set("agent_group_chat", agent_group_chat)
    cl.user_session.set("rag_plugin", rag_plugin)
    cl.user_session.set("github_plugin", github_plugin)

###############################################################################
# セッションクリーンアップ
###############################################################################
@cl.on_chat_end
async def on_chat_end():
    github_plugin = cl.user_session.get("github_plugin")
    if github_plugin:
        try:
            await github_plugin.close()
            print("GitHub MCP プラグインをクローズしました")
        except Exception as e:  # noqa: BLE001
            print(f"GitHub MCP プラグイン終了エラー: {e}")

###############################################################################
# [ROUTING] 簡易キーワードヒューリスティック。
# 高度化案: 分類器導入 / コーディネータ LLM に決定させる 等。
###############################################################################
def route_user_input(user_input: str):
    text = user_input.lower()
    selected = []
    if re.search(r"github|repo|repository|commit|pull request", text):
        selected.append("GitHubAgent")
    if re.search(r"hackathon|project idea|competition|challenge|win", text):
        selected.append("HackathonAgent")
    if re.search(r"event|conference|meetup|workshop|webinar", text):
        selected.append("EventsAgent")
    return selected or ["GitHubAgent", "HackathonAgent", "EventsAgent"]

###############################################################################
# メッセージハンドラ
# 複数領域 → マルチエージェント連鎖 / 単一 → 通常ストリーミング + 関数呼び出し表示
###############################################################################
@cl.on_message
async def on_message(message: cl.Message):
    kernel = cl.user_session.get("kernel")
    chat_service = cl.user_session.get("chat_completion_service")
    chat_history: ChatHistory = cl.user_session.get("chat_history")
    settings = cl.user_session.get("settings")
    agent_group_chat: AgentGroupChat = cl.user_session.get("agent_group_chat")

    user_text = message.content
    target_agents = route_user_input(user_text)
    chat_history.add_user_message(user_text)

    # マルチエージェント経路
    if len(target_agents) > 1:
        await agent_group_chat.add_chat_message(user_text)
        msg = cl.Message(content=f"マルチエージェント実行: {', '.join(target_agents)}\n\n")
        await msg.send()
        collected = []
        try:
            async for content in agent_group_chat.invoke():
                name = content.name or "Agent"
                line = f"**{name}**: {content.content}"
                collected.append(line)
                await msg.stream_token(line + "\n\n")
            final = "\n\n".join(collected)
            chat_history.add_assistant_message(final)
            msg.content = final
            await msg.update()
        except Exception as e:  # noqa: BLE001
            err = f"マルチエージェント実行中エラー: {e}"
            await msg.stream_token("\n\n❌ " + err + "\n")
            chat_history.add_assistant_message(err)
            msg.content += "\n\n❌ " + err
            await msg.update()
        return

    # シングルエージェント経路
    agent_name = target_agents[0]
    msg = cl.Message(content=f"{agent_name} を使用します…\n\n")
    await msg.send()
    try:  # [FUNCTION CALL STREAM] 関数 / ツール呼び出しを逐次表示
        async for part in chat_service.get_streaming_chat_message_content(
            chat_history=chat_history,
            user_input=user_text,
            settings=settings,
            kernel=kernel,
        ):
            if part.content:
                await msg.stream_token(part.content)
            if isinstance(part, FunctionCallContent):
                await msg.stream_token(
                    f"\n\n[関数呼び出し] {part.function_name} 引数={part.arguments}\n"
                )
            if isinstance(part, FunctionResultContent):
                await msg.stream_token(
                    f"\n[関数結果]\n{part.content}\n"
                )
        chat_history.add_assistant_message(msg.content)
        await msg.update()
    except Exception as e:  # noqa: BLE001
        await msg.stream_token(f"\n\n❌ エラー: {e}\n")
        chat_history.add_assistant_message(f"Error: {e}")
        msg.content += f"\n\n❌ エラー: {e}"
        await msg.update()

# ファイル終端 (学習用に明示的に区切り)


    HACKATHON_AGENT = """
あなたは AI エージェント系ハッカソンで勝てる提案を行う戦略アドバイザーです。

タスク:
1. ユーザーの GitHub 活動を分析して技術スキルを把握します。
2. そのスキルに適した創造的な AI エージェントプロジェクトを提案します。
3. Microsoft の AI Agent Hackathon の賞カテゴリと整合させます。

提案の指針:
- ユーザーのリポジトリ、言語、ツールの実績に厳密に基づきます。
- 使用を推奨する言語、ツール、フレームワークを具体的に示します。
- アーキテクチャと実装アプローチを含む詳細な説明を提供します。
- どの賞カテゴリを狙えるか理由を述べます。
- 参照したリポジトリや言語を明示します。

出力形式:
- プロジェクト名
- プロジェクト概要
- 推奨言語・ツール
- 参照リポジトリのリンク
"""

    EVENTS_AGENT = """
あなたは 技術イベント推薦エージェントです。
1. Hackathon Agent の提案したプロジェクト概要を読みます。
2. search_events 関数を使い関連イベントを検索します。
3. ユーザーが実際に使った技術と無関係なイベントを推薦しません。
4. search_events が返していないイベントを捏造しません。

手順:
- まずプロジェクト内の具体的技術キーワードを用いて search_events を呼び出します。
- 必要であれば複数クエリを試します。

イベント出力:
- 返却されたイベントのみ列挙して関連性を説明します。
- 見つからない場合は代替クエリを提案します。
"""

    github_agent = ChatCompletionAgent(
        service=chat_service,
        name="GithubAgent",
        instructions=GITHUB_INSTRUCTIONS,
        plugins=[github_plugin]
    )

    hackathon_agent = ChatCompletionAgent(
        service=chat_service,
        name="HackathonAgent",
        instructions=HACKATHON_AGENT
    )

    events_agent = ChatCompletionAgent(
        service=chat_service,
        name="EventsAgent",
        instructions=EVENTS_AGENT,
        plugins=[rag_plugin]
    )

    agent_group_chat = AgentGroupChat(
        agents=[github_agent, hackathon_agent, events_agent],
        selection_strategy=SequentialSelectionStrategy(initial_agent=github_agent),
        termination_strategy=DefaultTerminationStrategy(maximum_iterations=3)
    )

    chat_history = ChatHistory()

    cl.user_session.set("kernel", kernel)
    cl.user_session.set("settings", settings)
    cl.user_session.set("chat_completion_service", chat_service)
    cl.user_session.set("chat_history", chat_history)
    cl.user_session.set("mcp_tools", {})
    cl.user_session.set("agent_group_chat", agent_group_chat)

@cl.on_chat_end
async def on_chat_end():
    github_plugin = cl.user_session.get("github_plugin")
    if github_plugin:
        try:
            await github_plugin.close()
            print("GitHub プラグインを正常にクローズしました。")
        except Exception as e:
            print(f"GitHub プラグイン終了時のエラー: {str(e)}")

def route_user_input(user_input: str):
    """ユーザー入力を解析して起動すべきエージェント名リストを返します。"""
    user_input_lower = user_input.lower()
    agents = []
    # GitHub 関連キーワード（日本語も追加）
    if re.search(r"github|repo|repository|commit|pull request|リポジトリ", user_input_lower):
        agents.append("GitHubAgent")
    # ハッカソン関連（日本語も追加）
    if re.search(r"hackathon|project idea|competition|challenge|win|ハッカソン|アイデア|企画|コンテスト", user_input_lower):
        agents.append("HackathonAgent")
    # イベント関連（日本語も追加）
    if re.search(r"event|conference|meetup|workshop|webinar|イベント|勉強会|カンファレンス|ワークショップ", user_input_lower):
        agents.append("EventsAgent")
    if not agents:
        agents = ["GitHubAgent", "HackathonAgent", "EventsAgent"]
    return agents

@cl.on_message
async def on_message(message: cl.Message):
    kernel = cl.user_session.get("kernel")
    chat_completion_service = cl.user_session.get("chat_completion_service")
    chat_history = cl.user_session.get("chat_history")
    settings = cl.user_session.get("settings")
    agent_group_chat = cl.user_session.get("agent_group_chat")

    user_input = message.content
    agent_names = route_user_input(user_input)

    chat_history.add_user_message(message.content)

    if len(agent_names) > 1:
        await agent_group_chat.add_chat_message(message.content)
        answer = cl.Message(content=f"次のエージェントで処理します: {', '.join(agent_names)}...\n\n")
        await answer.send()
        agent_responses = []
        try:
            async for content in agent_group_chat.invoke():
                agent_name = content.name or "Agent"
                response = f"**{agent_name}**: {content.content}"
                agent_responses.append(response)
                await answer.stream_token(f"{response}\n\n")
            full_response = "\n\n".join(agent_responses)
            chat_history.add_assistant_message(full_response)
            answer.content = full_response
            await answer.update()
        except Exception as e:
            await answer.stream_token(f"\n\nエラー: {str(e)}\n\n")
            chat_history.add_assistant_message(f"Error: {str(e)}")
            answer.content += f"\n\nエラー: {str(e)}"
            await answer.update()
    else:
        agent_name = agent_names[0]
        answer = cl.Message(content=f"{agent_name} で処理します...\n\n")
        await answer.send()
        try:
            async for msg in chat_completion_service.get_streaming_chat_message_content(
                chat_history=chat_history,
                user_input=message.content,
                settings=settings,
                kernel=kernel,
            ):
                if msg.content:
                    await answer.stream_token(msg.content)
                if isinstance(msg, FunctionCallContent):
                    await answer.stream_token(f"\n\n関数呼び出し: {msg.function_name} 引数: {msg.arguments}\n\n")
                if isinstance(msg, FunctionResultContent):
                    await answer.stream_token(f"関数結果: {msg.content}\n\n")
            chat_history.add_assistant_message(answer.content)
            await answer.update()
        except Exception as e:
            await answer.stream_token(f"\n\nエラー: {str(e)}\n\n")
            chat_history.add_assistant_message(f"Error: {str(e)}")
            answer.content += f"\n\nエラー: {str(e)}"
            await answer.update()
