// SteamXRay v2.0 Frontend Controller — Live Telemetry, Studio OSINT (Wikidata/Wikipedia), Localization & Bilingual UI (EN / UA)

let currentAppId = 1643320; // Default: S.T.A.L.K.E.R. 2: Heart of Chornobyl (or Cyberpunk 1091500)
let currentCompareAppId = 1091500;
let currentLang = "uk"; // Start in Ukrainian so the user can immediately inspect both UA and EN
let currentGameReport = null;
let activePortfolioTab = "dev"; // 'dev' or 'pub'
let trendingPresets = [];
let tagDnaChartInstance = null;
let vsRadarChartInstance = null;

const I18N = {
  en: {
    subtitle: "Live Steam Telemetry, Studio Country OSINT, Localization & Price Radar",
    searchPlaceholder: "Search any Steam game (e.g. Stalker 2, Cyberpunk, Witcher 3)...",
    searchBtn: "Search",
    noSearchResults: "No games found matching query.",
    quickXray: "Quick X-Ray:",
    loadingTitle: "Scanning Steam, Wikidata & CheapShark APIs...",
    loadingSub: "Aggregating live players, developer/publisher country OSINT & localization",
    heroDev: "Developer:",
    heroPub: "Publisher:",
    livePlayers: "Live Players Now",
    steamPrice: "Steam UA Price",
    kpiVerdict: "X-Ray Verdict",
    compositeIndex: "/ 100 Index",
    kpiApproval: "Community Rating",
    reviewsWord: "reviews",
    kpiLocalization: "Localization Check",
    langsWord: "langs",
    voiceAudioListPrefix: "Full Audio:",
    textOnlySub: "Supported text languages:",
    kpiPriceHistory: "Price History & Value",
    lowestEver: "All-Time Low (USD)",
    avgPlaytime: "Avg Playtime",
    hrsWord: "hrs",
    ownersWord: "owners",
    studioIntelTitle: "🕵️‍♂️ Developer & Publisher OSINT Intelligence",
    studioIntelSub: "Verified country of origin, headquarters city, founding year, parent organization, and corporate biography.",
    roleDeveloper: "DEVELOPER STUDIO",
    rolePublisher: "PUBLISHER",
    lblCountry: "Country",
    lblHeadquarters: "Headquarters",
    lblFounded: "Founded",
    lblParentOrg: "Parent / Owner",
    lblIndependent: "Independent / Self-Owned",
    originUkrainian: "🇺🇦 Ukrainian Studio",
    originAllied: "🛡️ Verified Country",
    originWarning: "⚠️ RU / BY Origin Warning",
    originUnknown: "🌐 International",
    officialSite: "Official Website ↗",
    wikiArticle: "Wikipedia ↗",
    noBioFallback: "Official Steam registered studio. Corporate metadata verified via Steam Store and Wikidata registries.",
    tabDevGames: "🎮 Developer's Other Games",
    tabPubGames: "🏢 Publisher's Other Games",
    noMoreGames: "No additional standalone titles found on Steam for",
    inspectBtn: "X-Ray →",
    compareCardBtn: "⚔️ VS",
    tagDnaTitle: "Game Tag-DNA Vector Profile",
    tagDnaSub: "Normalized community tag weights from SteamSpy",
    mediaTitle: "Visual Inspection & System Specs",
    vsTitle: "⚔️ Head-to-Head Game Comparison (VS Mode)",
    vsCompareBtn: "Compare",
    dnaOverlap: "DNA Overlap:",
    metricCol: "Metric",
    metricScore: "Overall X-Ray Score",
    metricApproval: "Community Approval",
    metricLive: "Live Players Right Now",
    metricPrice: "Steam Ukraine Price",
    metricAllTimeLow: "Historical Lowest Price",
    metricStudioOrigin: "Developer Country",
    metricUaLoc: "Ukrainian Localization",
    footer: "SteamXRay Analytics v2.0 — Powered by FastAPI, Steam Store API, Wikidata/Wikipedia Studio OSINT, CheapShark & SteamSpy.",
  },
  uk: {
    subtitle: "Жива телеметрія Steam, OSINT-досьє розробників і видавців, локалізація та ціновий радар",
    searchPlaceholder: "Пошук будь-якої гри в Steam (напр. Stalker 2, Cyberpunk, Witcher 3)...",
    searchBtn: "Знайти",
    noSearchResults: "Ігор за цим запитом не знайдено.",
    quickXray: "Швидкий огляд:",
    loadingTitle: "Сканування Steam, Wikidata та CheapShark API...",
    loadingSub: "Збір живого онлайну, країни походження розробника/видавця та локалізації",
    heroDev: "Розробник:",
    heroPub: "Видавець:",
    livePlayers: "Гравців онлайн зараз",
    steamPrice: "Ціна в Steam (UA)",
    kpiVerdict: "Вердикт X-Ray",
    compositeIndex: "/ 100 Індекс",
    kpiApproval: "Рейтинг спільноти",
    reviewsWord: "відгуків",
    kpiLocalization: "Перевірка локалізації",
    langsWord: "мов",
    voiceAudioListPrefix: "Озвучка:",
    textOnlySub: "Підтримка тексту (мов):",
    kpiPriceHistory: "Історія цін та вигода",
    lowestEver: "Історичний мінімум",
    avgPlaytime: "Сер. час гри",
    hrsWord: "год",
    ownersWord: "власників",
    studioIntelTitle: "🕵️‍♂️ OSINT-досьє: Розробник та Видавець",
    studioIntelSub: "Країна походження, штаб-квартира, рік заснування, материнська компанія та довідка з Вікіпедії.",
    roleDeveloper: "СТУДІЯ-РОЗРОБНИК",
    rolePublisher: "ВИДАВЕЦЬ",
    lblCountry: "Країна",
    lblHeadquarters: "Штаб-квартира",
    lblFounded: "Рік заснування",
    lblParentOrg: "Власник / Холдинг",
    lblIndependent: "Незалежна компанія",
    originUkrainian: "🇺🇦 Українська студія",
    originAllied: "🛡️ Перевірена країна",
    originWarning: "⚠️ Увага: сліди РФ / РБ",
    originUnknown: "🌐 Міжнародна",
    officialSite: "Офіційний сайт ↗",
    wikiArticle: "Вікіпедія ↗",
    noBioFallback: "Офіційно зареєстрована в Steam компанія. Метадані перевірено через реєстри Steam та Wikidata.",
    tabDevGames: "🎮 Інші ігри розробника",
    tabPubGames: "🏢 Інші ігри видавця",
    noMoreGames: "Додаткових окремих ігор у Steam не знайдено для",
    inspectBtn: "Огляд →",
    compareCardBtn: "⚔️ VS",
    tagDnaTitle: "Профіль жанрового ДНК гри (Tag-DNA)",
    tagDnaSub: "Нормалізовані ваги користувацьких тегів зі SteamSpy",
    mediaTitle: "Візуальний огляд та системні вимоги",
    vsTitle: "⚔️ Порівняння ігор віч-на-віч (Режим VS)",
    vsCompareBtn: "Порівняти",
    dnaOverlap: "Схожість ДНК:",
    metricCol: "Показник",
    metricScore: "Загальний індекс X-Ray",
    metricApproval: "Схвалення спільноти",
    metricLive: "Гравців онлайн зараз",
    metricPrice: "Ціна в Steam (Україна)",
    metricAllTimeLow: "Історичний мінімум ціни",
    metricStudioOrigin: "Країна розробника",
    metricUaLoc: "Українська локалізація",
    footer: "SteamXRay Analytics v2.0 — Працює на базі FastAPI, Steam Store API, Wikidata/Wikipedia OSINT, CheapShark та SteamSpy.",
  },
};

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || I18N.en[key] || key;
}

