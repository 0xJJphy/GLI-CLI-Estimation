"""
run_scrapers.py
Orchestrator script that runs all scrapers in a single process,
sharing the same TradingView session for efficiency.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.tv_client import get_tv_session, close_session, TV_AVAILABLE

def main():
    """Run all supplementary scrapers with shared TV session."""
    
    # Parse arguments
    force_refresh = '--force' in sys.argv or '-f' in sys.argv
    
    # Initialize TV session once
    if TV_AVAILABLE:
        print("Initializing shared TradingView session...")
        tv = get_tv_session()
        if tv:
            print("✓ TradingView session ready")
        else:
            print("⚠ Running without authenticated TV session")
    else:
        print("⚠ TvDatafeed not available - scrapers may fail")
    
    # Run Index scraper
    print("\n" + "="*50)
    print("RUNNING: scraper_indexes.py")
    print("="*50)
    try:
        from scrapers import scraper_indexes
        scraper_indexes.run_scraper(force_refresh=force_refresh)
    except Exception as e:
        print(f"Error in scraper_indexes: {e}")
    
    # Run Commodities scraper (reuses same session)
    print("\n" + "="*50)
    print("RUNNING: scraper_commodities.py")
    print("="*50)
    try:
        from scrapers import scraper_commodities
        scraper_commodities.run_scraper(force_refresh=force_refresh)
    except Exception as e:
        print(f"Error in scraper_commodities: {e}")
    
    # Cleanup
    close_session()
    print("\n✓ All scrapers completed")

if __name__ == "__main__":
    main()
