const state = {
  bootstrap: null,
  scheduler: null,
  manualSearchRunning: false,
};

const FIXED_BOARD_ROUTE_COUNT = 10;

/** 英文城市名（IATA → city），用于内部与回退展示 */
const AIRPORT_CITIES_EN = {
  YVR: "Vancouver",
  YXX: "Abbotsford",
  YYF: "Penticton",
  YYC: "Calgary",
  YYJ: "Victoria",
  YLW: "Kelowna",
  YEG: "Edmonton",
  YWG: "Winnipeg",
  YUL: "Montreal",
  YOW: "Ottawa",
  YYZ: "Toronto",
  YHZ: "Halifax",
  YXE: "Saskatoon",
  YQR: "Regina",
  YQM: "Moncton",
  YQB: "Quebec City",
  YYT: "St. John's",
  YTZ: "Toronto (Billy Bishop)",
  YHM: "Hamilton",
  YKF: "Kitchener",
  YCD: "Nanaimo",
  YXS: "Prince George",
  YXT: "Terrace",
  YPR: "Prince Rupert",
  YDF: "Deer Lake",
  YQX: "Gander",
  YFC: "Fredericton",
  YQY: "Sydney NS",
  YAM: "Sault Ste. Marie",
  YTS: "Timmins",
  YXU: "London ON",
  YMM: "Fort McMurray",
  YVO: "Val-d'Or",
  YZV: "Sept-Îles",
  YWK: "Wabush",
  YYG: "Charlottetown",
  YXY: "Whitehorse",
  YQQ: "Comox",
  BLI: "Bellingham",
  LAS: "Las Vegas",
  LAX: "Los Angeles",
  PDX: "Portland",
  SEA: "Seattle",
  SFO: "San Francisco",
  SJC: "San Jose",
  OAK: "Oakland",
  SAN: "San Diego",
  SMF: "Sacramento",
  PHX: "Phoenix",
  DEN: "Denver",
  SLC: "Salt Lake City",
  ORD: "Chicago",
  MDW: "Chicago Midway",
  BOS: "Boston",
  EWR: "Newark",
  JFK: "New York JFK",
  LGA: "New York LGA",
  IAD: "Washington Dulles",
  DCA: "Washington Reagan",
  BWI: "Baltimore",
  IAH: "Houston",
  HOU: "Houston Hobby",
  DFW: "Dallas",
  ATL: "Atlanta",
  MCO: "Orlando",
  TPA: "Tampa",
  FLL: "Fort Lauderdale",
  MIA: "Miami",
  MSP: "Minneapolis",
  DTW: "Detroit",
  CLT: "Charlotte",
  BNA: "Nashville",
  AUS: "Austin",
  MSY: "New Orleans",
  STL: "St. Louis",
  ANC: "Anchorage",
  HNL: "Honolulu",
};

/** 中文城市名，卡片上与 IATA 并列展示 */
const AIRPORT_CITIES_ZH = {
  YVR: "温哥华",
  YXX: "阿博茨福德",
  YYF: "彭蒂克顿",
  YYC: "卡尔加里",
  YYJ: "维多利亚",
  YLW: "基洛纳",
  YEG: "埃德蒙顿",
  YWG: "温尼伯",
  YUL: "蒙特利尔",
  YOW: "渥太华",
  YYZ: "多伦多",
  YHZ: "哈利法克斯",
  YXE: "萨斯卡通",
  YQR: "里贾纳",
  YQM: "蒙克顿",
  YQB: "魁北克城",
  YYT: "圣约翰斯",
  YTZ: "多伦多岛",
  YHM: "汉密尔顿",
  YKF: "基奇纳",
  YCD: "纳奈莫",
  YXS: "乔治王子城",
  YXT: "特勒斯",
  YPR: "鲁珀特王子港",
  YDF: "迪尔莱克",
  YQX: "甘德",
  YFC: "弗雷德里克顿",
  YQY: "悉尼（加）",
  YAM: "苏圣玛丽",
  YTS: "蒂明斯",
  YXU: "伦敦（加）",
  YMM: "麦克默里堡",
  YVO: "瓦多尔",
  YZV: "七岛港",
  YWK: "沃布什",
  YYG: "夏洛特敦",
  YXY: "怀特霍斯",
  YQQ: "科莫克斯",
  BLI: "贝灵厄姆",
  LAS: "拉斯维加斯",
  LAX: "洛杉矶",
  PDX: "波特兰",
  SEA: "西雅图",
  SFO: "旧金山",
  SJC: "圣何塞",
  OAK: "奥克兰",
  SAN: "圣迭戈",
  SMF: "萨克拉门托",
  PHX: "菲尼克斯",
  DEN: "丹佛",
  SLC: "盐湖城",
  ORD: "芝加哥",
  MDW: "芝加哥中途",
  BOS: "波士顿",
  EWR: "纽瓦克",
  JFK: "纽约 JFK",
  LGA: "纽约拉瓜迪亚",
  IAD: "华盛顿杜勒斯",
  DCA: "华盛顿里根",
  BWI: "巴尔的摩",
  IAH: "休斯敦",
  HOU: "休斯敦 Hobby",
  DFW: "达拉斯",
  ATL: "亚特兰大",
  MCO: "奥兰多",
  TPA: "坦帕",
  FLL: "劳德代尔堡",
  MIA: "迈阿密",
  MSP: "明尼阿波利斯",
  DTW: "底特律",
  CLT: "夏洛特",
  BNA: "纳什维尔",
  AUS: "奥斯汀",
  MSY: "新奥尔良",
  STL: "圣路易斯",
  ANC: "安克雷奇",
  HNL: "檀香山",
};