document.addEventListener("DOMContentLoaded", async () => {
  applyStaticTranslations();
  setupSearchEvents();
  await loadTrendingBar();
  await loadGameXRay(currentAppId);
  await runComparison(currentAppId, currentCompareAppId, false);
});

window.setLanguage = async function (lang) {
  if (lang !== "en" && lang !== "uk") return;
  currentLang = lang;
  applyStaticTranslations();
  await loadGameXRay(currentAppId, false);
  const vsSelect = document.getElementById("vsSelectGameB");
  const secondId = (vsSelect && parseInt(vsSelect.value, 10)) || currentCompareAppId;
  await runComparison(currentAppId, secondId, false);
};

function applyStaticTranslations() {
  const enBtn = document.getElementById("langEnBtn");
  const ukBtn = document.getElementById("langUkBtn");
  if (currentLang === "en") {
    enBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold transition bg-sky-500 text-slate-950";
    ukBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold transition text-slate-400 hover:text-white";
  } else {
    ukBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold transition bg-sky-500 text-slate-950";
    enBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold transition text-slate-400 hover:text-white";
  }

  document.getElementById("uiSubtitle").textContent = t("subtitle");
  document.getElementById("searchInput").placeholder = t("searchPlaceholder");
  document.getElementById("searchBtn").textContent = t("searchBtn");
  document.getElementById("lblQuickXray").textContent = t("quickXray");
  document.getElementById("lblLoadingTitle").textContent = t("loadingTitle");
  document.getElementById("lblLoadingSub").textContent = t("loadingSub");
  document.getElementById("lblHeroDev").textContent = t("heroDev");
  document.getElementById("lblHeroPub").textContent = t("heroPub");
  document.getElementById("lblLivePlayers").textContent = t("livePlayers");
  document.getElementById("lblSteamPrice").textContent = t("steamPrice");
  document.getElementById("lblKpiVerdict").textContent = t("kpiVerdict");
  document.getElementById("lblCompositeIndex").textContent = t("compositeIndex");
  document.getElementById("lblKpiApproval").textContent = t("kpiApproval");
  document.getElementById("lblKpiLocalization").textContent = t("kpiLocalization");
  document.getElementById("lblKpiPriceHistory").textContent = t("kpiPriceHistory");
  document.getElementById("lblLowestEver").textContent = t("lowestEver");
  document.getElementById("lblAvgPlaytime").textContent = t("avgPlaytime");
  document.getElementById("lblStudioIntelTitle").textContent = t("studioIntelTitle");
  document.getElementById("lblStudioIntelSub").textContent = t("studioIntelSub");
  document.getElementById("tabDevGamesBtn").textContent = t("tabDevGames");
  document.getElementById("tabPubGamesBtn").textContent = t("tabPubGames");
  document.getElementById("lblTagDnaTitle").textContent = t("tagDnaTitle");
  document.getElementById("lblTagDnaSub").textContent = t("tagDnaSub");
  document.getElementById("lblMediaTitle").textContent = t("mediaTitle");
  document.getElementById("lblVsTitle").textContent = t("vsTitle");
  document.getElementById("runCompareBtn").textContent = t("vsCompareBtn");
  document.getElementById("uiFooter").textContent = t("footer");
}

