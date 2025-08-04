import asyncio
from typing import List
from mcp.server.fastmcp import FastMCP, Context
from webscout import YepSearch

# 初始化 FastMCP 服务器
mcp = FastMCP("yep-search")

# MCP工具：使用YepSearch进行网页搜索并返回格式化结果
@mcp.tool()
async def search(query: str, ctx: Context, max_results: int = 5) -> str:
    """
    使用YepSearch进行网页搜索并返回格式化结果。

    参数:
        query: 搜索关键词
        max_results: 返回的最大结果数（默认10）
        ctx: MCP日志上下文
    """
    try:
        yep = YepSearch(
            timeout=120,
            proxies=None,
            verify=False
        )
        await ctx.info(f"正在YepSearch搜索: {query}")
        # YepSearch为同步接口，这里用线程池异步化
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(
            None,
            lambda: list(
                yep.text(
                    query,
                    region="all",
                    safesearch="moderate",
                    max_results=max_results
                )
            )
        )
        if not search_results:
            return "未找到任何搜索结果。"
        output = []
        output.append(f"共找到 {len(search_results)} 条搜索结果：\n")
        for idx, result in enumerate(search_results, 1):
            output.append(f"{idx}. {result.get('title', '')}")
            output.append(f"   URL: {result.get('href', '')}")
            output.append(f"   摘要: {result.get('body', '')}")
            output.append("")  # 结果间空行
        await ctx.info(f"成功找到 {len(search_results)} 条结果")
        return "\n".join(output)
    except Exception as e:
        await ctx.error(f"搜索时发生错误: {str(e)}")
        return f"搜索时发生错误: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()