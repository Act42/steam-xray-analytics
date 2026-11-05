"""Pydantic v2 schemas for SteamXRay: Game Telemetry, Studio OSINT (Wikidata/Wikipedia), Localization & Price History."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class GameCard(BaseModel):
    appid: int
    name: str
    header_image: str = ""
    price_formatted: str = "Free / N/A"
    discount_percent: int = 0
    release_year: Optional[int] = None
    developers: List[str] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)


class TagDNAItem(BaseModel):
    tag: str
    votes: int
    weight_pct: float = Field(..., description="Normalized percentage weight (0-100) in game DNA profile")


class StudioIntelligence(BaseModel):
    name: str
    role: str = Field(default="Developer", description="Developer or Publisher")
    wikidata_id: str = ""
    country: str = "Unknown"
    country_code: str = "🌐"
    headquarters: str = "N/A"
    founded_year: str = "N/A"
    parent_company: str = ""
    official_website: str = ""
    description: str = ""
    wikipedia_extract: str = ""
    wikipedia_url: str = ""
    origin_status: str = Field(
        default="verified",
        description="ukrainian (UA studio), allied (EU/US/JP/etc.), warning (RU/BY ties), or unknown",
    )


class LocalizationInfo(BaseModel):
    has_ukrainian_text: bool = False
    has_ukrainian_audio: bool = False
    ukrainian_status_label: str = ""
    total_languages_count: int = 0
    full_audio_languages: List[str] = Field(default_factory=list)
    text_only_languages: List[str] = Field(default_factory=list)


class PriceHistoryInfo(BaseModel):
    cheapest_ever_usd: Optional[float] = None
    cheapest_ever_date: str = ""
    current_best_deal_usd: Optional[float] = None
    active_deals_count: int = 0
    historical_max_discount_est_pct: int = 0


class ValueVerdict(BaseModel):
    verdict_label: str
    verdict_color: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    approval_pct: float = Field(..., ge=0.0, le=100.0)
    wilson_score_pct: float = Field(..., ge=0.0, le=100.0)
    cost_per_hour_uah: Optional[float] = None
    summary_reason: str = ""


class GameXRayReport(BaseModel):
    appid: int
    lang: str = "en"
    name: str
    short_description: str = ""
    header_image: str = ""
    background_image: str = ""
    website: str = ""
    release_date: str = ""
    developers: List[str] = Field(default_factory=list)
    publishers: List[str] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    is_free: bool = False
    price_formatted: str = "Free to Play"
    initial_price_formatted: str = ""
    price_uah: float = 0.0
    discount_percent: int = 0
    live_players: int = 0
    owners_range: str = "N/A"
    owners_midpoint: int = 0
    positive_reviews: int = 0
    negative_reviews: int = 0
    total_reviews: int = 0
    average_playtime_hours: float = 0.0
    median_playtime_hours: float = 0.0
    metacritic_score: Optional[int] = None
    metacritic_url: str = ""
    screenshots: List[str] = Field(default_factory=list)
    trailer_url: str = ""
    pc_requirements_min: str = ""
    tag_dna: List[TagDNAItem] = Field(default_factory=list)
    verdict: ValueVerdict
    localization: LocalizationInfo
    price_history: PriceHistoryInfo
    developer_intel: StudioIntelligence
    publisher_intel: StudioIntelligence
    developer_other_games: List[GameCard] = Field(default_factory=list)
    publisher_other_games: List[GameCard] = Field(default_factory=list)
    latency_ms: float = 0.0


class SearchResponse(BaseModel):
    query: str
    count: int
    items: List[GameCard]
    latency_ms: float


class CompareResponse(BaseModel):
    game_a: GameXRayReport
    game_b: GameXRayReport
    dna_overlap_pct: float
    shared_tags: List[str]
    shared_Radar_axes: List[str]
    game_a_radar_values: List[float]
    game_b_radar_values: List[float]
    winner_summary: str
