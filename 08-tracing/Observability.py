# Copyright (c) Microsoft. All rights reserved.
# Updated to use the working Azure documentation approach

import asyncio
import os
from random import randint
from typing import Annotated

import dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.trace.span import format_trace_id
from pydantic import Field

"""
This sample shows you can can setup telemetry for an Azure AI agent.
It uses the Azure AI client to setup the telemetry, this calls out to
Azure AI for the connection string of the attached Application Insights
instance.

You must add an Application Insights instance to your Azure AI project
for this sample to work.
"""

# For loading the `AZURE_AI_PROJECT_ENDPOINT` environment variable
dotenv.load_dotenv()

# Enable content recording for input/output in traces
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

# Set OpenAI API version if not already set
if "OPENAI_API_VERSION" not in os.environ:
    os.environ["OPENAI_API_VERSION"] = "2024-08-01-preview"


async def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    await asyncio.sleep(randint(0, 10) / 10.0)  # Simulate a network call
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


def main():
    # Step 1: Create AIProjectClient and get connection string
    project_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    )
    connection_string = project_client.telemetry.get_application_insights_connection_string()
    
    # Step 2: Configure Azure Monitor and instrument OpenAI SDK
    configure_azure_monitor(connection_string=connection_string)
    OpenAIInstrumentor().instrument()
    
    # Step 3: Get OpenAI client
    client = project_client.get_openai_client()
    
    # Step 4: Example with weather questions using custom spans
    tracer = trace.get_tracer(__name__)
    
    questions = [
        "What's the weather in Amsterdam?",
        "What's the weather in Tokyo?",
        "What's the weather in New York?"
    ]
    
    for question in questions:
        with tracer.start_as_current_span(f"Weather Question: {question[:30]}...") as span:
            print(f"Trace ID: {format_trace_id(span.get_span_context().trace_id)}")
            span.set_attribute("operation.type", "weather_inquiry")
            span.set_attribute("user.question", question)
            
            # Create a system message that includes the weather function
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful weather assistant. When asked about weather, provide a realistic weather forecast for the requested location."
                },
                {"role": "user", "content": question}
            ]
            
            print(f"User: {question}")
            print(f"Assistant: ", end="")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            
            response_text = response.choices[0].message.content
            span.set_attribute("assistant.response", response_text)
            span.set_attribute("response.length", len(response_text))
            
            print(response_text)
            print("-" * 80)


if __name__ == "__main__":
    main()