function showLoading(show) {
  const el = document.getElementById("loadingIndicator");
  if (!el) return;
  if (show) el.classList.remove("hidden");
  else el.classList.add("hidden");
}

async function loadTrendingBar() {
  try {
    const resp = await fetch("/api/v1/trending");
    trendingPresets = await resp.json();
    const bar = document.getElementById("trendingBar");
    const vsSelect = document.getElementById("vsSelectGameB");
    bar.innerHTML = "";
    vsSelect.innerHTML = "";

    trendingPresets.forEach((game, idx) => {
      const btn = document.createElement("button");
      btn.className =
        "px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-900 hover:bg-sky-500/20 text-slate-300 hover:text-sky-300 border border-slate-800 hover:border-sky-500/40 shrink-0 transition";
      btn.textContent = game.name;
      btn.onclick = () => loadGameXRay(game.appid);
      bar.appendChild(btn);

      const opt = document.createElement("option");
      opt.value = game.appid;
      opt.textContent = `${game.name} (${game.price_formatted})`;
      if (idx === 1) opt.selected = true;
      vsSelect.appendChild(opt);
    });

    document.getElementById("runCompareBtn").onclick = () => {
      const secondId = parseInt(vsSelect.value, 10);
      if (secondId) {
        currentCompareAppId = secondId;
        runComparison(currentAppId, secondId, true);
      }
    };
  } catch (err) {
    console.error("Failed to load trending presets:", err);
  }
}

function setupSearchEvents() {
  const input = document.getElementById("searchInput");
  const btn = document.getElementById("searchBtn");
  const dropdown = document.getElementById("searchDropdown");
  let debounceTimer = null;

  const triggerAutocomplete = async () => {
    const q = input.value.trim();
    if (q.length < 2) {
      dropdown.classList.add("hidden");
      return;
    }
    try {
      const resp = await fetch(`/api/v1/search?q=${encodeURIComponent(q)}&limit=8&lang=${currentLang}`);
      const data = await resp.json();
      renderSearchDropdown(data.items || []);
    } catch (err) {
      console.error("Autocomplete failed:", err);
    }
  };

  // Explicit search (Enter or Search button click): runs search, selects top match (or shows dropdown), and clears the search input!
  const executeExplicitSearch = async () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q) return;
    // Immediately clear the search bar as requested by user
    input.value = "";
    try {
      const resp = await fetch(`/api/v1/search?q=${encodeURIComponent(q)}&limit=8&lang=${currentLang}`);
      const data = await resp.json();
      const items = data.items || [];
      if (items.length > 0) {
        dropdown.classList.add("hidden");
        await loadGameXRay(items[0].appid);
      } else {
        renderSearchDropdown([]);
      }
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(triggerAutocomplete, 260);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      executeExplicitSearch();
    }
  });

  btn.addEventListener("click", (e) => {
    e.preventDefault();
    executeExplicitSearch();
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target) && !btn.contains(e.target)) {
      dropdown.classList.add("hidden");
    }
  });
}