/** 检索/OTA 常用 metro 码 → 主 IATA，便于生成 Kayak/Google深链 */
const IATA_ALIASES = {
  YTO: "YYZ",
  YTOA: "YYZ",
  YMQ: "YUL",
  YMQA: "YUL",
  YVRA: "YVR",
  YLWA: "YLW",
  LASA: "LAS",
  YOWA: "YOW",
  YBAA: "YYC",
  PHXB: "PHX",
  SFOB: "SFO",
};

function isValidIata(code) {
  return /^[A-Z]{3}$/.test(String(code || "").trim().toUpperCase());
}

function canonicalIata(code) {
  const u = String(code || "").trim().toUpperCase();
  if (!isValidIata(u)) return u;
  return IATA_ALIASES[u] || u;
}

/** 从 route 字段解析 YVR -> YYC */
function parseRouteAirports(route) {
  if (!route) return null;
  const m = String(route).match(/([A-Z]{3})\s*[-–>→]\s*([A-Z]{3})/i);
  if (!m) return null;
  return { origin: m[1].toUpperCase(), dest: m[2].toUpperCase() };
}

/** 从字段里抠出 IATA 三字码；纯数字等非机场代码返回空串，交给 route 解析 */
function normalizeAirportToken(raw) {
  if (raw == null || raw === "") return "";
  const s = String(raw).trim().toUpperCase();
  const m = s.match(/\b([A-Z]{3})\b/);
  if (m) return m[1];
  if (s.length === 3 && /^[A-Z]{3}$/.test(s)) return s;
  return "";
}

function resolveFindingAirports(finding) {
  let o = normalizeAirportToken(finding.origin_airport);
  let d = normalizeAirportToken(finding.destination_airport);
  const parsed = parseRouteAirports(finding.route || "");
  if (parsed) {
    if (!isValidIata(o)) o = parsed.origin;
    if (!isValidIata(d)) d = parsed.dest;
  }
  return { origin: o, dest: d };
}

function extractIsoDates(...parts) {
  const re = /\b(\d{4}-\d{2}-\d{2})\b/g;
  const out = [];
  for (const p of parts) {
    if (!p) continue;
    let m;
    const s = String(p);
    while ((m = re.exec(s)) !== null) {
      out.push(m[1]);
    }
  }
  return [...new Set(out)].sort();
}

/** YYYY-MM-DD + n天（UTC，避免本地时区偏移） */
function addDaysIso(iso, days) {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(Date.UTC(y, mo - 1, d));
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}

/** 仅生成往返深链：有去程无回程时，回程默认去程+7 天 */
function roundTripIsoPair(dates) {
  const dep = dates[0] || "";
  let ret = dates[1] || "";
  if (dep && !ret) ret = addDaysIso(dep, 7);
  return { dep, ret };
}

