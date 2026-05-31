"""MongoDB MCP integration with an explicit Atlas fallback."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _database_name() -> str:
    return os.environ.get("MONGODB_DATABASE", "resumeiq")


def _collection_name() -> str:
    return os.environ.get("MONGODB_COLLECTION", "analyses")


async def _call_mcp(
    operation: str,
    payload: dict[str, Any],
    *,
    allow_fallback: bool = True,
) -> dict[str, Any]:
    """Call the MCP endpoint and use direct MongoDB only when explicitly allowed."""
    session_id = payload.get("session_id", "unknown")
    timestamp = datetime.now(timezone.utc).isoformat()
    endpoint = os.environ.get("MONGODB_MCP_SERVER_URL", "")
    try:
        if not endpoint:
            raise RuntimeError("MONGODB_MCP_SERVER_URL is not configured")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                endpoint,
                json={
                    "operation": operation,
                    "database": _database_name(),
                    "collection": _collection_name(),
                    "payload": payload,
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise RuntimeError("MCP server returned a non-object response")
            logger.info(
                "MCP call success | operation=%s | session_id=%s | timestamp=%s",
                operation,
                session_id,
                timestamp,
            )
            return result
    except Exception as exc:
        logger.warning(
            "MCP call failed | operation=%s | session_id=%s | timestamp=%s | error=%s",
            operation,
            session_id,
            timestamp,
            exc,
        )
        if not allow_fallback:
            return {"error": "MCP_UNREACHABLE", "reason": str(exc)}
        return await _pymongo_fallback(operation, payload)


def _run_pymongo(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    import pymongo  # Optional direct driver is loaded only when fallback is needed.

    uri = os.environ.get("MONGODB_ATLAS_URI")
    if not uri:
        raise RuntimeError("MONGODB_ATLAS_URI is not configured")

    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        database = client[_database_name()]
        collection = database[_collection_name()]
        if operation == "list_collections":
            return {"collections": database.list_collection_names()}
        if operation == "insert":
            result = collection.insert_one(payload)
            return {"inserted_id": str(result.inserted_id)}
        if operation == "find":
            documents = list(
                collection.find(
                    {"session_id": payload["session_id"]},
                    sort=[("timestamp", pymongo.DESCENDING)],
                )
            )
            for document in documents:
                document["_id"] = str(document["_id"])
            return {"documents": documents}
        if operation == "aggregate":
            return {"documents": list(collection.aggregate(payload.get("pipeline", [])))}
        return {"error": "UNKNOWN_OPERATION", "reason": f"Unknown MCP operation: {operation}"}
    finally:
        client.close()


async def _pymongo_fallback(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the synchronous MongoDB driver outside the event loop."""
    logger.warning("Using pymongo fallback for operation=%s", operation)
    try:
        return await asyncio.to_thread(_run_pymongo, operation, payload)
    except Exception as exc:
        logger.error("pymongo fallback failed: %s", exc, exc_info=True)
        return {"error": "MONGO_FALLBACK_FAILED", "reason": str(exc)}


async def save_to_mongo(
    session_id: str,
    analysis: dict[str, Any] | None,
    company_result: dict[str, Any] | None,
    rewrite_result: dict[str, Any] | None,
    roadmap: dict[str, Any] | None,
) -> str | dict[str, Any]:
    """Persist the complete current session snapshot via MongoDB MCP."""
    analysis = analysis or {}
    document = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": analysis.get("mode", "general"),
        "overall_score": analysis.get("overall_score"),
        "analysis": analysis or None,
        "company_result": company_result,
        "rewrite_result": rewrite_result,
        "roadmap": roadmap,
    }
    result = await _call_mcp("insert", document)
    if "error" in result:
        return result
    return str(result.get("inserted_id", "unknown"))


async def get_history(session_id: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Return session snapshots ordered newest first."""
    result = await _call_mcp("find", {"session_id": session_id})
    if "error" in result:
        return result
    return result.get("documents", [])


async def get_benchmark() -> dict[str, Any]:
    """Aggregate useful comparison statistics across saved session snapshots."""
    pipeline = [
        {
            "$facet": {
                "summary": [
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": 1},
                            "average_overall_score": {"$avg": "$overall_score"},
                        }
                    }
                ],
                "dimensions": [
                    {"$unwind": "$analysis.dimensions"},
                    {
                        "$group": {
                            "_id": "$analysis.dimensions.name",
                            "average_score": {"$avg": "$analysis.dimensions.score"},
                        }
                    },
                    {"$project": {"_id": 0, "name": "$_id", "average_score": {"$round": ["$average_score", 1]}}},
                    {"$sort": {"name": 1}},
                ],
                "fixes": [
                    {"$unwind": "$analysis.critical_fixes"},
                    {"$group": {"_id": "$analysis.critical_fixes.issue", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5},
                    {"$project": {"_id": 0, "issue": "$_id", "count": 1}},
                ],
            }
        }
    ]
    result = await _call_mcp("aggregate", {"pipeline": pipeline})
    if "error" in result:
        return result
    documents = result.get("documents", [])
    if not documents:
        return {"total_resumes_analyzed": 0, "dimension_averages": [], "most_common_fixes": []}

    facets = documents[0]
    summary = facets.get("summary", [])
    summary_row = summary[0] if summary else {}
    return {
        "total_resumes_analyzed": summary_row.get("total", 0),
        "average_overall_score": summary_row.get("average_overall_score"),
        "dimension_averages": facets.get("dimensions", []),
        "most_common_fixes": facets.get("fixes", []),
    }

