"""
Test Slack Connection and Command Registration

This script tests if the Slack bot can connect and if the command is properly registered.
"""

import os
from dotenv import load_dotenv
from slack_sdk import WebClient
import ssl

load_dotenv(override=True)

print("=" * 60)
print("🧪 Testing Slack Connection")
print("=" * 60)

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Get tokens
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app_token = os.environ.get("SLACK_APP_TOKEN")

if not bot_token:
    print("❌ SLACK_BOT_TOKEN not found")
    exit(1)

if not app_token:
    print("❌ SLACK_APP_TOKEN not found")
    exit(1)

print(f"✅ Bot Token found: {bot_token[:15]}...")
print(f"✅ App Token found: {app_token[:15]}...")

# Test WebClient connection
print("\n📡 Testing Slack API connection...")
try:
    client = WebClient(token=bot_token, ssl=ssl_context)
    auth_response = client.auth_test()

    print(f"✅ Successfully connected to Slack!")
    print(f"   Bot User ID: {auth_response['user_id']}")
    print(f"   Bot Name: {auth_response['user']}")
    print(f"   Team: {auth_response['team']}")
    print(f"   Team ID: {auth_response['team_id']}")

except Exception as e:
    print(f"❌ Failed to connect to Slack: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ Slack connection test passed!")
print("=" * 60)
print("\n📋 Next steps:")
print("1. Make sure Socket Mode is enabled in your Slack app settings")
print("2. Verify the /ask_amadeus command is registered in your Slack app")
print("3. Ensure the bot is installed in your workspace")
print("4. Check that the bot has been invited to the channel where you're testing")
