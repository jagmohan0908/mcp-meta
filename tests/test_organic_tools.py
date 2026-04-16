import json
from unittest.mock import AsyncMock, patch

import pytest

from meta_ads_mcp.core.organic import (
    get_page_insights,
    get_instagram_account,
    get_instagram_media_insights,
)


@pytest.mark.asyncio
async def test_get_page_insights_uses_default_metrics():
    mock_response = {"data": [{"name": "page_impressions", "values": []}]}
    with patch("meta_ads_mcp.core.organic.make_api_request", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response

        result = await get_page_insights(
            page_id="12345",
            access_token="token",
        )
        payload = json.loads(result)

        assert "data" in payload
        mock_api.assert_awaited_once()
        args = mock_api.await_args.args
        assert args[0] == "12345/insights"
        assert args[1] == "token"
        assert args[2]["period"] == "day"
        assert "page_impressions" in args[2]["metric"]
        assert "page_reach" in args[2]["metric"]


@pytest.mark.asyncio
async def test_get_instagram_account_builds_expected_endpoint():
    mock_response = {"id": "1", "instagram_business_account": {"id": "ig_1"}}
    with patch("meta_ads_mcp.core.organic.make_api_request", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response

        result = await get_instagram_account(
            page_id="999",
            access_token="token",
        )
        payload = json.loads(result)

        assert payload["id"] == "1"
        args = mock_api.await_args.args
        assert args[0] == "999"
        assert args[1] == "token"
        assert "instagram_business_account" in args[2]["fields"]


@pytest.mark.asyncio
async def test_get_instagram_media_insights_requires_media_id():
    result = await get_instagram_media_insights(media_id="", access_token="token")
    payload = json.loads(result)
    if "error" in payload:
        assert payload["error"] == "media_id is required"
    else:
        nested = json.loads(payload["data"])
        assert nested["error"] == "media_id is required"