function googleFlightsSearchUrl(origin, dest, depIso, retIso) {
  const o = canonicalIata(origin);
  const d = canonicalIata(dest);
  if (!isValidIata(o) || !isValidIata(d)) return null;
  let q;
  if (depIso && retIso) {
    q = `Roundtrip flights from ${o} to ${d} on ${depIso} returning ${retIso}`;
  } else {
    q = `Roundtrip flights from ${o} to ${d}`;
  }
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(q)}`;
}

function kayakSearchUrl(origin, dest, depIso, retIso) {
  const o = canonicalIata(origin);
  const d = canonicalIata(dest);
  if (!isValidIata(o) || !isValidIata(d)) return null;
  const base = `https://www.kayak.com/flights/${o}-${d}`;
  if (depIso && retIso) return `${base}/${depIso}/${retIso}`;
  return `${base}/`;
}

function isoToSkyscannerSegment(iso) {
  return iso.replaceAll("-", "").slice(2);
}

/** Skyscanner 往返：/o/d/YYMMDD/YYMMDD/；无日期则仅城市对（用户在页内选往返） */
function skyscannerRoundTripUrl(origin, dest, depIso, retIso) {
  const o = canonicalIata(origin).toLowerCase();
  const d = canonicalIata(dest).toLowerCase();
  if (!isValidIata(o.toUpperCase()) || !isValidIata(d.toUpperCase())) return null;
  const base = `https://www.skyscanner.com/transport/flights/${o}/${d}/`;
  if (depIso && retIso) {
    return `${base}${isoToSkyscannerSegment(depIso)}/${isoToSkyscannerSegment(retIso)}/`;
  }
  return base;
}

function airportLabel(code) {
  const raw = String(code ?? "").trim();
  if (!raw) return "未知机场";
  const norm = normalizeAirportToken(raw);
  const c = norm ? canonicalIata(norm) : "";
  if (!isValidIata(c)) {
    return raw ? `未映射机场（${raw}）` : "未知机场";
  }
  const zh = AIRPORT_CITIES_ZH[c];
  const en = AIRPORT_CITIES_EN[c];
  if (zh) return `${zh}（${c}）`;
  if (en) return `${en}（${c}）`;
  return `${c}`;
}

function routeLabel(finding) {
  const { origin, dest } = resolveFindingAirports(finding);
  return `${airportLabel(origin)} ↔ ${airportLabel(dest)}`;
}

function buildFindingLinkRows(finding) {
  const { origin, dest } = resolveFindingAirports(finding);
  const rawDates = extractIsoDates(
    finding.date_range,
    finding.note,
    finding.route,
    finding.price_display,
  );
  const { dep, ret } = roundTripIsoPair(rawDates);
  const g = googleFlightsSearchUrl(origin, dest, dep || null, ret || null);
  const k = kayakSearchUrl(origin, dest, dep || null, ret || null);
  const sk = skyscannerRoundTripUrl(origin, dest, dep || null, ret || null);
  const rows = [];
  if (g) {
    const hint = dep && ret ? " 往返·含日期" : " 往返·页内选日期";
    rows.push(
      `<a class="finding-link finding-link--primary" href="${escapeHtml(g)}" target="_blank" rel="noreferrer">Google Flights 往返：${escapeHtml(canonicalIata(origin))}→${escapeHtml(canonicalIata(dest))}${hint}</a>`,
    );
  }
  if (k) {
    rows.push(
      `<a class="finding-link finding-link--secondary" href="${escapeHtml(k)}" target="_blank" rel="noreferrer">Kayak 往返：${escapeHtml(canonicalIata(origin))}-${escapeHtml(canonicalIata(dest))}</a>`,
    );
  }
  if (sk) {
    rows.push(
      `<a class="finding-link finding-link--secondary" href="${escapeHtml(sk)}" target="_blank" rel="noreferrer">Skyscanner 往返：${escapeHtml(canonicalIata(origin).toLowerCase())}/${escapeHtml(canonicalIata(dest).toLowerCase())}${dep && ret ? "·双程日期" : ""}</a>`,
    );
  }
  if (!rows.length) return "";
  return `<div class="finding-links" role="group" aria-label="按往返航线搜索">${rows.join("")}</div>`;
}

