"""
AI Agent with Tools and Threads Demo
===================================

This example demonstrates how to create AI agents with custom tools and manage
conversation threads, similar to the Azure OpenAI Assistants API pattern.
"""

import asyncio
import os
from typing import Any, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure OpenAI client
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

# Import agent framework for tracing
from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework.observability import setup_observability


# Define custom tools for the agent
class WeatherTool:
    """A simple weather tool that provides mock weather data"""
    
    @staticmethod
    def get_weather(location: str) -> str:
        """Get the weather for a given location"""
        # Mock weather data - in real implementation, you'd call a weather API
        weather_data = {
            "Amsterdam": "cloudy with a high of 15°C",
            "New York": "sunny with a high of 22°C", 
            "London": "rainy with a high of 12°C",
            "Tokyo": "partly cloudy with a high of 18°C",
            "Sydney": "sunny with a high of 25°C"
        }
        
        weather = weather_data.get(location, f"partly cloudy with a high of 20°C")
        return f"The weather in {location} is {weather}."


class CalculatorTool:
    """A simple calculator tool for basic math operations"""
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Safely evaluate a mathematical expression"""
        try:
            # Basic safety check - only allow numbers, operators, and parentheses
            allowed_chars = set('0123456789+-*/()., ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            result = eval(expression)
            return f"The result of {expression} is {result}"
        except Exception as e:
            return f"Error calculating {expression}: {str(e)}"


class AgentWithTools:
    """AI Agent that can use tools and manage conversation threads"""
    
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview"
        )
        
        # Available tools
        self.tools = {
            "get_weather": WeatherTool.get_weather,
            "calculate": CalculatorTool.calculate
        }
        
        # Conversation threads storage
        self.threads: Dict[str, List[Dict[str, Any]]] = {}
        
        # Agent configuration
        self.model_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
    
    def create_thread(self, thread_id: str = None) -> str:
        """Create a new conversation thread"""
        if thread_id is None:
            thread_id = f"thread_{len(self.threads) + 1}"
        
        self.threads[thread_id] = [
            {
                "role": "system",
                "content": """You are a helpful assistant with access to weather and calculator tools.
                
Available tools:
- get_weather(location): Get weather information for a location
- calculate(expression): Perform mathematical calculations

