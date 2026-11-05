"""FastAPI Server for SteamXRay: Bilingual (EN/UA) REST API Endpoints and Interactive Web UI Hosting."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.analytics import build_game_xray, compare_two_games
from src.schemas import CompareResponse, GameCard, GameXRayReport, SearchResponse
from src.steam_client import CURATED_GAME_DNA_CATALOG, SteamAPIClient

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="SteamXRay — Live Game & Studio OSINT Intelligence API",
    description=(
        "Full-stack FastAPI service orchestrating live Steam Store, Steam UserStats (Concurrent Players), "
        "Wikidata/Wikipedia Developer & Publisher OSINT (Country, HQ, Founded Year, Parent Company), "
        "Ukrainian Localization Verification, CheapShark Historical Lowest Price, and SteamSpy Tag-DNA APIs."
    ),
    version="2.0.0",
)

steam_client = SteamAPIClient(timeout_sec=8.0, cache_ttl_sec=900)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>SteamXRay API is running. Visit <a href='/docs'>/docs</a></h1>")


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, object]:
    return {
        "status": "healthy",
        "service": "steam-xray-analytics",
        "version": "2.0.0",
        "dna_catalog_games": len(steam_client.dna_catalog),
    }


@app.get("/api/v1/trending", response_model=List[GameCard], tags=["Discovery"])
async def get_trending_presets() -> List[GameCard]:
    """Return curated popular Steam games for one-click instant X-Ray inspection."""
    featured_ids = [1643320, 1091500, 1245620, 1086940, 292030, 412020, 730, 367520]
    cards: List[GameCard] = []
    for aid in featured_ids:
        info = CURATED_GAME_DNA_CATALOG.get(aid)
        if not info:
            continue
        cards.append(
            GameCard(
                appid=aid,
                name=info["name"],
                header_image=f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{aid}/header.jpg",
                price_formatted=info.get("price_formatted", "Steam"),
                developers=info.get("developers", []),
                genres=list(info.get("tags", {}).keys())[:3],
            )
        )
    return cards


@app.get("/api/v1/search", response_model=SearchResponse, tags=["Discovery"])
async def search_steam_games(
    q: str = Query(..., min_length=1, max_length=120, description="Game title or developer name"),
    limit: int = Query(default=10, ge=1, le=25),
    lang: str = Query(default="en", pattern="^(en|uk)$", description="Language code: en or uk"),
) -> SearchResponse:
    """Search live Steam Store catalog by title or keyword."""
    t0 = time.perf_counter()
    items = await steam_client.search_games(q, limit=limit, lang=lang)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return SearchResponse(query=q, count=len(items), items=items, latency_ms=elapsed_ms)


@app.get("/api/v1/game/{appid}/xray", response_model=GameXRayReport, tags=["X-Ray Intelligence"])
async def get_game_xray(
    appid: int,
    lang: str = Query(default="en", pattern="^(en|uk)$", description="Language code: en or uk"),
) -> GameXRayReport:
    """
    Generate complete X-Ray intelligence report for a Steam game:
    - Live concurrent players right now
    - Developer & Publisher OSINT Dossier via Wikidata + Wikipedia (Country, Flag, HQ, Founded Year, Parent Org, Website)
    - Ukrainian Localization Check (Full Audio vs Text/Subtitles)
    - Historical Lowest Price via CheapShark API
    - Other games by the Developer & Publisher on Steam
    """
    if appid <= 0:
        raise HTTPException(status_code=400, detail="Invalid Steam AppID")
    return await build_game_xray(steam_client, appid, lang=lang)


@app.get("/api/v1/compare", response_model=CompareResponse, tags=["X-Ray Intelligence"])
async def compare_games_endpoint(
    appid_a: int = Query(..., description="First Steam AppID"),
    appid_b: int = Query(..., description="Second Steam AppID"),
    lang: str = Query(default="en", pattern="^(en|uk)$", description="Language code: en or uk"),
) -> CompareResponse:
    """Compare two Steam games side-by-side across ratings, live players, studio origin, localization, and Tag DNA overlap."""
    if appid_a <= 0 or appid_b <= 0:
        raise HTTPException(status_code=400, detail="Invalid Steam AppIDs")
    return await compare_two_games(steam_client, appid_a, appid_b, lang=lang)
