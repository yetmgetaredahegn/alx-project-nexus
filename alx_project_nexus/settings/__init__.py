"""
Django settings for alx_project_nexus project.

This module automatically loads the appropriate settings based on the
DJANGO_ENV environment variable or defaults to development.

Usage:
    - Development: DJANGO_ENV=development (default)
    - Production: DJANGO_ENV=production
    - Test: DJANGO_ENV=test or use --settings=alx_project_nexus.settings.test
"""
import os

# Determine which environment to use
# Priority: 1. DJANGO_ENV env var, 2. Check if DEBUG is False (production), 3. Default to development
DJANGO_ENV = os.environ.get("DJANGO_ENV", "").lower()

# If DJANGO_ENV is not set, try to infer from other environment variables
if not DJANGO_ENV:
    # Check if we're in production (common indicators)
    if os.environ.get("RENDER") or os.environ.get("DATABASE_URL"):
        # Check if DEBUG is explicitly False
        debug_value = os.environ.get("DEBUG", "").lower()
        if debug_value == "false" or debug_value == "0":
            DJANGO_ENV = "production"
        else:
            # Default to development even if DATABASE_URL exists (could be local dev with remote DB)
            DJANGO_ENV = "development"
    else:
        DJANGO_ENV = "development"

# Load the appropriate settings module
if DJANGO_ENV == "production":
    from .production import *
elif DJANGO_ENV == "test":
    from .test import *
else:  # development (default)
    from .development import *

