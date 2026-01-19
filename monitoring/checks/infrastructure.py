"""
Health checks for infrastructure components (Redis, PostgreSQL, Celery).
"""
import redis
from django.conf import settings
from django.db import connection
from typing import Dict, Any, Optional

from .base import BaseHealthCheck, HealthCheckResult
from ..constants import (
    HealthCheckCategory,
    REDIS_TEST_KEY,
    REDIS_TEST_VALUE,
    REDIS_TEST_EXPIRY_SECONDS,
    DB_TEST_QUERY,
    DB_SIZE_QUERY
)


class RedisHealthCheck(BaseHealthCheck):
    """Check Redis connectivity and basic operations."""
    
    def __init__(self):
        super().__init__()
        self.category = HealthCheckCategory.INFRASTRUCTURE
        self.service_name = 'Redis'
    
    def _check(self) -> HealthCheckResult:
        """Test Redis connection and SET/GET operations."""
        redis_url = settings.CELERY_BROKER_URL
        
        try:
            client = redis.from_url(redis_url)
            
            # Test connectivity
            if not self._test_ping(client):
                return self._create_error_result(
                    message="Redis PING failed",
                    details={'redis_url': redis_url}
                )
            
            # Test operations
            operation_error = self._test_set_get_operations(client)
            if operation_error:
                return operation_error
            
            # Get memory info
            memory_info = self._get_memory_info(client)
            
            return self._create_success_result(
                message="Redis is healthy and responsive",
                details={
                    'redis_url': redis_url,
                    **memory_info
                }
            )
            
        except redis.ConnectionError as e:
            return self._create_error_result(
                message=f"Cannot connect to Redis: {str(e)}",
                error=e
            )
        except Exception as e:
            return self._create_error_result(
                message=f"Redis health check failed: {str(e)}",
                error=e
            )
    
    def _test_ping(self, client: redis.Redis) -> bool:
        """Test Redis PING command."""
        return client.ping()
    
    def _test_set_get_operations(self, client: redis.Redis) -> Optional[HealthCheckResult]:
        """
        Test Redis SET/GET operations.
        
        Returns:
            HealthCheckResult if error occurred, None if successful.
        """
        client.set(REDIS_TEST_KEY, REDIS_TEST_VALUE, ex=REDIS_TEST_EXPIRY_SECONDS)
        retrieved_value = client.get(REDIS_TEST_KEY)
        
        if retrieved_value.decode('utf-8') != REDIS_TEST_VALUE:
            return self._create_error_result(
                message="Redis SET/GET operation failed",
                details={
                    'expected': REDIS_TEST_VALUE,
                    'got': retrieved_value.decode('utf-8')
                }
            )
        
        # Clean up
        client.delete(REDIS_TEST_KEY)
        return None
    
    def _get_memory_info(self, client: redis.Redis) -> Dict[str, Any]:
        """Get Redis memory usage information."""
        info = client.info('memory')
        used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
        return {'used_memory_mb': round(used_memory_mb, 2)}


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
