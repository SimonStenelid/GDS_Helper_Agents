"""
Query Agent for Amadeus GDS Flight Search

This agent handles natural language flight queries and converts them into
Amadeus API calls using the OpenAI agents SDK framework.

Usage:
    from build_agents.Query_agent import create_query_agent

    agent = create_query_agent()
    # Use with Runner.run(agent, user_message)
"""

from dotenv import load_dotenv
import os
import json
from agents import Agent, function_tool
from datetime import datetime, timedelta
from openai import OpenAI
import requests
from typing import Dict

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Amadeus API Configuration
AMADEUS_BASE_URL_V1 = "https://test.api.amadeus.com/v1"
AMADEUS_BASE_URL_V2 = "https://test.api.amadeus.com/v2"
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"


class AmadeusAPIClient:
    """
    Handles Amadeus API authentication with automatic token refresh.
    """

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self) -> str:
        """Get or refresh Amadeus API access token."""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token

        print("🔑 Getting new Amadeus access token...")

        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(AMADEUS_AUTH_URL, data=auth_data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            print("✅ Access token obtained successfully")
            return self.access_token
        else:
            raise Exception(f"Failed to get Amadeus access token: {response.status_code} - {response.text}")


# Initialize Amadeus client
amadeus_client = AmadeusAPIClient(
    client_id=os.environ.get('AMADEUS_API_KEY'),
    client_secret=os.environ.get('AMADEUS_API_SECRECT')
)


@function_tool
def parse_flight_query(user_query: str) -> Dict[str, any]:
    """
    Parse natural language flight queries into structured Amadeus API commands.

    Args:
        user_query: Natural language flight query (e.g., "Find flights from ARN to LHR")

    Returns:
        Dictionary with structured Amadeus API command including endpoint, method, and parameters
    """

    print(f"\n🔍 Analyzing flight query: '{user_query}'")

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    parser_instructions = f"""You are an Amadeus SDK expert. Generate EXACT request structures based on official SDK templates.

CONTEXT:
- Today: {today}
- Tomorrow: {tomorrow}

AMADEUS SDK ENDPOINT TEMPLATES:

1. FLIGHT SEARCH - amadeus.shopping.flightOffersSearch.get(params)
   Endpoint: "shopping/flight-offers"
   Method: "GET"
   Template: {{
     "originLocationCode": "ARN",
     "destinationLocationCode": "LHR",
     "departureDate": "2025-10-10",
     "adults": "1",
     "travelClass": "ECONOMY",
     "max": "10"
   }}

2. FLIGHT AVAILABILITIES - amadeus.shopping.availability.flightAvailabilities.post(body)
   Endpoint: "shopping/availability/flight-availabilities"
   Method: "POST"
   Template: {{
     "originDestinations": [{{
       "id": "1",
       "originLocationCode": "ARN",
       "destinationLocationCode": "LHR",
       "departureDateTime": {{
         "date": "2025-10-10"
       }}
     }}],
     "travelers": [{{
       "id": "1",
       "travelerType": "ADULT"
     }}],
     "sources": ["GDS"]
   }}

3. FLIGHT PRICING - amadeus.shopping.flightOffers.pricing.post(body)
   Endpoint: "shopping/flight-offers/pricing"
   Method: "POST"
   Template: {{
     "data": {{
       "type": "flight-offers-pricing",
       "flightOffers": [{{
         "type": "flight-offer",
         "id": "1"
       }}]
     }}
   }}

INTENT MATCHING:
- "search flights", "find flights", "flight options" → Template 1 (GET)
- "booking classes", "seat availability", "available seats" → Template 2 (POST)
- "confirm price", "pricing", "check price" → Template 3 (POST)

PARAMETER MAPPING:
- Stockholm/ARN: ARN
- London: LHR
- Hanoi: HAN
- SAS: SK
- Air China: CA
- Turkish: TK

RESPONSE FORMAT - Use EXACT SDK template structure:
{{
  "user_intent": "search_flights|booking_classes|price_confirmation",
  "query_type": "flight_search|availability_check|price_confirmation",
  "amadeus_command": {{
    "endpoint": "exact-endpoint-path",
    "method": "GET|POST",
    "parameters": {{
      // COPY EXACT TEMPLATE STRUCTURE
      // For GET: flat parameters
      // For POST: nested SDK structure
    }}
  }},
  "reasoning": "Selected endpoint based on SDK method signature",
  "filled_defaults": [],
  "user_provided": []
}}

CRITICAL:
- COPY the exact SDK template structure
- For booking classes queries, use Template 2 EXACTLY
- Do NOT modify the nested structure
- Return ONLY valid JSON

EXAMPLE for "booking classes ARN to LHR":
{{
  "user_intent": "booking_classes",
  "query_type": "availability_check",
  "amadeus_command": {{
    "endpoint": "shopping/availability/flight-availabilities",
    "method": "POST",
    "parameters": {{
      "originDestinations": [{{
        "id": "1",
        "originLocationCode": "ARN",
        "destinationLocationCode": "LHR",
        "departureDateTime": {{
          "date": "{tomorrow}"
        }}
      }}],
      "travelers": [{{
        "id": "1",
        "travelerType": "ADULT"
      }}],
      "sources": ["GDS"]
    }}
  }}
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": parser_instructions},
                {"role": "user", "content": user_query}
            ]
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        if result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        parsed_result = json.loads(result_text)

        print(f"🎯 Intent: {parsed_result.get('user_intent')}")
        print(f"🔗 Endpoint: {parsed_result['amadeus_command']['endpoint']}")
        print(f"⚡ Method: {parsed_result['amadeus_command']['method']}")

        return parsed_result

    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
        raise ValueError(f"Failed to parse JSON: {result_text}")
    except Exception as e:
        print(f"❌ Parse error: {e}")
        raise


@function_tool(strict_mode=False)
def execute_amadeus_query(parsed_query_json: str) -> str:
    """
    Execute structured Amadeus API query with retry logic.

    Args:
        parsed_query_json: JSON string containing structured Amadeus API command from query parser

    Returns:
        JSON string containing the full response from Amadeus API
    """

    print(f"\n🚀 Executing Amadeus API query...")

    try:
        parsed_query = json.loads(parsed_query_json)
        print(f"🎯 User intent: {parsed_query.get('user_intent', 'unknown')}")
        print(f"📊 Query type: {parsed_query.get('query_type', 'unknown')}")

        amadeus_command = parsed_query.get('amadeus_command', {})
        endpoint = amadeus_command.get('endpoint', '')
        method = amadeus_command.get('method', 'GET').upper()
        parameters = amadeus_command.get('parameters', {}).copy()

        print(f"🔗 Endpoint: {endpoint}")
        print(f"⚡ Method: {method}")
        print(f"📋 Parameters: {parameters}")

        if not endpoint:
            return json.dumps({
                "status": "error",
                "error": "Missing endpoint in query"
            })

        # Check credentials
        if not amadeus_client.client_id or not amadeus_client.client_secret:
            error_result = {
                "status": "credentials_error",
                "error": "Amadeus API credentials not available",
                "query_info": {
                    "endpoint": endpoint,
                    "method": method,
                    "parameters": parameters
                }
            }
            print("❌ Credentials not available")
            return json.dumps(error_result)

        # Get access token
        try:
            access_token = amadeus_client.get_access_token()
        except Exception as auth_error:
            print(f"🔑 Authentication failed: {auth_error}")
            error_result = {
                "status": "authentication_error",
                "error": str(auth_error),
                "query_info": {
                    "endpoint": endpoint,
                    "method": method,
                    "parameters": parameters
                }
            }
            return json.dumps(error_result)

        # Retry strategies
        max_retries = 3
        retry_strategies = [
            {"base_url": AMADEUS_BASE_URL_V2, "endpoint_clean": endpoint.replace('v1/', '').replace('v2/', ''), "description": "v2 API"},
            {"base_url": AMADEUS_BASE_URL_V1, "endpoint_clean": endpoint.replace('v1/', '').replace('v2/', ''), "description": "v1 API"},
            {"base_url": AMADEUS_BASE_URL_V2, "endpoint_clean": endpoint.replace('v1/', '').replace('v2/', ''), "description": "v2 API with adjusted date", "adjust_date": True}
        ]

        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

        for attempt in range(max_retries):
            strategy = retry_strategies[attempt]
            current_params = parameters.copy()

            # Adjust date if strategy requires it
            if strategy.get('adjust_date') and 'departureDate' in current_params:
                try:
                    current_date = datetime.strptime(current_params['departureDate'], '%Y-%m-%d')
                    adjusted_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    current_params['departureDate'] = adjusted_date
                    print(f"🔄 Adjusting date to: {adjusted_date}")
                except:
                    pass

            full_url = f"{strategy['base_url']}/{strategy['endpoint_clean']}"

            print(f"🔄 Attempt {attempt + 1}/3: Trying {strategy['description']}")
            print(f"📡 Making {method} request to: {full_url}")

            try:
                if method == 'GET':
                    response = requests.get(full_url, headers=headers, params=current_params)
                else:
                    response = requests.post(full_url, headers=headers, json=current_params)

                print(f"📊 Response status: {response.status_code}")

                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "amadeus_response": response.json(),
                        "query_info": {
                            "endpoint": strategy['endpoint_clean'],
                            "method": method,
                            "parameters": current_params,
                            "user_intent": parsed_query.get('user_intent', 'unknown'),
                            "successful_attempt": attempt + 1,
                            "strategy_used": strategy['description']
                        }
                    }
                    print(f"✅ API call successful on attempt {attempt + 1}")
                    return json.dumps(result)
                else:
                    print(f"❌ Attempt {attempt + 1} failed: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying with different strategy...")
                        continue
                    else:
                        error_result = {
                            "status": "amadeus_api_error",
                            "message": f"Amadeus API returned an error after {max_retries} attempts",
                            "final_status_code": response.status_code,
                            "final_error": response.text,
                            "attempts_made": max_retries,
                            "query_info": {
                                "endpoint": strategy['endpoint_clean'],
                                "method": method,
                                "parameters": current_params
                            }
                        }
                        print(f"❌ All {max_retries} attempts failed.")
                        return json.dumps(error_result)

            except requests.RequestException as req_error:
                print(f"❌ Request error on attempt {attempt + 1}: {req_error}")
                if attempt < max_retries - 1:
                    continue
                else:
                    error_result = {
                        "status": "request_error",
                        "message": f"Request failed after {max_retries} attempts",
                        "error": str(req_error)
                    }
                    return json.dumps(error_result)

    except Exception as e:
        print(f"💥 Execution error: {str(e)}")
        error_result = {
            "status": "execution_error",
            "error": str(e)
        }
        return json.dumps(error_result)


def create_query_agent() -> Agent:
    """
    Factory function to create and configure the Query Agent.

    Returns:
        Configured Agent instance with parse and execute tools

    Usage:
        from build_agents.Query_agent import create_query_agent

        query_agent = create_query_agent()
        result = await Runner.run(query_agent, "Find flights from ARN to LHR")
    """

    instructions = """
You are a DATA RETRIEVAL agent for the Amadeus GDS system. You are NOT user-facing.

Your ONLY job is to:
1. Parse the user's flight query into Amadeus API format
2. Execute the Amadeus API call
3. Return the RAW JSON response exactly as received

YOUR ROLE: Internal data retrieval tool (not user-facing)

WORKFLOW:
1. User query arrives → Call parse_flight_query(user_query)
2. Get structured command → Convert to JSON string with json.dumps()
3. Call execute_amadeus_query(json_string)
4. Return the EXACT output from execute_amadeus_query with NO modifications

CRITICAL RULES:
- DO NOT summarize the API response
- DO NOT explain the results
- DO NOT format the data for users
- DO NOT add any commentary or interpretation
- Return the complete JSON string from execute_amadeus_query unchanged
- Another agent (Explainer Agent) will format the data for users

EXAMPLE:
User: "Find flights from ARN to HAN"
1. parsed = parse_flight_query("Find flights from ARN to HAN")
2. json_string = json.dumps(parsed)
3. raw_response = execute_amadeus_query(json_string)
4. Return raw_response EXACTLY as-is

You are a pipeline component, not the final output. Pass the raw data forward.
"""

    return Agent(
        name="Amadeus Flight Search Agent",
        instructions=instructions,
        tools=[parse_flight_query, execute_amadeus_query],
        model="gpt-5-mini"
    )
