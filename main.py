# main.py
from mcp.server.fastmcp import FastMCP
from fb_page import get_fb_page_data as _get_fb_page_data
from ig_data import get_ig_data as _get_ig_data
from teams import post_to_teams as _post_to_teams

mcp = FastMCP("resonate-analytics-relay")


@mcp.tool()
async def get_fb_page_data(token: str, page_id: str, since: str, until: str) -> dict:
    """Fetch Facebook Page organic data for a date range.

    Returns reach, impressions, new_followers, profile_views, total_followers,
    and top_posts (list of top 3 by reach with caption and reach count).
    On error, returns {"error": "<description>"}.
    """
    return await _get_fb_page_data(token, page_id, since, until)


@mcp.tool()
async def get_ig_data(token: str, ig_account_id: str, since: str, until: str) -> dict:
    """Fetch Instagram Business Account organic data for a date range.

    Requires instagram_manage_insights scope on the System User token.
    Returns reach, impressions, new_followers, profile_views, website_clicks,
    total_followers, and top_posts (list of top 3 by reach).
    On error, returns {"error": "<description>"}.
    """
    return await _get_ig_data(token, ig_account_id, since, until)


@mcp.tool()
async def post_to_teams(webhook_url: str, message: str) -> dict:
    """Post a message to Microsoft Teams via a Power Automate HTTP webhook.

    Returns {"status": 202} on success or {"error": "HTTP <code>"} on failure.
    """
    return await _post_to_teams(webhook_url, message)


# ASGI app object for gunicorn: gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app
app = mcp.sse_app()
