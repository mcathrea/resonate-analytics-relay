# ig_data.py
import httpx
from typing import Any, Dict

GRAPH_BASE = "https://graph.facebook.com/v21.0"


async def get_ig_data(
    token: str, ig_account_id: str, since: str, until: str
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Fetch IG account insights — daily values, summed over period
            r = await client.get(
                f"{GRAPH_BASE}/{ig_account_id}/insights",
                params={
                    "metric": "reach,impressions,profile_views,website_clicks",
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

            # Step 2: Fetch follower count daily snapshots for gain + current total
            r = await client.get(
                f"{GRAPH_BASE}/{ig_account_id}/insights",
                params={
                    "metric": "follower_count",
                    "period": "day",
                    "since": since,
                    "until": until,
                    "access_token": token,
                },
            )
            r.raise_for_status()
            follower_data = r.json()["data"]
            follower_values = (
                [v["value"] for v in follower_data[0]["values"]] if follower_data else []
            )
            total_followers = follower_values[-1] if follower_values else 0
            new_followers = (
                follower_values[-1] - follower_values[0]
                if len(follower_values) >= 2
                else 0
            )

            # Step 3: Fetch recent media IDs and captions
            r = await client.get(
                f"{GRAPH_BASE}/{ig_account_id}/media",
                params={
                    "fields": "id,caption,timestamp",
                    "limit": "20",
                    "access_token": token,
                },
            )
            r.raise_for_status()
            media_items = r.json().get("data", [])

            # Step 4: Fetch reach per media item — skip items that return errors
            media_with_reach = []
            for item in media_items:
                try:
                    r2 = await client.get(
                        f"{GRAPH_BASE}/{item['id']}/insights",
                        params={"metric": "reach", "access_token": token},
                    )
                    if r2.status_code == 200:
                        reach = r2.json()["data"][0]["values"][0]["value"]
                        media_with_reach.append(
                            {
                                "caption": item.get("caption", "")[:50],
                                "reach": reach,
                            }
                        )
                except Exception:
                    pass

            top_posts = sorted(media_with_reach, key=lambda m: m["reach"], reverse=True)[:3]

            return {
                "reach": sums.get("reach", 0),
                "impressions": sums.get("impressions", 0),
                "new_followers": new_followers,
                "profile_views": sums.get("profile_views", 0),
                "website_clicks": sums.get("website_clicks", 0),
                "total_followers": total_followers,
                "top_posts": top_posts,
            }
    except Exception as e:
        return {"error": str(e)}
