import os
import sys
import json
import anyio

from openai import OpenAI
from mcp import Client, StdioServerParameters
from mcp.types import TextContent


llm = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

MODEL = "deepseek-flash"
MAX_STEPS = 10
INSTRUCTIONS = "你是一个问答 Agent。需要时请调用可用工具。"

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

async def main():

    async with Client(server) as mcp_client:

        # ① 从 MCP Server 自动发现工具
        mcp_tools_result = await mcp_client.list_tools()

        tools = [
            mcp_tool_to_llm_tool(tool)
            for tool in mcp_tools_result.tools
        ]

        print("Agent 可用工具：")
        for tool in tools:
            print("-", tool["name"])

        prompt = input("\n请输入问题：")

        context = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        for step in range(1, MAX_STEPS + 1):

            print(f"\n======== Step {step} ========")

            # ② LLM 根据 MCP 提供的工具定义自主决策
            response = llm.responses.create(
                model=MODEL,
                instructions=INSTRUCTIONS,
                input=context,
                tools=tools,
                parallel_tool_calls=False,
            )

            calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not calls:
                print("\nAgent 最终回答：")
                print(response.output_text)
                break

            tool_outputs = []

            for call in calls:
                args = json.loads(call.arguments)

                print("Tool:", call.name)
                print("Args:", args)

                try:
                    # ③ 不再 execute_tool()
                    # 直接通过 MCP 调用
                    result = await mcp_client.call_tool(
                        call.name,
                        args,
                    )

                    result_text = mcp_result_to_text(result)

                except Exception as e:
                    result_text = f"Tool execution failed: {e}"

                print("Result:")
                print(result_text)

                # ④ MCP 的结果仍然以 function_call_output
                # 交还给 LLM
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": result_text,
                })

            context.extend(
                item.model_dump(exclude_none=True)
                for item in response.output
            )

            context.extend(tool_outputs)

        else:
            print("达到最大步骤数，强制结束。")


if __name__ == "__main__":
    anyio.run(main)