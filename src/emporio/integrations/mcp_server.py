"""Thin MCP stdio adapter. No additional machine or public port required."""
import asyncio
import json
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
from emporio.web.app import ROOT
from emporio.data.catalog import Catalog
from emporio.data.policies import Policies
from emporio.agent.tools import Tools

async def serve():
    # A separate derived DB avoids rebuilding the web process's database.
    tools = Tools(Catalog(ROOT / "data", ROOT / ".runtime" / "mcp.sqlite3"),
                  Policies(ROOT / "data" / "políticas_da_loja.pdf"))
    server = Server("emporio-musicstore")

    @server.list_tools()
    async def list_tools():
        # Private orders stay in the verified browser session. Navigation is browser-local.
        return [Tool(name=t["name"], description=t["description"], inputSchema=t["input_schema"], outputSchema=t["output_schema"])
                for t in tools.catalog_schema() if t["name"] not in {"get_order", "navigate_catalog"}]

    @server.call_tool()
    async def call_tool(name, arguments):
        if name in {"get_order", "navigate_catalog"}:
            result = {"error": "browser_session_required",
                      "message": "Private orders and UI navigation are available in the web session only."}
        else:
            result = tools.execute(name, arguments)
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
                              structuredContent=result, isError=bool(result.get("error")))

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(serve())
