"""Analytics Engine: Telemetry Aggregation, Studio OSINT (Developer & Publisher), Ukrainian Localization, Price History & VS Comparison."""

from __future__ import annotations

import asyncio
import html
import math
import re
import time
from typing import Dict, List, Optional, Tuple

from src.schemas import (
    CompareResponse,
    GameXRayReport,
    LocalizationInfo,
    StudioIntelligence,
    TagDNAItem,
    ValueVerdict,
)
from src.steam_client import SteamAPIClient


def parse_owners_midpoint(owners_str: str) -> int:
    """Parse SteamSpy owners string like '20,000,000 .. 50,000,000' into integer midpoint."""
    if not owners_str:
        return 0
    nums = [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", owners_str) if n.replace(",", "").isdigit()]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) // 2
    if len(nums) == 1:
        return nums[0]
    return 0


def wilson_lower_bound(pos: int, neg: int, z: float = 1.96) -> float:
    """Compute Wilson score lower bound (0-100%) for statistical confidence in game rating."""
    n = pos + neg
    if n <= 0:
        return 0.0
    phat = pos / n
    denom = 1.0 + (z * z) / n
    num = phat + (z * z) / (2.0 * n) - z * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * n)) / n)
    return round(max(0.0, min(100.0, (num / denom) * 100.0)), 2)


def parse_localization(supported_languages_html: str, lang: str = "en") -> LocalizationInfo:
    """
    Parse Steam's `supported_languages` HTML string to detect Ukrainian text/voice support
    and classify all supported languages into full audio vs text-only.
    """
    if not supported_languages_html:
        empty_lbl = "Немає даних про мови" if lang == "uk" else "Language data N/A"
        return LocalizationInfo(ukrainian_status_label=empty_lbl)

    # Strip the footnote after <br> (e.g., "<br><strong>*</strong>languages with full audio support")
    main_part = re.split(r"<br\s*/?>", supported_languages_html, flags=re.IGNORECASE)[0]
    raw_tokens = [tok.strip() for tok in main_part.split(",") if tok.strip()]

    full_audio: List[str] = []
    text_only: List[str] = []
    has_ua_text = False
    has_ua_audio = False

    for tok in raw_tokens:
        is_audio = "*" in tok
        clean_name = re.sub(r"<[^>]+>", "", tok)
        clean_name = html.unescape(clean_name).replace("*", "").strip()
        if not clean_name:
            continue

        if is_audio:
            full_audio.append(clean_name)
        else:
            text_only.append(clean_name)

        low = clean_name.lower()
        if "ukrainian" in low or "україн" in low:
            has_ua_text = True
            if is_audio:
                has_ua_audio = True

    if has_ua_audio:
        status_label = (
            "Повна українська (Текст + Озвучка)"
            if lang == "uk"
            else "Full Ukrainian (Text + Audio)"
        )
    elif has_ua_text:
        status_label = (
            "Українська локалізація (Текст / Субтитри)"
            if lang == "uk"
            else "Ukrainian Text & Subtitles"
        )
    else:
        status_label = (
            "Без офіційної української"
            if lang == "uk"
            else "No Official Ukrainian"
        )

    return LocalizationInfo(
        has_ukrainian_text=has_ua_text,
        has_ukrainian_audio=has_ua_audio,
        ukrainian_status_label=status_label,
        total_languages_count=len(full_audio) + len(text_only),
        full_audio_languages=full_audio,
        text_only_languages=text_only,
    )


def build_tag_dna(
    raw_tags: Dict[str, int],
    fallback_genres: List[str],
    fallback_categories: List[str],
    top_n: int = 10,
) -> List[TagDNAItem]:
    """Convert raw SteamSpy tag vote counts into normalized TagDNAItem profile (0-100% relative to top tag)."""
    if not raw_tags:
        synthesized: Dict[str, int] = {}
        for idx, g in enumerate(fallback_genres[:6]):
            synthesized[g] = max(1000 - idx * 140, 200)
        for idx, c in enumerate(fallback_categories[:4]):
            if c not in synthesized:
                synthesized[c] = max(550 - idx * 90, 150)
        raw_tags = synthesized

    if not raw_tags:
        return []

    sorted_pairs = sorted(raw_tags.items(), key=lambda x: int(x[1]), reverse=True)[:top_n]
    max_votes = max(int(sorted_pairs[0][1]), 1)

    return [
        TagDNAItem(
            tag=tag_name,
            votes=int(votes),
            weight_pct=round((int(votes) / max_votes) * 100.0, 1),
        )
        for tag_name, votes in sorted_pairs
    ]