function renderSearchDropdown(items) {
  const dropdown = document.getElementById("searchDropdown");
  if (!items.length) {
    dropdown.innerHTML = `<div class="p-3 text-xs text-slate-400">${t("noSearchResults")}</div>`;
    dropdown.classList.remove("hidden");
    return;
  }

  dropdown.innerHTML = items
    .map(
      (item) => `
    <div
      onclick="selectSearchResult(${item.appid})"
      class="flex items-center justify-between gap-3 p-2.5 hover:bg-slate-800/90 cursor-pointer border-b border-slate-800/60 last:border-none transition"
    >
      <div class="flex items-center gap-3 min-w-0">
        <img src="${item.header_image}" alt="" class="w-16 h-9 object-cover rounded border border-slate-700 shrink-0" />
        <div class="truncate">
          <div class="text-xs font-bold text-white truncate">${item.name}</div>
          <div class="text-[10px] text-slate-400 mono">AppID: ${item.appid}</div>
        </div>
      </div>
      <div class="text-xs font-bold text-sky-300 mono shrink-0">${item.price_formatted}</div>
    </div>
  `
    )
    .join("");
  dropdown.classList.remove("hidden");
}

window.selectSearchResult = async function (appid) {
  const input = document.getElementById("searchInput");
  if (input) input.value = ""; // Always clear search input when selecting a game
  document.getElementById("searchDropdown").classList.add("hidden");
  await loadGameXRay(appid);
};

