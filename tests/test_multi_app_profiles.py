from meta_ads_mcp.core.auth import MetaConfig


def test_meta_config_loads_profiles_from_env_json(monkeypatch):
    monkeypatch.setenv(
        "META_APP_CREDENTIALS_JSON",
        '{"default":{"app_id":"111","app_secret":"sec1","oauth_redirect_uri":"https://x/callback"},'
        '"dr_health":{"app_id":"222","app_secret":"sec2","oauth_redirect_uri":"https://y/callback"}}',
    )
    cfg = MetaConfig()
    default_profile = cfg.get_app_profile()
    dr_profile = cfg.get_app_profile("dr_health")
    assert default_profile.app_id == "111"
    assert dr_profile.app_id == "222"
    assert dr_profile.oauth_redirect_uri == "https://y/callback"


def test_meta_config_fallback_to_default_profile(monkeypatch):
    monkeypatch.delenv("META_APP_CREDENTIALS_JSON", raising=False)
    monkeypatch.setenv("META_APP_ID", "single")
    monkeypatch.setenv("META_APP_SECRET", "single-secret")
    monkeypatch.setenv("OAUTH_REDIRECT_URI", "https://single/callback")
    cfg = MetaConfig()
    unknown = cfg.get_app_profile("unknown")
    assert unknown.label == "default"
    assert unknown.app_id == "single"


def test_invalid_profile_json_uses_single_app_env(monkeypatch):
    monkeypatch.setenv("META_APP_CREDENTIALS_JSON", "{bad-json")
    monkeypatch.setenv("META_APP_ID", "fallback")
    monkeypatch.setenv("META_APP_SECRET", "fallback-secret")
    monkeypatch.setenv("OAUTH_REDIRECT_URI", "https://fallback/callback")
    cfg = MetaConfig()
    fallback = cfg.get_app_profile()
    assert fallback.app_id == "fallback"
    assert fallback.app_secret == "fallback-secret"
