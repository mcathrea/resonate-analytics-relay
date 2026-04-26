# fb_page.py
import httpx
from typing import Any, Dict

GRAPH_BASE = "https://graph.facebook.com/v21.0"


async def get_fb_page_data(
    token: str, page_id: str, since: str, until: str
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            # System User tokens can call Page Insights directly — no page token exchange needed.
            # The exchange requires pages_manage_metadata scope which System Users typically lack.

            # Step 1: Fetch Page Insights — daily values, summed over period
            r = await client.get(
                f"{GRAPH_BASE}/{page_id}/insights",
                params={
                    "metric": "page_impressions_unique,page_impressions,page_views_total",
                    "period": "day",
                    "since": since,
                    "until": until,
                    "access_token": token,
                },
            )
            r.raise_for_status()
            sums: Dict[str, int] = {}
            for metric in r.json()["data"]:
                sums[metric["name"]] = sum(v["value"] for v in metric["values"])

            # Step 2: Fetch current total followers (point-in-time)
            r = await client.get(
                f"{GRAPH_BASE}/{page_id}",
                params={"fields": "fan_count", "access_token": token},
            )
            r.raise_for_status()
            total_followers = r.json()["fan_count"]

            # Step 3: Fetch top 3 posts by reach
            r = await client.get(
                f"{GRAPH_BASE}/{page_id}/posts",
                params={
                    "fields": "message,post_impressions_unique",
                    "limit": "20",
                    "access_token": token,
                },
            )
            r.raise_for_status()
            posts = r.json().get("data", [])
            posts_sorted = sorted(
                posts,
                key=lambda p: p.get("post_impressions_unique", 0),
                reverse=True,
            )
            top_posts = [
                {
                    "caption": p.get("message", "")[:50],
                    "reach": p.get("post_impressions_unique", 0),
                }
                for p in posts_sorted[:3]
            ]

            return {
                "reach": sums.get("page_impressions_unique", 0),
                "impressions": sums.get("page_impressions", 0),
                "new_followers": 0,  # page_follows deprecated in Graph API v21 — omitted
                "profile_views": sums.get("page_views_total", 0),
                "total_followers": total_followers,
                "top_posts": top_posts,
            }
    except httpx.HTTPStatusError as e:
        try:
            meta_error = e.response.json()
            return {"error": f"HTTP {e.response.status_code}: {meta_error}"}
        except Exception:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}
