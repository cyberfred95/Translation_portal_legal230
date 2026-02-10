"""
PostgreSQL health check.
"""
from django.conf import settings
from django.db import connection
from typing import Dict, Optional

from ..base import BaseHealthCheck, HealthCheckResult
from ...constants import (
    HealthCheckCategory,
    DB_TEST_QUERY,
    DB_SIZE_QUERY
)


class PostgreSQLHealthCheck(BaseHealthCheck):
    """Check PostgreSQL database connectivity and basic operations."""
    
    def __init__(self):
        super().__init__()
        self.category = HealthCheckCategory.DATABASE
        self.service_name = 'PostgreSQL'
    
    def _check(self) -> HealthCheckResult:
        """Test database connection and query execution."""
        try:
            with connection.cursor() as cursor:
                # Test basic query
                query_error = self._test_basic_query(cursor)
                if query_error:
                    return query_error
                
                # Get database metrics
                db_size = self._get_database_size(cursor)
                db_info = self._get_database_info()
                
                return self._create_success_result(
                    message="PostgreSQL is healthy and responsive",
                    details={
                        **db_info,
                        'size_mb': db_size
                    }
                )
                
        except Exception as e:
            return self._create_error_result(
                message=f"Database health check failed: {str(e)}",
                error=e
            )
    
    def _test_basic_query(self, cursor) -> Optional[HealthCheckResult]:
        """
        Test basic database query.
        
        Returns:
            HealthCheckResult if error occurred, None if successful.
        """
        cursor.execute(DB_TEST_QUERY)
        result = cursor.fetchone()
        
        if result[0] != 1:
            return self._create_error_result(
                message="Database query returned unexpected result",
                details={'expected': 1, 'got': result[0]}
            )
        
        return None
    
    def _get_database_size(self, cursor) -> Optional[float]:
        """Get database size in MB."""
        cursor.execute(DB_SIZE_QUERY)
        size_result = cursor.fetchone()
        return round(size_result[0], 2) if size_result else None
    
    def _get_database_info(self) -> Dict[str, str]:
        """Get database connection information."""
        db_settings = settings.DATABASES['default']
        return {
            'database': db_settings.get('NAME'),
            'host': db_settings.get('HOST')
        }
