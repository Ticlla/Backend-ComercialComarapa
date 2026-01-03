"""Database health check functionality.

This module provides health check utilities for verifying database connectivity.
"""

from __future__ import annotations

from comercial_comarapa.config import settings


async def check_db_connection() -> dict:
    """Check if database connection is working.

    Returns:
        Dictionary with connection status and details.
    """
    try:
        if settings.is_local_db:
            from comercial_comarapa.db.database import get_db_client  # noqa: PLC0415

            client = get_db_client()
            # Try a simple query to verify connection
            client.table("categories").select("id").limit(1).execute()
            return {
                "status": "connected",
                "mode": "local",
                "message": "Local PostgreSQL connection successful",
            }
        elif settings.is_supabase_db:
            from comercial_comarapa.db.supabase import (  # noqa: PLC0415
                check_supabase_connection,
            )

            return await check_supabase_connection()
        else:
            return {
                "status": "error",
                "message": f"Invalid DATABASE_MODE: {settings.database_mode}",
            }
    except Exception as e:
        error_msg = str(e)
        # Check if it's just a missing table (OK during initial setup)
        if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
            return {
                "status": "connected",
                "mode": settings.database_mode,
                "message": "Database connected (tables not yet created)",
            }
        return {
            "status": "error",
            "mode": settings.database_mode,
            "message": f"Database connection failed: {error_msg}",
        }


