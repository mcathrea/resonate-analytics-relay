# tests/test_ig_data.py
import pytest
import respx
import httpx
from ig_data import get_ig_data

IG_ID = "17841401065753526"
TOKEN = "test_system_user_token"
SINCE = "2026-04-12"
UNTIL = "2026-04-25"

INSIGHTS_RESPONSE = {
    "data": [
        {"name": "reach", "values": [{"value": 1000, "end_time": "2026-04-13"}, {"value": 1345, "end_time": "2026-04-14"}]},
        {"name": "impressions", "values": [{"value": 4000, "end_time": "2026-04-13"}, {"value": 4901, "end_time": "2026-04-14"}]},
        {"name": "profile_views", "values": [{"value": 200, "end_time": "2026-04-13"}, {"value": 367, "end_time": "2026-04-14"}]},
        {"name": "website_clicks", "values": [{"value": 10, "end_time": "2026-04-13"}, {"value": 12, "end_time": "2026-04-14"}]},
    ]
}

FOLLOWER_RESPONSE = {
    "data": [
        {
            "name": "follower_count",
            "values": [
                {"value": 3192, "end_time": "2026-04-12"},
                {"value": 3210, "end_time": "2026-04-25"},
            ],
        }
    ]
}

MEDIA_RESPONSE = {
    "data": [
        {"id": "media_1", "caption": "First reel caption text here", "timestamp": "2026-04-20"},
        {"id": "media_2", "caption": "Second post caption", "timestamp": "2026-04-18"},
        {"id": "media_3", "caption": "Third post", "timestamp": "2026-04-15"},
    ]
}


@pytest.mark.asyncio
@respx.mock
async def test_get_ig_data_success():
    base = f"https://graph.facebook.com/v21.0/{IG_ID}"

    # Insights called twice: metrics + follower_count
    respx.get(f"{base}/insights").mock(
        side_effect=[
            httpx.Response(200, json=INSIGHTS_RESPONSE),
            httpx.Response(200, json=FOLLOWER_RESPONSE),
        ]
    )
    respx.get(f"{base}/media").mock(return_value=httpx.Response(200, json=MEDIA_RESPONSE))

    # Per-media reach calls
    respx.get("https://graph.facebook.com/v21.0/media_1/insights").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "reach", "values": [{"value": 1200}]}]})
    )
    respx.get("https://graph.facebook.com/v21.0/media_2/insights").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "reach", "values": [{"value": 780}]}]})
    )
    respx.get("https://graph.facebook.com/v21.0/media_3/insights").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "reach", "values": [{"value": 340}]}]})
    )

    result = await get_ig_data(TOKEN, IG_ID, SINCE, UNTIL)

    assert result["reach"] == 2345          # 1000 + 1345
    assert result["impressions"] == 8901    # 4000 + 4901
    assert result["profile_views"] == 567   # 200 + 367
    assert result["website_clicks"] == 22   # 10 + 12
    assert result["total_followers"] == 3210
    assert result["new_followers"] == 18    # 3210 - 3192
    assert len(result["top_posts"]) == 3
    assert result["top_posts"][0]["reach"] == 1200


@pytest.mark.asyncio
@respx.mock
async def test_get_ig_data_scope_error():
    base = f"https://graph.facebook.com/v21.0/{IG_ID}"
    respx.get(f"{base}/insights").mock(
        return_value=httpx.Response(
            403,
            json={"error": {"message": "Permission denied", "code": 200}},
        )
    )

    result = await get_ig_data(TOKEN, IG_ID, SINCE, UNTIL)

    assert "error" in result
