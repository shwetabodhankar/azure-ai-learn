#!/usr/bin/env python3
"""
Fixed MCP Client that uses direct Python execution instead of 'uv'.
This version should work with your current Python setup.
"""
import asyncio
import os
from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
import sys

load_dotenv()

async def fixed_mcp_example():
    """Fixed MCP example using direct Python execution."""
    print("🔧 Fixed MCP Client Example")
    print("=" * 40)
    
    # Get the current Python executable
    python_exe = sys.executable
    server_script = os.path.join(os.getcwd(), "stdio-server.py")
    
    print(f"🐍 Using Python: {python_exe}")
    print(f"📄 Server script: {server_script}")
    
    try:
        async with (
            MCPStdioTool(
                name="calculator", 
                command=python_exe,  # Use current Python executable
                args=[server_script]  # Direct path to server script
            ) as mcp_server,
            ChatAgent(
                chat_client=AzureOpenAIChatClient(credential=AzureCliCredential()),
                name="MathAgent",
                instructions="You are a helpful math assistant that can solve calculations using the calculator tools.",
            ) as agent,
        ):
            print("✅ MCP Server and Agent initialized successfully!")
            
            # Test the connection
            result = await agent.run(
                "What is 100 + 200 - 50? Please use the calculator tools to compute this.", 
                tools=mcp_server
            )
            
            print(f"\n🤖 Agent Response:")
            print(f"{result.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your Azure credentials are set up")
        print("2. Ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_DEPLOYMENT_NAME are in your .env file")
        print("3. Check that stdio-server.py is working independently")

def simple_fallback_demo():
    """Fallback demo that works without Azure dependencies."""
    print("\n" + "=" * 50)
    print("🔄 Fallback Demo (No Azure Required)")
    print("=" * 50)
    
    # Simple calculation without MCP
    calculation = "100 + 200 - 50"
    result = eval(calculation)
    
    print(f"📊 Calculation: {calculation}")
    print(f"🎯 Result: {result}")
    print("✅ Fallback demo completed!")

if __name__ == "__main__":
    print("🚀 Starting Fixed MCP Client...")
    
    try:
        # Try the full MCP example
        asyncio.run(fixed_mcp_example())
    except Exception as e:
        print(f"⚠️  MCP example failed: {e}")
        print("🔄 Running fallback demo instead...")
        simple_fallback_demo()
    
    print("\n✅ Script completed!")