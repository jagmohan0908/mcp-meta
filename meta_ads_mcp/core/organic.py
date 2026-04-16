"""Organic Facebook/Instagram insights tools for Meta Graph API."""

import json
from typing import Optional, List

from .api import meta_api_tool, make_api_request
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_page_posts(
    page_id: str,
    access_token: Optional[str] = None,
    limit: int = 25,
    since: str = "",
    until: str = "",
) -> str:
    """
    Get organic posts from a Facebook Page.

    Args:
        page_id: Facebook Page ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        limit: Maximum number of posts to return (default: 25)
        since: Optional start date/time filter (YYYY-MM-DD or ISO timestamp)
        until: Optional end date/time filter (YYYY-MM-DD or ISO timestamp)
    """
    if not page_id:
        return json.dumps({"error": "page_id is required"}, indent=2)

    endpoint = f"{page_id}/posts"
    params = {
        "fields": (
            "id,message,created_time,permalink_url,status_type,"
            "attachments{media_type,media,url,target},"
            "shares,likes.summary(true),comments.summary(true)"
        ),
        "limit": limit,
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_page_insights(
    page_id: str,
    access_token: Optional[str] = None,
    metrics: Optional[List[str]] = None,
    period: str = "day",
    since: str = "",
    until: str = "",
) -> str:
    """
    Get organic insights for a Facebook Page.

    Args:
        page_id: Facebook Page ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        metrics: Optional list of page insight metrics
        period: Insight period (day, week, days_28, lifetime depending on metric)
        since: Optional start date (YYYY-MM-DD)
        until: Optional end date (YYYY-MM-DD)
    """
    if not page_id:
        return json.dumps({"error": "page_id is required"}, indent=2)

    default_metrics = [
        "page_impressions",
        "page_reach",
        "page_engaged_users",
        "page_post_engagements",
        "page_fans",
    ]
    selected_metrics = metrics or default_metrics

    endpoint = f"{page_id}/insights"
    params = {
        "metric": ",".join(selected_metrics),
        "period": period,
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_post_insights(
    post_id: str,
    access_token: Optional[str] = None,
    metrics: Optional[List[str]] = None,
) -> str:
    """
    Get organic insights for a Facebook post.

    Args:
        post_id: Facebook post ID (format: {page_id}_{post_id})
        access_token: Meta API access token (optional - will use cached token if not provided)
        metrics: Optional list of post insight metrics
    """
    if not post_id:
        return json.dumps({"error": "post_id is required"}, indent=2)

    default_metrics = [
        "post_impressions",
        "post_impressions_unique",
        "post_engaged_users",
        "post_reactions_by_type_total",
        "post_clicks",
    ]
    selected_metrics = metrics or default_metrics

    endpoint = f"{post_id}/insights"
    params = {
        "metric": ",".join(selected_metrics),
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_instagram_account(
    page_id: str,
    access_token: Optional[str] = None,
) -> str:
    """
    Get Instagram business account linked to a Facebook Page.

    Args:
        page_id: Facebook Page ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not page_id:
        return json.dumps({"error": "page_id is required"}, indent=2)

    endpoint = f"{page_id}"
    params = {
        "fields": (
            "id,name,instagram_business_account{id,username,name,"
            "profile_picture_url,followers_count,media_count}"
        )
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_instagram_insights(
    ig_user_id: str,
    access_token: Optional[str] = None,
    metrics: Optional[List[str]] = None,
    period: str = "day",
    since: str = "",
    until: str = "",
) -> str:
    """
    Get organic insights for an Instagram business/creator account.

    Args:
        ig_user_id: Instagram business/creator account ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        metrics: Optional list of IG account insight metrics
        period: Insight period (day, week, days_28, lifetime depending on metric)
        since: Optional start date (YYYY-MM-DD)
        until: Optional end date (YYYY-MM-DD)
    """
    if not ig_user_id:
        return json.dumps({"error": "ig_user_id is required"}, indent=2)

    default_metrics = [
        "impressions",
        "reach",
        "profile_views",
        "website_clicks",
        "follower_count",
    ]
    selected_metrics = metrics or default_metrics

    endpoint = f"{ig_user_id}/insights"
    params = {
        "metric": ",".join(selected_metrics),
        "period": period,
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_instagram_media(
    ig_user_id: str,
    access_token: Optional[str] = None,
    limit: int = 25,
    media_type: str = "",
    since: str = "",
    until: str = "",
) -> str:
    """
    Get media published by an Instagram business/creator account.

    Args:
        ig_user_id: Instagram business/creator account ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        limit: Maximum number of media objects to return (default: 25)
        media_type: Optional media type filter (IMAGE, VIDEO, CAROUSEL_ALBUM, REELS)
        since: Optional start date/time filter (YYYY-MM-DD or ISO timestamp)
        until: Optional end date/time filter (YYYY-MM-DD or ISO timestamp)
    """
    if not ig_user_id:
        return json.dumps({"error": "ig_user_id is required"}, indent=2)

    endpoint = f"{ig_user_id}/media"
    params = {
        "fields": (
            "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
            "permalink,timestamp,username,like_count,comments_count"
        ),
        "limit": limit,
    }
    if media_type:
        params["media_type"] = media_type
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_instagram_media_insights(
    media_id: str,
    access_token: Optional[str] = None,
    metrics: Optional[List[str]] = None,
) -> str:
    """
    Get organic insights for a specific Instagram media object.

    Args:
        media_id: Instagram media ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        metrics: Optional list of IG media insight metrics
    """
    if not media_id:
        return json.dumps({"error": "media_id is required"}, indent=2)

    default_metrics = [
        "impressions",
        "reach",
        "engagement",
        "saved",
        "video_views",
        "likes",
        "comments",
        "shares",
        "total_interactions",
    ]
    selected_metrics = metrics or default_metrics

    endpoint = f"{media_id}/insights"
    params = {
        "metric": ",".join(selected_metrics),
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)
