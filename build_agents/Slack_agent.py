"""
Slack Bot Handler for Amadeus GDS Agent System

This module handles Slack slash command interactions and serves
as the entry point for the agent workflow.

Usage:
    from build_agents.Slack_agent import start_slack_bot

    start_slack_bot()  # Starts listening for /ask_amadeus commands
"""

import os
import sys
import ssl
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Add parent directory to path so we can import build_agents modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(override=True)


def initialize_slack_app() -> App:
    """
    Initialize and configure the Slack Bolt app.

    Returns:
        Configured Slack App instance

    Raises:
        ValueError: If required environment variables are missing
    """

    # Validate environment variables
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_app_token = os.environ.get("SLACK_APP_TOKEN")

    if not slack_bot_token:
        raise ValueError("SLACK_BOT_TOKEN environment variable is required")
    if not slack_app_token:
        raise ValueError("SLACK_APP_TOKEN environment variable is required")

    # Create SSL context that doesn't verify certificates (development only)
    # WARNING: This should be fixed for production deployment
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    print("✅ Slack app initialized (SSL verification disabled for development)")
    print("⚠️  WARNING: Fix SSL certificates before production use")

    # Initialize Slack WebClient with custom SSL context
    web_client = WebClient(token=slack_bot_token, ssl=ssl_context)

    # Initialize Slack Bolt app (only pass client, not token since we already have client)
    app = App(client=web_client)

    return app


def create_command_handler(app: App):
    """
    Register the /ask_amadeus command handler with the Slack app.

    Args:
        app: Configured Slack App instance
    """

    @app.command("/ask_amadeus")
    def handle_ask_amadeus_command(ack, command, say):
        """
        Handle the /ask_amadeus slash command.

        This is the entry point for the Amadeus GDS agent workflow.
        Flow: Slack → Main Agent → Query Agent → Explainer Agent → Slack Response

        Args:
            ack: Slack acknowledgement function (must be called immediately)
            command: Command payload containing user query and metadata
            say: Function to post messages back to Slack channel
        """

        # Acknowledge the command request immediately (required by Slack)
        ack()

        # Extract information from the command
        user_query = command.get('text', '').strip()
        user_id = command.get('user_id', '')
        channel_id = command.get('channel_id', '')

        print(f"\n📨 Received /ask_amadeus command")
        print(f"👤 User: {user_id}")
        print(f"📝 Query: '{user_query}'")
        print(f"📍 Channel: {channel_id}")

        # Validate user input
        if not user_query:
            say("❌ Please provide a query. Usage: `/ask_amadeus <your flight query>`")
            print("⚠️  Empty query received")
            return

        try:
            # Send initial progress message
            say("👋 Got your message! I am on it. This could take a couple of minutes... ⏱️")

            # Call main_agent to process the query with progress callback
            response = trigger_main_agent(user_query, say)

            # Post final response to Slack
            say(response)
            print("✅ Response sent to Slack")

        except Exception as e:
            error_message = f"❌ Error processing your request: {str(e)}"
            say(error_message)
            print(f"💥 Error in command handler: {e}")

    print("✅ Command handler registered: /ask_amadeus")


def trigger_main_agent(user_query: str, progress_callback=None) -> str:
    """
    Trigger the main agent to process user query.

    This function orchestrates the complete workflow:
    1. Calls main_agent with user_query
    2. Main agent calls query_agent (parses query + calls Amadeus API)
    3. Main agent calls explainer_agent (formats API response)
    4. Returns formatted response

    Args:
        user_query: Natural language query from Slack user
        progress_callback: Optional callback function for progress updates (e.g., Slack say function)

    Returns:
        Formatted response string to post back to Slack
    """

    from build_agents.main_agent import process_user_query

    # Call the main agent's entry point with progress callback
    response = process_user_query(user_query, progress_callback)

    return response


def start_slack_bot():
    """
    Initialize and start the Slack bot in Socket Mode.

    This is the main entry point to start listening for Slack commands.
    The bot will run continuously until interrupted (Ctrl+C).

    Raises:
        ValueError: If required environment variables are missing
        Exception: For any other initialization or runtime errors
    """

    try:
        print("\n" + "="*60)
        print("🚀 Starting Amadeus GDS Slack Bot")
        print("="*60 + "\n")

        # Initialize Slack app
        app = initialize_slack_app()

        # Register command handlers
        create_command_handler(app)

        # Get app token for Socket Mode
        slack_app_token = os.environ.get("SLACK_APP_TOKEN")

        # Create Socket Mode handler
        handler = SocketModeHandler(app, slack_app_token)

        print("\n✅ Slack bot is running!")
        print("💬 Listening for /ask_amadeus commands...")
        print("\nPress Ctrl+C to stop\n")

        # Start the bot (blocking call)
        handler.start()

    except KeyboardInterrupt:
        print("\n\n⏹️  Bot stopped by user")
    except ValueError as ve:
        print(f"\n❌ Configuration error: {ve}")
        print("Please check your .env file and ensure all required variables are set.")
        raise
    except Exception as e:
        print(f"\n💥 Error starting bot: {e}")
        raise


if __name__ == "__main__":
    """
    Run the Slack bot when this file is executed directly.

    Usage:
        python Slack_agent.py
    """
    start_slack_bot()
