"""
Supabase/PostgreSQL Database Adapter

Provides connection management and CRUD operations for Supabase.
This adapter will be used when migrating from JSON files to database.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Will be imported when ready to use
# from supabase import create_client, Client


class SupabaseAdapter:
    """
    Database adapter for Supabase PostgreSQL.
    
    Uses environment variables for connection:
    - SUPABASE_URL: Project URL
    - SUPABASE_KEY: Service role key (for server-side operations)
    """
    
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL')
        self.key = os.environ.get('SUPABASE_KEY')
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Supabase client."""
        if self._client is None:
            if not self.url or not self.key:
                raise ValueError(
                    "Supabase credentials not found. "
                    "Set SUPABASE_URL and SUPABASE_KEY environment variables."
                )
            # Import here to avoid dependency issues when not using DB
            from supabase import create_client
            self._client = create_client(self.url, self.key)
        return self._client
    
    def upsert_domain_data(
        self, 
        table_name: str, 
        data: List[Dict[str, Any]],
        on_conflict: str = 'date'
    ) -> Dict[str, Any]:
        """
        Upsert domain data to database table.
        
        Args:
            table_name: Target table name
            data: List of row dictionaries
            on_conflict: Column for conflict resolution
        
        Returns:
            Supabase response with count of affected rows
        """
        if not data:
            logger.warning(f"No data to upsert for {table_name}")
            return {'count': 0}
        
        try:
            response = (
                self.client.table(table_name)
                .upsert(data, on_conflict=on_conflict)
                .execute()
            )
            logger.info(f"Upserted {len(data)} rows to {table_name}")
            return {'count': len(data), 'data': response.data}
        except Exception as e:
            logger.error(f"Error upserting to {table_name}: {e}")
            raise
    
    def get_latest_date(self, table_name: str, date_column: str = 'date') -> Optional[str]:
        """
        Get the most recent date in a table.
        
        Useful for incremental updates.
        """
        try:
            response = (
                self.client.table(table_name)
                .select(date_column)
                .order(date_column, desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0][date_column]
            return None
        except Exception as e:
            logger.error(f"Error getting latest date from {table_name}: {e}")
            return None
    
    def query_domain(
        self, 
        table_name: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query domain data from database.
        
        Args:
            table_name: Source table name
            start_date: Filter start date (inclusive)
            end_date: Filter end date (inclusive)
            columns: Specific columns to select
        
        Returns:
            List of row dictionaries
        """
        try:
            query = self.client.table(table_name)
            
            if columns:
                query = query.select(','.join(columns))
            else:
                query = query.select('*')
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
            
            query = query.order('date', desc=False)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error querying {table_name}: {e}")
            raise


# Singleton instance for convenience
_db_adapter: Optional[SupabaseAdapter] = None


def get_db_adapter() -> SupabaseAdapter:
    """Get or create singleton database adapter."""
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = SupabaseAdapter()
    return _db_adapter
