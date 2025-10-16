{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Install required packages\n",
    "!pip install slack-bolt python-dotenv"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Slack Command Trigger for Amadeus GDS Agent System\n",
    "\n",
    "This notebook creates a Slack slash command handler that serves as the entry point for the Amadeus GDS agent workflow.\n",
    "\n",
    "## Setup Requirements:\n",
    "1. Create a Slack App at https://api.slack.com/apps\n",
    "2. Enable Socket Mode (Settings → Socket Mode)\n",
    "3. Create an App-Level Token with `connections:write` scope\n",
    "4. Add Bot Token Scopes: `commands`, `chat:write`\n",
    "5. Create a Slash Command: `/ask_amadeus`\n",
    "6. Install the app to your workspace\n",
    "\n",
    "## Environment Variables Needed:\n",
    "```\n",
    "SLACK_BOT_TOKEN=xoxb-your-bot-token\n",
    "SLACK_APP_TOKEN=xapp-your-app-token\n",
    "```"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import ssl\n",
    "from dotenv import load_dotenv\n",
    "from slack_sdk import WebClient\n",
    "from slack_bolt import App\n",
    "from slack_bolt.adapter.socket_mode import SocketModeHandler\n",
    "\n",
    "# Load environment variables\n",
    "load_dotenv(override=True)\n",
    "\n",
    "# Create SSL context that doesn't verify certificates (development only)\n",
    "ssl_context = ssl.create_default_context()\n",
    "ssl_context.check_hostname = False\n",
    "ssl_context.verify_mode = ssl.CERT_NONE\n",
    "\n",
    "# Initialize Slack WebClient with custom SSL context\n",
    "web_client = WebClient(token=os.environ.get(\"SLACK_BOT_TOKEN\"), ssl=ssl_context)\n",
    "\n",
    "# Initialize Slack Bolt app with the custom WebClient\n",
    "app = App(client=web_client, token=os.environ.get(\"SLACK_BOT_TOKEN\"))\n",
    "\n",
    "print(\"✅ Slack app initialized (SSL verification disabled for development)\")\n",
    "print(\"⚠️  Remember to fix SSL certificates before production use\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Slash Command Handler\n",
    "\n",
    "The `/ask_amadeus` command receives user queries and will trigger the agent workflow."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "@app.command(\"/ask_amadeus\")\n",
    "def handle_ask_amadeus_command(ack, command, say):\n",
    "    \"\"\"\n",
    "    Handle the /ask_amadeus slash command.\n",
    "    \n",
    "    This is the entry point for the Amadeus GDS agent workflow.\n",
    "    Later, this will trigger: main_agent → query_agent → explainer_agent\n",
    "    \"\"\"\n",
    "    # Acknowledge the command request immediately\n",
    "    ack()\n",
    "    \n",
    "    # Extract information from the command\n",
    "    user_query = command['text']\n",
    "    user_id = command['user_id']\n",
    "    channel_id = command['channel_id']\n",
    "    \n",
    "    print(f\"\\n📨 Received command from user {user_id}\")\n",
    "    print(f\"📝 Query: {user_query}\")\n",
    "    print(f\"📍 Channel: {channel_id}\")\n",
    "    \n",
    "    # For now, just acknowledge receipt\n",
    "    # TODO: Later, this will call the main_agent with the user_query\n",
    "    response_text = f\"✅ Received your request: *{user_query}*\\n\\n_Processing with Amadeus GDS Agent System..._\\n\\n(Agent workflow will be connected here)\"\n",
    "    \n",
    "    # Send response back to Slack\n",
    "    say(response_text)\n",
    "    \n",
    "    print(\"✅ Response sent to Slack\")\n",
    "    \n",
    "    # Return the query for potential further processing\n",
    "    return {\n",
    "        \"user_query\": user_query,\n",
    "        \"user_id\": user_id,\n",
    "        \"channel_id\": channel_id\n",
    "    }\n",
    "\n",
    "print(\"✅ Slash command handler registered: /ask_amadeus\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Start the Bot\n",
    "\n",
    "Run this cell to start listening for Slack commands via Socket Mode."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Start the Socket Mode handler\n",
    "handler = SocketModeHandler(app, os.environ.get(\"SLACK_APP_TOKEN\"))\n",
    "\n",
    "print(\"\\n🚀 Slack bot is running!\")\n",
    "print(\"💬 Listening for /ask_amadeus commands...\")\n",
    "print(\"\\nPress Ctrl+C to stop\\n\")\n",
    "\n",
    "handler.start()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
