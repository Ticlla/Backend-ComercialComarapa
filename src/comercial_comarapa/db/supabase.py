"""Supabase client configuration and connection.

This module provides a singleton Supabase client instance for database operations.
"""

from functools import lru_cache

from supabase import Client, create_client

from comercial_comarapa.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """Get cached Supabase client instance.

    Creates a Supabase client using the configured URL and key.
    The client is cached to ensure a single connection is reused.

    Returns:
        Supabase Client instance.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment variables. "
            "Check your .env file or environment configuration."
        )

    return create_client(settings.supabase_url, settings.supabase_key)


def get_supabase() -> Client:
    """Dependency for FastAPI to inject Supabase client.

    This function is used with FastAPI's Depends() for dependency injection.

    Returns:
        Supabase Client instance.
    """
    return get_supabase_client()


async def check_supabase_connection() -> dict:
    """Check if Supabase connection is working.

    Attempts to connect to Supabase and verify the connection is healthy.

    Returns:
        Dictionary with connection status and details.
    """
    try:
        if not settings.supabase_url or not settings.supabase_key:
            return {
                "status": "not_configured",
                "message": "Supabase credentials not configured",
            }

        client = get_supabase_client()
        # Try a simple query to verify connection
        # This will fail gracefully if tables don't exist yet
        client.table("categories").select("id").limit(1).execute()

        return {
            "status": "connected",
            "message": "Supabase connection successful",
            "url": settings.supabase_url.split("//")[1].split(".")[0],  # Project ID only
        }
    except Exception as e:
        error_msg = str(e)
        # Check if it's just a missing table (which is OK during setup)
        if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
            return {
                "status": "connected",
                "message": "Supabase connected (tables not yet created)",
            }
        return {
            "status": "error",
            "message": f"Supabase connection failed: {error_msg}",
        }

