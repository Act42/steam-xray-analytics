"""Asynchronous client for Steam Store, Live Players, SteamSpy, Wikidata/Wikipedia Studio OSINT, and CheapShark Price API."""

from __future__ import annotations

import asyncio
from datetime import datetime
import html
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import httpx

from src.schemas import GameCard, PriceHistoryInfo, StudioIntelligence

logger = logging.getLogger(__name__)

STEAM_STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_PLAYERS_URL = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
STEAM_SEARCH_RESULTS_URL = "https://store.steampowered.com/search/results/"
STEAMSPY_URL = "https://steamspy.com/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
CHEAPSHARK_GAMES_URL = "https://www.cheapshark.com/api/1.0/games"

COUNTRY_FLAG_MAP: Dict[str, Tuple[str, str]] = {
    "ukraine": ("🇺🇦", "ukrainian"),
    "україна": ("🇺🇦", "ukrainian"),
    "poland": ("🇵🇱", "allied"),
    "польща": ("🇵🇱", "allied"),
    "united states": ("🇺🇸", "allied"),
    "сша": ("🇺🇸", "allied"),
    "сполучені штати америки": ("🇺🇸", "allied"),
    "japan": ("🇯🇵", "allied"),
    "японія": ("🇯🇵", "allied"),
    "belgium": ("🇧🇪", "allied"),
    "бельгія": ("🇧🇪", "allied"),
    "sweden": ("🇸🇪", "allied"),
    "швеція": ("🇸🇪", "allied"),
    "united kingdom": ("🇬🇧", "allied"),
    "велика британія": ("🇬🇧", "allied"),
    "france": ("🇫🇷", "allied"),
    "франція": ("🇫🇷", "allied"),
    "germany": ("🇩🇪", "allied"),
    "німеччина": ("🇩🇪", "allied"),
    "canada": ("🇨🇦", "allied"),
    "канада": ("🇨🇦", "allied"),
    "czech republic": ("🇨🇿", "allied"),
    "czechia": ("🇨🇿", "allied"),
    "чехія": ("🇨🇿", "allied"),
    "finland": ("🇫🇮", "allied"),
    "фінляндія": ("🇫🇮", "allied"),
    "south korea": ("🇰🇷", "allied"),
    "південна корея": ("🇰🇷", "allied"),
    "china": ("🇨🇳", "allied"),
    "китай": ("🇨🇳", "allied"),
    "australia": ("🇦🇺", "allied"),
    "австралія": ("🇦🇺", "allied"),
    "malta": ("🇲🇹", "allied"),
    "мальта": ("🇲🇹", "allied"),
    "cyprus": ("🇨🇾", "allied"),
    "кіпр": ("🇨🇾", "allied"),
    "russia": ("⚠️", "warning"),
    "росія": ("⚠️", "warning"),
    "російська федерація": ("⚠️", "warning"),
    "belarus": ("⚠️", "warning"),
    "білорусь": ("⚠️", "warning"),
}


