#!/usr/bin/env python3
"""
Debug script to test router logic
"""

from router import LlamaIndexRouter

def test_amazon_query():
    router = LlamaIndexRouter()
    query = "amazon"

    print(f"Testing query: '{query}'")
    print("=" * 50)

    # Test company extraction
    companies = router.extract_companies(query)
    print(f"Extracted companies: {companies}")

    # Test ticker mapping
    tickers = router.map_to_tickers(companies)
    print(f"Mapped tickers: {tickers}")

    # Test finance query detection
    is_finance = router.is_finance_query(query)
    print(f"Is finance query: {is_finance}")

    # Test agent determination
    agents = router.determine_agents(query, tickers)
    print(f"Selected agents: {agents}")

    print("\nExpected agents for Amazon query:")
    print("Should include: FinanceAgent, YahooAgent, SECAgent, RedditAgent, GeneralAgent")

if __name__ == "__main__":
    test_amazon_query()