def compute_tag_similarity(
    target_dna: List[TagDNAItem],
    target_genres: List[str],
    candidate_tags: Dict[str, int],
) -> Tuple[float, List[str]]:
    """Compute hybrid Rank-Weighted Cosine + Jaccard similarity between two games' Tag DNA."""
    if not target_dna or not candidate_tags:
        return 0.0, []

    target_weights: Dict[str, float] = {}
    for rank_idx, item in enumerate(target_dna):
        rank_factor = 1.0 / math.sqrt(rank_idx + 1.0)
        target_weights[item.tag.lower()] = (item.weight_pct / 100.0) * rank_factor

    for g in target_genres:
        g_low = g.lower()
        if g_low not in target_weights:
            target_weights[g_low] = 0.35

    cand_sorted = sorted(candidate_tags.items(), key=lambda x: int(x[1]), reverse=True)[:12]
    cand_max = max(int(cand_sorted[0][1]), 1)
    cand_weights: Dict[str, float] = {}
    cand_original_names: Dict[str, str] = {}
    for rank_idx, (t_name, votes) in enumerate(cand_sorted):
        t_low = t_name.lower()
        rank_factor = 1.0 / math.sqrt(rank_idx + 1.0)
        cand_weights[t_low] = (int(votes) / cand_max) * rank_factor
        cand_original_names[t_low] = t_name

    shared_keys = [k for k in target_weights if k in cand_weights]
    if not shared_keys:
        return 0.0, []

    dot = sum(target_weights[k] * cand_weights[k] for k in shared_keys)
    norm_a = math.sqrt(sum(v * v for v in target_weights.values())) + 1e-9
    norm_b = math.sqrt(sum(v * v for v in cand_weights.values())) + 1e-9
    cosine = dot / (norm_a * norm_b)

    jaccard = len(shared_keys) / max(min(len(target_weights), len(cand_weights)), 1)
    blended = 0.65 * cosine + 0.35 * jaccard
    calibrated_pct = round(min(99.0, blended * 112.0), 1)

    shared_display = [cand_original_names[k] for k in shared_keys[:5]]
    return calibrated_pct, shared_display


def compute_value_verdict(
    approval_pct: float,
    wilson_pct: float,
    price_uah: float,
    discount_pct: int,
    live_players: int,
    avg_playtime_hrs: float,
    metacritic: Optional[int],
    is_free: bool,
    lang: str = "en",
) -> ValueVerdict:
    """Compute composite 0-100 quality/value score and localized human-readable purchase verdict."""
    meta_component = float(metacritic) if metacritic else approval_pct
    engagement_bonus = min(math.log10(live_players + 1) * 3.2, 15.0)
    discount_bonus = min(discount_pct * 0.12, 8.0)

    overall = round(
        min(
            99.5,
            0.50 * wilson_pct + 0.25 * meta_component + 0.15 * approval_pct + engagement_bonus * 0.6 + discount_bonus,
        ),
        1,
    )

    cost_per_hr: Optional[float] = None
    if not is_free and price_uah > 0 and avg_playtime_hrs >= 1.0:
        cost_per_hr = round(price_uah / avg_playtime_hrs, 1)

    if is_free and approval_pct >= 80.0:
        color = "emerald"
        if lang == "uk":
            label = "Безкоштовний хіт"
            reason = f"Безкоштовна гра з {approval_pct:.1f}% позитивних відгуків та {live_players:,} гравцями онлайн прямо зараз."
        else:
            label = "Must-Play Free Hit"
            reason = f"Free-to-Play title with {approval_pct:.1f}% positive reviews and {live_players:,} active players right now."
    elif overall >= 88.0 and approval_pct >= 90.0:
        color = "emerald"
        if lang == "uk":
            label = "Шедевр (Must-Play)"
            reason = f"Всесвітнє визнання ({approval_pct:.1f}% схвалення спільноти, {live_players:,} онлайн). Безпечна покупка."
        else:
            label = "Must-Play Masterpiece"
            reason = f"Universal acclaim ({approval_pct:.1f}% community approval, {live_players:,} live players). Safe instant buy."
    elif discount_pct >= 35 and approval_pct >= 78.0:
        color = "emerald"
        if lang == "uk":
            label = f"Гаряча знижка (-{discount_pct}%)"
            reason = f"Високий рейтинг ({approval_pct:.1f}%) у поєднанні зі знижкою -{discount_pct}%."
        else:
            label = f"Hot Deal (-{discount_pct}% Off)"
            reason = f"Strong {approval_pct:.1f}% rating combined with a steep -{discount_pct}% discount."
    elif overall >= 76.0:
        color = "cyan"
        if lang == "uk":
            label = "Впевнена рекомендація"
            reason = f"Схвальні відгуки гравців ({approval_pct:.1f}% позитивних) та активна спільнота."
        else:
            label = "Solid Recommendation"
            reason = f"Well-received by players ({approval_pct:.1f}% positive) with strong genre DNA and active community."
    elif approval_pct >= 65.0:
        color = "amber"
        if lang == "uk":
            label = "Варто чекати розпродажу"
            reason = f"Стримано-позитивний рейтинг ({approval_pct:.1f}%). Оптимально брати на сезонному розпродажі."
        else:
            label = "Wait for Sale"
            reason = f"Mixed-to-positive reception ({approval_pct:.1f}%). Best picked up during a seasonal Steam discount."
    else:
        color = "rose"
        if lang == "uk":
            label = "Змішані відгуки / Ризик"
            reason = f"Рівень схвалення спільноти становить {approval_pct:.1f}%. Рекомендується перевірити останні патчі."
        else:
            label = "High Risk / Mixed Reviews"
            reason = f"Community approval is relatively low ({approval_pct:.1f}%). Check recent patch notes before buying."

    return ValueVerdict(
        verdict_label=label,
        verdict_color=color,
        overall_score=overall,
        approval_pct=round(approval_pct, 1),
        wilson_score_pct=round(wilson_pct, 1),
        cost_per_hour_uah=cost_per_hr,
        summary_reason=reason,
    )