# Pre-indexed fallback studio intelligence for common studios to guarantee instant resilience
KNOWN_STUDIO_FALLBACKS: Dict[str, Dict[str, str]] = {
    "cd projekt red": {
        "country_en": "Poland", "country_uk": "Польща",
        "hq_en": "Warsaw", "hq_uk": "Варшава",
        "founded": "1994", "parent": "CD Projekt S.A.",
        "web": "https://www.cdprojektred.com",
        "desc_en": "Polish video game development studio renowned for The Witcher series and Cyberpunk 2077.",
        "desc_uk": "Польська студія розробки відеоігор у Варшаві, відома серією «Відьмак» (The Witcher) та Cyberpunk 2077.",
    },
    "gsc game world": {
        "country_en": "Ukraine", "country_uk": "Україна",
        "hq_en": "Kyiv / Prague", "hq_uk": "Київ / Прага",
        "founded": "1995", "parent": "Independent (Sergiy Grygorovych)",
        "web": "https://www.gsc-game.com",
        "desc_en": "Ukrainian video game developer founded in Kyiv in 1995, creator of the Cossacks and S.T.A.L.K.E.R. franchises.",
        "desc_uk": "Українська компанія з розробки відеоігор, заснована у Києві в 1995 році, творець культових серій «Козаки» та S.T.A.L.K.E.R.",
    },
    "4a games": {
        "country_en": "Ukraine", "country_uk": "Україна",
        "hq_en": "Kyiv / Sliema", "hq_uk": "Київ / Сліма",
        "founded": "2006", "parent": "Embracer Group",
        "web": "https://www.4a-games.com.mt",
        "desc_en": "Ukrainian-Maltese video game development studio founded in Kyiv, famous for the Metro series (Metro 2033, Last Light, Exodus).",
        "desc_uk": "Українсько-мальтійська студія розробки відеоігор, заснована в Києві у 2006 році, відома серією ігор Metro.",
    },
    "fromsoftware": {
        "country_en": "Japan", "country_uk": "Японія",
        "hq_en": "Tokyo", "hq_uk": "Токіо",
        "founded": "1986", "parent": "Kadokawa Corporation",
        "web": "https://www.fromsoftware.jp",
        "desc_en": "Japanese video game development company founded in 1986, creator of Dark Souls, Bloodborne, Sekiro, Armored Core, and Elden Ring.",
        "desc_uk": "Японська компанія з розробки відеоігор у Токіо, творець культових ігор Dark Souls, Sekiro, Bloodborne та Elden Ring.",
    },
    "larian studios": {
        "country_en": "Belgium", "country_uk": "Бельгія",
        "hq_en": "Ghent", "hq_uk": "Гент",
        "founded": "1996", "parent": "Independent (Swen Vincke)",
        "web": "https://larian.com",
        "desc_en": "Belgian independent RPG developer founded in 1996 by Swen Vincke, creator of Divinity: Original Sin and Baldur's Gate 3.",
        "desc_uk": "Бельгійська незалежна студія розробки рольових ігор, заснована у 1996 році Сріном Вінке, творець серії Divinity та Baldur's Gate 3.",
    },
    "valve": {
        "country_en": "United States", "country_uk": "США",
        "hq_en": "Bellevue, Washington", "hq_uk": "Белв'ю, Вашингтон",
        "founded": "1996", "parent": "Independent (Gabe Newell)",
        "web": "https://www.valvesoftware.com",
        "desc_en": "American video game developer, publisher, and digital distribution company behind Half-Life, Counter-Strike, Portal, Dota 2, and Steam.",
        "desc_uk": "Американська компанія-розробник Half-Life, Counter-Strike, Portal, Dota 2 та власник платформи Steam.",
    },
}


