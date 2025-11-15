# BankerAI - LlamaIndex Implementation

This is a complete reimplementation of the BankerAI backend using the LlamaIndex framework instead of CrewAI.

## Overview

BankerAI is an AI-powered financial analysis system that provides comprehensive insights by combining data from multiple sources:

- **Internal Financial Documents** (RAG-based analysis using LlamaIndex)
- **Real-time Stock Data** (Yahoo Finance API)
- **SEC Filings** (SEC EDGAR API)
- **Social Media Sentiment** (Reddit API)

## Architecture

### Core Components

1. **Router** (`router.py`) - Routes queries to appropriate agents based on content analysis
2. **Finance Agent** (`finance_agent.py`) - RAG analysis of internal PDF documents using LlamaIndex
3. **Yahoo Agent** (`yahoo_agent.py`) - Real-time stock data analysis
4. **SEC Agent** (`sec_agent.py`) - SEC filing analysis and regulatory insights
5. **Reddit Agent** (`reddit_agent.py`) - Social media sentiment analysis
6. **General Agent** (`general_agent.py`) - General queries and system information

### Key Features

- **LlamaIndex Integration**: Advanced RAG capabilities for document analysis
- **Multi-Agent Architecture**: Specialized agents for different data sources
- **Async Processing**: Concurrent agent execution for faster responses
- **Smart Routing**: Automatic query classification and agent selection
- **Response Enhancement**: LLM-powered response improvement and summarization

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

3. Prepare document data:
   - Place PDF documents in `./raw_data/`
   - Documents should be named in format: `company-year.pdf` (e.g., `apple-2023.pdf`)

## Usage

### Start the Server

```bash
python main.py
```

This starts:
- FastAPI server on port 8001
- Interactive CLI interface

### API Endpoints

- **POST /query** - Process financial queries
- **GET /health** - Health check
- **GET /agents** - List available agents

### Example Queries

```python
# Stock analysis
"What is the performance of Apple stock in the last 30 days?"

# Company analysis
"Analyze Tesla's financial performance and recent SEC filings"

# Market sentiment
"What is the sentiment around NVIDIA on social media?"

# Document analysis
"What are the key metrics in Microsoft's latest financial reports?"
```

## Configuration

### Agent Selection Logic

- **Non-finance queries** → GeneralAgent only
- **Finance queries with tickers** → All financial agents
- **Finance queries without tickers** → FinanceAgent + RedditAgent + GeneralAgent

### Supported Companies

The system includes built-in mappings for major companies:
- Apple (AAPL)
- Microsoft (MSFT)
- Google/Alphabet (GOOGL)
- Amazon (AMZN)
- Meta/Facebook (META)
- Tesla (TSLA)
- NVIDIA (NVDA)
- Netflix (NFLX)
- Intel (INTC)
- IBM (IBM)

Additional companies can be added by:
1. Adding PDF documents to `raw_data/`
2. Updating the company-ticker mapping in `router.py`

## Technical Details

### Document Processing

- Uses LlamaIndex's `SimpleDirectoryReader` for PDF loading
- HuggingFace embeddings model: "all-MiniLM-L6-v2"
- ChromaDB for vector storage and retrieval
- Automatic metadata extraction from filenames

### LLM Integration

- OpenAI GPT-3.5-turbo for analysis and insights
- Response improvement and summarization
- Temperature settings optimized per use case

### Error Handling

- Comprehensive error logging to `monitor_logs.json`
- Graceful fallbacks when agents fail
- Partial success handling for multi-agent queries

## Performance

- Concurrent agent execution using `asyncio.gather()`
- Vector index caching for faster document retrieval
- Optimized embedding and retrieval parameters

## Monitoring

All agent activities are logged to `monitor_logs.json` with:
- Timestamps
- Agent performance metrics
- Error details
- Query processing statistics

## Differences from CrewAI Implementation

1. **Framework**: LlamaIndex instead of CrewAI
2. **RAG Capabilities**: Advanced document analysis with vector similarity search
3. **LLM Integration**: Direct OpenAI integration instead of LangChain
4. **Vector Storage**: ChromaDB with persistent storage
5. **Response Quality**: Enhanced LLM-powered response improvement
6. **Performance**: Optimized concurrent processing

## Development

To extend the system:

1. **Add new agents**: Create agent class with `run()` method returning `MCPResponse`
2. **Update router**: Add agent to routing logic in `router.py`
3. **Add data sources**: Implement new APIs in respective agent files
4. **Extend document types**: Update document loaders in `finance_agent.py`