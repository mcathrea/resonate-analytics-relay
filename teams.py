import httpx
from typing import Any, Dict


async def post_to_teams(webhook_url: str, message: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                webhook_url,
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )
            if r.status_code in (200, 202):
                return {"status": r.status_code}
            return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}