CURATED_GAME_DNA_CATALOG: Dict[int, Dict[str, Any]] = {
    1091500: {
        "name": "Cyberpunk 2077",
        "developers": ["CD PROJEKT RED"],
        "price_formatted": "1 399₴",
        "approval_pct": 83.8,
        "tags": {"Cyberpunk": 6520, "Open World": 5940, "RPG": 5480, "Sci-fi": 4290, "FPS": 3980, "Story Rich": 3890, "Futuristic": 3510, "Action": 3420, "Atmospheric": 3180, "Singleplayer": 3120},
    },
    292030: {
        "name": "The Witcher 3: Wild Hunt",
        "developers": ["CD PROJEKT RED"],
        "price_formatted": "949₴",
        "approval_pct": 96.2,
        "tags": {"Open World": 12400, "RPG": 11900, "Story Rich": 10800, "Atmospheric": 9200, "Fantasy": 8900, "Action RPG": 8100, "Singleplayer": 7800, "Third Person": 7100, "Adventure": 6900, "Mature": 6400},
    },
    1643320: {
        "name": "S.T.A.L.K.E.R. 2: Heart of Chornobyl",
        "developers": ["GSC Game World"],
        "price_formatted": "1 399₴",
        "approval_pct": 82.5,
        "tags": {"Open World": 4800, "Post-apocalyptic": 4650, "FPS": 4500, "Survival": 4120, "Atmospheric": 4080, "Horror": 3420, "Action": 3300, "RPG": 3100, "Story Rich": 2950, "Singleplayer": 2900},
    },
    1245620: {
        "name": "ELDEN RING",
        "developers": ["FromSoftware, Inc."],
        "price_formatted": "1 799₴",
        "approval_pct": 93.1,
        "tags": {"Souls-like": 9800, "Open World": 8900, "Dark Fantasy": 8500, "RPG": 8300, "Difficult": 7900, "Action RPG": 7600, "Third Person": 6800, "Atmospheric": 6400, "Singleplayer": 6100, "Multiplayer": 5200},
    },
    1086940: {
        "name": "Baldur's Gate 3",
        "developers": ["Larian Studios"],
        "price_formatted": "899₴",
        "approval_pct": 96.8,
        "tags": {"RPG": 11200, "Choices Matter": 10400, "Story Rich": 10100, "Party-Based RPG": 9500, "Turn-Based Combat": 9100, "Fantasy": 8800, "Character Customization": 8600, "Online Co-Op": 7900, "Adventure": 7400, "Singleplayer": 7200},
    },
    730: {
        "name": "Counter-Strike 2",
        "developers": ["Valve"],
        "price_formatted": "Free to Play",
        "approval_pct": 87.4,
        "tags": {"FPS": 91000, "Shooter": 65000, "Multiplayer": 62000, "Competitive": 58000, "Action": 54000, "Team-Based": 46000, "eSports": 43000, "Tactical": 41000, "First-Person": 39000, "PvP": 35000},
    },
    367520: {
        "name": "Hollow Knight",
        "developers": ["Team Cherry"],
        "price_formatted": "325₴",
        "approval_pct": 97.1,
        "tags": {"Metroidvania": 7400, "Souls-like": 6800, "Platformer": 6500, "2D": 6200, "Indie": 5900, "Atmospheric": 5600, "Difficult": 5400, "Singleplayer": 5200, "Story Rich": 4900, "Great Soundtrack": 4800},
    },
    412020: {
        "name": "Metro Exodus",
        "developers": ["4A Games"],
        "price_formatted": "524₴",
        "approval_pct": 89.6,
        "tags": {"Post-apocalyptic": 5600, "Atmospheric": 5400, "FPS": 5200, "Story Rich": 4900, "Singleplayer": 4800, "Survival": 4500, "Action": 4400, "Open World": 4100, "Horror": 3800, "Shooter": 3700},
    },
}


