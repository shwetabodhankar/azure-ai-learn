#!/usr/bin/env python3
"""
Simple test script to verify stdio-server.py is working correctly.
This bypasses the agent framework complexity.
"""
import json
import subprocess
import sys

def test_mcp_server():
    """Test the MCP server directly using subprocess."""
    print("🧪 Testing MCP Server Directly...")
    
    # Start the server process
    server_process = subprocess.Popen(
        [sys.executable, "stdio-server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="."
    )
    
    # Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Send the request
    request_str = json.dumps(init_request) + "\n"
    print(f"📤 Sending: {request_str.strip()}")
    
    try:
        stdout, stderr = server_process.communicate(input=request_str, timeout=5)
        print(f"📥 Response: {stdout}")
        if stderr:
            print(f"❌ Error: {stderr}")
        
        return_code = server_process.returncode
        print(f"🔄 Return code: {return_code}")
        
        if return_code == 0:
            print("✅ Server is working correctly!")
        else:
            print("❌ Server failed")
            
    except subprocess.TimeoutExpired:
        print("⏰ Server test timed out")
        server_process.kill()
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        server_process.kill()

if __name__ == "__main__":
    test_mcp_server()