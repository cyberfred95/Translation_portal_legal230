"""
Celery tasks for scheduled health checks.
"""
from celery import shared_task
import logging

from .runner import run_all_health_checks

logger = logging.getLogger(__name__)


@shared_task(name='monitoring.run_scheduled_health_checks')
def run_scheduled_health_checks():
    """
    Celery task to run all health checks on a schedule.
    
    This task should be configured in Celery Beat schedule to run daily.
    """
    logger.info("Starting scheduled health check run")
    
    try:
        result = run_all_health_checks(trigger='scheduled')
        
        if result['failed_checks'] > 0:
            logger.error(
                f"Scheduled health checks completed with {result['failed_checks']} failures"
            )
        else:
            logger.info(
                f"Scheduled health checks completed successfully: "
                f"{result['successful_checks']} passed, {result['warning_checks']} warnings"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error running scheduled health checks: {e}", exc_info=True)
        raise
