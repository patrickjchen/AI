from datetime import datetime
from typing import Dict, Any
from llama_index.llms.openai import OpenAI
from schemas import MCPRequest, MCPResponse
from monitor import MonitorAgent

class GeneralAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.2)

    def run(self, request: MCPRequest) -> MCPResponse:
        """Process general queries using LlamaIndex LLM"""
        start_time = datetime.now()
        user_query = request.context.user_query
        companies = request.context.companies
        status = "processing"

        try:
            # Determine if this is a finance-related query that should be handled by other agents
            if self._is_finance_query(user_query):
                prompt = f"""
                You are a helpful financial assistant. The user has asked: "{user_query}"

                This appears to be a finance-related question. I can provide general guidance, but for detailed financial analysis including:
                - Real-time stock data and analysis
                - SEC filing information
                - Social media sentiment analysis
                - Internal financial document analysis

                You should use the specialized financial agents available in this system.

                However, I can provide general information about: {user_query}

                Please provide a helpful general response while noting that specialized financial agents can provide more detailed analysis.
                """
            else:
                # Handle general non-finance queries
                prompt = f"""
                You are a helpful AI assistant. Please provide a comprehensive and accurate response to the following question:

                {user_query}

                Provide factual, helpful information that directly addresses the user's question.
                """

            response = self.llm.complete(prompt)
            response_text = str(response)

            response_data = {
                "query": user_query,
                "response": response_text,
                "query_type": "finance_related" if self._is_finance_query(user_query) else "general",
                "companies_mentioned": companies if companies else [],
                "timestamp": datetime.now().isoformat()
            }

            status = "success"
            self.monitor.log_health("GeneralAgent", "SUCCESS", f"Processed general query: {user_query[:50]}...")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            response_data = {"error": error_msg, "query": user_query}
            self.monitor.log_error("GeneralAgent", error_msg, {"query": user_query})

        completed_time = datetime.now()

        return MCPResponse(
            request_id=request.request_id,
            data={"general": response_data},
            context_updates={"last_general_query": completed_time.isoformat()},
            status=status,
            timestamp=completed_time
        )

    def _is_finance_query(self, query: str) -> bool:
        """Determine if a query is finance-related"""
        finance_keywords = [
            "stock", "stocks", "investment", "invest", "finance", "financial",
            "bank", "banking", "loan", "credit", "dividend", "equity", "bond",
            "portfolio", "asset", "liability", "revenue", "profit", "earnings",
            "market", "trading", "ticker", "SEC", "10-K", "10-Q", "filing",
            "balance sheet", "income statement", "cash flow", "valuation",
            "P/E ratio", "EPS", "market cap", "merger", "acquisition", "IPO"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in finance_keywords)

    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the BankerAI system"""
        return {
            "system": "BankerAI",
            "version": "2.0 - LlamaIndex Implementation",
            "description": "AI-powered financial analysis system",
            "available_agents": [
                "GeneralAgent - General queries and system information",
                "FinanceAgent - Internal financial document analysis using RAG",
                "YahooAgent - Real-time stock data and analysis",
                "SECAgent - SEC filing analysis",
                "RedditAgent - Social media sentiment analysis"
            ],
            "capabilities": [
                "Multi-agent financial analysis",
                "Real-time stock data processing",
                "SEC filing analysis",
                "Social media sentiment analysis",
                "Document-based RAG analysis",
                "LLM-powered insights and recommendations"
            ]
        }