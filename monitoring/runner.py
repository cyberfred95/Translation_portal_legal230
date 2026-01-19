"""
Health check runner - orchestrates execution of all health checks.
"""
import time
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

from .checks.base import HealthCheckResult as CheckResult, HealthCheckStatus
from .checks.infrastructure import RedisHealthCheck, PostgreSQLHealthCheck
from .models import HealthCheckResult, HealthCheckRun

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    """Summary of a health check run."""
    total_checks: int
    successful_checks: int
    failed_checks: int
    warning_checks: int
    
    @classmethod
    def from_results(cls, results: List[CheckResult]) -> 'RunSummary':
        """Create summary from list of results."""
        return cls(
            total_checks=len(results),
            successful_checks=sum(1 for r in results if r.status == HealthCheckStatus.SUCCESS),
            failed_checks=sum(1 for r in results if r.status == HealthCheckStatus.ERROR),
            warning_checks=sum(1 for r in results if r.status == HealthCheckStatus.WARNING)
        )


def get_all_health_checks() -> List:
    """
    Get list of all health check classes to run.
    
    Returns:
        List of health check class instances.
    """
    return [
        # Infrastructure checks
        RedisHealthCheck(),
        PostgreSQLHealthCheck(),
        
        # TODO: Add more checks as they are implemented
        # External API checks
        # OpenAIHealthCheck(),
        # StripeHealthCheck(),
        # ActiveTrailHealthCheck(),
        # AdobeHealthCheck(),
        
        # Translation checks
        # LaraHealthCheck(),
        # LaraTextTranslationCheck(),
        # LaraDocumentTranslationCheck(),
        # LaraGlossaryCheck(),
        
        # Docker checks
        # DockerLexaHealthCheck(),
        # DockerLaraHealthCheck(),
    ]


def run_single_health_check(health_check) -> CheckResult:
    """
    Run a single health check with error handling.
    
    Args:
        health_check: Health check instance to run
    
    Returns:
        CheckResult with the health check result
    """
    logger.info(f"Running health check: {health_check.service_name}")
    
    try:
        result = health_check.run()
        logger.info(
            f"Health check completed: {health_check.service_name} - "
            f"{result.status.value} ({result.execution_time_ms}ms)"
        )
        return result
    except Exception as e:
        logger.error(f"Health check failed with exception: {health_check.service_name} - {e}")
        # Fallback error result if BaseHealthCheck.run() didn't catch it
        return CheckResult(
            service_name=health_check.service_name,
            status=HealthCheckStatus.ERROR,
            message=f"Unexpected error: {str(e)}",
            category=health_check.category,
            details={'error': str(e), 'error_type': type(e).__name__}
        )


def save_health_check_results(
    results: List[CheckResult],
    summary: RunSummary,
    total_execution_time_ms: int,
    trigger: str
) -> HealthCheckRun:
    """
    Save health check results to database.
    
    Args:
        results: List of health check results
        summary: Summary of the run
        total_execution_time_ms: Total execution time
        trigger: Trigger type ('manual' or 'scheduled')
    
    Returns:
        Created HealthCheckRun instance
    """
    # Save run summary
    run_summary = HealthCheckRun.objects.create(
        trigger=trigger,
        total_checks=summary.total_checks,
        successful_checks=summary.successful_checks,
        failed_checks=summary.failed_checks,
        warning_checks=summary.warning_checks,
        total_execution_time_ms=total_execution_time_ms
    )
    
    # Save individual results
    for result in results:
        HealthCheckResult.objects.create(
            category=result.category,
            service_name=result.service_name,
            status=result.status.value,
            message=result.message,
            details=result.details,
            execution_time_ms=result.execution_time_ms
        )
    
    return run_summary


def run_all_health_checks(trigger: str = 'manual') -> Dict[str, Any]:
    """
    Run all health checks and save results to database.
    
    Args:
        trigger: How the health check was triggered ('manual' or 'scheduled')
    
    Returns:
        Dictionary with summary of results.
    """
    logger.info(f"Starting health check run (trigger: {trigger})")
    start_time = time.time()
    
    # Get all health checks
    health_checks = get_all_health_checks()
    
    # Run each check
    results = [run_single_health_check(hc) for hc in health_checks]
    
    # Calculate summary
    summary = RunSummary.from_results(results)
    total_execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Save to database
    run_summary = save_health_check_results(
        results=results,
        summary=summary,
        total_execution_time_ms=total_execution_time_ms,
        trigger=trigger
    )
    
    logger.info(
        f"Health check run completed: {summary.successful_checks} successful, "
        f"{summary.failed_checks} failed, {summary.warning_checks} warnings "
        f"({total_execution_time_ms}ms total)"
    )
    
    return {
        'run_id': run_summary.id,
        'total_checks': summary.total_checks,
        'successful_checks': summary.successful_checks,
        'failed_checks': summary.failed_checks,
        'warning_checks': summary.warning_checks,
        'total_execution_time_ms': total_execution_time_ms,
        'results': [r.to_dict() for r in results]
    }
