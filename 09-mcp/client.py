import asyncio
from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
import os
from dotenv import load_dotenv

load_dotenv()

async def local_mcp_example():
    """Example using a local MCP server via stdio."""
    async with (
        MCPStdioTool(
            name="calculator", 
            command="uv", 
            args=["run", "--directory", os.environ.get("MCP_SERVER_BASE_DIR"), "stdio-server.py"]
        ) as mcp_server,
        ChatAgent(
            chat_client=AzureOpenAIChatClient(credential=AzureCliCredential()),
            name="MathAgent",
            instructions="You are a helpful math assistant that can solve calculations.",
        ) as agent,
    ):
        result = await agent.run(
            "What is 100 + 200 - 50", 
            tools=mcp_server
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(local_mcp_example())