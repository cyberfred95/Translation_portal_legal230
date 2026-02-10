"""
Monitoring module for Lexa application health checks.

This module provides comprehensive health monitoring for all external services,
infrastructure components, and critical functionality used by Lexa.

Main components:
- models: Database models for storing health check results
- checks: Individual health check implementations
- runner: Orchestrator for running all health checks
- tasks: Celery tasks for scheduled execution
- admin: Admin interface for manual execution and viewing results
"""

default_app_config = 'monitoring.apps.MonitoringConfig'
