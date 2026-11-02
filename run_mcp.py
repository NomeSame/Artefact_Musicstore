"""Start the local MCP stdio adapter from the repository root."""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from emporio.integrations.mcp_server import serve

if __name__ == "__main__":
    asyncio.run(serve())
