"""Verify Amadeus API credentials with a real OAuth2 token request."""
from __future__ import annotations

from typing import Tuple

import httpx

from flight_deal_agent.settings import AmadeusConfig, AppConfig


def fetch_access_token(cfg: AmadeusConfig) -> Tuple[bool, str]:
    """Return (ok, message). On success message includes truncated token info."""
    if not cfg.client_id or not cfg.client_secret:
        return False, "缺少 AMADEUS_CLIENT_ID 或 AMADEUS_CLIENT_SECRET（请配置 .env）"

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{cfg.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cfg.client_id,
                    "client_secret": cfg.client_secret,
                },
            )
    except httpx.RequestError as exc:
        return False, f"网络错误: {exc}"

    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}: {resp.text[:500]}"

    body = resp.json()
    token = body.get("access_token", "")
    expires = body.get("expires_in", "?")
    if not token:
        return False, f"响应异常（无 access_token）: {body}"
    return True, f"OAuth2成功，token 前8 位: {token[:8]}…，expires_in={expires}s"


def verify_amadeus_live(config: AppConfig, *, oauth_only: bool = False) -> Tuple[bool, str]:
    """
    OAuth2 取 token；默认再对第一个出发机场发一条 Flight Inspiration 探测（额外1 次 GET）。
    oauth_only=True 时只测 OAuth2，不占 Inspiration 配额。
    """
    if not config.amadeus.client_id or not config.amadeus.client_secret:
        return False, "缺少 AMADEUS_CLIENT_ID 或 AMADEUS_CLIENT_SECRET（请配置 .env）"

    try:
        with httpx.Client(timeout=30) as client:
            token_resp = client.post(
                f"{config.amadeus.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": config.amadeus.client_id,
                    "client_secret": config.amadeus.client_secret,
                },
            )
            if token_resp.status_code != 200:
                return (
                    False,
                    f"OAuth2 失败 HTTP {token_resp.status_code}: {token_resp.text[:500]}",
                )
            body = token_resp.json()
            token = body.get("access_token", "")
            expires = body.get("expires_in", "?")
            if not token:
                return False, f"OAuth2 响应异常: {body}"
            base_msg = f"OAuth2 成功，token 前8 位: {token[:8]}…，expires_in={expires}s"

            if oauth_only:
                return True, base_msg + "（--oauth-only，已跳过 Inspiration）"

            if not config.origin_airports:
                return True, base_msg + " | 未配置出发机场，跳过 Inspiration 探测"

            origin = config.origin_airports[0]
            insp = client.get(
                f"{config.amadeus.base_url}/v1/shopping/flight-destinations",
                params={"origin": origin},
                headers={"Authorization": f"Bearer {token}"},
            )
            if insp.status_code != 200:
                return (
                    False,
                    base_msg
                    + f" | Inspiration 失败 HTTP {insp.status_code}: {insp.text[:300]}",
                )
            data = insp.json().get("data") or []
            return True, base_msg + f" | Inspiration OK（{origin} 返回 {len(data)} 条样本）"
    except httpx.RequestError as exc:
        return False, f"网络错误: {exc}"
