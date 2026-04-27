# ads_data.py
import httpx
from typing import Any, Dict, Optional

GRAPH_BASE = "https://graph.facebook.com/v21.0"


async def get_ads_data(
    token: str,
    ad_account_id: str,
    since: str,
    until: str,
    prior_since: Optional[str] = None,
    prior_until: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch active campaign insights for a date range.

    prior_since / prior_until are optional — when provided, also fetches
    a comparison period (used by the Tier 1 anomaly alert).
    """
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: List all active campaigns with objective and daily budget
            r = await client.get(
                f"{GRAPH_BASE}/{ad_account_id}/campaigns",
                params={
                    "effective_status": '["ACTIVE"]',
                    "fields": "id,name,objective,daily_budget",
                    "access_token": token,
                },
            )
            r.raise_for_status()
            campaigns = r.json().get("data", [])

            if not campaigns:
                return {"campaigns": [], "total_spend": 0.0, "total_reach": 0, "campaign_count": 0}

            # Step 2: Fetch insights per campaign for current and optional prior period
            campaign_data = []
            total_spend = 0.0
            total_reach = 0

            for campaign in campaigns:
                campaign_id = campaign["id"]

                async def fetch_insights(c_id: str, s: str, u: str) -> Dict[str, Any]:
                    r2 = await client.get(
                        f"{GRAPH_BASE}/{c_id}/insights",
                        params={
                            "fields": "spend,reach,impressions",
                            "time_range": f'{{"since":"{s}","until":"{u}"}}',
                            "access_token": token,
                        },
                    )
                    if r2.status_code != 200:
                        return {}
                    data = r2.json().get("data", [])
                    if not data:
                        return {}
                    row = data[0]
                    return {
                        "spend": float(row.get("spend", 0)),
                        "reach": int(row.get("reach", 0)),
                        "impressions": int(row.get("impressions", 0)),
                    }

                current = await fetch_insights(campaign_id, since, until)
                total_spend += current.get("spend", 0)
                total_reach += current.get("reach", 0)

                prior: Dict[str, Any] = {}
                if prior_since and prior_until:
                    prior = await fetch_insights(campaign_id, prior_since, prior_until)

                campaign_data.append({
                    "id": campaign_id,
                    "name": campaign["name"],
                    "objective": campaign.get("objective", ""),
                    "daily_budget_cents": int(campaign.get("daily_budget", 0)),
                    "current": current,
                    "prior": prior,
                })

            return {
                "campaigns": campaign_data,
                "total_spend": round(total_spend, 2),
                "total_reach": total_reach,
                "campaign_count": len(campaigns),
            }

    except httpx.HTTPStatusError as e:
        try:
            meta_error = e.response.json()
            return {"error": f"HTTP {e.response.status_code}: {meta_error}"}
        except Exception:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}
