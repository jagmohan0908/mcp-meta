# Meta Ads MCP

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with Meta Ads. Analyze, manage and optimize Meta advertising campaigns through an AI interface. Use an LLM to retrieve performance data, visualize ad creatives, and provide strategic insights for your ads on Facebook, Instagram, and other Meta platforms.

> **Note:** This is an independent open-source project that uses Meta's public APIs. It is not affiliated with or endorsed by Meta. Meta, Facebook, Instagram, and other Meta brand names are trademarks of their respective owners.

[![Meta Ads MCP Server Demo](https://github.com/user-attachments/assets/3e605cee-d289-414b-814c-6299e7f3383e)](https://github.com/user-attachments/assets/3e605cee-d289-414b-814c-6299e7f3383e)

[![Repository](https://img.shields.io/badge/GitHub-jagmohan0908%2Fmcp--meta-181717?logo=github)](https://github.com/jagmohan0908/mcp-meta)

mcp-name: jagmohan0908/mcp-meta

## Community & Support

- Use issues in this repository for bugs and feature requests.
- For deployment/runbook details, see [`SELF_HOSTED_RUNBOOK.md`](SELF_HOSTED_RUNBOOK.md).

## Table of Contents

- [Self-Hosted Quick Start](#self-hosted-quick-start)
- [Authentication Model (Multi-Tenant)](#authentication-model-multi-tenant)
- [Local Installation](#local-installation)
- [Features](#features)
- [Configuration](#configuration)
- [Available MCP Tools](#available-mcp-tools)
- [Licensing](#licensing)
- [Privacy and Security](#privacy-and-security)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Self-Hosted Quick Start

This repository is configured for a self-hosted workflow with native Meta OAuth and multi-tenant authorization.

1. Copy env template and set values:

   ```bash
   cp .env.example .env
   ```

   Required:
   - `META_APP_ID`
   - `META_APP_SECRET`
   - `OAUTH_REDIRECT_URI` (must match Meta app OAuth settings exactly)
   - `META_MCP_ENCRYPTION_KEY`

2. Start server:

   ```bash
   python -m meta_ads_mcp --transport streamable-http --host 0.0.0.0 --port 8080
   ```

3. Bootstrap first tenant:
   - Call `mcp_meta_ads_get_login_link(tenant_id)`
   - Complete Meta login and capture `code`
   - Call `mcp_meta_ads_complete_oauth(tenant_id, code)`
   - Register tenant key via `mcp_meta_ads_register_tenant_api_key`
   - Allow account access via `mcp_meta_ads_grant_tenant_account_access`

4. Send MCP HTTP requests with tenant headers:
   - `X-TENANT-ID`
   - `X-TENANT-API-KEY`
   - optional `X-META-APP-LABEL` (example: `dr_health`, `sriaas`, `siya`)
   - optional `Authorization: Bearer <meta_access_token>`

For detailed bootstrap and validation flow, see [`SELF_HOSTED_RUNBOOK.md`](SELF_HOSTED_RUNBOOK.md).

## Authentication Model (Multi-Tenant)

- **Tenant isolation**: each tenant has separate tokens and account access policy.
- **Encrypted token storage**: tenant tokens are encrypted at rest in SQLite.
- **Account-level authorization**: account operations are checked against tenant grants.
- **Direct token fallback**: `META_ACCESS_TOKEN` can be used for quick local testing.

## Local Installation

```bash
git clone https://github.com/jagmohan0908/mcp-meta.git
cd mcp-meta
python -m pip install -r requirements.txt
python -m meta_ads_mcp --transport streamable-http --host 0.0.0.0 --port 8080
```

See [`STREAMABLE_HTTP_SETUP.md`](STREAMABLE_HTTP_SETUP.md) for full HTTP transport and deployment details.

## Features

- **AI-Powered Campaign Analysis**: Let your favorite LLM analyze your campaigns and provide actionable insights on performance
- **Strategic Recommendations**: Receive data-backed suggestions for optimizing ad spend, targeting, and creative content
- **Automated Monitoring**: Ask any MCP-compatible LLM to track performance metrics and alert you about significant changes
- **Budget Optimization**: Get recommendations for reallocating budget to better-performing ad sets
- **Creative Improvement**: Receive feedback on ad copy, imagery, and calls-to-action
- **Dynamic Creative Testing**: Easy API for both simple ads (single headline/description) and advanced A/B testing (multiple headlines/descriptions)
- **Campaign Management**: Request changes to campaigns, ad sets, and ads (all changes require explicit confirmation)
- **Cross-Platform Integration**: Works with Facebook, Instagram, and all Meta ad platforms
- **Universal LLM Support**: Compatible with any MCP client including Claude Desktop, Cursor, Cherry Studio, and more
- **Enhanced Search**: Generic search function includes page searching when queries mention "page" or "pages"
- **Simple Authentication**: Easy setup with secure OAuth authentication
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## Configuration

### Self-Hosted Configuration (Recommended)

Set these env vars:

- `META_APP_ID`
- `META_APP_SECRET`
- `OAUTH_REDIRECT_URI`
- `META_MCP_ENCRYPTION_KEY`
- `META_MCP_DB_PATH` (optional, defaults under home directory)
- `META_ACCESS_TOKEN` (optional quick-start token)

### Available MCP Tools

1. `mcp_meta_ads_get_ad_accounts`
   - Get ad accounts accessible by a user
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `user_id`: Meta user ID or "me" for the current user
     - `limit`: Maximum number of accounts to return (default: 200)
   - Returns: List of accessible ad accounts with their details

2. `mcp_meta_ads_get_account_info`
   - Get detailed information about a specific ad account
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
   - Returns: Detailed information about the specified account

3. `mcp_meta_ads_get_account_pages`
   - Get pages associated with a Meta Ads account
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX) or "me" for the current user's pages
   - Returns: List of pages associated with the account, useful for ad creation and management

4. `mcp_meta_ads_get_campaigns`
   - Get campaigns for a Meta Ads account with optional filtering
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
     - `limit`: Maximum number of campaigns to return (default: 10)
     - `status_filter`: Filter by status (empty for all, or 'ACTIVE', 'PAUSED', etc.)
   - Returns: List of campaigns matching the criteria

5. `mcp_meta_ads_get_campaign_details`
   - Get detailed information about a specific campaign
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `campaign_id`: Meta Ads campaign ID
   - Returns: Detailed information about the specified campaign

6. `mcp_meta_ads_create_campaign`
   - Create a new campaign in a Meta Ads account
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
     - `name`: Campaign name
     - `objective`: Campaign objective (ODAX, outcome-based). Must be one of:
       - `OUTCOME_AWARENESS`
       - `OUTCOME_TRAFFIC`
       - `OUTCOME_ENGAGEMENT`
       - `OUTCOME_LEADS`
       - `OUTCOME_SALES`
       - `OUTCOME_APP_PROMOTION`
       
       Note: Legacy objectives such as `BRAND_AWARENESS`, `LINK_CLICKS`, `CONVERSIONS`, `APP_INSTALLS`, etc. are no longer valid for new campaigns and will cause a 400 error. Use the outcome-based values above. Common mappings:
       - `BRAND_AWARENESS` → `OUTCOME_AWARENESS`
       - `REACH` → `OUTCOME_AWARENESS`
       - `LINK_CLICKS`, `TRAFFIC` → `OUTCOME_TRAFFIC`
       - `POST_ENGAGEMENT`, `PAGE_LIKES`, `EVENT_RESPONSES`, `VIDEO_VIEWS` → `OUTCOME_ENGAGEMENT`
       - `LEAD_GENERATION` → `OUTCOME_LEADS`
       - `CONVERSIONS`, `CATALOG_SALES`, `MESSAGES` (sales-focused flows) → `OUTCOME_SALES`
       - `APP_INSTALLS` → `OUTCOME_APP_PROMOTION`
     - `status`: Initial campaign status (default: PAUSED)
     - `special_ad_categories`: List of special ad categories if applicable
     - `daily_budget`: Daily budget in account currency (in cents)
     - `lifetime_budget`: Lifetime budget in account currency (in cents)
     - `bid_strategy`: Bid strategy. Must be one of: `LOWEST_COST_WITHOUT_CAP`, `LOWEST_COST_WITH_BID_CAP`, `COST_CAP`, `LOWEST_COST_WITH_MIN_ROAS`.
   - Returns: Confirmation with new campaign details

   - Example:
     ```json
     {
       "name": "2025 - Bedroom Furniture - Awareness",
       "account_id": "act_123456789012345",
       "objective": "OUTCOME_AWARENESS",
       "special_ad_categories": [],
       "status": "PAUSED",
       "buying_type": "AUCTION",
       "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
       "daily_budget": 10000
     }
     ```

7. `mcp_meta_ads_get_adsets`
   - Get ad sets for a Meta Ads account with optional filtering by campaign
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
     - `limit`: Maximum number of ad sets to return (default: 10)
     - `campaign_id`: Optional campaign ID to filter by
   - Returns: List of ad sets matching the criteria

8. `mcp_meta_ads_get_adset_details`
   - Get detailed information about a specific ad set
   - Inputs:
     - `access_token` (optional): Meta API access token (will use cached token if not provided)
     - `adset_id`: Meta Ads ad set ID
   - Returns: Detailed information about the specified ad set

9. `mcp_meta_ads_create_adset`
   - Create a new ad set in a Meta Ads account
   - Inputs:
     - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
     - `campaign_id`: Meta Ads campaign ID this ad set belongs to
     - `name`: Ad set name
     - `status`: Initial ad set status (default: PAUSED)
     - `daily_budget`: Daily budget in account currency (in cents) as a string
     - `lifetime_budget`: Lifetime budget in account currency (in cents) as a string
     - `targeting`: Targeting specifications (e.g., age, location, interests)
     - `optimization_goal`: Conversion optimization goal (e.g., 'LINK_CLICKS')
     - `billing_event`: How you're charged (e.g., 'IMPRESSIONS')
     - `bid_amount`: Bid amount in cents. Required for LOWEST_COST_WITH_BID_CAP, COST_CAP, TARGET_COST.
     - `bid_strategy`: Bid strategy (e.g., 'LOWEST_COST_WITHOUT_CAP', 'LOWEST_COST_WITH_MIN_ROAS')
     - `bid_constraints`: Bid constraints dict. Required for LOWEST_COST_WITH_MIN_ROAS (e.g., `{"roas_average_floor": 20000}`)
     - `start_time`, `end_time`: Optional start/end times (ISO 8601)
     - `access_token` (optional): Meta API access token
   - Returns: Confirmation with new ad set details

10. `mcp_meta_ads_get_ads`
    - Get ads for a Meta Ads account with optional filtering
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
      - `limit`: Maximum number of ads to return (default: 10)
      - `campaign_id`: Optional campaign ID to filter by
      - `adset_id`: Optional ad set ID to filter by
    - Returns: List of ads matching the criteria

11. `mcp_meta_ads_create_ad`
    - Create a new ad with an existing creative
    - Inputs:
      - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
      - `name`: Ad name
      - `adset_id`: Ad set ID where this ad will be placed
      - `creative_id`: ID of an existing creative to use
      - `status`: Initial ad status (default: PAUSED)
      - `bid_amount`: Optional bid amount (in cents)
      - `tracking_specs`: Optional tracking specifications
      - `access_token` (optional): Meta API access token
    - Returns: Confirmation with new ad details

12. `mcp_meta_ads_get_ad_details`
    - Get detailed information about a specific ad
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `ad_id`: Meta Ads ad ID
    - Returns: Detailed information about the specified ad

13. `mcp_meta_ads_get_ad_creatives`
    - Get creative details for a specific ad
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `ad_id`: Meta Ads ad ID
    - Returns: Creative details including text, images, and URLs

14. `mcp_meta_ads_create_ad_creative`
    - Create a new ad creative using an uploaded image hash
    - Inputs:
      - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
      - `name`: Creative name
      - `image_hash`: Hash of the uploaded image
      - `page_id`: Facebook Page ID for the ad
      - `link_url`: Destination URL
      - `message`: Ad copy/text
      - `headline`: Single headline for simple ads (cannot be used with headlines)
      - `headlines`: List of headlines for dynamic creative testing (cannot be used with headline)
      - `description`: Single description for simple ads (cannot be used with descriptions)
      - `descriptions`: List of descriptions for dynamic creative testing (cannot be used with description)
      - `dynamic_creative_spec`: Dynamic creative optimization settings
      - `call_to_action_type`: CTA button type (e.g., 'LEARN_MORE')
      - `instagram_actor_id`: Optional Instagram account ID
      - `access_token` (optional): Meta API access token
    - Returns: Confirmation with new creative details

15. `mcp_meta_ads_update_ad_creative`
    - Update an existing ad creative with new content or settings
    - Inputs:
      - `creative_id`: Meta Ads creative ID to update
      - `name`: New creative name
      - `message`: New ad copy/text
      - `headline`: Single headline for simple ads (cannot be used with headlines)
      - `headlines`: New list of headlines for dynamic creative testing (cannot be used with headline)
      - `description`: Single description for simple ads (cannot be used with descriptions)
      - `descriptions`: New list of descriptions for dynamic creative testing (cannot be used with description)
      - `dynamic_creative_spec`: New dynamic creative optimization settings
      - `call_to_action_type`: New call to action button type
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
    - Returns: Confirmation with updated creative details

16. `mcp_meta_ads_upload_ad_image`
    - Upload an image to use in Meta Ads creatives
    - Inputs:
      - `account_id`: Meta Ads account ID (format: act_XXXXXXXXX)
      - `image_path`: Path to the image file to upload
      - `name`: Optional name for the image
      - `access_token` (optional): Meta API access token
    - Returns: JSON response with image details including hash

17. `mcp_meta_ads_get_ad_image`
    - Get, download, and visualize a Meta ad image in one step
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `ad_id`: Meta Ads ad ID
    - Returns: The ad image ready for direct visual analysis

18. `mcp_meta_ads_update_ad`
    - Update an ad with new settings
    - Inputs:
      - `ad_id`: Meta Ads ad ID
      - `status`: Update ad status (ACTIVE, PAUSED, etc.)
      - `bid_amount`: Bid amount in account currency (in cents for USD)
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
    - Returns: Confirmation with updated ad details and a confirmation link

19. `mcp_meta_ads_update_adset`
    - Update an ad set with new settings including frequency caps
    - Inputs:
      - `adset_id`: Meta Ads ad set ID
      - `frequency_control_specs`: List of frequency control specifications
      - `bid_strategy`: Bid strategy (e.g., 'LOWEST_COST_WITH_BID_CAP', 'LOWEST_COST_WITH_MIN_ROAS')
      - `bid_amount`: Bid amount in cents. Required for LOWEST_COST_WITH_BID_CAP, COST_CAP, TARGET_COST.
      - `bid_constraints`: Bid constraints dict. Required for LOWEST_COST_WITH_MIN_ROAS (e.g., `{"roas_average_floor": 20000}`)
      - `status`: Update ad set status (ACTIVE, PAUSED, etc.)
      - `targeting`: Targeting specifications including targeting_automation
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
    - Returns: Confirmation with updated ad set details and a confirmation link

20. `mcp_meta_ads_get_insights`
    - Get performance insights for a campaign, ad set, ad or account
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `object_id`: ID of the campaign, ad set, ad or account
      - `time_range`: Time range for insights (default: maximum)
      - `breakdown`: Optional breakdown dimension (e.g., age, gender, country)
      - `level`: Level of aggregation (ad, adset, campaign, account)
      - `action_attribution_windows` (optional): List of attribution windows for conversion data (e.g., ["1d_click", "1d_view", "7d_click", "7d_view"]). When specified, actions and cost_per_action_type include additional fields for each window. The 'value' field always shows 7d_click attribution.
    - Returns: Performance metrics for the specified object

21. `mcp_meta_ads_get_login_link`
    - Get a clickable login link for Meta Ads authentication
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
    - Returns: A clickable resource link for Meta authentication

22. `mcp_meta_ads_create_budget_schedule`
    - Create a budget schedule for a Meta Ads campaign
    - Inputs:
      - `campaign_id`: Meta Ads campaign ID
      - `budget_value`: Amount of budget increase
      - `budget_value_type`: Type of budget value ("ABSOLUTE" or "MULTIPLIER")
      - `time_start`: Unix timestamp for when the high demand period should start
      - `time_end`: Unix timestamp for when the high demand period should end
      - `access_token` (optional): Meta API access token
    - Returns: JSON string with the ID of the created budget schedule or an error message

23. `mcp_meta_ads_search_interests`
    - Search for interest targeting options by keyword
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `query`: Search term for interests (e.g., "baseball", "cooking", "travel")
      - `limit`: Maximum number of results to return (default: 25)
    - Returns: Interest data with id, name, audience_size, and path fields

24. `mcp_meta_ads_get_interest_suggestions`
    - Get interest suggestions based on existing interests
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `interest_list`: List of interest names to get suggestions for (e.g., ["Basketball", "Soccer"])
      - `limit`: Maximum number of suggestions to return (default: 25)
    - Returns: Suggested interests with id, name, audience_size, and description fields

25. `mcp_meta_ads_validate_interests`
    - Validate interest names or IDs for targeting
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `interest_list`: List of interest names to validate (e.g., ["Japan", "Basketball"])
      - `interest_fbid_list`: List of interest IDs to validate (e.g., ["6003700426513"])
    - Returns: Validation results showing valid status and audience_size for each interest

26. `mcp_meta_ads_search_behaviors`
    - Get all available behavior targeting options
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `limit`: Maximum number of results to return (default: 50)
    - Returns: Behavior targeting options with id, name, audience_size bounds, path, and description

27. `mcp_meta_ads_search_demographics`
    - Get demographic targeting options
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `demographic_class`: Type of demographics ('demographics', 'life_events', 'industries', 'income', 'family_statuses', 'user_device', 'user_os')
      - `limit`: Maximum number of results to return (default: 50)
    - Returns: Demographic targeting options with id, name, audience_size bounds, path, and description

28. `mcp_meta_ads_search_geo_locations`
    - Search for geographic targeting locations
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `query`: Search term for locations (e.g., "New York", "California", "Japan")
      - `location_types`: Types of locations to search (['country', 'region', 'city', 'zip', 'geo_market', 'electoral_district'])
      - `limit`: Maximum number of results to return (default: 25)
    - Returns: Location data with key, name, type, and geographic hierarchy information

29. `mcp_meta_ads_search` (Enhanced)
    - Generic search across accounts, campaigns, ads, and pages
    - Automatically includes page searching when query mentions "page" or "pages"
    - Inputs:
      - `access_token` (optional): Meta API access token (will use cached token if not provided)
      - `query`: Search query string (e.g., "Injury Payouts pages", "active campaigns")
    - Returns: List of matching record IDs in ChatGPT-compatible format

## Licensing

Meta Ads MCP is licensed under the [Business Source License 1.1](LICENSE), which means:

- ✅ **Free to use** for individual and business purposes
- ✅ **Modify and customize** as needed
- ✅ **Redistribute** to others
- ✅ **Becomes fully open source** (Apache 2.0) on January 1, 2029

The only restriction is that you cannot offer this as a competing hosted service. For questions about commercial licensing, please contact us.

## Privacy and Security

Meta Ads MCP uses tenant-scoped auth and encrypted token persistence.

- Tenant API keys are stored hashed.
- Meta access tokens are encrypted at rest.
- Account actions are tenant-authorized before execution.
- Use HTTPS and a reverse proxy in production.

## Testing

### Basic Testing

Test your Meta Ads MCP connection with any MCP client:

1. **Verify Auth**: run `mcp_meta_ads_get_login_link` and `mcp_meta_ads_complete_oauth`
2. **Verify Tenant Access**: call `mcp_meta_ads_register_tenant_api_key` and `mcp_meta_ads_grant_tenant_account_access`
3. **Read Flow**: use `mcp_meta_ads_get_ad_accounts` and `mcp_meta_ads_get_campaigns`
4. **Write Flow**: test one safe write action in a non-production account

For operator steps, see [`SELF_HOSTED_RUNBOOK.md`](SELF_HOSTED_RUNBOOK.md).

## Troubleshooting

### Common Self-Hosted Issues

- **401/403 from Meta API**: verify tenant token is valid and app permissions are granted.
- **Forbidden account access**: ensure account is granted with `mcp_meta_ads_grant_tenant_account_access`.
- **OAuth redirect mismatch**: `OAUTH_REDIRECT_URI` must exactly match Meta app OAuth settings.
- **Token persistence problems**: confirm `META_MCP_ENCRYPTION_KEY` and writable DB path.
