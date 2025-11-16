import os
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from schemas import MCPRequest, MCPResponse, MCPContext
from monitor import MonitorAgent

class LlamaIndexRouter:
    def __init__(self):
        self.monitor = MonitorAgent()

        # Finance keywords for query classification
        self.finance_keywords = [
            "stock", "stocks", "loan", "loans", "invest", "investment", "finance",
            "bank", "banks", "banking", "dividend", "equity", "bond", "bonds",
            "portfolio", "asset", "assets", "liability", "liabilities",
            "balance sheet", "income statement", "cash flow", "financial report",
            "earnings", "revenue", "profit", "loss", "market cap", "valuation",
            "merger", "acquisition", "IPO", "interest rate", "inflation",
            "recession", "bull market", "bear market", "trading", "exchange",
            "securities", "broker", "dividend yield", "P/E ratio", "EPS"
        ]

        # Company to ticker mapping
        self.company_ticker_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "intel": "INTC",
            "ibm": "IBM",
        }

        # Load additional keywords from raw data directory
        self._load_additional_finance_keywords()

    def _load_additional_finance_keywords(self):
        """Load additional finance keywords from document filenames"""
        raw_data_dir = "./raw_data"
        if os.path.exists(raw_data_dir):
            try:
                file_topics = [
                    os.path.splitext(f)[0].replace("-", " ").replace("_", " ")
                    for f in os.listdir(raw_data_dir)
                    if f.lower().endswith(".pdf")
                ]
                self.finance_keywords.extend(file_topics)
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Error loading additional keywords: {e}")

    def extract_companies(self, query: str) -> List[str]:
        """Extract company names from query"""
        companies = set()
        if not query:
            return []

        query_lower = query.lower()

        # Check against known companies
        for company_name in self.company_ticker_map.keys():
            try:
                if re.search(rf'\b{re.escape(company_name)}\b', query_lower):
                    companies.add(company_name)
            except re.error:
                if company_name in query_lower:
                    companies.add(company_name)

        # Check against raw data directory files
        raw_data_dir = "./raw_data"
        if os.path.exists(raw_data_dir):
            try:
                for fname in os.listdir(raw_data_dir):
                    if fname.lower().endswith(".pdf"):
                        base = os.path.splitext(fname)[0]
                        company = base.split("-")[0] if "-" in base else base
                        company_lower = company.lower()
                        try:
                            if re.search(rf'\b{re.escape(company_lower)}\b', query_lower):
                                companies.add(company_lower)
                        except re.error:
                            if company_lower in query_lower:
                                companies.add(company_lower)
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Error extracting companies: {e}")

        return list(companies)

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        """Map company names to stock tickers"""
        if not companies:
            return []

        tickers = []
        for company in companies:
            ticker = self.company_ticker_map.get(company.lower())
            if ticker:
                tickers.append(ticker)

        return list(set(tickers))

    def is_finance_query(self, query: str) -> bool:
        """Determine if query is finance-related"""
        if not query or not isinstance(query, str):
            return False

        query_lower = query.lower()

        # Check for finance keywords
        for keyword in self.finance_keywords:
            try:
                if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                    return True
            except re.error:
                if keyword in query_lower:
                    return True

        # Check for ticker patterns (e.g., AAPL, MSFT)
        try:
            if re.search(r'\b[A-Z]{2,5}\b', query):
                return True
        except re.error:
            pass

        return False

    def determine_agents(self, user_query: str, tickers: List[str]) -> List[str]:
        """Determine which agents to run based on query analysis"""
        try:
            is_finance = self.is_finance_query(user_query)

            if not is_finance:
                return ["GeneralAgent"]
            elif is_finance and tickers:
                # Full financial analysis with all agents
                return ["FinanceAgent", "YahooAgent", "SECAgent", "RedditAgent", "GeneralAgent"]
            else:
                # Finance query without specific tickers
                return ["FinanceAgent", "RedditAgent", "GeneralAgent"]

        except Exception as e:
            self.monitor.log_error("LlamaIndexRouter", f"Error determining agents: {e}")
            return ["GeneralAgent"]  # Fallback

    async def run_agent(self, agent_name: str, mcp_request: MCPRequest) -> Optional[Any]:
        """Run a specific agent with error handling"""
        try:
            # Dynamic import to avoid circular dependencies
            if agent_name == "GeneralAgent":
                from general_agent import GeneralAgent
                agent = GeneralAgent()
                return agent.run(mcp_request)

            elif agent_name == "FinanceAgent":
                from finance_agent import FinanceAgent
                agent = FinanceAgent()
                return agent.run(mcp_request)

            elif agent_name == "YahooAgent":
                from yahoo_agent import YahooAgent
                agent = YahooAgent()
                return agent.run(mcp_request)

            elif agent_name == "SECAgent":
                from sec_agent import SECAgent
                agent = SECAgent()
                return agent.run(mcp_request)

            elif agent_name == "RedditAgent":
                from reddit_agent import RedditAgent
                agent = RedditAgent()
                return agent.run(mcp_request)

            else:
                self.monitor.log_error("LlamaIndexRouter", f"Unknown agent: {agent_name}")
                return {"error": f"Agent {agent_name} not found"}

        except ImportError as e:
            error_msg = f"Import error for {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Error running {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

    async def route(self, mcp_request: MCPRequest) -> MCPResponse:
        """Main routing logic for processing requests"""
        start_time = datetime.now()
        user_query = mcp_request.context.user_query if mcp_request.context else ""

        try:
            # Extract companies and tickers
            companies = self.extract_companies(user_query)
            tickers = self.map_to_tickers(companies)

            # Determine which agents to run
            agent_names = self.determine_agents(user_query, tickers)

            # Update context
            updated_context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={"agent_names": agent_names},
                version=getattr(mcp_request.context, "version", "1.0")
            )

            updated_request = MCPRequest(
                request_id=mcp_request.request_id,
                context=updated_context
            )

            # Log routing decision
            routing_log = {
                "router": "LlamaIndexRouter",
                "timestamp": start_time.isoformat(),
                "query": user_query,
                "companies": companies,
                "tickers": tickers,
                "agents": agent_names,
                "status": "routing"
            }

            # Run agents concurrently
            tasks = []
            for agent_name in agent_names:
                task = self.run_agent(agent_name, updated_request)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            responses = {}
            context_updates = {}
            overall_status = "success"

            for agent_name, result in zip(agent_names, results):
                agent_key = agent_name.lower().replace("agent", "")

                if isinstance(result, Exception):
                    responses[agent_key] = {"error": str(result)}
                    overall_status = "partial_failure"
                elif result is None:
                    responses[agent_key] = {"error": "Agent returned no response"}
                    overall_status = "partial_failure"
                else:
                    # Handle MCPResponse objects
                    if hasattr(result, 'data'):
                        responses.update(result.data)
                        if hasattr(result, 'context_updates') and result.context_updates:
                            context_updates.update(result.context_updates)
                    elif isinstance(result, dict):
                        responses[agent_key] = result
                    else:
                        responses[agent_key] = {"response": str(result)}

            completed_time = datetime.now()

            # Update routing log
            routing_log.update({
                "completed_timestamp": completed_time.isoformat(),
                "status": overall_status,
                "agents_completed": len(responses)
            })

            # Log results
            try:
                with open("monitor_logs.json", "a") as f:
                    f.write(json.dumps(routing_log) + "\n")
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Logging error: {e}")

            return MCPResponse(
                request_id=mcp_request.request_id,
                data=responses,
                context_updates=context_updates,
                status=overall_status,
                timestamp=completed_time
            )

        except Exception as e:
            error_msg = f"Routing failed: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)

            return MCPResponse(
                request_id=mcp_request.request_id,
                data={"error": error_msg},
                context_updates={},
                status="failed",
                timestamp=datetime.now()
            )