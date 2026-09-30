import sys
import anyio

from mcp import Client, StdioServerParameters
from mcp.types import TextContent


server = StdioServerParameters(
    command=sys.executable,
    args=["mcp_server.py"],
)


async def main():
    async with Client(server) as client:

        # 1. 自动发现 MCP Server 提供的工具
        result = await client.list_tools()

        print("=== Tools ===")

        for tool in result.tools:
            print("name:", tool.name)
            print("description:", tool.description)
            print("input_schema:", tool.input_schema)
            print()

        # 2. 调用其中一个工具
        # result = await client.call_tool(
        #     "search_knowledge",
        #     {
        #         "query": "RAG 基本流程",
        #         "top_k": 3,
        #     }
        # )

        result = await client.call_tool(
            "echo",
            {
                "message": "Hello, MCP Server!",
            }
        )

        print("=== Result ===")

        for block in result.content:
            if isinstance(block, TextContent):
                print(block.text)


if __name__ == "__main__":
    anyio.run(main)