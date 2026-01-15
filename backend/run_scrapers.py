"""
run_scrapers.py
Master orchestrator that runs all scrapers AND data pipeline in a single process,
sharing the same TradingView session for efficiency.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.tv_client import get_tv_session, close_session, TV_AVAILABLE

def main():
    """Run all scrapers and data pipeline with shared TV session."""
    
    # Parse arguments
    force_refresh = '--force' in sys.argv or '-f' in sys.argv
    skip_pipeline = '--no-pipeline' in sys.argv
    only_pipeline = '--only-pipeline' in sys.argv
    
    # Initialize TV session once (shared across all scripts)
    if TV_AVAILABLE:
        print("Initializing shared TradingView session...")
        tv = get_tv_session()
        if tv:
            print("[OK] TradingView session ready")
        else:
            print("[WARN] Running without authenticated TV session")
    else:
        print("[WARN] TvDatafeed not available - scrapers may fail")
    
    if not only_pipeline:
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
    
    if not skip_pipeline:
        # Run Data Pipeline (reuses same session)
        print("\n" + "="*50)
        print("RUNNING: data_pipeline.py")
        print("="*50)
        try:
            import data_pipeline
            data_pipeline.run_pipeline()
        except Exception as e:
            print(f"Error in data_pipeline: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    close_session()
    print("\n[OK] All tasks completed")

if __name__ == "__main__":
    main()

