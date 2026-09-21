import os
import json
from openai import OpenAI

from tools import read_file, write_file, run_tests

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

MODEL = "deepseek-flash"
INSTRUCTIONS = """
你是一个代码修复 Agent。

你的目标是修复 target 项目，使所有 pytest 测试通过。

项目包含：
- calculator.py
- test_calculator.py

你可以读取文件、修改文件以及运行测试。

规则：
1. 在不了解代码时，先读取相关文件。
2. 修改代码后必须运行测试验证。
3. 只有测试全部通过后，任务才算成功。
4. 不要修改测试来让错误代码通过测试。
"""
TOOLS = [
    {
        "type": "function",
        "name": "read_file",
        "description": "读取 target 目录中的一个文件。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相对于 target 目录的文件路径，例如 calculator.py"
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "覆盖写入 target 目录中的一个文件。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string"
                },
                "content": {
                    "type": "string"
                }
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "run_tests",
        "description": "运行 target 项目的 pytest，并返回测试结果。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_knowledge",
        "description": "在知识库中搜索相关内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的结果数量，默认为 3",
                    "default": 3
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]
MAX_STEPS = 10

def execute_tool(name: str, arguments: dict) -> str:
    if name == "read_file":
        return read_file(**arguments)

    if name == "write_file":
        return write_file(**arguments)

    if name == "run_tests":
        return run_tests()

    raise ValueError(f"Unknown tool: {name}")

context = [
    {
        "role": "user",
        "content": "修复这个项目，使所有测试通过。"
    }
]

for step in range(1, MAX_STEPS + 1):
    print(f"\n======== Step {step} ========")

    response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        input=context,
        tools=TOOLS,
        parallel_tool_calls=False,
    )

    calls = [
        item
        for item in response.output
        if item.type == "function_call"
    ]

    # 没有工具调用：说明 Agent 决定结束
    if not calls:
        print("\nAgent 最终回答：")
        print(response.output_text)
        break

    tool_outputs = []

    for call in calls:
        args = json.loads(call.arguments)

        print(f"Tool: {call.name}")
        print(f"Args: {args}")

        try:
            result = execute_tool(call.name, args)
        except Exception as e:
            result = f"Tool execution failed: {e}"

        print(f"Result:\n{result}")

        tool_outputs.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": result,
        })

    context.extend(
        item.model_dump(exclude_none=True)
        for item in response.output
    )
    context.extend(tool_outputs)

else:
    print("\n达到最大步骤数，强制结束。")