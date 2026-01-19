"""
Constants used across the monitoring module.
"""

# Status colors for admin display
STATUS_COLORS = {
    'success': 'green',
    'warning': 'orange',
    'error': 'red',
}

# Health check categories
class HealthCheckCategory:
    """Health check category constants."""
    INFRASTRUCTURE = 'infrastructure'
    EXTERNAL_API = 'external_api'
    TRANSLATION = 'translation'
    DATABASE = 'database'
    DOCKER = 'docker'

# Redis health check constants
REDIS_TEST_KEY = 'health_check_test'
REDIS_TEST_VALUE = 'ok'
REDIS_TEST_EXPIRY_SECONDS = 10

# Database health check constants
DB_TEST_QUERY = "SELECT 1"
DB_SIZE_QUERY = "SELECT pg_database_size(current_database()) / (1024 * 1024) as size_mb"

# Celery health check constants
CELERY_TASK_TIMEOUT_SECONDS = 5
CELERY_TASK_EXPIRES_SECONDS = 10
CELERY_TEST_TASK_INPUT = 'health_check'
CELERY_TEST_TASK_EXPECTED_OUTPUT = 'health_check_ok'
CELERY_PING_EXPECTED_RESPONSE = 'pong'

# External API health check constants
API_KEY_MASK_PREFIX_LENGTH = 8
API_KEY_MASK_SUFFIX_LENGTH = 4
API_REQUEST_TIMEOUT_SECONDS = 5

# LARA Bridge health check constants
LARA_TEST_TEXT_SOURCE = "Hello world"
LARA_TEST_TEXT_TARGET_LANGUAGE = "fr"
LARA_TEST_TEXT_SOURCE_LANGUAGE = "en"
LARA_REQUEST_TIMEOUT_SECONDS = 30
