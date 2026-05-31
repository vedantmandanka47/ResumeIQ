"""
ResumeIQ — MongoDB MCP Client
Communicates with the MongoDB MCP server via the Google Cloud Agent Builder
runtime (per hackathon partner-track requirement).
Also provides a direct motor fallback for aggregate/benchmark queries.
"""

import logging
from typing import Any

import httpx          # async HTTP — for MCP REST calls
import motor.motor_asyncio as motor   # Rule 2: top-level import

from app.config import get_settings

logger = logging.getLogger(__name__)


# ---------- MCP HTTP Client -------------------------------------------------

async def _mcp_request(
    method: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Sends a request to the MongoDB MCP server endpoint.
    All MCP calls go through here — never call the MCP server directly
    in feature code.
    """
    settings = get_settings()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.mcp_api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                method=method.upper(),
                url=settings.mcp_server_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error("MCP HTTP error %s: %s", exc.response.status_code, exc)
        raise
    except Exception as exc:
        logger.error("MCP request failed: %s", exc)
        raise


# ---------- Direct Motor Client (fallback + benchmarks) --------------------

def _get_motor_client() -> motor.AsyncIOMotorClient:
    """Returns a motor async MongoDB client. Cached per process."""
    settings = get_settings()
    return motor.AsyncIOMotorClient(settings.mongodb_uri)


def _get_collection(collection_name: str):
    """Returns a motor collection handle."""
    settings = get_settings()
    client = _get_motor_client()
    db = client[settings.mongodb_database]
    return db[collection_name]


# ---------- Health Check Helper ---------------------------------------------

async def check_mcp_connection() -> dict[str, Any]:
    """
    Verifies the MongoDB MCP server is reachable.
    Tries the MCP endpoint first; falls back to a direct motor ping.
    Used by GET /health/mcp.
    """
    settings = get_settings()

    # --- Attempt 1: MCP server ping -------------------------------------
    if settings.mcp_server_url:
        try:
            result = await _mcp_request(
                "POST",
                {"action": "listCollections", "database": settings.mongodb_database},
            )
            collections = result.get("collections", result.get("result", []))
            logger.info("MCP health check: OK — collections: %s", collections)
            return {
                "mcp": "connected",
                "transport": "mcp_server",
                "collections": collections,
            }
        except Exception as exc:
            logger.warning("MCP server unreachable, trying direct motor: %s", exc)

    # --- Attempt 2: Direct motor ping (dev fallback) --------------------
    try:
        client = _get_motor_client()
        db = client[settings.mongodb_database]
        collections = await db.list_collection_names()
        logger.info("MongoDB direct health check: OK — collections: %s", collections)
        return {
            "mcp": "connected",
            "transport": "direct_motor",
            "collections": collections,
            "note": "MCP server URL not set — using direct MongoDB connection",
        }
    except Exception as exc:
        logger.error("MongoDB health check failed: %s", exc)
        return {"mcp": "error", "detail": str(exc)}


# ---------- Document Save (via MCP — partner track) --------------------------

async def save_session_snapshot(session_id: str, payload: dict[str, Any]) -> str:
    """
    Saves a complete session snapshot to MongoDB via the MCP server.
    Returns the MongoDB document ID.
    """
    settings = get_settings()
    document = {
        "session_id": session_id,
        **payload,
    }

    if settings.mcp_server_url:
        try:
            result = await _mcp_request(
                "POST",
                {
                    "action": "insertOne",
                    "database": settings.mongodb_database,
                    "collection": "session_snapshots",
                    "document": document,
                },
            )
            return str(result.get("insertedId", "unknown"))
        except Exception as exc:
            logger.warning("MCP insert failed, falling back to motor: %s", exc)

    # Direct motor fallback
    collection = _get_collection("session_snapshots")
    result = await collection.insert_one(document)
    return str(result.inserted_id)


# ---------- Session History -------------------------------------------------

async def get_session_history(session_id: str) -> list[dict[str, Any]]:
    """Retrieves all saved snapshots for a session, ordered by timestamp."""
    collection = _get_collection("session_snapshots")
    cursor = collection.find(
        {"session_id": session_id},
        sort=[("timestamp", -1)],
    )
    docs = await cursor.to_list(length=100)
    # Convert ObjectId to string for JSON serialisation
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


# ---------- Benchmark Aggregation ------------------------------------------

async def get_benchmark_stats() -> dict[str, Any]:
    """
    Aggregates stats across all stored analyses:
    - Average score per dimension
    - Most common critical fixes
    - Most common fresher mode triggers
    """
    collection = _get_collection("session_snapshots")
    try:
        pipeline = [
            {"$match": {"analysis": {"$exists": True}}},
            {"$unwind": "$analysis.dimensions"},
            {
                "$group": {
                    "_id": "$analysis.dimensions.name",
                    "avg_score": {"$avg": "$analysis.dimensions.score"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        dimension_avgs = await collection.aggregate(pipeline).to_list(length=50)
        return {
            "dimension_averages": dimension_avgs,
            "total_analyses": await collection.count_documents(
                {"analysis": {"$exists": True}}
            ),
        }
    except Exception as exc:
        logger.error("Benchmark aggregation failed: %s", exc)
        return {"error": "BENCHMARK_FAILED", "reason": str(exc)}
