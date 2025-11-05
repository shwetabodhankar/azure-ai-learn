#!/usr/bin/env python3
"""
Simple standalone Python script demonstrating basic functionality.
This doesn't use MCP but shows how to run Python files with functions.
"""
import asyncio
import os
from typing import Annotated
from pydantic import Field

# Simple calculator functions (similar to what the MCP server provides)
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print(f"Adding: {a} + {b}")
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print(f"Subtracting: {a} - {b}")
    return a - b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print(f"Multiplying: {a} * {b}")
    return a * b

def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    print(f"Dividing: {a} / {b}")
    return a / b

async def simple_calculator_demo():
    """Demo function showing how to use the calculator functions."""
    print("🧮 Simple Calculator Demo")
    print("=" * 30)
    
    # Test calculations
    calculations = [
        (100, 200, add),
        (300, 50, subtract),
        (15, 4, multiply),
        (20, 5, divide)
    ]
    
    results = []
    for a, b, func in calculations:
        try:
            result = func(a, b)
            print(f"✅ {func.__name__.title()}: {result}")
            results.append(result)
        except Exception as e:
            print(f"❌ Error in {func.__name__}: {e}")
            results.append(None)
    
    # Final calculation similar to the original client
    print(f"\n🔢 Final calculation: 100 + 200 - 50 = {100 + 200 - 50}")
    return results

def main():
    """Main function - entry point of the script."""
    print("🚀 Starting Simple Python Demo...")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"🐍 Python script: {__file__}")
    print()
    
    # Run the async demo
    results = asyncio.run(simple_calculator_demo())
    
    print(f"\n📊 All results: {results}")
    print("✅ Demo completed successfully!")

if __name__ == "__main__":
    main()