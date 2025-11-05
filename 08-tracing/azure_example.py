# Copyright (c) Microsoft. All rights reserved.
# Based on the exact example from Azure AI Foundry documentation
# https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-application

import os
import dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.trace.span import format_trace_id

# Load environment variables
dotenv.load_dotenv()

# (Optional) Capture message content
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

# Set OpenAI API version if not already set
if "OPENAI_API_VERSION" not in os.environ:
    os.environ["OPENAI_API_VERSION"] = "2024-08-01-preview"

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
    
    # Step 3: Get OpenAI client and send a request
    client = project_client.get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": "Write a short poem on open telemetry."}],
    )
    print("Response:")
    print(response.choices[0].message.content)
    
    # Step 4: Example with custom spans and attributes
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("custom_weather_question") as span:
        print(f"Trace ID: {format_trace_id(span.get_span_context().trace_id)}")
        span.set_attribute("operation.type", "weather_inquiry")
        span.set_attribute("location", "Seattle")
        
        weather_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "What's the weather like in Seattle?"}],
        )
        
        span.set_attribute("response.length", len(weather_response.choices[0].message.content))
        print("\nWeather Response:")
        print(weather_response.choices[0].message.content)

if __name__ == "__main__":
    main()