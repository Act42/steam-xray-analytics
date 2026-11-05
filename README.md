# SteamXRay v2.0 — Live Game & Studio OSINT Intelligence Dashboard

Full-stack **FastAPI + Async httpx** web application and REST API that aggregates real-time data from **5 live public APIs** without requiring paid API keys:

1. **Steam Storefront API (`cc=UA`, `l=ukrainian | english`)** — Live Ukrainian regional pricing (`₴`), active discounts, localized descriptions, release dates, Metacritic scores, screenshots, and system requirements.
2. **Steam UserStats API (`ISteamUserStats/GetNumberOfCurrentPlayers/v1`)** — Real-time concurrent players in-game right now.
3. **Wikidata & Wikipedia REST OSINT APIs** — Live corporate intelligence for both the **Developer** and **Publisher**:
   - **Country of Origin** with flag & origin status verification (`🇺🇦 Українська студія`, `🛡️ Перевірена країна`, or `⚠️ Увага: сліди РФ / РБ`),
   - **Headquarters City** (`P159`),
   - **Founding Year** (`P571`),
   - **Parent Company / Owner** (`P749` / `P127`),
   - **Official Website** (`P856`) and **Wikipedia Biography** (`uk.wikipedia.org` / `en.wikipedia.org`).
4. **Steam Localization Parser & Company Portfolio Search** — Automatically parses Steam's `supported_languages` matrix to detect **Full Ukrainian (Text + Audio)** vs **Ukrainian Text/Subtitles**, and fetches separate portfolios of **other games by the Developer** and **other games by the Publisher**.
5. **CheapShark Price History API & SteamSpy Tag-DNA** — Tracks the **Historical Lowest Price Ever (`$`)**, maximum historical discount, community review counts, Wilson confidence lower bound, and Tag-DNA vectors.

---

## Key Features in v2.0

- **Bilingual Interface (`🇺🇦 UA` / `EN`)**: Instant language toggle in the header that translates the entire interface and switches live API queries (`Steam` + `Wikidata` + `Wikipedia`) between Ukrainian and English without layout distortion.
- **Developer & Publisher OSINT Dossier**: Side-by-side corporate intelligence cards for both the development studio and publisher, plus switchable tabs for **Developer's Other Games** and **Publisher's Other Games**.
- **Ukrainian Localization & Audio Matrix**: Instant check for Ukrainian text and full Ukrainian voice acting (`🇺🇦🎙️`).
- **All-Time Lowest Price Radar**: Compares current Steam price against the historical lowest price recorded by CheapShark.
- **Auto-Clearing Search Bar**: Searching or selecting any game automatically clears the search input (`#searchInput`).
- **Head-to-Head VS Mode**: Side-by-side comparison table and dual 6-axis Radar chart.

---

## Quick Start

```powershell
py -3.11 -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Web Dashboard**: `http://localhost:8000`
- **Swagger OpenAPI Docs**: `http://localhost:8000/docs`

## Running Tests

```powershell
py -3.11 -m pytest -v
```
