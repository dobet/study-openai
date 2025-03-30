import os
import json
from typing import Annotated
from typing_extensions import TypedDict
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import ToolMessage, BaseMessage
from langfuse.callback import CallbackHandler
from langgraph.checkpoint.memory import MemorySaver

# ============= 配置部分 =============
# 环境变量配置
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "chatbot"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["TAVILY_API_KEY"] = "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"

# API密钥配置
TAVILY_API_KEY = "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"
TONGYI_API_KEY = "sk-cbb67cfa61024480a7f514c0888cca43"
LANGFUSE_PUBLIC_KEY = "pk-lf-42535dbc-90d1-4fd8-9081-949489e81d1d"
LANGFUSE_SECRET_KEY = "sk-lf-f315da72-7c36-428c-9e34-dd33bd797b00"
LANGFUSE_HOST = "http://192.168.116.142:3000"

# ============= 类型定义 =============
class State(TypedDict):
    messages: Annotated[list, add_messages]

# ============= 工具类 =============
class BasicToolNode:
    def __init__(self, tools: list):
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, input: dict):
        if messages := input.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No messages provided")

        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
            )

        return {"messages": outputs}

# ============= 图构建相关函数 =============
def route_tools(state: State):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"输入状态中未找到消息: {state}")
    
    if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
        return "tools"
    return "__end__"

def chatbot(state: State):
    llm_with_tools = chat_model.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke(state["messages"], config={"callbacks": [langfuse_handler]})]}

def build_graph(memory: MemorySaver = None):
    graph_builder = StateGraph(State)
    
    # 添加节点
    graph_builder.add_node("chatbot", chatbot)
    tool_node = BasicToolNode(tools)
    graph_builder.add_node("tools", tool_node)
    
    # 添加边
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        {
            "tools": "tools",
            "__end__": "__end__"
        },
    )
    graph_builder.add_edge("tools", "chatbot")
    if memory is not None:
        return graph_builder.compile(checkpointer=memory, interrupt_before=["tools"])
    else:
        return graph_builder.compile()

def display_graph():
    memaid_code = graph.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(memaid_code)

    img = mpimg.imread("graph.png")
    plt.imshow(img)
    plt.axis("off")
    plt.show()

# ============= 初始化配置 =============
# 初始化Langfuse回调
langfuse_handler = CallbackHandler(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

# 初始化聊天模型
chat_model = ChatTongyi(
    model="qwen-plus",
    temperature=0.5,
    api_key=TONGYI_API_KEY
)

# 初始化工具
tool = TavilySearchResults(max_results=2)
tools = [tool]

# 构建记忆存储
memory = MemorySaver()

# 构建图
graph = build_graph(memory)





# ============= 主程序 =============
def main():
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("goodbye!")
            break
        
        config = {"configurable": {"thread_id": "1"}}
        events = graph.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )

        for event in events:
            event["messages"][-1].pretty_print()

        # for event in graph.stream({"messages": [user_input]}, config, stream_mode="values"):
        #     for value in event.values():
        #         if (
        #             isinstance(value, dict) 
        #             and "messages" in value 
        #             and value["messages"] 
        #             and isinstance(value["messages"][-1], BaseMessage)
        #         ):
        #             print("Assistant: ", value["messages"][-1].content)
        #         else:
        #             event["messages"][-1].pretty_print()

if __name__ == "__main__":
    # display_graph()  # 取消注释以显示图
    main()
            