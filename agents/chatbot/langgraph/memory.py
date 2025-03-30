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
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver


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


chat_model = ChatTongyi(
    model="qwen-plus",
    temperature=0.5,
    api_key=TONGYI_API_KEY
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    chat_model.invoke(state["messages"])
    return {"messages": [chat_model.invoke(state["messages"])]}

# 初始化 SQLiteSaver
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

def build_graph():
    graph_builder = StateGraph(State)
    
    graph_builder.add_node("chatbot", chatbot)
    
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    
    return graph_builder.compile(checkpointer=memory)


    
def main():
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("goodbye!")
            break
        
        graph = build_graph()

        config = {"configurable": {"thread_id": "1"}}
        events = graph.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )

        for event in events:
            event["messages"][-1].pretty_print()

if __name__ == "__main__":
    main()