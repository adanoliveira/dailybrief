"""
Admin configuration for content fetcher app.

Note: This app doesn't have its own models anymore.
All fetching-related data is stored in the Article model in the articles app.
"""

from django.contrib import admin

# No models to register in this app.
# Fetching-related fields are managed through the Article admin in the articles app.
