"""
Explainer Agent for Amadeus GDS Response Formatting

This agent converts technical Amadeus API responses into beginner-friendly
explanations tailored to the user's original question.

Usage:
    from build_agents.explainer_agent import create_explainer_agent

    agent = create_explainer_agent()
    # Use with Runner.run(agent, message)
"""

from dotenv import load_dotenv
import os
from agents import Agent, function_tool
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


@function_tool
def explain_amadeus_response(amadeus_api_result: str, user_original_query: str = "") -> str:
    """
    Analyze and explain Amadeus API responses in beginner-friendly language.

    This function takes raw Amadeus API response data (in any format) and converts it into
    clear, easy-to-understand explanations tailored to the user's original question.

    Args:
        amadeus_api_result: API response data (JSON, partial JSON, text, or error messages)
        user_original_query: The original user query for context (optional)

    Returns:
        Clear, beginner-friendly explanation of the flight data
    """

    print(f"\n📖 Explaining Amadeus API response...")
    if user_original_query:
        print(f"🎯 Original query context: '{user_original_query}'")

    # System instructions for explaining flight data
    explainer_instructions = f"""You are a professional Amadeus GDS expert with many years of experience in the Flight Travel Industry.

Your task is to analyze the provided Amadeus API response data and create a clear, beginner-friendly explanation.

ANALYSIS REQUIREMENTS:
- Read and analyze the ENTIRE response - do not skip any sections
- The data may be in JSON format, partial JSON, plain text, or even error messages
- Extract whatever useful information is available
- Focus on answering the user's original question directly
- Focus on the most important information for travelers
- Explain technical terms in simple language
- Structure your response clearly with sections/bullet points

KEY AREAS TO EXPLAIN:
- Flight details (times, routes, airlines, flight numbers)
- Pricing information (total cost, currency, fare breakdown if available)
- Booking classes and cabin types
- Baggage allowances (if present)
- Any restrictions or conditions
- Duration and connections

EXPLANATION STYLE:
- Use simple, clear language
- Avoid technical jargon unless explaining it
- Organize information logically
- Highlight the most important details first
- Use headings and bullet points for easy reading
- If the response contains errors or is mock data, explain that clearly
- If the data is malformed or incomplete, extract and explain what is available

CONTEXT: {user_original_query if user_original_query else "General flight search"}

IMPORTANT:
- Tailor your explanation to directly answer the user's original question
- If they asked about booking classes, focus on that
- If they asked about prices, emphasize pricing details
- If they asked about specific airlines, filter and highlight those
- If the response contains errors, explain them in a user-friendly way

Format your response with clear headings and bullet points for easy reading in Slack."""

    try:
        # Call OpenAI to explain the response (no JSON validation needed)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": explainer_instructions},
                {"role": "user", "content": f"Please explain this Amadeus API response:\n\n{amadeus_api_result}"}
            ],

        )

        explanation = response.choices[0].message.content.strip()

        print("✅ Explanation generated successfully")
        return explanation

    except Exception as e:
        print(f"❌ Explanation error: {e}")
        return f"I encountered an error while trying to explain the flight data: {str(e)}\n\nHere's the raw response I received:\n\n{amadeus_api_result[:500]}..."


def create_explainer_agent() -> Agent:
    """
    Factory function to create and configure the Explainer Agent.

    Returns:
        Configured Agent instance with explanation tool

    Usage:
        from build_agents.explainer_agent import create_explainer_agent

        explainer_agent = create_explainer_agent()
        result = await Runner.run(explainer_agent, message)
    """

    instructions = """
You are an Expert Flight Travel Explainer that converts technical Amadeus GDS API responses into clear, beginner-friendly explanations.

Your workflow:
1. Receive Amadeus API response data (any format: JSON, partial JSON, text, errors) and the user's original query
2. Use the explain_amadeus_response tool to analyze and format the response
3. Return the generated explanation directly to the user

Crucial Rules:
- ALWAYS use the explain_amadeus_response tool to process API responses
- Pass both the API result AND the user's original query for context
- The tool is flexible and can handle any data format (JSON, malformed JSON, plain text, errors)
- The tool will handle all formatting and explanation generation
- Present the tool's output as your final response
- Focus on clarity and answering the user's specific question

Example workflow:
1. Receive: API response data + user query "What are the booking classes for SK flights?"
2. Call: explain_amadeus_response(api_data, user_query)
3. Return: The formatted explanation from the tool

Your goal is to make complex GDS data accessible and easy to understand for travelers, regardless of the data format received.
"""

    return Agent(
        name="Amadeus Response Explainer Agent",
        instructions=instructions,
        tools=[explain_amadeus_response],
        model="gpt-5-mini"
    )