window.loadGameXRay = async function (appid, scrollTop = true) {
  const input = document.getElementById("searchInput");
  if (input) input.value = ""; // Ensure search input is clean whenever a new game loads
  showLoading(true);
  try {
    const resp = await fetch(`/api/v1/game/${appid}/xray?lang=${currentLang}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    currentAppId = data.appid;
    currentGameReport = data;
    renderGameXRay(data);
    if (scrollTop) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  } catch (err) {
    console.error("Failed to load X-Ray report:", err);
  } finally {
    showLoading(false);
  }
};

function renderGameXRay(r) {
  document.getElementById("latencyBadge").innerHTML = `API: <span class="text-emerald-400 font-semibold">${r.latency_ms} ms</span>`;

  // Hero section
  const bgUrl = r.background_image || r.header_image;
  document.getElementById("heroBg").style.backgroundImage = `url('${bgUrl}')`;
  document.getElementById("gameHeaderImg").src = r.header_image;
  document.getElementById("gameAppIdBadge").textContent = `AppID: ${r.appid}`;
  document.getElementById("gameReleaseDate").textContent = r.release_date;
  document.getElementById("gameTitle").textContent = r.name;
  document.getElementById("gameShortDesc").textContent = r.short_description || "";

  // Hero Studio Origin Pills
  const devIntel = r.developer_intel || {};
  const pubIntel = r.publisher_intel || {};
  document.getElementById("heroDevFlag").textContent = devIntel.country_code || "🌐";
  document.getElementById("gameDevelopers").textContent = (r.developers || []).join(", ");
  document.getElementById("heroDevCountry").textContent = devIntel.country ? `(${devIntel.country})` : "";

  document.getElementById("heroPubFlag").textContent = pubIntel.country_code || "🌐";
  document.getElementById("gamePublishers").textContent = (r.publishers || []).join(", ");
  document.getElementById("heroPubCountry").textContent = pubIntel.country ? `(${pubIntel.country})` : "";

  document.getElementById("genreBadges").innerHTML = (r.genres || [])
    .slice(0, 4)
    .map(
      (g) =>
        `<span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 border border-sky-500/30">${g}</span>`
    )
    .join("");

  document.getElementById("livePlayersCount").textContent = (r.live_players || 0).toLocaleString();
  document.getElementById("gamePrice").textContent = r.price_formatted;
  const discBadge = document.getElementById("gameDiscountBadge");
  if (r.discount_percent > 0) {
    discBadge.textContent = `-${r.discount_percent}%`;
    discBadge.classList.remove("hidden");
  } else {
    discBadge.classList.add("hidden");
  }
  document.getElementById("steamStoreLink").href = `https://store.steampowered.com/app/${r.appid}/`;

  // KPI 1: Verdict
  const vBadge = document.getElementById("verdictBadge");
  vBadge.textContent = r.verdict.verdict_label;
  const colorMap = {
    emerald: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    cyan: "bg-sky-500/20 text-sky-300 border-sky-500/30",
    amber: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    rose: "bg-rose-500/20 text-rose-300 border-rose-500/30",
  };
  vBadge.className = `text-[11px] font-bold px-2.5 py-0.5 rounded-full border truncate ${colorMap[r.verdict.verdict_color] || colorMap.cyan}`;
  document.getElementById("overallScoreVal").textContent = r.verdict.overall_score;
  document.getElementById("verdictReason").textContent = r.verdict.summary_reason;

  // KPI 2: Approval
  document.getElementById("wilsonBadge").textContent = `Wilson: ${r.verdict.wilson_score_pct}%`;
  document.getElementById("approvalPctVal").textContent = `${r.verdict.approval_pct}%`;
  document.getElementById("totalReviewsVal").textContent = `(${r.total_reviews.toLocaleString()} ${t("reviewsWord")})`;
  document.getElementById("approvalBar").style.width = `${r.verdict.approval_pct}%`;
  document.getElementById("posReviewsVal").textContent = `+${r.positive_reviews.toLocaleString()}`;
  document.getElementById("negReviewsVal").textContent = `-${r.negative_reviews.toLocaleString()}`;

  // KPI 3: Ukrainian Localization Check
  const loc = r.localization || {};
  document.getElementById("totalLangsBadge").textContent = `${loc.total_languages_count || 0} ${t("langsWord")}`;
  const uaBox = document.getElementById("uaStatusBox");
  const uaIcon = document.getElementById("uaStatusIcon");
  const uaLbl = document.getElementById("uaStatusLabel");
  const uaSub = document.getElementById("uaAudioSub");

  if (loc.has_ukrainian_audio) {
    uaBox.className = "p-2.5 rounded-lg border bg-emerald-950/40 border-emerald-500/40 flex items-center gap-2.5";
    uaIcon.textContent = "🇺🇦🎙️";
    uaLbl.className = "text-xs font-extrabold text-emerald-300 leading-snug";
  } else if (loc.has_ukrainian_text) {
    uaBox.className = "p-2.5 rounded-lg border bg-sky-950/40 border-sky-500/40 flex items-center gap-2.5";
    uaIcon.textContent = "🇺🇦";
    uaLbl.className = "text-xs font-bold text-sky-300 leading-snug";
  } else {
    uaBox.className = "p-2.5 rounded-lg border bg-slate-900 border-slate-800 flex items-center gap-2.5";
    uaIcon.textContent = "🌐";
    uaLbl.className = "text-xs font-semibold text-slate-400 leading-snug";
  }
  uaLbl.textContent = loc.ukrainian_status_label || "N/A";
  const audioCount = (loc.full_audio_languages || []).length;
  uaSub.textContent =
    audioCount > 0
      ? `${t("voiceAudioListPrefix")} ${(loc.full_audio_languages || []).slice(0, 4).join(", ")}`
      : `${t("textOnlySub")} ${loc.total_languages_count || 0}`;
  document.getElementById("audioLangsList").textContent = (loc.text_only_languages || []).length
    ? `${(loc.text_only_languages || []).slice(0, 6).join(", ")}`
    : "";

  // KPI 4: Price History (CheapShark) & Playtime Value
  const ph = r.price_history || {};
  document.getElementById("costPerHourBadge").textContent = r.verdict.cost_per_hour_uah
    ? `~${r.verdict.cost_per_hour_uah}₴ / ${t("hrsWord")}`
    : r.is_free
    ? `0₴ / ${t("hrsWord")}`
    : "Steam UA";

  if (r.is_free) {
    document.getElementById("cheapestEverVal").textContent = "Free";
    document.getElementById("cheapestDateVal").textContent = "Always Free";
  } else if (ph.cheapest_ever_usd !== null && ph.cheapest_ever_usd !== undefined) {
    const maxDiscStr = ph.historical_max_discount_est_pct > 0 ? ` (-${ph.historical_max_discount_est_pct}%)` : "";
    document.getElementById("cheapestEverVal").textContent = `$${ph.cheapest_ever_usd.toFixed(2)}${maxDiscStr}`;
    document.getElementById("cheapestDateVal").textContent = ph.cheapest_ever_date || "CheapShark";
  } else {
    document.getElementById("cheapestEverVal").textContent = r.price_formatted;
    document.getElementById("cheapestDateVal").textContent = "Steam Store";
  }

  document.getElementById("avgPlaytimeVal").textContent = `${r.average_playtime_hours} ${t("hrsWord")}`;
  document.getElementById("ownersShortVal").textContent = `${r.owners_range}`;

  // Developer & Publisher OSINT Dossier Cards
  renderStudioIntelCard("devIntelCard", r.developer_intel, t("roleDeveloper"), "sky");
  renderStudioIntelCard("pubIntelCard", r.publisher_intel, t("rolePublisher"), "indigo");

  // Company Other Games Portfolio
  renderPortfolioSection();

  // Metacritic & System Specs
  document.getElementById("metacriticBadge").textContent = r.metacritic_score
    ? `Metacritic: ${r.metacritic_score}`
    : "Metacritic: N/A";
  document.getElementById("pcReqsVal").textContent =
    r.pc_requirements_min || "Standard 64-bit Windows PC configuration.";

  // Tag DNA Chart & Screenshots
  renderTagDnaChart(r.tag_dna || []);
  renderScreenshots(r.screenshots || [], r.header_image);
}

function renderStudioIntelCard(containerId, intel, roleLabel, accentColor) {
  const el = document.getElementById(containerId);
  if (!el || !intel) return;

  let originBadgeHtml = "";
  if (intel.origin_status === "ukrainian") {
    originBadgeHtml = `<span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/40">${t("originUkrainian")}</span>`;
  } else if (intel.origin_status === "warning") {
    originBadgeHtml = `<span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-500/25 text-rose-300 border border-rose-500/50">${t("originWarning")}</span>`;
  } else if (intel.origin_status === "allied") {
    originBadgeHtml = `<span class="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">${t("originAllied")}</span>`;
  } else {
    originBadgeHtml = `<span class="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">${t("originUnknown")}</span>`;
  }

  const wikidataBadge = intel.wikidata_id
    ? `<a href="https://www.wikidata.org/wiki/${intel.wikidata_id}" target="_blank" class="text-[10px] mono px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">Wikidata: ${intel.wikidata_id} ↗</a>`
    : "";

  const parentText = intel.parent_company || t("lblIndependent");
  const bioText = intel.wikipedia_extract || intel.description || t("noBioFallback");

  const webBtn = intel.official_website
    ? `<a href="${intel.official_website}" target="_blank" class="text-xs font-semibold text-${accentColor}-400 hover:text-${accentColor}-300 transition">${t("officialSite")}</a>`
    : `<span class="text-xs text-slate-500">Steam Verified</span>`;

  const wikiBtn = intel.wikipedia_url
    ? `<a href="${intel.wikipedia_url}" target="_blank" class="text-xs font-semibold text-slate-300 hover:text-white px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 transition">${t("wikiArticle")}</a>`
    : "";

  el.innerHTML = `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded bg-${accentColor}-500/20 text-${accentColor}-300 border border-${accentColor}-500/30">
            ${roleLabel}
          </span>
          ${wikidataBadge}
        </div>
        ${originBadgeHtml}
      </div>

      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-2xl shrink-0">
          ${intel.country_code || "🌐"}
        </div>
        <div class="min-w-0">
          <h4 class="text-lg font-extrabold text-white truncate" title="${intel.name}">${intel.name}</h4>
          <p class="text-xs text-slate-400 truncate">${intel.description || roleLabel}</p>
        </div>
      </div>

      <!-- 4 Metadata Cells: Country, HQ, Founded, Parent Org -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
        <div class="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800/90">
          <div class="text-[10px] text-slate-400 uppercase">${t("lblCountry")}</div>
          <div class="font-bold text-white truncate mt-0.5" title="${intel.country}">${intel.country_code} ${intel.country}</div>
        </div>
        <div class="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800/90">
          <div class="text-[10px] text-slate-400 uppercase">${t("lblHeadquarters")}</div>
          <div class="font-bold text-slate-200 truncate mt-0.5" title="${intel.headquarters}">${intel.headquarters}</div>
        </div>
        <div class="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800/90">
          <div class="text-[10px] text-slate-400 uppercase">${t("lblFounded")}</div>
          <div class="font-bold text-sky-300 mono truncate mt-0.5">${intel.founded_year}</div>
        </div>
        <div class="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800/90">
          <div class="text-[10px] text-slate-400 uppercase">${t("lblParentOrg")}</div>
          <div class="font-semibold text-slate-200 truncate mt-0.5" title="${parentText}">${parentText}</div>
        </div>
      </div>

      <p class="text-xs text-slate-300 leading-relaxed line-clamp-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/70">
        ${bioText}
      </p>
    </div>

    <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
      ${webBtn}
      ${wikiBtn}
    </div>
  `;
}

window.switchPortfolioTab = function (tab) {
  activePortfolioTab = tab;
  renderPortfolioSection();
};

function renderPortfolioSection() {
  if (!currentGameReport) return;
  const devBtn = document.getElementById("tabDevGamesBtn");
  const pubBtn = document.getElementById("tabPubGamesBtn");
  const studioLabel = document.getElementById("portfolioStudioName");
  const grid = document.getElementById("companyGamesGrid");

  const isDev = activePortfolioTab === "dev";
  if (isDev) {
    devBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-sky-500 text-slate-950";
    pubBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-slate-300 hover:text-white border border-slate-800";
  } else {
    pubBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-indigo-500 text-white";
    devBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-slate-300 hover:text-white border border-slate-800";
  }

  const studioName = isDev
    ? (currentGameReport.developer_intel && currentGameReport.developer_intel.name) || "Developer"
    : (currentGameReport.publisher_intel && currentGameReport.publisher_intel.name) || "Publisher";
  const gamesList = isDev
    ? currentGameReport.developer_other_games || []
    : currentGameReport.publisher_other_games || [];

  studioLabel.textContent = `${studioName} (${gamesList.length})`;

  if (!gamesList.length) {
    grid.innerHTML = `<div class="text-xs text-slate-400 col-span-6 py-2">${t("noMoreGames")} <span class="text-white font-semibold">${studioName}</span>.</div>`;
    return;
  }

  grid.innerHTML = gamesList
    .map(
      (g) => `
    <div class="glass-card rounded-xl overflow-hidden flex flex-col justify-between">
      <div onclick="loadGameXRay(${g.appid})" class="cursor-pointer">
        <img src="${g.header_image}" alt="${g.name}" class="w-full h-24 object-cover" />
        <div class="p-2.5">
          <div class="text-xs font-bold text-white truncate hover:text-sky-400 transition" title="${g.name}">${g.name}</div>
          <div class="flex items-center justify-between mt-1">
            <span class="text-[10px] text-slate-400 mono">#${g.appid}</span>
            <span class="text-[11px] font-semibold text-sky-300 mono">${g.price_formatted}</span>
          </div>
        </div>
      </div>
      <div class="px-2.5 py-1.5 bg-slate-950/70 border-t border-slate-800/80 flex items-center justify-between">
        <button onclick="loadGameXRay(${g.appid})" class="text-[11px] font-semibold text-sky-400 hover:text-sky-300">
          ${t("inspectBtn")}
        </button>
        <button onclick="runComparison(${currentAppId}, ${g.appid}, true)" class="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30">
          ${t("compareCardBtn")}
        </button>
      </div>
    </div>
  `
    )
    .join("");
}

function renderTagDnaChart(tagDna) {
  const ctx = document.getElementById("tagDnaChart").getContext("2d");
  if (tagDnaChartInstance) tagDnaChartInstance.destroy();

  const labels = tagDna.map((tItem) => tItem.tag);
  const weights = tagDna.map((tItem) => tItem.weight_pct);
  const votes = tagDna.map((tItem) => tItem.votes);

  tagDnaChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "DNA Weight (%)",
          data: weights,
          backgroundColor: "rgba(56, 189, 248, 0.72)",
          borderColor: "rgba(56, 189, 248, 1)",
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const i = context.dataIndex;
              return ` ${weights[i]}% (${votes[i].toLocaleString()} votes)`;
            },
          },
        },
      },
      scales: {
        x: {
          max: 100,
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94a3b8", callback: (v) => v + "%" },
        },
        y: {
          grid: { display: false },
          ticks: { color: "#f1f5f9", font: { weight: "600", size: 11 } },
        },
      },
    },
  });
}