async def build_game_xray(client: SteamAPIClient, appid: int, lang: str = "en") -> GameXRayReport:
    """
    Orchestrate parallel calls to Steam Store, Live Players, SteamSpy, CheapShark Price History,
    Wikidata/Wikipedia Studio OSINT (Developer & Publisher), and Company Portfolios.
    """
    t0 = time.perf_counter()

    app_data, live_players, spy_data, price_history = await asyncio.gather(
        client.fetch_app_details(appid, lang=lang),
        client.fetch_live_players(appid),
        client.fetch_steamspy(appid),
        client.fetch_price_history(appid),
    )

    fallback = client.dna_catalog.get(appid, {})
    name = app_data.get("name") or spy_data.get("name") or fallback.get("name") or f"Steam App {appid}"
    developers = app_data.get("developers") or (
        [spy_data["developer"]] if spy_data.get("developer") else fallback.get("developers", ["Unknown Studio"])
    )
    publishers = app_data.get("publishers") or (
        [spy_data["publisher"]] if spy_data.get("publisher") else developers
    )

    lead_developer = developers[0] if developers else "Unknown Studio"
    lead_publisher = publishers[0] if publishers else lead_developer
    same_studio = lead_developer.lower().strip() == lead_publisher.lower().strip()

    # Fetch Studio Intelligence (Wikidata + Wikipedia) and Other Games on Steam concurrently
    if same_studio:
        dev_intel, dev_other_games, pub_other_games = await asyncio.gather(
            client.fetch_studio_intelligence(lead_developer, role="Developer", lang=lang),
            client.fetch_company_games(lead_developer, "developer", exclude_appid=appid, limit=6),
            client.fetch_company_games(lead_publisher, "publisher", exclude_appid=appid, limit=6),
        )
        pub_intel = StudioIntelligence(
            **{
                **dev_intel.model_dump(),
                "name": lead_publisher,
                "role": "Publisher (Self-Published)" if lang == "en" else "Видавець (Власне видання)",
            }
        )
    else:
        dev_intel, pub_intel, dev_other_games, pub_other_games = await asyncio.gather(
            client.fetch_studio_intelligence(lead_developer, role="Developer", lang=lang),
            client.fetch_studio_intelligence(lead_publisher, role="Publisher", lang=lang),
            client.fetch_company_games(lead_developer, "developer", exclude_appid=appid, limit=6),
            client.fetch_company_games(lead_publisher, "publisher", exclude_appid=appid, limit=6),
        )

    genres = [g["description"] for g in app_data.get("genres", []) if g.get("description")]
    categories = [c["description"] for c in app_data.get("categories", []) if c.get("description")][:8]

    is_free = bool(app_data.get("is_free", False))
    price_info = app_data.get("price_overview") or {}
    discount_pct = int(price_info.get("discount_percent", 0))
    price_uah = round(int(price_info.get("final", 0)) / 100.0, 2) if price_info else 0.0

    if is_free:
        price_formatted = "Безкоштовно" if lang == "uk" else "Free to Play"
        initial_formatted = ""
    elif price_info.get("final_formatted"):
        price_formatted = price_info["final_formatted"]
        initial_formatted = price_info.get("initial_formatted", "")
    else:
        price_formatted = fallback.get("price_formatted", "Steam Store")
        initial_formatted = ""

    pos_reviews = int(spy_data.get("positive", 0))
    neg_reviews = int(spy_data.get("negative", 0))
    total_rec = int((app_data.get("recommendations") or {}).get("total", 0))

    if pos_reviews + neg_reviews == 0 and total_rec > 0:
        est_ratio = (fallback.get("approval_pct", 85.0)) / 100.0
        pos_reviews = int(total_rec * est_ratio)
        neg_reviews = max(total_rec - pos_reviews, 1)
    elif pos_reviews + neg_reviews == 0 and fallback.get("approval_pct"):
        pos_reviews = int(fallback["approval_pct"] * 100)
        neg_reviews = int((100.0 - fallback["approval_pct"]) * 100)

    total_reviews = pos_reviews + neg_reviews
    approval_pct = round((pos_reviews / total_reviews) * 100.0, 1) if total_reviews > 0 else 80.0
    wilson_pct = wilson_lower_bound(pos_reviews, neg_reviews)

    owners_range = spy_data.get("owners") or "1,000,000 .. 2,000,000"
    owners_mid = parse_owners_midpoint(owners_range)

    avg_playtime_min = int(spy_data.get("average_forever", 0))
    med_playtime_min = int(spy_data.get("median_forever", 0))
    avg_playtime_hrs = round(avg_playtime_min / 60.0, 1) if avg_playtime_min > 0 else 28.5
    med_playtime_hrs = round(med_playtime_min / 60.0, 1) if med_playtime_min > 0 else 18.0

    raw_tags = spy_data.get("tags")
    if not isinstance(raw_tags, dict) or not raw_tags:
        raw_tags = fallback.get("tags", {})

    tag_dna = build_tag_dna(raw_tags, genres, categories, top_n=10)
    if not genres and tag_dna:
        genres = [t.tag for t in tag_dna[:3]]

    localization = parse_localization(app_data.get("supported_languages", ""), lang=lang)

    metacritic_obj = app_data.get("metacritic") or {}
    metacritic_score = int(metacritic_obj["score"]) if metacritic_obj.get("score") else None
    metacritic_url = metacritic_obj.get("url", "")

    screenshots = [
        s.get("path_full") or s.get("path_thumbnail", "")
        for s in app_data.get("screenshots", [])[:6]
        if s.get("path_thumbnail") or s.get("path_full")
    ]

    trailer_url = ""
    movies = app_data.get("movies") or []
    if movies:
        mp4_dict = movies[0].get("mp4") or {}
        webm_dict = movies[0].get("webm") or {}
        trailer_url = mp4_dict.get("480") or mp4_dict.get("max") or webm_dict.get("480") or ""

    pc_reqs = app_data.get("pc_requirements")
    pc_min = ""
    if isinstance(pc_reqs, dict):
        pc_min = client.clean_html(pc_reqs.get("minimum", ""))

    verdict = compute_value_verdict(
        approval_pct=approval_pct,
        wilson_pct=wilson_pct,
        price_uah=price_uah,
        discount_pct=discount_pct,
        live_players=live_players,
        avg_playtime_hrs=avg_playtime_hrs,
        metacritic=metacritic_score,
        is_free=is_free,
        lang=lang,
    )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return GameXRayReport(
        appid=appid,
        lang=lang,
        name=name,
        short_description=client.clean_html(app_data.get("short_description", "")),
        header_image=app_data.get("header_image")
        or f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
        background_image=app_data.get("background_raw") or app_data.get("background") or "",
        website=app_data.get("website") or f"https://store.steampowered.com/app/{appid}/",
        release_date=(app_data.get("release_date") or {}).get("date", "Released"),
        developers=developers,
        publishers=publishers,
        genres=genres,
        categories=categories,
        is_free=is_free,
        price_formatted=price_formatted,
        initial_price_formatted=initial_formatted,
        price_uah=price_uah,
        discount_percent=discount_pct,
        live_players=live_players,
        owners_range=owners_range,
        owners_midpoint=owners_mid,
        positive_reviews=pos_reviews,
        negative_reviews=neg_reviews,
        total_reviews=total_reviews,
        average_playtime_hours=avg_playtime_hrs,
        median_playtime_hours=med_playtime_hrs,
        metacritic_score=metacritic_score,
        metacritic_url=metacritic_url,
        screenshots=screenshots,
        trailer_url=trailer_url,
        pc_requirements_min=pc_min,
        tag_dna=tag_dna,
        verdict=verdict,
        localization=localization,
        price_history=price_history,
        developer_intel=dev_intel,
        publisher_intel=pub_intel,
        developer_other_games=dev_other_games,
        publisher_other_games=pub_other_games,
        latency_ms=elapsed_ms,
    )


