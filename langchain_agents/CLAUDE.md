# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BankerAI is a FastAPI-based multi-agent system that answers financial queries by intelligently routing user questions to specialized agents. The system uses semantic similarity to classify queries and dispatches them to appropriate agents for finance-related research, stock analysis, social media sentiment, and general queries.

## Architecture

### Core Components

**RouterAgent** (agents/router.py:37)
- Central orchestrator that classifies incoming queries using sentence transformers
- Extracts company names and maps them to stock tickers via COMPANY_TICKER_MAP
- Uses semantic similarity (threshold: 0.4) to determine if a query is finance-related
- Dispatches queries to multiple specialized agents in parallel using asyncio
- Routing logic (agents/router.py:111-158):
  - Non-finance queries → GeneralAgent only
  - Finance + tickers → All agents (Reddit, Finance, Yahoo, SEC, General)
  - Finance + companies (no tickers) → Reddit, Finance, General
  - Finance (no companies) → Reddit, General

**FinanceAgent** (agents/finance_agent.py:13)
- Performs RAG (Retrieval-Augmented Generation) on internal PDF documents
- Uses ChromaDB vector database stored at `vector_db/chroma_index`
- Builds embeddings from PDFs in `raw_data/` directory if index doesn't exist
- Extracts company names and years from PDF filenames (e.g., "apple-2023.pdf")
- Returns structured financial data with metrics, summaries, and key data points

**YahooAgent** (agents/yahoo_agent.py:14)
- Fetches 30-day stock price data using yfinance
- Calculates statistics: min/max/mean close, volatility, percent change
- Uses OpenAI GPT-3.5-turbo to generate analysis summaries from raw statistics

**RedditAgent** (agents/reddit_agent.py:10)
- Scrapes r/stocks subreddit using PRAW (Python Reddit API Wrapper)
- Searches for posts from the last 30 days related to companies or queries
- Extracts top comments (up to 10 per post) and performs sentiment analysis
- Returns post summaries with average sentiment scores

**SECAgent** (agents/sec_agent.py:7)
- Designed to fetch SEC filings (currently uses mock data)
- Extracts key financial data and time periods from filing content
- Placeholder for production SEC EDGAR API integration

**GeneralAgent** (agents/general_agent.py:14)
- Handles non-finance queries using OpenAI GPT-3.5-turbo
- Uses randomized prompts to vary response style
- Returns long-form text responses formatted as plain text

**MonitorAgent** (agents/monitor.py:4)
- Logs agent health, status, and errors to `monitor_logs.json`
- Each agent logs: timestamps, query details, responses, and status

### MCP Protocol

The system uses a custom Message Context Protocol (MCP) for agent communication:

**MCPContext** (mcp/schemas.py:7)
- Shared context containing: user_query, companies, tickers, extracted_terms, version
- Passed to all agents to ensure consistent data

**MCPRequest** (mcp/schemas.py:15)
- Standardized request format with context, timestamp, source, and request_id

**MCPResponse** (mcp/schemas.py:22)
- Standardized response format with request_id, data, context_updates, status, timestamp

### API Endpoints

**POST /query** (main.py:156)
- Accepts MessageRequest with query field
- Routes query through RouterAgent
- Post-processes each agent's response using LLM for summarization (main.py:53-82)
- Returns JSON with agent responses keyed by agent name (e.g., "FinanceAgent", "YahooAgent")

## Development Commands

### Running the Application

```bash
# Start FastAPI server (HTTP + CLI loop)
python main.py

# Using Docker
docker build -t bankerai-backend .
docker run -p 8000:8000 bankerai-backend

# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (pytest is listed in requirements)
pytest
```

### Environment Setup

Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

## Important Implementation Details

### Company and Ticker Extraction

- RouterAgent maintains COMPANY_TICKER_MAP (agents/router.py:21-35) for common companies
- Also scans `raw_data/` directory for PDF filenames to extract additional companies
- Company names in queries are case-insensitive matched

### Vector Database Management

- FinanceAgent checks if ChromaDB index exists at startup (agents/finance_agent.py:35)
- If missing, builds index from all PDFs in `raw_data/` directory
- Metadata stored includes: file_name, year, company
- Uses HuggingFace model 'all-MiniLM-L6-v2' for embeddings

### Parallel Agent Execution

- RouterAgent uses asyncio.gather() to run agents concurrently (agents/router.py:159)
- Some agents use loop.run_in_executor() for sync code (Finance, Yahoo, SEC, General)
- RedditAgent is async-native

### Response Processing Pipeline

1. RouterAgent dispatches query to agents
2. Each agent returns MCPResponse with data field
3. main.py post-processes responses with improve_agent_response() (main.py:53)
4. LLM (GPT-3.5-turbo) summarizes and cleans agent output
5. Final response maps agent names to {summary: "..."} structure

### Logging

All agents log to `monitor_logs.json` using JSON lines format with:
- Agent name, timestamps, query details, responses, status

## File Structure

```
backend/
├── agents/          # All agent implementations
├── mcp/            # MCP protocol schemas and context store
├── raw_data/       # PDF documents for RAG (FinanceAgent)
├── vector_db/      # ChromaDB persistence directory
├── main.py         # FastAPI app and CLI entry point
└── dockerfile      # Container configuration
```

## Known Limitations

- SECAgent uses mock data (agents/sec_agent.py:94-97)
- RedditAgent sentiment analysis uses random scores (agents/reddit_agent.py:138)
- Context store (mcp/context_store.py) requires Redis but is not used in current flow
- CLI loop (main.py:141) runs concurrently with FastAPI but is primarily for testing
