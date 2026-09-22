from mcp.server import MCPServer

from rag import retrieve


mcp = MCPServer("my-agent-demo")


@mcp.tool()
def search_knowledge(query: str, top_k: int = 3) -> str:
    """在本地知识库中搜索与查询相关的内容。"""

    results = retrieve(query, top_k=top_k)

    return "\n\n".join(
        f"[来源: {r['source']}]\n{r['text']}"
        for r in results
    )


if __name__ == "__main__":
    mcp.run()