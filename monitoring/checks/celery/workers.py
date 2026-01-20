"""
Celery workers health check.
"""
import logging
from typing import Dict, Any, List
from celery.app.control import Inspect

from .base import BaseCeleryHealthCheck
from ..base import HealthCheckResult
from ...constants import CELERY_PING_EXPECTED_RESPONSE

logger = logging.getLogger(__name__)


class CeleryWorkersHealthCheck(BaseCeleryHealthCheck):
    """
    Check Celery workers availability and responsiveness.
    
    Verifies:
    - At least one worker is active
    - Workers can respond to ping
    - Workers have registered tasks
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'Celery Workers'
    
    def _check(self) -> HealthCheckResult:
        """Test Celery workers status and responsiveness."""
        try:
            inspector = self._get_inspector()
            
            # Get active workers
            active_workers = self._get_active_workers(inspector)
            if not active_workers:
                return self._create_error_result(
                    message="No active Celery workers found",
                    details={'active_workers': 0}
                )
            
            # Test worker ping
            ping_error = self._verify_worker_ping(inspector)
            if ping_error:
                return ping_error
            
            # Collect worker information
            worker_info = self._collect_worker_info(inspector, active_workers)
            
            return self._create_success_result(
                message=f"Celery is healthy with {len(active_workers)} active worker(s)",
                details=worker_info
            )
            
        except Exception as e:
            return self._create_error_result(
                message=f"Celery health check failed: {str(e)}",
                error=e
            )
    
    def _get_active_workers(self, inspector: Inspect) -> List[str]:
        """Get list of active worker names."""
        active = inspector.active()
        return list(active.keys()) if active else []
    
    def _verify_worker_ping(self, inspector: Inspect) -> HealthCheckResult:
        """
        Verify workers respond to ping.
        
        Returns:
            HealthCheckResult if error, None if successful
        """
        ping_response = inspector.ping()
        
        if not ping_response:
            return self._create_error_result(
                message="No ping response from workers"
            )
        
        successful_pings = self._count_successful_pings(ping_response)
        
        if successful_pings == 0:
            return self._create_error_result(
                message="Workers did not respond with pong",
                details={'total_workers': len(ping_response)}
            )
        
        return None
    
    def _count_successful_pings(self, ping_response: dict) -> int:
        """Count number of successful ping responses."""
        return sum(
            1 for response in ping_response.values()
            if response and response.get('ok') == CELERY_PING_EXPECTED_RESPONSE
        )
    
    def _collect_worker_info(self, inspector: Inspect, worker_names: List[str]) -> Dict[str, Any]:
        """
        Collect comprehensive worker information.
        
        Args:
            inspector: Celery inspector instance
            worker_names: List of active worker names
        
        Returns:
            Dictionary with worker information
        """
        stats = self._get_worker_stats(inspector, worker_names)
        registered_tasks = self._get_registered_tasks(inspector)
        
        return {
            'active_workers': len(worker_names),
            'worker_names': worker_names,
            'total_registered_tasks': len(registered_tasks),
            'stats': stats
        }
    
    def _get_worker_stats(self, inspector: Inspect, worker_names: List[str]) -> Dict[str, int]:
        """
        Get aggregated statistics from workers.
        
        Args:
            inspector: Celery inspector instance
            worker_names: List of worker names
        
        Returns:
            Dictionary with aggregated stats
        """
        try:
            stats = inspector.stats()
            if not stats:
                return {}
            
            return {
                'total_pool_size': self._sum_pool_sizes(stats, worker_names),
                'total_prefetch': self._sum_prefetch_counts(stats, worker_names)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get worker stats: {e}")
            return {}
    
    def _sum_pool_sizes(self, stats: dict, worker_names: List[str]) -> int:
        """Sum pool sizes across all workers."""
        return sum(
            stats.get(name, {}).get('pool', {}).get('max-concurrency', 0)
            for name in worker_names
        )
    
    def _sum_prefetch_counts(self, stats: dict, worker_names: List[str]) -> int:
        """Sum prefetch counts across all workers."""
        return sum(
            stats.get(name, {}).get('prefetch_count', 0)
            for name in worker_names
        )
    
    def _get_registered_tasks(self, inspector: Inspect) -> List[str]:
        """
        Get list of registered tasks across all workers.
        
        Args:
            inspector: Celery inspector instance
        
        Returns:
            Sorted list of unique registered task names
        """
        try:
            registered = inspector.registered()
            if not registered:
                return []
            
            # Collect all unique task names
            all_tasks = set()
            for worker_tasks in registered.values():
                all_tasks.update(worker_tasks)
            
            return sorted(list(all_tasks))
            
        except Exception as e:
            logger.warning(f"Failed to get registered tasks: {e}")
            return []
