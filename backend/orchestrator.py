"""
Data Orchestrator

Replaces the monolithic run_pipeline() by coordinating domain-based processing.
Maintains backward compatibility with dashboard_data.json while enabling
modular domain outputs.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from domains.base import BaseDomain, MetadataDomain, clean_for_json
from domains.currencies import CurrenciesDomain
from domains.core import SharedDomain, GLIDomain, USSystemDomain, M2Domain
from domains.cli import CLIDomain
from domains.treasury import TreasuryDomain
from domains.stablecoins import StablecoinsDomain

logger = logging.getLogger(__name__)


class DataOrchestrator:
    """
    Orchestrates domain-based data processing.
    
    Responsibilities:
    - Coordinate domain processors in correct dependency order
    - Save individual domain JSON files
    - Generate combined dashboard_data.json for backward compatibility
    - Track processing metadata and timing
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize orchestrator.
        
        Args:
            output_dir: Base directory for data output (e.g., backend/data)
        """
        self.output_dir = output_dir
        self.domains_dir = os.path.join(output_dir, 'domains')
        os.makedirs(self.domains_dir, exist_ok=True)
        
        # Register domains in processing order (dependencies first)
        self._domains: List[BaseDomain] = [
            MetadataDomain(),       # Always first - provides shared dates
            SharedDomain(),         # Shared data (BTC, CB balance sheets)
            CurrenciesDomain(),     # DXY, FX pairs
            GLIDomain(),            # Global Liquidity Index
            M2Domain(),             # Global M2 Money Supply
            USSystemDomain(),       # Fed, TGA, RRP, Net Liquidity
            CLIDomain(),            # Credit Liquidity Index
            TreasuryDomain(),       # Yields, curves
            StablecoinsDomain(),    # Stablecoin analytics
            # TODO: Add remaining domains
            # CryptoDomain(),
            # FedForecastsDomain(),
            # MacroRegimeDomain(),
            # OffshoreDomain(),
        ]
        
        self._results: Dict[str, Any] = {}
        self._timing: Dict[str, float] = {}
    
    @property 
    def domains(self) -> List[BaseDomain]:
        """Get list of registered domains."""
        return self._domains
    
    def register_domain(self, domain: BaseDomain) -> None:
        """Register a new domain processor."""
        self._domains.append(domain)
    
    def process_domain(self, domain: BaseDomain, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process a single domain and save its output.
        
        Args:
            domain: Domain processor instance
            df: Main DataFrame with all columns
        
        Returns:
            Processed domain data
        """
        start_time = datetime.now()
        
        try:
            # Process domain, passing previous results as context
            data = domain.process(df, **self._results)
            
            # Save to domain-specific JSON file
            domain.save_json(data, self.output_dir)
            
            # Track results and timing
            self._results[domain.name] = data
            elapsed = (datetime.now() - start_time).total_seconds()
            self._timing[domain.name] = elapsed
            
            logger.info(f"Processed {domain.name} in {elapsed:.2f}s")
            return data
            
        except Exception as e:
            logger.error(f"Error processing {domain.name}: {e}")
            raise
    
    def run(self, df: pd.DataFrame, generate_legacy: bool = True) -> Dict[str, Any]:
        """
        Process all registered domains.
        
        Args:
            df: Main DataFrame with all columns
            generate_legacy: If True, also generate dashboard_data.json
        
        Returns:
            Dict with all domain results
        """
        start_time = datetime.now()
        logger.info(f"Starting orchestration with {len(self._domains)} domains")
        
        # Reset results for new run
        self._results = {}
        self._timing = {}
        
        # Process each domain in order
        for domain in self._domains:
            self.process_domain(domain, df)
        
        # Generate legacy format if requested
        if generate_legacy:
            self._generate_legacy_format(df)
        
        total_elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Orchestration complete in {total_elapsed:.2f}s")
        
        # Save timing metadata
        self._save_timing_metadata(total_elapsed)
        
        return self._results
    
    def _generate_legacy_format(self, df: pd.DataFrame) -> None:
        """
        Generate combined dashboard_data.json for backward compatibility.
        
        This merges domain outputs back into the legacy format that the
        frontend currently expects. Will be deprecated once frontend
        migrates to domain-specific endpoints.
        """
        # Load existing dashboard_data.json if it exists
        legacy_path = os.path.join(self.output_dir, 'dashboard_data.json')
        
        if os.path.exists(legacy_path):
            with open(legacy_path, 'r') as f:
                legacy_data = json.load(f)
        else:
            legacy_data = {}
        
        # Merge domain results into legacy format
        # For now, just update the domains we've processed
        if 'currencies' in self._results:
            legacy_data['currencies'] = self._results['currencies']
        
        if 'metadata' in self._results:
            legacy_data['dates'] = self._results['metadata'].get('dates', [])
            legacy_data['last_dates'] = self._results['metadata'].get('last_dates', {})
            legacy_data['timestamp'] = self._results['metadata'].get('timestamp')
        
        # Save merged legacy format
        with open(legacy_path, 'w') as f:
            json.dump(legacy_data, f)
        
        logger.info(f"Updated legacy dashboard_data.json")
    
    def _save_timing_metadata(self, total_elapsed: float) -> None:
        """Save processing timing metadata."""
        timing_data = {
            'timestamp': datetime.now().isoformat(),
            'total_seconds': total_elapsed,
            'domains': self._timing
        }
        
        timing_path = os.path.join(self.domains_dir, 'processing_metadata.json')
        with open(timing_path, 'w') as f:
            json.dump(timing_data, f, indent=2)
    
    def get_domain_result(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get result for a specific domain from last run."""
        return self._results.get(domain_name)
    
    def load_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Load domain data from saved JSON file."""
        file_path = os.path.join(self.domains_dir, f"{domain_name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None


def create_orchestrator(output_dir: str) -> DataOrchestrator:
    """Factory function to create configured orchestrator."""
    return DataOrchestrator(output_dir)