class SteamAPIClient:
    """Async client orchestrating Steam Store, Live Players, SteamSpy, Wikidata/Wikipedia, and CheapShark."""

    def __init__(self, timeout_sec: float = 8.0, cache_ttl_sec: int = 900) -> None:
        self.timeout_sec = timeout_sec
        self.cache_ttl_sec = cache_ttl_sec
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.dna_catalog: Dict[int, Dict[str, Any]] = dict(CURATED_GAME_DNA_CATALOG)

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.cache_ttl_sec:
                return val
        return None

    def _set_cache(self, key: str, val: Any) -> None:
        self._cache[key] = (time.time(), val)

    @staticmethod
    def clean_html(raw_html: str) -> str:
        if not raw_html:
            return ""
        text = re.sub(r"<br\s*/?>", " | ", raw_html, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    async def search_games(self, query: str, limit: int = 10, lang: str = "en") -> List[GameCard]:
        """Search Steam Store by title or keyword."""
        steam_lang = "ukrainian" if lang == "uk" else "english"
        cache_key = f"search::{query.lower().strip()}::{limit}::{steam_lang}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        cards: List[GameCard] = []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_sec,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 SteamXRay/2.0"},
            ) as client:
                resp = await client.get(
                    STEAM_STORE_SEARCH_URL,
                    params={"term": query, "l": steam_lang, "cc": "UA"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", [])[:limit]:
                        appid = int(item.get("id", 0))
                        if not appid:
                            continue
                        price_info = item.get("price") or {}
                        initial_p = price_info.get("initial", 0)
                        final_p = price_info.get("final", 0)
                        discount = 0
                        if initial_p > 0 and final_p < initial_p:
                            discount = round((1.0 - final_p / initial_p) * 100)
                        price_str = f"{int(final_p / 100):,}₴".replace(",", " ") if final_p > 0 else "Free / N/A"

                        cards.append(
                            GameCard(
                                appid=appid,
                                name=item.get("name", f"App {appid}"),
                                header_image=f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
                                price_formatted=price_str,
                                discount_percent=discount,
                            )
                        )
        except Exception as exc:
            logger.warning("Steam search failed for '%s': %s", query, exc)

        self._set_cache(cache_key, cards[:limit])
        return cards[:limit]

    async def fetch_app_details(self, appid: int, lang: str = "en") -> Dict[str, Any]:
        steam_lang = "ukrainian" if lang == "uk" else "english"
        cache_key = f"appdetails::{appid}::{steam_lang}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_sec,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 SteamXRay/2.0"},
            ) as client:
                resp = await client.get(
                    STEAM_APPDETAILS_URL,
                    params={"appids": appid, "cc": "UA", "l": steam_lang},
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    app_block = payload.get(str(appid), {})
                    if app_block.get("success") and "data" in app_block:
                        data = app_block["data"]
                        self._set_cache(cache_key, data)
                        return data
        except Exception as exc:
            logger.warning("AppDetails failed for %d: %s", appid, exc)
        return {}

    async def fetch_live_players(self, appid: int) -> int:
        cache_key = f"players::{appid}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return int(cached)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_sec,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 SteamXRay/2.0"},
            ) as client:
                resp = await client.get(STEAM_PLAYERS_URL, params={"appid": appid})
                if resp.status_code == 200:
                    count = int(resp.json().get("response", {}).get("player_count", 0))
                    self._set_cache(cache_key, count)
                    return count
        except Exception as exc:
            logger.warning("LivePlayers failed for %d: %s", appid, exc)
        return 0

    async def fetch_steamspy(self, appid: int) -> Dict[str, Any]:
        cache_key = f"steamspy::{appid}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_sec,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 SteamXRay/2.0"},
            ) as client:
                resp = await client.get(STEAMSPY_URL, params={"request": "appdetails", "appid": appid})
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("name"):
                        self._set_cache(cache_key, data)
                        return data
        except Exception as exc:
            logger.warning("SteamSpy failed for %d: %s", appid, exc)
        return {}

    async def fetch_company_games(
        self, company_name: str, param_type: str, exclude_appid: int, limit: int = 6
    ) -> List[GameCard]:
        """Fetch other games by developer (`param_type='developer'`) or publisher (`param_type='publisher'`)."""
        if not company_name:
            return []
        cache_key = f"companygames::{param_type}::{company_name.lower().strip()}::{exclude_appid}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        cards: List[GameCard] = []
        seen_ids = {exclude_appid}
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_sec,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 SteamXRay/2.0"},
            ) as client:
                resp = await client.get(
                    STEAM_SEARCH_RESULTS_URL,
                    params={param_type: company_name, "json": 1, "cc": "UA", "l": "english"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        logo_url = item.get("logo", "")
                        m = re.search(r"/apps/(\d+)/", logo_url)
                        if not m:
                            continue
                        item_appid = int(m.group(1))
                        if item_appid in seen_ids:
                            continue
                        seen_ids.add(item_appid)
                        name = html.unescape(item.get("name", f"App {item_appid}"))
                        if any(k in name.lower() for k in ["soundtrack", "artbook", "bonus content", "ost"]):
                            continue
                        cat_price = self.dna_catalog.get(item_appid, {}).get("price_formatted", "Steam Store")
                        cards.append(
                            GameCard(
                                appid=item_appid,
                                name=name,
                                header_image=f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{item_appid}/header.jpg",
                                price_formatted=cat_price,
                                developers=[company_name],
                            )
                        )
                        if len(cards) >= limit:
                            break
        except Exception as exc:
            logger.warning("Company games search failed for '%s': %s", company_name, exc)

        self._set_cache(cache_key, cards[:limit])
        return cards[:limit]

    async def fetch_studio_intelligence(self, studio_name: str, role: str = "Developer", lang: str = "en") -> StudioIntelligence:
        """
        Query Wikidata API (Country P17, Headquarters P159, Inception P571, Parent P749, Website P856)
        and Wikipedia REST Summary API (en / uk) for live developer or publisher dossier.
        """
        if not studio_name:
            return StudioIntelligence(name="Unknown", role=role)

        cache_key = f"studio_intel::{studio_name.lower().strip()}::{role}::{lang}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        # Clean studio name for search (strip corporate suffixes like ", Inc.", " Ltd.", " S.A.")
        clean_search = re.sub(r",?\s*(?:Inc\.?|LLC|Ltd\.?|S\.A\.?|Corp\.?|GmbH|Co\.,?\s*Ltd\.?)$", "", studio_name, flags=re.IGNORECASE).strip()
        norm_key = clean_search.lower()

        fb = next((v for k, v in KNOWN_STUDIO_FALLBACKS.items() if k in norm_key or norm_key in k), None)

        wikidata_id = ""
        country = (fb["country_uk"] if lang == "uk" else fb["country_en"]) if fb else ("Невідомо" if lang == "uk" else "Unknown")
        hq = (fb["hq_uk"] if lang == "uk" else fb["hq_en"]) if fb else "N/A"
        founded = fb["founded"] if fb else "N/A"
        parent_org = fb.get("parent", "") if fb else ""
        website = fb.get("web", "") if fb else ""
        desc = (fb["desc_uk"] if lang == "uk" else fb["desc_en"]) if fb else ""
        wiki_extract = ""
        wiki_url = ""

        try:
            async with httpx.AsyncClient(
                timeout=6.5,
                follow_redirects=True,
                headers={"User-Agent": "SteamXRay/2.0 (https://github.com/Act42; Educational Game Analytics)"},
            ) as client:
                w_search = await client.get(
                    WIKIDATA_API_URL,
                    params={
                        "action": "wbsearchentities",
                        "search": clean_search,
                        "language": "en",
                        "format": "json",
                        "limit": 3,
                    },
                )
                if w_search.status_code == 200:
                    search_hits = w_search.json().get("search", [])
                    if search_hits:
                        wikidata_id = search_hits[0].get("id", "")

                if wikidata_id:
                    ent_resp = await client.get(
                        WIKIDATA_API_URL,
                        params={
                            "action": "wbgetentities",
                            "ids": wikidata_id,
                            "languages": "en|uk",
                            "props": "labels|descriptions|claims|sitelinks",
                            "format": "json",
                        },
                    )
                    if ent_resp.status_code == 200:
                        ent = ent_resp.json().get("entities", {}).get(wikidata_id, {})
                        descriptions = ent.get("descriptions", {})
                        wd_desc = (
                            descriptions.get(lang, {}).get("value")
                            or descriptions.get("en", {}).get("value")
                            or ""
                        )
                        if wd_desc and not desc:
                            desc = wd_desc.capitalize()

                        claims = ent.get("claims", {})
                        p17_id = self._extract_claim_id(claims, "P17")
                        p159_id = self._extract_claim_id(claims, "P159")
                        p749_id = self._extract_claim_id(claims, "P749") or self._extract_claim_id(claims, "P127")
                        p571_time = self._extract_claim_value(claims, "P571", "time")
                        p856_url = self._extract_claim_value(claims, "P856", "str")

                        if p571_time:
                            ym = re.search(r"(\d{4})", str(p571_time))
                            if ym:
                                founded = ym.group(1)
                        if p856_url:
                            website = str(p856_url)

                        to_resolve = [x for x in [p17_id, p159_id, p749_id] if x]
                        if to_resolve:
                            res_resp = await client.get(
                                WIKIDATA_API_URL,
                                params={
                                    "action": "wbgetentities",
                                    "ids": "|".join(to_resolve),
                                    "languages": "en|uk",
                                    "props": "labels",
                                    "format": "json",
                                },
                            )
                            if res_resp.status_code == 200:
                                res_entities = res_resp.json().get("entities", {})
                                if p17_id and p17_id in res_entities:
                                    c_lbls = res_entities[p17_id].get("labels", {})
                                    country = c_lbls.get(lang, {}).get("value") or c_lbls.get("en", {}).get("value") or country
                                if p159_id and p159_id in res_entities:
                                    h_lbls = res_entities[p159_id].get("labels", {})
                                    hq = h_lbls.get(lang, {}).get("value") or h_lbls.get("en", {}).get("value") or hq
                                if p749_id and p749_id in res_entities:
                                    p_lbls = res_entities[p749_id].get("labels", {})
                                    parent_org = p_lbls.get(lang, {}).get("value") or p_lbls.get("en", {}).get("value") or parent_org

                        # Fetch Wikipedia summary in preferred language (fallback to English)
                        sitelinks = ent.get("sitelinks", {})
                        wiki_site_key = "ukwiki" if (lang == "uk" and "ukwiki" in sitelinks) else ("enwiki" if "enwiki" in sitelinks else "")
                        wiki_lang_host = "uk" if wiki_site_key == "ukwiki" else "en"
                        if wiki_site_key:
                            wiki_title = sitelinks[wiki_site_key].get("title", "")
                            if wiki_title:
                                sum_url = f"https://{wiki_lang_host}.wikipedia.org/api/rest_v1/page/summary/{quote(wiki_title)}"
                                sum_resp = await client.get(sum_url)
                                if sum_resp.status_code == 200:
                                    s_json = sum_resp.json()
                                    wiki_extract = s_json.get("extract", "")
                                    wiki_url = s_json.get("content_urls", {}).get("desktop", {}).get("page", "")
        except Exception as exc:
            logger.warning("Studio Wikidata lookup failed for '%s': %s", studio_name, exc)

        if not wiki_extract and desc:
            wiki_extract = desc

        c_low = country.lower().strip()
        flag, origin_status = COUNTRY_FLAG_MAP.get(c_low, ("🌐", "verified"))
        for k, (flg, st) in COUNTRY_FLAG_MAP.items():
            if k in c_low:
                flag, origin_status = flg, st
                break

        intel = StudioIntelligence(
            name=studio_name,
            role=role,
            wikidata_id=wikidata_id,
            country=country,
            country_code=flag,
            headquarters=hq,
            founded_year=founded,
            parent_company=parent_org,
            official_website=website,
            description=desc,
            wikipedia_extract=wiki_extract,
            wikipedia_url=wiki_url,
            origin_status=origin_status,
        )
        self._set_cache(cache_key, intel)
        return intel

    @staticmethod
    def _extract_claim_id(claims: dict, prop: str) -> str:
        items = claims.get(prop, [])
        if not items:
            return ""
        val = items[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        return val.get("id", "") if isinstance(val, dict) else ""

    @staticmethod
    def _extract_claim_value(claims: dict, prop: str, mode: str) -> str:
        items = claims.get(prop, [])
        if not items:
            return ""
        val = items[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if mode == "time" and isinstance(val, dict):
            return str(val.get("time", ""))
        return str(val) if isinstance(val, str) else ""

    async def fetch_price_history(self, appid: int) -> PriceHistoryInfo:
        """Query CheapShark API for historical lowest price ever recorded and active deals count."""
        cache_key = f"price_history::{appid}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        info = PriceHistoryInfo()
        try:
            async with httpx.AsyncClient(
                timeout=6.0,
                follow_redirects=True,
                headers={"User-Agent": "SteamXRay/2.0"},
            ) as client:
                r1 = await client.get(CHEAPSHARK_GAMES_URL, params={"steamAppID": appid})
                if r1.status_code == 200:
                    matches = r1.json()
                    if isinstance(matches, list) and matches:
                        cs_game_id = matches[0].get("gameID")
                        cheapest_curr = matches[0].get("cheapest")
                        if cheapest_curr:
                            info.current_best_deal_usd = float(cheapest_curr)
                        if cs_game_id:
                            r2 = await client.get(CHEAPSHARK_GAMES_URL, params={"id": cs_game_id})
                            if r2.status_code == 200:
                                details = r2.json()
                                cheapest_ever = details.get("cheapestPriceEver") or {}
                                deals = details.get("deals") or []
                                info.active_deals_count = len(deals)
                                if cheapest_ever.get("price"):
                                    info.cheapest_ever_usd = float(cheapest_ever["price"])
                                if cheapest_ever.get("date"):
                                    ts = int(cheapest_ever["date"])
                                    info.cheapest_ever_date = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                                if deals:
                                    retail = float(deals[0].get("retailPrice") or 0)
                                    if retail > 0 and info.cheapest_ever_usd is not None:
                                        info.historical_max_discount_est_pct = max(
                                            0, min(95, round((1.0 - info.cheapest_ever_usd / retail) * 100))
                                        )
        except Exception as exc:
            logger.warning("CheapShark lookup failed for %d: %s", appid, exc)

        self._set_cache(cache_key, info)
        return info
