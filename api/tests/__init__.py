"""
Test configuration for the Legal230 API.

This module contains shared settings for all API tests.
"""

# Standard library imports
import os
import sys

# Ensure Django uses SQLite for tests
if 'test' in sys.argv:
    os.environ.setdefault('TESTING', 'True')
