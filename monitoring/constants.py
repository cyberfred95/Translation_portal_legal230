"""
Constants used across the monitoring module.
"""

# Status colors for admin display
STATUS_COLORS = {
    'success': 'green',
    'warning': 'orange',
    'error': 'red',
}

# User-friendly descriptions for each health check service
SERVICE_DESCRIPTIONS = {
    # Infrastructure
    'Redis': {
        'short': 'Cache & messaging',
        'long': 'Redis is our in-memory data store used for caching frequently accessed data and managing background task queues. It helps make the application faster by storing temporary data in memory rather than constantly querying the database.'
    },
    'PostgreSQL': {
        'short': 'Main database',
        'long': 'PostgreSQL is our primary database where all application data is permanently stored (users, documents, translations, etc.). This check ensures the database is accessible and responding properly to queries.'
    },
    
    # Celery
    'Celery Workers': {
        'short': 'Background task workers',
        'long': 'Celery workers are background processes that handle time-consuming tasks asynchronously (like sending emails, processing documents, etc.) without blocking the main application. This check verifies that workers are active and responsive.'
    },
    'Celery Task Execution': {
        'short': 'Task processing',
        'long': 'This verifies that Celery workers can actually execute tasks successfully. It runs a simple test task to ensure the entire task execution pipeline (from submission to completion) is working properly.'
    },
    
    # External APIs
    'OpenAI': {
        'short': 'AI translation engine',
        'long': 'OpenAI provides the AI-powered translation capabilities used in the application. This check verifies that our API key is valid and that we can successfully communicate with OpenAI\'s services for text translation and processing.'
    },
    'Stripe': {
        'short': 'Payment processing',
        'long': 'Stripe handles all payment processing and subscription management for the application. This check ensures our Stripe integration is working correctly and that we can access account and billing information.'
    },
    'Active Trail': {
        'short': 'Email delivery',
        'long': 'Active Trail is our email service provider that sends automated emails to users (notifications, confirmations, etc.). This check sends a real test email to verify the email delivery system is functioning properly.'
    },
    
    # Translation (LARA Bridge)
    'LARA Text Translation': {
        'short': 'Text translation API',
        'long': 'LARA Bridge provides real-time text translation services. This check verifies that we can successfully send text to LARA and receive accurate translations back, ensuring the core translation functionality is operational.'
    },
    'LARA Document Translation': {
        'short': 'Document translation',
        'long': 'This tests LARA\'s ability to translate entire documents (PDFs, Word files, etc.). It uploads a test document, waits for translation to complete, and then cleans up. This ensures the full document processing pipeline is working.'
    },
    'LARA Glossary': {
        'short': 'Custom terminology',
        'long': 'LARA glossaries allow users to define custom terminology and translations for specialized terms. This check creates a test glossary, verifies it was created successfully, and then removes it to ensure the glossary management system is functioning.'
    },
    
    # Document Processing
    'WeasyPrint PDF Generation': {
        'short': 'PDF creation',
        'long': 'WeasyPrint converts HTML templates into PDF documents (like quotes and reports). This check generates a test PDF from HTML to verify that the PDF generation engine is working correctly and all required system dependencies (fonts, libraries) are available.'
    },
    'Adobe PDF Services': {
        'short': 'PDF to DOCX conversion',
        'long': 'Adobe PDF Services converts PDF documents to DOCX format for editing. This check verifies that our Adobe API credentials are valid, OAuth authentication works, and that we can successfully connect to Adobe\'s PDF Services API.'
    },
    'Document Libraries (docx/pptx)': {
        'short': 'Word/PowerPoint processing',
        'long': 'python-docx and python-pptx are libraries used to extract text from Word and PowerPoint documents. This check verifies that both libraries are installed correctly and can perform basic operations like creating empty documents.'
    },
}

# Health check categories
class HealthCheckCategory:
    """Health check category constants."""
    INFRASTRUCTURE = 'infrastructure'
    EXTERNAL_API = 'external_api'
    TRANSLATION = 'translation'
    DATABASE = 'database'
    DOCKER = 'docker'
    DOCUMENT_PROCESSING = 'document_processing'

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
