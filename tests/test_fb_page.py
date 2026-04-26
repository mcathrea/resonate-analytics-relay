# tests/test_fb_page.py
import pytest
import respx
import httpx
from fb_page import get_fb_page_data

PAGE_ID = "296571737122013"
TOKEN = "test_system_user_token"
SINCE = "2026-04-12"
UNTIL = "2026-04-25"

INSIGHTS_RESPONSE = {
    "data": [
        {
            "name": "page_impressions_unique",
            "values": [{"value": 100, "end_time": "2026-04-13"}, {"value": 200, "end_time": "2026-04-14"}],
        },
        {
            "name": "page_impressions",
            "values": [{"value": 500, "end_time": "2026-04-13"}, {"value": 600, "end_time": "2026-04-14"}],
        },
        {
            "name": "page_follows",
            "values": [{"value": 5, "end_time": "2026-04-13"}, {"value": 3, "end_time": "2026-04-14"}],
        },
        {
            "name": "page_views_total",
            "values": [{"value": 50, "end_time": "2026-04-13"}, {"value": 60, "end_time": "2026-04-14"}],
        },
    ]
}

POSTS_RESPONSE = {
    "data": [
        {"message": "Third post text here", "post_impressions_unique": 210},
        {"message": "First post text here — the highest reach post by far", "post_impressions_unique": 890},
        {"message": "Second post text", "post_impressions_unique": 450},
    ]
}


@pytest.mark.asyncio
@respx.mock
async def test_get_fb_page_data_success():
    base_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}"

    # Call 1: token exchange, Call 2: fan count — same URL, different params
    respx.get(base_url).mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "PAGE_TOKEN", "id": PAGE_ID}),
            httpx.Response(200, json={"fan_count": 1890, "id": PAGE_ID}),
        ]
    )
    respx.get(f"{base_url}/insights").mock(return_value=httpx.Response(200, json=INSIGHTS_RESPONSE))
    respx.get(f"{base_url}/posts").mock(return_value=httpx.Response(200, json=POSTS_RESPONSE))

    result = await get_fb_page_data(TOKEN, PAGE_ID, SINCE, UNTIL)

    assert result["reach"] == 300          # 100 + 200
    assert result["impressions"] == 1100   # 500 + 600
    assert result["new_followers"] == 8    # 5 + 3
    assert result["profile_views"] == 110  # 50 + 60
    assert result["total_followers"] == 1890
    assert len(result["top_posts"]) == 3
    # Top 3 sorted by reach descending
    assert result["top_posts"][0]["reach"] == 890
    assert result["top_posts"][1]["reach"] == 450
    assert result["top_posts"][2]["reach"] == 210
    # Captions truncated to 50 chars
    assert len(result["top_posts"][0]["caption"]) <= 50


@pytest.mark.asyncio
@respx.mock
async def test_get_fb_page_data_token_exchange_fails():
    base_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}"
    respx.get(base_url).mock(return_value=httpx.Response(400, json={"error": {"message": "Invalid token"}}))

    result = await get_fb_page_data(TOKEN, PAGE_ID, SINCE, UNTIL)

    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_fb_page_data_insights_fail():
    base_url = f"https://graph.facebook.com/v21.0/{PAGE_ID}"
    respx.get(base_url).mock(
        return_value=httpx.Response(200, json={"access_token": "PAGE_TOKEN", "id": PAGE_ID})
    )
    respx.get(f"{base_url}/insights").mock(return_value=httpx.Response(403, json={"error": {"message": "Permission denied"}}))

    result = await get_fb_page_data(TOKEN, PAGE_ID, SINCE, UNTIL)

    assert "error" in result