async def compare_two_games(
    client: SteamAPIClient, appid_a: int, appid_b: int, lang: str = "en"
) -> CompareResponse:
    """Build side-by-side comparison and unified Radar DNA axes for two Steam games."""
    report_a, report_b = await asyncio.gather(
        build_game_xray(client, appid_a, lang=lang),
        build_game_xray(client, appid_b, lang=lang),
    )

    cand_b_tags = {t.tag: t.votes for t in report_b.tag_dna}
    overlap_pct, shared_tags = compute_tag_similarity(report_a.tag_dna, report_a.genres, cand_b_tags)

    if lang == "uk":
        axes = [
            "Схвалення спільноти",
            "Загальний індекс якості",
            "Активність онлайн",
            "Тривалість гри",
            "Обсяг відгуків",
            "Широта локалізацій",
        ]
    else:
        axes = [
            "Community Approval",
            "Overall Value Score",
            "Live Players Activity",
            "Replayability (Playtime)",
            "Review Volume Confidence",
            "Localization Reach",
        ]

    def _radar_metrics(r: GameXRayReport) -> List[float]:
        live_norm = min(100.0, round(math.log10(r.live_players + 10) * 18.5, 1))
        play_norm = min(100.0, round(math.log10(r.average_playtime_hours + 2) * 48.0, 1))
        rev_norm = min(100.0, round(math.log10(r.total_reviews + 10) * 16.5, 1))
        loc_norm = min(100.0, round(r.localization.total_languages_count * 7.5, 1))
        return [
            r.verdict.approval_pct,
            r.verdict.overall_score,
            live_norm,
            play_norm,
            rev_norm,
            loc_norm,
        ]

    vals_a = _radar_metrics(report_a)
    vals_b = _radar_metrics(report_b)

    if report_a.verdict.overall_score >= report_b.verdict.overall_score:
        lead, trail = report_a, report_b
    else:
        lead, trail = report_b, report_a

    if lang == "uk":
        summary = (
            f"{lead.name} лідирує з індексом {lead.verdict.overall_score}/100 "
            f"({lead.verdict.approval_pct}% схвалення, {lead.live_players:,} онлайн, студія з країни: {lead.developer_intel.country_code} {lead.developer_intel.country}) проти "
            f"{trail.name} ({trail.verdict.overall_score}/100, {trail.verdict.approval_pct}% схвалення, "
            f"{trail.live_players:,} онлайн). Схожість жанрового ДНК: {overlap_pct}%."
        )
    else:
        summary = (
            f"{lead.name} leads with an Overall Score of {lead.verdict.overall_score}/100 "
            f"({lead.verdict.approval_pct}% approval, {lead.live_players:,} live players, studio origin: {lead.developer_intel.country_code} {lead.developer_intel.country}) vs "
            f"{trail.name} ({trail.verdict.overall_score}/100, {trail.verdict.approval_pct}% approval, "
            f"{trail.live_players:,} live players). Genre DNA overlap is {overlap_pct}%."
        )

    return CompareResponse(
        game_a=report_a,
        game_b=report_b,
        dna_overlap_pct=overlap_pct,
        shared_tags=shared_tags,
        shared_Radar_axes=axes,
        game_a_radar_values=vals_a,
        game_b_radar_values=vals_b,
        winner_summary=summary,
    )
