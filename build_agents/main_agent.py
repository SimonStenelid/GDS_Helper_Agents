"""
Main Orchestrator Agent for Amadeus GDS System

Coordinates the workflow between query_agent and explainer_agent.
Entry point for Slack integration.

Usage:
    from build_agents.main_agent import process_user_query

    response = process_user_query("Find flights ARN to HAN")
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool

# Add parent directory to path so we can import build_agents modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_agents.Query_agent import create_query_agent
from build_agents.explainer_agent import create_explainer_agent

# Load environment variables
load_dotenv(override=True)

# Initialize sub-agents at module level
query_agent = create_query_agent()
explainer_agent = create_explainer_agent()

print("✅ Query Agent initialized")
print("✅ Explainer Agent initialized")


@function_tool
async def query_flight_data(user_query: str) -> str:
    """
    Query flight data from Amadeus API using the query_agent.

    This tool wraps the query_agent to get flight information from Amadeus GDS.

    Args:
        user_query: Natural language flight query from the user

    Returns:
        JSON string containing Amadeus API response with flight data
    """

    print(f"\n🔍 Query Flight Data Tool called")
    print(f"📝 User query: '{user_query}'")

    try:
        # Run the query agent to get Amadeus API data
        result = await Runner.run(query_agent, user_query)

        # Extract the final output (should be the API response)
        api_response = result.final_output

        print(f"✅ Query Agent completed successfully")
        return api_response

    except Exception as e:
        error_msg = f"Error querying flight data: {str(e)}"
        print(f"❌ {error_msg}")
        # Return error as JSON for consistency
        return json.dumps({
            "status": "error",
            "error": error_msg,
            "message": "Failed to query flight data from Amadeus API"
        })


@function_tool
async def format_flight_response(amadeus_api_result: str, user_original_query: str) -> str:
    """
    Format Amadeus API response into beginner-friendly explanation using explainer_agent.

    This tool wraps the explainer_agent to convert technical API responses
    into clear, easy-to-understand explanations.

    Args:
        amadeus_api_result: JSON string containing Amadeus API response
        user_original_query: The original user query for context

    Returns:
        Clear, beginner-friendly formatted response string
    """

    print(f"\n📝 Format Flight Response Tool called")
    print(f"🎯 Original query: '{user_original_query}'")

    try:
        # Prepare message for explainer agent with both API data and original query
        explainer_message = f"""
Please explain this Amadeus API response to answer the user's question.

User's Original Question: {user_original_query}

Amadeus API Response:
{amadeus_api_result}

Provide a clear, beginner-friendly explanation that directly answers the user's question.
"""

        # Run the explainer agent
        result = await Runner.run(explainer_agent, explainer_message)

        # Extract the formatted explanation
        formatted_response = result.final_output

        print(f"✅ Explainer Agent completed successfully")
        return formatted_response

    except Exception as e:
        error_msg = f"Error formatting response: {str(e)}"
        print(f"❌ {error_msg}")
        # Return a fallback message with the raw data
        return f"I received flight data but had trouble formatting it clearly. Here's what I found:\n\n{amadeus_api_result}\n\nError: {error_msg}"


def create_main_agent() -> Agent:
    """
    Factory function to create and configure the Main Orchestrator Agent.

    Returns:
        Configured Agent instance that coordinates query_agent and explainer_agent

    Usage:
        from build_agents.main_agent import create_main_agent

        main_agent = create_main_agent()
        result = await Runner.run(main_agent, user_query)
    """

    instructions = """
You are the Main Orchestrator for the Amadeus GDS Helper System.

Your role is to coordinate between the query_agent and explainer_agent to provide users with clear flight information.

WORKFLOW:
1. Receive user's natural language query about flights
2. Call query_flight_data tool to get Amadeus API response
3. Call format_flight_response tool with the API response AND the original user query
4. Return the formatted response to the user

CRITICAL RULES:
- ALWAYS call query_flight_data FIRST to get the flight data
- ALWAYS pass BOTH the API response AND the original user query to format_flight_response
- The user's original query is crucial for the explainer to tailor the response
- Handle errors gracefully - if one step fails, inform the user clearly
- Be concise in your own responses - let the tools do the work

TOOL USAGE:
- query_flight_data(user_query) → Returns API JSON response
- format_flight_response(api_response, original_query) → Returns formatted explanation

EXAMPLE FLOW:
User: "Find SK flights from ARN to HAN"
1. api_data = query_flight_data("Find SK flights from ARN to HAN")
2. formatted = format_flight_response(api_data, "Find SK flights from ARN to HAN")
3. Return formatted response to user

Your goal is to orchestrate a smooth workflow that gives users clear, helpful flight information.
"""

    return Agent(
        name="Amadeus GDS Main Orchestrator",
        instructions=instructions,
        tools=[query_flight_data, format_flight_response],
        model="gpt-5-mini"
    )


async def process_user_query_async(user_query: str, progress_callback=None) -> str:
    """
    Process a user query through the main agent workflow (async version).

    This function orchestrates the complete workflow:
    1. Query agent gets Amadeus API data
    2. Explainer agent formats the response
    3. Returns formatted response for Slack

    Args:
        user_query: Natural language query from Slack user
        progress_callback: Optional callback function to report progress updates

    Returns:
        str: Formatted response ready for Slack posting
    """

    try:
        print(f"\n{'='*60}")
        print(f"🚀 Processing query: {user_query}")
        print(f"{'='*60}\n")

        # Progress update: Starting to query Amadeus
        if progress_callback:
            progress_callback("✈️ Currently having a nice convo with Amadeus... 💬")

        # Create main agent instance
        main_agent = create_main_agent()

        # Run the agent workflow with tracing
        with trace("main_agent_workflow", metadata={"query": user_query}):
            result = await Runner.run(main_agent, user_query)

        # Progress update: Got response, now formatting
        if progress_callback:
            progress_callback("📋 Got the Amadeus response, making it sensible for you now... 🧠")

        # Extract the final response
        response = result.final_output

        print(f"\n{'='*60}")
        print(f"✅ Workflow completed successfully")
        print(f"{'='*60}\n")

        return response

    except Exception as e:
        error_message = f"❌ Error processing query: {str(e)}"
        print(f"\n{error_message}\n")
        return f"Sorry, I encountered an error while processing your request: {str(e)}\n\nPlease try again or contact support."


def process_user_query(user_query: str, progress_callback=None) -> str:
    """
    Synchronous wrapper for process_user_query_async.

    This is the main entry point called by Slack handler.
    Handles event loop management for both Jupyter and script environments.

    Args:
        user_query: Natural language query from Slack user
        progress_callback: Optional callback function to report progress updates

    Returns:
        str: Formatted response ready for Slack posting
    """

    try:
        # Try to get the running event loop
        loop = asyncio.get_running_loop()
        # If we're here, there's already a loop running (Jupyter)
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(process_user_query_async(user_query, progress_callback))
    except RuntimeError:
        # No event loop running (normal Python script)
        return asyncio.run(process_user_query_async(user_query, progress_callback))

