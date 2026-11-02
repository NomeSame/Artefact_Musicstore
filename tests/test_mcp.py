"""Real MCP subprocess handshake and shared tool execution."""
import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def test_stdio_handshake_and_public_tools():
    async def run():
        parameters=StdioServerParameters(command=sys.executable,
            args=[str(Path(__file__).resolve().parents[1] / "run_mcp.py")],env=dict(os.environ))
        async with stdio_client(parameters) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                names={tool.name for tool in tools.tools}
                assert names=={"search_products","get_product","lookup_policy"}
                result=await session.call_tool("get_product",{"product_id":81,"payment":"pix"})
                assert not result.isError
                assert '"product_id": 81' in result.content[0].text
                assert '"price_cents": 56991' in result.content[0].text
    asyncio.run(run())
