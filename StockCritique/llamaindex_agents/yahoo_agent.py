import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
from llama_index.llms.openai import OpenAI
from schemas import MCPRequest, MCPResponse
from monitor import MonitorAgent

class YahooAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

    def _fetch_stock_data(self, ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """Fetch stock data for a given ticker"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)

            if data.empty:
                return {"error": f"No data found for {ticker}"}

            # Calculate statistics
            close_prices = data['Close']
            min_price = float(close_prices.min())
            max_price = float(close_prices.max())
            mean_price = float(close_prices.mean())
            last_close = float(close_prices.iloc[-1])
            std_dev = float(close_prices.std())

            # Calculate percentage change
            pct_change = float(((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100) if close_prices.iloc[0] != 0 else 0

            # Calculate annualized volatility
            volatility = float(close_prices.pct_change().std() * (252 ** 0.5) * 100)

            # Get additional info
            info = stock.info
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'Unknown')
            market_cap = info.get('marketCap', 'Unknown')

            return {
                "ticker": ticker,
                "company_name": company_name,
                "sector": sector,
                "market_cap": market_cap,
                "period": period,
                "statistics": {
                    "min_close": min_price,
                    "max_close": max_price,
                    "mean_close": mean_price,
                    "std_dev_30d": std_dev,
                    "percent_change_30d": pct_change,
                    "volatility_annualized": volatility,
                    "last_close": last_close
                },
                "data_points": len(data)
            }

        except Exception as e:
            return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}

    def _analyze_with_llm(self, stock_data: Dict[str, Any], user_query: str) -> str:
        """Use LLM to analyze stock data and provide insights"""
        try:
            if "error" in stock_data:
                return stock_data["error"]

            stats = stock_data["statistics"]
            prompt = f"""
            As a financial analyst, analyze the following 30-day stock data for {stock_data['ticker']} ({stock_data.get('company_name', 'Unknown')}) and respond to the user's query: "{user_query}"

            Stock Information:
            - Company: {stock_data.get('company_name', 'Unknown')}
            - Sector: {stock_data.get('sector', 'Unknown')}
            - Market Cap: {stock_data.get('market_cap', 'Unknown')}

            30-Day Statistics:
            - Current Price: ${stats['last_close']:.2f}
            - Price Range: ${stats['min_close']:.2f} - ${stats['max_close']:.2f}
            - Average Price: ${stats['mean_close']:.2f}
            - 30-Day Return: {stats['percent_change_30d']:.2f}%
            - Volatility (Annualized): {stats['volatility_annualized']:.2f}%
            - Standard Deviation: ${stats['std_dev_30d']:.2f}

            Please provide:
            1. A brief analysis of the stock's recent performance
            2. Notable trends or patterns
            3. Risk assessment based on volatility
            4. Any relevant insights related to the user's specific query

            Keep the response concise and professional.
            """

            response = self.llm.complete(prompt)
            return str(response)

        except Exception as e:
            return f"Analysis error: {str(e)}"

    def run(self, request: MCPRequest) -> MCPResponse:
        """Process Yahoo Finance query using LlamaIndex LLM"""
        start_time = datetime.now()
        tickers = request.context.tickers
        user_query = request.context.user_query
        response_data = []
        status = "processing"

        try:
            if not tickers:
                return MCPResponse(
                    request_id=request.request_id,
                    data={"yahoo": {"error": "No tickers provided"}},
                    status="failed",
                    timestamp=datetime.now()
                )

            for ticker in tickers:
                # Fetch stock data
                stock_data = self._fetch_stock_data(ticker)

                if "error" in stock_data:
                    ticker_response = {
                        "ticker": ticker,
                        "error": stock_data["error"]
                    }
                else:
                    # Analyze with LLM
                    analysis = self._analyze_with_llm(stock_data, user_query)

                    ticker_response = {
                        "ticker": ticker,
                        "company_name": stock_data.get("company_name", ticker),
                        "sector": stock_data.get("sector", "Unknown"),
                        "market_cap": stock_data.get("market_cap", "Unknown"),
                        "statistics": stock_data["statistics"],
                        "llm_analysis": analysis,
                        "data_period": stock_data.get("period", "1mo"),
                        "data_points": stock_data.get("data_points", 0)
                    }

                response_data.append(ticker_response)

            status = "success"
            self.monitor.log_health("YahooAgent", "SUCCESS", f"Processed {len(tickers)} tickers")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            response_data = {"error": error_msg}
            self.monitor.log_error("YahooAgent", error_msg, {"tickers": tickers, "query": user_query})

        completed_time = datetime.now()

        return MCPResponse(
            request_id=request.request_id,
            data={"yahoo": response_data},
            context_updates={"last_yahoo_query": completed_time.isoformat()},
            status=status,
            timestamp=completed_time
        )

    def get_market_summary(self, tickers: List[str]) -> Dict[str, Any]:
        """Get a market summary for multiple tickers"""
        try:
            summary_data = []
            for ticker in tickers:
                data = self._fetch_stock_data(ticker)
                if "error" not in data:
                    summary_data.append({
                        "ticker": ticker,
                        "company": data.get("company_name", ticker),
                        "last_price": data["statistics"]["last_close"],
                        "change_30d": data["statistics"]["percent_change_30d"],
                        "volatility": data["statistics"]["volatility_annualized"]
                    })

            return {"market_summary": summary_data}

        except Exception as e:
            self.monitor.log_error("YahooAgent", f"Market summary error: {e}")
            return {"error": str(e)}