When a user asks about weather, use the get_weather tool.
When a user asks for calculations, use the calculate tool.
Always be helpful and provide clear responses."""
            }
        ]
        
        print(f"✅ Created thread: {thread_id}")
        return thread_id
    
    def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a thread"""
        return self.threads.get(thread_id, [])
    
    def add_message_to_thread(self, thread_id: str, role: str, content: str):
        """Add a message to a thread"""
        if thread_id not in self.threads:
            self.create_thread(thread_id)
        
        self.threads[thread_id].append({
            "role": role,
            "content": content
        })
    
    def detect_tool_usage(self, message: str) -> tuple[str, str]:
        """Simple tool detection based on message content"""
        message_lower = message.lower()
        
        # Weather detection
        weather_keywords = ["weather", "temperature", "rain", "sunny", "cloudy"]
        if any(keyword in message_lower for keyword in weather_keywords):
            # Extract location (simple approach)
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                    location = words[i + 1].strip(".,!?")
                    return "get_weather", location
        
        # Calculator detection
        calc_keywords = ["calculate", "compute", "math", "+", "-", "*", "/", "="]
        if any(keyword in message_lower for keyword in calc_keywords):
            # Extract mathematical expression
            import re
            math_pattern = r'[\d\+\-\*/\(\)\.\s]+'
            matches = re.findall(math_pattern, message)
            if matches:
                expression = max(matches, key=len).strip()
                return "calculate", expression
        
        return None, None
    
    async def run_with_thread(self, message: str, thread_id: str) -> str:
        """Run the agent with a message in a specific thread"""
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("agent_run_with_thread") as span:
            span.set_attribute("thread_id", thread_id)
            span.set_attribute("user_message", message)
            span.set_attribute("agent.model", self.model_deployment)
            
            try:
                # Add user message to thread
                self.add_message_to_thread(thread_id, "user", message)
                
                # Detect if tools are needed
                tool_name, tool_param = self.detect_tool_usage(message)
                
                if tool_name and tool_name in self.tools:
                    with tracer.start_as_current_span("tool_execution") as tool_span:
                        tool_span.set_attribute("tool.name", tool_name)
                        tool_span.set_attribute("tool.parameter", tool_param)
                        
                        # Execute the tool
                        tool_result = self.tools[tool_name](tool_param)
                        tool_span.set_attribute("tool.result", tool_result)
                        
                        print(f"🔧 Used tool: {tool_name}({tool_param})")
                        print(f"📊 Tool result: {tool_result}")
                        
                        # Add tool result to context
                        enhanced_message = f"{message}\n\nTool result: {tool_result}\n\nPlease provide a helpful response based on this information."
                        self.threads[thread_id][-1]["content"] = enhanced_message
                
                # Get AI response
                with tracer.start_as_current_span("ai_completion") as ai_span:
                    ai_span.set_attribute("messages_count", len(self.threads[thread_id]))
                    
                    response = self.client.chat.completions.create(
                        model=self.model_deployment,
                        messages=self.threads[thread_id],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    ai_response = response.choices[0].message.content
                    ai_span.set_attribute("response_tokens", len(ai_response.split()))
                    
                    # Add AI response to thread
                    self.add_message_to_thread(thread_id, "assistant", ai_response)
                    
                    span.set_attribute("response_length", len(ai_response))
                    span.set_attribute("tools_used", tool_name is not None)
                    
                    return ai_response
            
            except Exception as e:
                span.set_attribute("error", str(e))
                error_message = f"Error processing message: {str(e)}"
                self.add_message_to_thread(thread_id, "assistant", error_message)
                return error_message


async def demo_agent_with_tools():
    """Demonstrate the agent with tools and threads"""
    print("🤖 AI Agent with Tools and Threads Demo")
    print("=" * 50)
    
    # Setup tracing
    try:
        setup_observability(
            otlp_endpoint="http://localhost:4317",
            enable_sensitive_data=True
        )
        print("✅ Tracing configured for AI Foundry")
    except Exception as e:
        print(f"⚠️  Tracing setup failed: {e}")
    
    # Create agent
    agent = AgentWithTools()
    
    # Create a conversation thread
    thread_id = agent.create_thread("weather_demo")
    
    # Demo conversations
    demo_messages = [
        "What's the weather in Amsterdam?",
        "Is it likely to rain in London?", 
        "Can you calculate 15 * 8 + 12?",
        "What about the weather in Tokyo?",
        "Please compute (100 - 25) / 5"
    ]
    
    print(f"\n🎯 Starting conversation in thread: {thread_id}")
    print("-" * 40)
    
    for i, message in enumerate(demo_messages, 1):
        print(f"\n💬 User ({i}): {message}")
        
        response = await agent.run_with_thread(message, thread_id)
        print(f"🤖 Assistant: {response}")
        
        # Small delay for better readability
        await asyncio.sleep(1)
    
    # Show thread history
    print(f"\n📜 Thread History for {thread_id}:")
    print("-" * 40)
    messages = agent.get_thread_messages(thread_id)
    for i, msg in enumerate(messages[1:], 1):  # Skip system message
        role_emoji = "💬" if msg["role"] == "user" else "🤖"
        print(f"{role_emoji} {msg['role'].title()}: {msg['content'][:100]}...")
    
    print(f"\n📊 Total messages in thread: {len(messages) - 1}")  # Exclude system message
    print("🎉 Demo completed! Check AI Foundry portal for traces.")


# Interactive demo function
async def interactive_demo():
    """Interactive demo where user can chat with the agent"""
    print("🎮 Interactive Agent Demo")
    print("=" * 30)
    print("Type 'quit' to exit, 'new_thread' to start a new conversation")
    
    agent = AgentWithTools()
    current_thread = agent.create_thread("interactive")
    
    while True:
        user_input = input(f"\n💬 You (thread: {current_thread}): ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'new_thread':
            current_thread = agent.create_thread()
            continue
        elif user_input == '':
            continue
        
        response = await agent.run_with_thread(user_input, current_thread)
        print(f"🤖 Assistant: {response}")
    
    print("👋 Goodbye!")


if __name__ == "__main__":
    # Check environment variables
    required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file configuration")
    else:
        print("🚀 Starting AI Agent with Tools and Threads Demo...")
        
        # Run the automated demo
        asyncio.run(demo_agent_with_tools())
        
        # Uncomment the line below for interactive mode
        # asyncio.run(interactive_demo())