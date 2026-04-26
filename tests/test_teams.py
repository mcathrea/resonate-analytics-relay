import pytest
import respx
import httpx
from teams import post_to_teams


@pytest.mark.asyncio
@respx.mock
async def test_post_to_teams_success():
    webhook_url = "https://example.powerplatform.com/webhook"
    respx.post(webhook_url).mock(return_value=httpx.Response(202))

    result = await post_to_teams(webhook_url, "Test message")

    assert result == {"status": 202}


@pytest.mark.asyncio
@respx.mock
async def test_post_to_teams_failure():
    webhook_url = "https://example.powerplatform.com/webhook"
    respx.post(webhook_url).mock(return_value=httpx.Response(500))

    result = await post_to_teams(webhook_url, "Test message")

    assert result == {"error": "HTTP 500"}


@pytest.mark.asyncio
@respx.mock
async def test_post_to_teams_network_error():
    webhook_url = "https://example.powerplatform.com/webhook"
    respx.post(webhook_url).mock(side_effect=httpx.ConnectError("connection refused"))

    result = await post_to_teams(webhook_url, "Test message")

    assert "error" in result