async function fetchJson(url, options = {}) {
  const finalUrl = options.method
    ? url
    : `${url}${url.includes("?") ? "&" : "?"}_ts=${Date.now()}`;
  const resp = await fetch(finalUrl, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

function setSearchButtonState(running) {
  state.manualSearchRunning = running;
  const button = document.getElementById("startSearchButton");
  if (!button) return;
  button.disabled = running;
  button.textContent = running ? "检索中…" : "立即检索票价";
}

function formatStatusMoment(value) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatRunMoment(value) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function latestUsefulRun(runs) {
  return (
    runs.find(
      (run) => run.status === "ok" && Array.isArray(run.findings) && run.findings.length,
    ) ||
    runs[0] ||
    null
  );
}

function renderRunCard(run) {
  const findingsCount = Array.isArray(run.findings) ? run.findings.length : 0;
  const el = document.createElement("div");
  el.className = "list-item";
  el.innerHTML = `
    <div class="list-title">
      <span>${escapeHtml(run.run_id)}</span>
      <span class="pill ${run.status === "ok" ? "pill-ok" : "pill-bad"}">${escapeHtml(run.status === "ok" ? "成功" : run.status)}</span>
    </div>
    <div class="list-meta">
      ${escapeHtml(formatRunMoment(run.finished_at || run.started_at))}<br>
      ${findingsCount} 条航线 · ${escapeHtml(run.headline || run.narrative_summary || run.error || "无结构化摘要")}
    </div>
  `;
  return el;
}

function renderRuns(runs) {
  const root = document.getElementById("runsList");
  root.innerHTML = "";
  if (!runs.length) {
    root.innerHTML = `<div class="empty-state">还没有检索运行记录。完成首轮查价后会出现在这里。</div>`;
    return;
  }
  runs.forEach((run) => root.appendChild(renderRunCard(run)));
}

function renderFindingPlaceholder(index) {
  const card = document.createElement("article");
  card.className = "finding-card finding-card-empty";
  card.innerHTML = `
    <div class="finding-card__top">
      <div class="finding-route finding-route--hero">暂无更多航线入板</div>
      <span class="finding-rank finding-rank--badge" aria-hidden="true">#${index + 1}</span>
    </div>
    <div class="finding-price finding-price--muted">—</div>
    <div class="finding-dates">本轮检索到的已核实结果不足，此格预留。</div>
    <div class="finding-note">看板仍保留 10 个卡位，版式与「航班时刻墙」一致，避免跳变。</div>
    <div class="finding-link-stack finding-link-stack--footer">
      <span class="finding-link finding-link-placeholder">等待本轮索引到下一条低价</span>
    </div>
  `;
  return card;
}

function renderFindings(run, targetCount) {
  const root = document.getElementById("findingsGrid");
  root.innerHTML = "";
  if (!run || !Array.isArray(run.findings) || !run.findings.length) {
    for (let index = 0; index < FIXED_BOARD_ROUTE_COUNT; index += 1) {
      root.appendChild(renderFindingPlaceholder(index));
    }
    return;
  }
  const displayCount = Math.max(FIXED_BOARD_ROUTE_COUNT, targetCount || 0, run.findings.length);
  run.findings.slice(0, displayCount).forEach((finding, index) => {
    const card = document.createElement("article");
    card.className = "finding-card";
    const deepLinks = buildFindingLinkRows(finding);
    const searchBlock =
      deepLinks ||
      `<div class="finding-links finding-links--empty" role="status">暂无自动生成的往返搜索链接（缺少有效起降机场或 route 中无 AAA→BBB）</div>`;
    card.innerHTML = `
      <div class="finding-card__top">
        <div class="finding-route finding-route--hero">${escapeHtml(routeLabel(finding))}</div>
        <span class="finding-rank finding-rank--badge" aria-hidden="true">#${index + 1}</span>
      </div>
      <div class="finding-price">${escapeHtml(finding.price_display)}</div>
      <div class="finding-dates">${escapeHtml(finding.date_range)}</div>
      <div class="finding-note">${escapeHtml(finding.note || "无备注")}</div>
      <div class="finding-link-stack finding-link-stack--footer">
        ${searchBlock}
        <a class="finding-link finding-link--source" href="${escapeHtml(finding.source_url)}" target="_blank" rel="noreferrer">检索来源：${escapeHtml(finding.source_name)}</a>
      </div>
    `;
    root.appendChild(card);
  });
  for (let index = run.findings.length; index < displayCount; index += 1) {
    root.appendChild(renderFindingPlaceholder(index));
  }
}

function updateOverview(bootstrap, scheduler) {
  const cfg = bootstrap.config;
  setText("healthValue", bootstrap.codex.available ? "就绪" : "不可用");
  setText(
    "schedulerValue",
    scheduler.running ? "定时检索已开启（服务器）" : "定时检索未运行",
  );
  setText("hostName", bootstrap.codex.host || "未知");
  setText(
    "codexStatus",
    bootstrap.codex.available
      ? bootstrap.codex.path
      : `Codex 不可用：${bootstrap.codex.error}`,
  );
  setText("originValue", (cfg.origin_airports || []).join(", "));
  setText("scopeValue", cfg.destination_scope);
  setText(
    "topNValue",
    `${Math.max(FIXED_BOARD_ROUTE_COUNT, cfg.top_n || 0)} 条航线`,
  );
  setText("intervalValue", `每 ${cfg.interval_hours} 小时`);
  setText("configPath", bootstrap.paths.config);
  setText("promptPath", "flight-hourly-web-search（skill）");
}

function updateSummary(runs, config) {
  const run = latestUsefulRun(runs);
  if (!run) {
    setText("boardHeadline", "尚未完成任何一轮检索。");
    setText("latestMeta", "等待首次成功的上网查价任务…");
    setText("summaryText", "服务器跑完第一轮检索后，低价卡片和摘要会自动出现在这里。");
    renderFindings(null);
    return;
  }
  setText("boardHeadline", run.headline || "本轮机票检索快照");
  setText(
    "latestMeta",
    `${run.status === "ok" ? "最近成功" : "最近运行"} · ${formatRunMoment(run.finished_at || run.started_at)} · 展示 ${Math.max(FIXED_BOARD_ROUTE_COUNT, config?.top_n || 0)} 个航线卡位`,
  );
  setText(
    "summaryText",
    run.narrative_summary || run.error || run.output || "暂无文字摘要。",
  );
  renderFindings(run, config?.top_n || 10);
}

async function refreshDashboard() {
  const [bootstrap, scheduler, searchStatus] = await Promise.all([
    fetchJson("/api/gui/bootstrap"),
    fetchJson("/api/local/scheduler/status"),
    fetchJson("/api/local/search-status"),
  ]);
  state.bootstrap = bootstrap;
  state.scheduler = scheduler;

  updateOverview(bootstrap, scheduler);
  renderRuns(bootstrap.recent_runs || []);
  updateSummary(bootstrap.recent_runs || [], bootstrap.config || {});
  setSearchButtonState(Boolean(searchStatus.manual_search?.running));
  const nextRunText = scheduler.next_run_at
    ? ` 下次定时检索：${formatStatusMoment(scheduler.next_run_at)}。`
    : "";
  setText(
    "boardStatus",
    searchStatus.manual_search?.running
      ? `正在执行一次手动的上网查价（服务器）。${nextRunText}`
      : scheduler.job_running
        ? `定时检索任务正在跑。${nextRunText}`
        : scheduler.running
          ? `服务器将按间隔自动检索票价并更新本页。${nextRunText}需要加跑时，点「立即检索票价」。`
          : "服务已加载，但定时检索未开启。",
  );
}

async function triggerManualSearch() {
  if (state.manualSearchRunning) return;
  setSearchButtonState(true);
  setText("boardStatus", "正在向服务器发起一次额外检索…");
  try {
    await fetchJson("/api/local/search-now", { method: "POST" });
    await refreshDashboard();
    setText(
      "boardStatus",
      "已接受手动检索。新结果写入后，本页会自动刷新（也可稍后手动刷新浏览器）。",
    );
  } catch (error) {
    setText("boardStatus", `手动检索失败：${error}`);
  }
}

refreshDashboard().catch((error) => {
  setText("boardStatus", `看板初始化失败：${error}`);
  setText("healthValue", "错误");
  setText("schedulerValue", "见下方状态栏");
});

document.getElementById("startSearchButton")?.addEventListener("click", () => {
  triggerManualSearch().catch((error) => {
    setText("boardStatus", `手动检索失败：${error}`);
    setSearchButtonState(false);
  });
});

window.setInterval(() => {
  refreshDashboard().catch((error) => {
    setText("boardStatus", `自动刷新失败：${error}`);
  });
}, 60000);
