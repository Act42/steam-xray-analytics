"""Automated pytest suite for SteamXRay v2.0: Studio OSINT (Wikidata/Wikipedia), Ukrainian Localization, Price History & Bilingual API."""

from __future__ import annotations

import pytest
import httpx

from src.api import app


@pytest.mark.asyncio
async def test_ui_and_health():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r_ui = await client.get("/")
        assert r_ui.status_code == 200
        assert "SteamXRay" in r_ui.text
        assert "similarGamesGrid" not in r_ui.text  # Similar games section removed as requested

        r_health = await client.get("/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "healthy"
        assert r_health.json()["version"] == "2.0.0"


@pytest.mark.asyncio
async def test_trending_and_bilingual_search():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r_trend = await client.get("/api/v1/trending")
        assert r_trend.status_code == 200
        items = r_trend.json()
        assert len(items) >= 6

        r_search = await client.get("/api/v1/search", params={"q": "Cyberpunk", "limit": 5, "lang": "uk"})
        assert r_search.status_code == 200
        s_data = r_search.json()
        assert s_data["count"] >= 1
        assert any("Cyberpunk" in g["name"] for g in s_data["items"])


@pytest.mark.asyncio
async def test_game_xray_studio_intel_and_ukrainian_localization():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Inspect S.T.A.L.K.E.R. 2: Heart of Chornobyl (AppID 1643320) in Ukrainian
        resp = await client.get("/api/v1/game/1643320/xray", params={"lang": "uk"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["appid"] == 1643320
        assert data["lang"] == "uk"
        assert data["developer_intel"]["country_code"] == "🇺🇦"
        assert data["developer_intel"]["origin_status"] == "ukrainian"
        assert "1995" in data["developer_intel"]["founded_year"]
        assert data["localization"]["has_ukrainian_text"] is True


@pytest.mark.asyncio
async def test_game_xray_price_history_and_english_intel():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Inspect Cyberpunk 2077 (AppID 1091500) in English
        resp = await client.get("/api/v1/game/1091500/xray", params={"lang": "en"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["appid"] == 1091500
        assert data["lang"] == "en"
        assert data["developer_intel"]["country_code"] == "🇵🇱"
        assert "Poland" in data["developer_intel"]["country"]
        assert data["verdict"]["overall_score"] > 50.0


@pytest.mark.asyncio
async def test_head_to_head_compare_bilingual():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/compare", params={"appid_a": 1643320, "appid_b": 1091500, "lang": "uk"})
        assert resp.status_code == 200
        cmp = resp.json()
        assert cmp["game_a"]["appid"] == 1643320
        assert cmp["game_b"]["appid"] == 1091500
        assert len(cmp["shared_Radar_axes"]) == 6