function renderScreenshots(screenshots, fallbackImg) {
  const mainImg = document.getElementById("activeScreenshot");
  const thumbs = document.getElementById("screenshotThumbs");
  const list = screenshots.length ? screenshots.slice(0, 5) : [fallbackImg];
  mainImg.src = list[0];

  thumbs.innerHTML = list
    .map(
      (url, i) => `
    <img
      src="${url}"
      onclick="document.getElementById('activeScreenshot').src='${url}'"
      class="h-12 w-full object-cover rounded-lg border ${
        i === 0 ? "border-sky-400" : "border-slate-800"
      } hover:border-sky-400 cursor-pointer transition"
    />
  `
    )
    .join("");
}

window.runComparison = async function (appidA, appidB, scrollIntoView = true) {
  try {
    currentCompareAppId = appidB;
    const resp = await fetch(`/api/v1/compare?appid_a=${appidA}&appid_b=${appidB}&lang=${currentLang}`);
    if (!resp.ok) return;
    const cmp = await resp.json();
    renderComparisonSection(cmp);
    if (scrollIntoView) {
      document.getElementById("compareSection").scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  } catch (err) {
    console.error("Comparison failed:", err);
  }
};

function renderComparisonSection(cmp) {
  const a = cmp.game_a;
  const b = cmp.game_b;

  document.getElementById("vsOverlapBadge").textContent = `${t("dnaOverlap")} ${cmp.dna_overlap_pct}%`;
  document.getElementById("vsWinnerSummary").textContent = cmp.winner_summary;

  const lowA =
    a.price_history && a.price_history.cheapest_ever_usd != null
      ? `$${a.price_history.cheapest_ever_usd.toFixed(2)}`
      : a.price_formatted;
  const lowB =
    b.price_history && b.price_history.cheapest_ever_usd != null
      ? `$${b.price_history.cheapest_ever_usd.toFixed(2)}`
      : b.price_formatted;

  document.getElementById("vsTableContainer").innerHTML = `
    <table class="w-full text-left border-collapse text-xs">
      <thead>
        <tr class="border-b border-slate-800 text-slate-400 uppercase">
          <th class="py-2.5 px-3">${t("metricCol")}</th>
          <th class="py-2.5 px-3 text-sky-400 font-bold">${a.name}</th>
          <th class="py-2.5 px-3 text-indigo-400 font-bold">${b.name}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800/70 mono">
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricScore")}</td>
          <td class="py-2.5 px-3 font-bold text-white">${a.verdict.overall_score} / 100</td>
          <td class="py-2.5 px-3 font-bold text-white">${b.verdict.overall_score} / 100</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricApproval")}</td>
          <td class="py-2.5 px-3 text-emerald-400 font-bold">${a.verdict.approval_pct}%</td>
          <td class="py-2.5 px-3 text-emerald-400 font-bold">${b.verdict.approval_pct}%</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricLive")}</td>
          <td class="py-2.5 px-3 text-white font-semibold">${a.live_players.toLocaleString()}</td>
          <td class="py-2.5 px-3 text-white font-semibold">${b.live_players.toLocaleString()}</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricPrice")}</td>
          <td class="py-2.5 px-3 text-sky-300">${a.price_formatted}</td>
          <td class="py-2.5 px-3 text-indigo-300">${b.price_formatted}</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricAllTimeLow")}</td>
          <td class="py-2.5 px-3 text-emerald-300">${lowA}</td>
          <td class="py-2.5 px-3 text-emerald-300">${lowB}</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricStudioOrigin")}</td>
          <td class="py-2.5 px-3 font-sans text-slate-200">${a.developer_intel.country_code} ${a.developer_intel.name} (${a.developer_intel.country})</td>
          <td class="py-2.5 px-3 font-sans text-slate-200">${b.developer_intel.country_code} ${b.developer_intel.name} (${b.developer_intel.country})</td>
        </tr>
        <tr>
          <td class="py-2.5 px-3 font-sans text-slate-300">${t("metricUaLoc")}</td>
          <td class="py-2.5 px-3 font-sans text-slate-200">${a.localization.ukrainian_status_label}</td>
          <td class="py-2.5 px-3 font-sans text-slate-200">${b.localization.ukrainian_status_label}</td>
        </tr>
      </tbody>
    </table>
  `;

  const ctx = document.getElementById("vsRadarChart").getContext("2d");
  if (vsRadarChartInstance) vsRadarChartInstance.destroy();

  vsRadarChartInstance = new Chart(ctx, {
    type: "radar",
    data: {
      labels: cmp.shared_Radar_axes,
      datasets: [
        {
          label: a.name,
          data: cmp.game_a_radar_values,
          backgroundColor: "rgba(56, 189, 248, 0.22)",
          borderColor: "rgba(56, 189, 248, 1)",
          pointBackgroundColor: "#38bdf8",
          borderWidth: 2,
        },
        {
          label: b.name,
          data: cmp.game_b_radar_values,
          backgroundColor: "rgba(129, 140, 248, 0.22)",
          borderColor: "rgba(129, 140, 248, 1)",
          pointBackgroundColor: "#818cf8",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          angleLines: { color: "rgba(148, 163, 184, 0.15)" },
          grid: { color: "rgba(148, 163, 184, 0.15)" },
          pointLabels: { color: "#cbd5e1", font: { size: 10, weight: "600" } },
          ticks: { display: false },
        },
      },
      plugins: {
        legend: {
          labels: { color: "#f8fafc", font: { size: 11, weight: "bold" } },
        },
      },
    },
  });
}
