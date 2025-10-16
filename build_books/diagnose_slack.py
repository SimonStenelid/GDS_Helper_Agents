"""
Comprehensive Slack Diagnostics

This script checks all aspects of your Slack app configuration.
"""

import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_bolt import App
import ssl

load_dotenv(override=True)

print("=" * 70)
print("🔍 SLACK APP DIAGNOSTICS")
print("=" * 70)

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Get tokens
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app_token = os.environ.get("SLACK_APP_TOKEN")

# 1. Token Check
print("\n1️⃣  CHECKING TOKENS")
print("-" * 70)
if bot_token and bot_token.startswith("xoxb-"):
    print(f"✅ Bot Token format correct: {bot_token[:20]}...")
else:
    print("❌ Bot Token missing or incorrect format")
    exit(1)

if app_token and app_token.startswith("xapp-"):
    print(f"✅ App Token format correct: {app_token[:20]}...")
else:
    print("❌ App Token missing or incorrect format")
    exit(1)

# 2. API Connection Check
print("\n2️⃣  CHECKING API CONNECTION")
print("-" * 70)
try:
    client = WebClient(token=bot_token, ssl=ssl_context)
    auth = client.auth_test()
    print(f"✅ Connected as: {auth['user']} (ID: {auth['user_id']})")
    print(f"✅ Team: {auth['team']} (ID: {auth['team_id']})")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# 3. Bot Scopes Check
print("\n3️⃣  CHECKING BOT SCOPES")
print("-" * 70)
try:
    scopes_response = client.auth_test()
    # The scopes aren't directly in auth_test, but we can check if we have permissions
    print("ℹ️  Cannot check scopes via API. Please verify manually:")
    print("   Go to: https://api.slack.com/apps → Your App → OAuth & Permissions")
    print("   Required Bot Token Scopes:")
    print("   - commands (for slash commands)")
    print("   - chat:write (to post messages)")
except Exception as e:
    print(f"⚠️  Could not check scopes: {e}")

# 4. Check if Socket Mode app works
print("\n4️⃣  CHECKING SOCKET MODE SETUP")
print("-" * 70)
try:
    app = App(token=bot_token)
    print("✅ Bolt App initialized successfully")
    print("ℹ️  Socket Mode app created (handler not started)")
except Exception as e:
    print(f"❌ Failed to initialize Bolt App: {e}")
    exit(1)

# 5. Summary and Recommendations
print("\n" + "=" * 70)
print("📋 SUMMARY & NEXT STEPS")
print("=" * 70)
print("\n✅ CONNECTION TEST PASSED")
print("\nIf slash command still doesn't work, check these in Slack App settings:")
print("https://api.slack.com/apps\n")

print("□ 1. Socket Mode is ENABLED")
print("      → Settings → Socket Mode → Toggle ON")
print()
print("□ 2. Slash Command /ask_amadeus is REGISTERED")
print("      → Features → Slash Commands → Create New Command")
print("      → Command: /ask_amadeus")
print("      → Leave Request URL empty (Socket Mode handles it)")
print()
print("□ 3. App is INSTALLED/REINSTALLED to workspace")
print("      → Settings → Install App → (Re)install to Workspace")
print("      → Important: Reinstall after adding slash command!")
print()
print("□ 4. Bot has required SCOPES")
print("      → Features → OAuth & Permissions → Bot Token Scopes")
print("      → Add: commands, chat:write")
print()
print("□ 5. Bot is INVITED to the channel")
print("      → In Slack: /invite @oid_export_bot")
print()

print("=" * 70)
