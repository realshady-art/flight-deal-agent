from __future__ import annotations

from unittest.mock import MagicMock, patch

from flight_deal_agent.amadeus_verify import fetch_access_token, verify_amadeus_live
from flight_deal_agent.settings import AmadeusConfig, load_app_config


def test_fetch_access_token_missing(monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    cfg = AmadeusConfig()
    ok, msg = fetch_access_token(cfg)
    assert ok is False
    assert "缺少" in msg


def test_verify_amadeus_missing_env(tmp_config, monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    cfg = load_app_config(tmp_config)
    ok, msg = verify_amadeus_live(cfg, oauth_only=True)
    assert ok is False
    assert "缺少" in msg


def test_verify_oauth_only_success(tmp_config, monkeypatch):
    monkeypatch.setenv("AMADEUS_CLIENT_ID", "test_id")
    monkeypatch.setenv("AMADEUS_CLIENT_SECRET", "test_secret")
    cfg = load_app_config(tmp_config)

    mock_post = MagicMock(
        return_value=MagicMock(
            status_code=200,
            json=lambda: {"access_token": "abcdefghixyz", "expires_in": 1799},
        )
    )

    with patch("flight_deal_agent.amadeus_verify.httpx.Client") as m_client:
        inst = MagicMock()
        m_client.return_value.__enter__.return_value = inst
        m_client.return_value.__exit__.return_value = None
        inst.post = mock_post

        ok, msg = verify_amadeus_live(cfg, oauth_only=True)

    assert ok is True
    assert "OAuth2 成功" in msg
    assert "oauth-only" in msg or "跳过" in msg
    mock_post.assert_called_once()


def test_verify_with_inspiration_success(tmp_config, monkeypatch):
    monkeypatch.setenv("AMADEUS_CLIENT_ID", "id")
    monkeypatch.setenv("AMADEUS_CLIENT_SECRET", "sec")
    cfg = load_app_config(tmp_config)

    token_resp = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "token12345", "expires_in": 100},
    )
    insp_resp = MagicMock(status_code=200, json=lambda: {"data": [{"x": 1}]})

    with patch("flight_deal_agent.amadeus_verify.httpx.Client") as m_client:
        inst = MagicMock()
        m_client.return_value.__enter__.return_value = inst
        m_client.return_value.__exit__.return_value = None
        inst.post.return_value = token_resp
        inst.get.return_value = insp_resp

        ok, msg = verify_amadeus_live(cfg, oauth_only=False)

    assert ok is True
    assert "Inspiration OK" in msg
    inst.get.assert_called_once()
