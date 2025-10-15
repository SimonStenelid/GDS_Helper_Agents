# Amadeus GDS Agent System - Workflow Architecture

## Overview
This document describes the complete workflow architecture for the Amadeus GDS Helper Agent System, which provides intelligent flight booking assistance through Slack.

---

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SLACK INTERFACE                              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ User types:
                                    │ /ask_amadeus "Book a flight from NYC to LAX"
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SLACK COMMAND HANDLER                             │
│                    (Slack_agent.ipynb)                               │
│                                                                       │
│  • Receives /ask_amadeus command                                     │
│  • Extracts user query and context                                   │
│  • Validates input                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Passes query
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN AGENT                                    │
│                     (Orchestrator)                                   │
│                                                                       │
│  • Receives user query                                               │
│  • Determines intent (search, book, modify, cancel)                  │
│  • Routes to appropriate tools/agents                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Calls as tool
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        QUERY AGENT                                   │
│                   (Amadeus API Interface)                            │
│                                                                       │
│  • Translates natural language to API parameters                     │
│  • Calls Amadeus API endpoints                                       │
│  • Handles API responses and errors                                  │
│  • Returns structured flight data                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Raw API response
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXPLAINER AGENT                                 │
│                  (Response Formatter)                                │
│                                                                       │
│  • Receives raw Amadeus API data                                     │
│  • Formats into human-readable response                              │
│  • Adds helpful context and explanations                             │
│  • Creates user-friendly output                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Formatted response
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SLACK COMMAND HANDLER                             │
│                    (Response Posting)                                │
│                                                                       │
│  • Receives formatted response                                       │
│  • Posts back to Slack channel                                       │
│  • Handles any errors gracefully                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Posts message
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SLACK INTERFACE                              │
│                      (User sees response)                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### 1. Slack Command Handler
**Location:** `build_agents/Slack_agent.ipynb`

**Purpose:** Entry point for all user interactions

**Responsibilities:**
- Listen for `/ask_amadeus` slash commands
- Extract user query and metadata (user ID, channel ID)
- Validate input
- Trigger main agent workflow
- Post responses back to Slack

**Technology:** `slack-bolt` with Socket Mode (no public URL needed)

**Status:** ✅ Implemented

---

### 2. Main Agent (Orchestrator)
**Purpose:** Central intelligence that coordinates the workflow

**Responsibilities:**
- Receive user queries from Slack handler
- Understand user intent
- Decide which tools/agents to use
- Coordinate between query_agent and explainer_agent
- Handle workflow errors and edge cases

**Technology:** OpenAI Agents framework

**Status:** 🔜 To be implemented

---

### 3. Query Agent
**Purpose:** Interface with Amadeus GDS API

**Responsibilities:**
- Parse natural language queries
- Convert to Amadeus API parameters
- Make API calls (flight search, booking, etc.)
- Handle API responses and errors
- Return structured data

**API Operations:**
- Flight search
- Flight offers
- Pricing
- Booking creation
- Flight status

**Technology:** OpenAI Agents framework + Amadeus API SDK

**Status:** 🔜 To be implemented

---

### 4. Explainer Agent
**Purpose:** Make API responses human-friendly

**Responsibilities:**
- Receive raw Amadeus API data
- Format flight information clearly
- Add helpful context (layovers, duration, pricing)
- Explain any issues or limitations
- Create engaging, readable responses

**Technology:** OpenAI Agents framework

**Status:** 🔜 To be implemented

---

## Example User Flow

### Example 1: Flight Search
```
User Input:
/ask_amadeus Find me flights from New York to Los Angeles next Friday

Flow:
1. Slack Handler receives command
2. Main Agent analyzes: "This is a flight search request"
3. Main Agent calls Query Agent with parsed intent
4. Query Agent:
   - Extracts: origin=JFK, destination=LAX, date=next Friday
   - Calls Amadeus Flight Offers Search API
   - Returns flight options
5. Explainer Agent formats response:
   "I found 5 flights from New York (JFK) to Los Angeles (LAX) on [date]:

   ✈️ Option 1: American Airlines AA123
   • Departure: 8:00 AM - Arrival: 11:30 AM (3h 30m)
   • Price: $299
   • Non-stop

   ✈️ Option 2: Delta DL456..."
6. Slack Handler posts formatted response to channel
```

---

## Technology Stack

- **Slack Integration:** slack-bolt (Socket Mode)
- **Agent Framework:** OpenAI Agents (openai-agents package)
- **API Client:** Amadeus Python SDK
- **Environment:** Python 3.x, Jupyter notebooks for development
- **Dependencies:** See requirements.txt

---

## Environment Variables Required

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# Amadeus
AMADEUS_API_KEY=your-api-key
AMADEUS_API_SECRET=your-api-secret

# OpenAI (for agents)
OPENAI_API_KEY=your-openai-key
```

---

## Project Structure

```
GDS_Helper_Agents/
├── build_agents/
│   ├── Slack_agent.ipynb          # ✅ Slack command handler
│   ├── Main_agent.ipynb           # 🔜 Main orchestrator agent
│   ├── Query_agent.ipynb          # 🔜 Amadeus API interface
│   ├── Explainer_agent.ipynb      # 🔜 Response formatter
│   └── WORKFLOW_ARCHITECTURE.md   # 📄 This file
├── requirements.txt
└── .env                           # Environment variables
```

---

## Implementation Phases

### Phase 1: Slack Trigger ✅ COMPLETE
- [x] Install slack-bolt
- [x] Create slash command handler
- [x] Configure SSL context for development (disabled verification)
- [x] Test basic command reception
- [x] Document architecture

**Note:** SSL verification is currently disabled for local development. Before production deployment, ensure proper SSL certificates are installed.

### Phase 2: Query Agent 🔜 NEXT
- [ ] Set up Amadeus API client
- [ ] Create query_agent with Amadeus tools
- [ ] Implement flight search functionality
- [ ] Test API integration

### Phase 3: Explainer Agent 🔜
- [ ] Create explainer_agent
- [ ] Format flight search results
- [ ] Add contextual explanations
- [ ] Test output quality

### Phase 4: Main Agent Integration 🔜
- [ ] Create main orchestrator agent
- [ ] Connect query_agent as tool
- [ ] Connect explainer_agent as tool
- [ ] Implement error handling

### Phase 5: Slack Integration 🔜
- [ ] Connect main_agent to Slack handler
- [ ] Test end-to-end flow
- [ ] Add error responses to Slack
- [ ] Production deployment

---

## Design Principles

1. **Simplicity First:** Keep each component focused and simple
2. **Modularity:** Each agent/handler should work independently
3. **Clear Handoffs:** Well-defined interfaces between components
4. **Error Handling:** Graceful failures with helpful messages
5. **User-Friendly:** Natural language in, readable responses out

---

## Future Enhancements (Optional)

- Multi-turn conversations (follow-up questions)
- Booking confirmation workflows
- Price alerts and monitoring
- Multi-city itineraries
- Hotel and car rental integration
- User preference memory
