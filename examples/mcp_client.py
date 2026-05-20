"""Tiny MCP client example for the local tradingbot MCP server."""

from __future__ import annotations

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="python3",
        args=["-m", "binance_paper_assistant.mcp_server"],
        env={"PYTHONPATH": "src"},
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            result = await session.call_tool(
                "generate_market_report",
                arguments={"symbol": "SOLUSDT", "interval": "15m"},
            )

            print("\nMarket report:")
            print(json.dumps(result.structuredContent, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
