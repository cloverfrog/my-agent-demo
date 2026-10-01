import os
import sys
import json
import anyio
import operator
from typing import TypedDict, Annotated

from openai import AsyncOpenAI
from mcp import Client, StdioServerParameters
from mcp.types import TextContent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

MODEL = "deepseek-flash"
INSTRUCTIONS = "你是一个问答 Agent。需要时请调用可用工具。"

class AgentState(TypedDict):
    context: Annotated[list[dict], operator.add]
    pending_calls: list[dict]
    final_answer: str

mcp_client: Client
tools: list[dict]

server = StdioServerParameters(
    command=sys.executable,
    args=["mcp_server.py"],
)

def mcp_tool_to_llm_tool(tool):
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description or "",
        "parameters": tool.input_schema,
    }

def mcp_result_to_text(result) -> str:
    texts = []

    for block in result.content:
        if isinstance(block, TextContent):
            texts.append(block.text)

    return "\n".join(texts)

llm = AsyncOpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)
async def agent_node(state: AgentState):
    response = await llm.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        input=state["context"],
        tools=tools,
        parallel_tool_calls=False,
    )

    output_items = [
        item.model_dump(exclude_none=True)
        for item in response.output
    ]

    calls = []

    for item in response.output:
        if item.type == "function_call":
            calls.append({
                "name": item.name,
                "arguments": json.loads(item.arguments),
                "call_id": item.call_id,
            })

    return {
        "context": output_items,
        "pending_calls": calls,
        "final_answer": response.output_text,
    }

async def tool_node(state: AgentState):
    tool_outputs = []

    for call in state["pending_calls"]:

        print("Tool:", call["name"])
        print("Args:", call["arguments"])

        try:
            result = await mcp_client.call_tool(
                call["name"],
                call["arguments"],
            )

            result_text = mcp_result_to_text(result)

        except Exception as e:
            result_text = f"Tool execution failed: {e}"

        print("Result:")
        print(result_text)

        tool_outputs.append({
            "type": "function_call_output",
            "call_id": call["call_id"],
            "output": result_text,
        })

    return {
        "context": tool_outputs,
        "pending_calls": [],
    }

def should_continue(state: AgentState):
    if state["pending_calls"]:
        return "tools"

    return END

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END],
)

builder.add_edge(
    "tools",
    "agent",
)

# graph = builder.compile()

async def main():
    global mcp_client, tools

    async with Client(server) as client:
        mcp_client = client

        # MCP 自动发现工具
        result = await mcp_client.list_tools()

        tools = [
            mcp_tool_to_llm_tool(tool)
            for tool in result.tools
        ]

        print("Agent 可用工具：")

        for tool in tools:
            print("-", tool["name"])

        async with AsyncSqliteSaver.from_conn_string(
            "agent_checkpoints.db"
        ) as checkpointer:
            await checkpointer.setup()
            
            graph = builder.compile(checkpointer=checkpointer)

            prompt = input("\n请输入问题：")

            config = {
                "configurable": {
                    "thread_id": "demo-thread"
                },
                "recursion_limit": 10,
            }

            result = await graph.ainvoke(
                {
                    "context": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "pending_calls": [],
                    "final_answer": "",
                },
                config=config
            )

            print("\nAgent 最终回答：")
            print(result["final_answer"])

if __name__ == "__main__":
    anyio.run(main)