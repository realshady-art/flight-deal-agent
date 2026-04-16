const LANG_STORAGE_KEY = "flight_deal_dashboard_lang";

const state = {
  bootstrap: null,
  scheduler: null,
  manualSearchRunning: false,
  lang: "zh",
};

const FIXED_BOARD_ROUTE_COUNT = 10;

const I18N = {
  zh: {
    "doc.title": "机票低价看板 · OrbitScan",
    "logo.aria": "返回首页",
    "lang.groupAria": "界面语言",
    "nav.tag": "机票 · 航线监控",
    "nav.board": "票价看板",
    "nav.runs": "检索记录",
    "strip.text":
      "我们要盯的是<strong>真实航线与票价线索</strong>：按出发机场与目的地范围，让服务器<strong>定时去网上检索</strong>，把当前能抓到的低价组合排进看板——<strong>以源站价格为准</strong>，这里只做汇总与追溯。",
    "hero.kicker": "机票低价 · 定时检索看板",
    "hero.title": "航线与票价，<br>在一张粗砺看板上摊开。",
    "hero.lede":
      "后端按配置好的机场与区域，周期性调用 Codex 在网页里查价、摘路线；本页展示<strong>本轮最值得关注的 Top 航线卡片</strong>（含税价展示、出行日期区间、来源链接），并保留每一次检索的运行记录。需要加跑一轮时，点下面按钮即可。",
    "hero.btnSearch": "立即检索票价",
    "hero.btnBoard": "去看低价卡片",
    "hero.btnSearchRunning": "检索中…",
    "mock.hash": "# fare-scan",
    "mock.metaTitle": "本轮槽位",
    "mock.line1":
      '<span class="pix pix--v"></span> <strong>你</strong> · YVR→LAS 这条含税还成立吗？',
    "mock.line2":
      '<span class="pix pix--a"></span> <strong>检索任务</strong> · 已对比3 个源站，写入本轮 JSONL。',
    "mock.line3":
      '<span class="pix pix--l"></span> <strong>定时器</strong> · 下一整点继续扫低价。',
    "section.diff.title": "和「随便看看」的机票站有什么不同",
    "section.diff.sub":
      "三件事：按你的机场/区域配置检索、固定 10 张低价卡位不塌、每次查价都有日志可对账。",
    "feat1.title": "票价来自检索，不是瞎编",
    "feat1.body":
      "任务在服务器上打开真实网页上下文；卡片里的链接带你回<strong>航空公司 / OTA 源站</strong>复核，下单前务必以源站为准。",
    "feat2.title": "10 格低价卡位",
    "feat2.body":
      "再少也占满 10 格，空位会标明「等待本轮索引」，版面永远像一块<strong>航班时刻表墙</strong>。",
    "feat3.title": "随时加跑一次",
    "feat3.body":
      "不等下一个整点，点<strong>立即检索票价</strong>让主机马上再搜一轮，适合改配置后验收。",
    "board.kicker": "采集管线状态",
    "board.title": "监控范围与运行环境",
    "board.label.pipeline": "检索管线",
    "board.label.headline": "本轮摘要标题",
    "board.label.host": "主机名",
    "board.label.codex": "Codex 可执行",
    "board.label.origin": "出发机场",
    "board.label.scope": "目的地范围",
    "board.label.topn": "展示航线数",
    "board.label.interval": "定时检索间隔",
    "board.label.config": "配置文件",
    "board.label.skill": "检索用 Skill",
    "board.hint.scheduler": "检查定时检索",
    "board.wait.headline": "等待中…",
    "board.status.loading": "看板加载中…",
    "routes.kicker": "本轮低价结果",
    "routes.title": "当前最值得看的航线卡片",
    "routes.meta.wait": "等待最近一次成功的检索…",
    "routes.summary.empty": "尚无摘要。",
    "runs.kicker": "检索历史",
    "runs.title": "最近几次「上网查票价」任务",
    "cta.title": "下一波低价出现时，看板会替你排好队。",
    "cta.sub": "本地即可启动；所有结构化结果落在服务器 JSONL，方便你对账与复盘。",
    "common.loading": "加载中",
    "common.unknown": "未知",
    "overview.ready": "就绪",
    "overview.unavailable": "不可用",
    "overview.schedulerOn": "定时检索已开启（服务器）",
    "overview.schedulerOff": "定时检索未运行",
    "overview.codexBad": "Codex 不可用：{error}",
    "overview.routesCount": "{n} 条航线",
    "overview.interval": "每 {hours} 小时",
    "overview.skillName": "flight-hourly-web-search（skill）",
    "summary.noRun": "尚未完成任何一轮检索。",
    "summary.waitFirst": "等待首次成功的上网查价任务…",
    "summary.waitBody": "服务器跑完第一轮检索后，低价卡片和摘要会自动出现在这里。",
    "summary.headlineDefault": "本轮机票检索快照",
    "summary.meta.ok": "最近成功",
    "summary.meta.run": "最近运行",
    "summary.meta.slots": "展示 {n} 个航线卡位",
    "summary.summaryEmpty": "暂无文字摘要。",
    "run.ok": "成功",
    "run.routesCount": "{n} 条航线 · {rest}",
    "runs.empty": "还没有检索运行记录。完成首轮查价后会出现在这里。",
    "run.summaryFallback": "无结构化摘要",
    "airport.unknown": "未知机场",
    "airport.unmapped": "未映射机场（{code}）",
    "finding.noNote": "无备注",
    "finding.source": "检索来源：{name}",
    "finding.linksEmpty":
      "暂无自动生成的往返搜索链接（缺少有效起降机场或 route 中无 AAA→BBB）",
    "finding.google": "Google Flights 往返：{o}→{d}{hint}",
    "finding.google.hintDates": " · 往返·含日期",
    "finding.google.hintPick": " · 往返·页内选日期",
    "finding.kayak": "Kayak 往返：{o}-{d}",
    "finding.sky": "Skyscanner 往返：{o}/{d}{suffix}",
    "finding.sky.dates": " · 双程日期",
    "finding.linksAria": "按往返航线搜索",
    "placeholder.route": "暂无更多航线入板",
    "placeholder.dates": "本轮检索到的已核实结果不足，此格预留。",
    "placeholder.note":
      "看板仍保留 10 个卡位，版式与「航班时刻墙」一致，避免跳变。",
    "placeholder.waitLink": "等待本轮索引到下一条低价",
    "status.nextScheduled": " 下次定时检索：{time}。",
    "status.manualRunning": "正在执行一次手动的上网查价（服务器）。{next}",
    "status.jobRunning": "定时检索任务正在跑。{next}",
    "status.autoOk":
      "服务器将按间隔自动检索票价并更新本页。{next}需要加跑时，点「立即检索票价」。",
    "status.schedulerOff": "服务已加载，但定时检索未开启。",
    "status.initFail": "看板初始化失败：{error}",
    "status.healthError": "错误",
    "status.schedulerHint": "见下方状态栏",
    "status.manualStart": "正在向服务器发起一次额外检索…",
    "status.manualDone":
      "已接受手动检索。新结果写入后，本页会自动刷新（也可稍后手动刷新浏览器）。",
    "status.manualFail": "手动检索失败：{error}",
    "status.refreshFail": "自动刷新失败：{error}",
  },
  en: {
    "doc.title": "Low-fare board · OrbitScan",
    "logo.aria": "Back to home",
    "lang.groupAria": "Interface language",
    "nav.tag": "Flights · route watch",
    "nav.board": "Fare board",
    "nav.runs": "Run log",
    "strip.text":
      "We track <strong>real routes and fare leads</strong>: the server <strong>searches the web on a schedule</strong> by origin and destination scope, then ranks what it finds—<strong>fares are always as on the source site</strong>; this board only aggregates and links back.",
    "hero.kicker": "Low fares · scheduled web search",
    "hero.title": "Routes and prices<br>on one bold board.",
    "hero.lede":
      "The backend runs Codex on a timer to search and extract fares. This page shows the <strong>current Top route cards</strong> (tax-inclusive display, travel dates, source links) plus a log of every search run. Click below for an extra run anytime.",
    "hero.btnSearch": "Search fares now",
    "hero.btnBoard": "Jump to cards",
    "hero.btnSearchRunning": "Searching…",
    "mock.hash": "# fare-scan",
    "mock.metaTitle": "Slots this round",
    "mock.line1":
      '<span class="pix pix--v"></span> <strong>You</strong> · Is YVR→LAS still priced like this?',
    "mock.line2":
      '<span class="pix pix--a"></span> <strong>Job</strong> · Compared 3 sources, wrote this round to JSONL.',
    "mock.line3":
      '<span class="pix pix--l"></span> <strong>Scheduler</strong> · Next sweep on the hour.',
    "section.diff.title": "How this differs from “browsing” a fare site",
    "section.diff.sub":
      "Three things: searches match your configured airports/region, the 10-card grid never collapses, and every run is logged for audit.",
    "feat1.title": "Fares from search, not invention",
    "feat1.body":
      "Work happens on the server against real pages; card links go to <strong>airline / OTA sources</strong>—always re-check before booking.",
    "feat2.title": "Ten fare slots",
    "feat2.body":
      "The board always shows 10 cells; empty ones say <strong>waiting for this round</strong>—like a departure board.",
    "feat3.title": "Run again on demand",
    "feat3.body":
      "Don’t wait for the next hour—use <strong>Search fares now</strong> for an immediate pass (e.g. after changing config).",
    "board.kicker": "Pipeline status",
    "board.title": "Scope & environment",
    "board.label.pipeline": "Search pipeline",
    "board.label.headline": "This round headline",
    "board.label.host": "Host",
    "board.label.codex": "Codex binary",
    "board.label.origin": "Origin airports",
    "board.label.scope": "Destination scope",
    "board.label.topn": "Routes shown",
    "board.label.interval": "Scheduled interval",
    "board.label.config": "Config file",
    "board.label.skill": "Search skill",
    "board.hint.scheduler": "Scheduler status",
    "board.wait.headline": "Waiting…",
    "board.status.loading": "Loading board…",
    "routes.kicker": "This round",
    "routes.title": "Top route cards",
    "routes.meta.wait": "Waiting for the latest successful run…",
    "routes.summary.empty": "No summary yet.",
    "runs.kicker": "History",
    "runs.title": "Recent web fare searches",
    "cta.title": "When the next deal shows up, the board queues it for you.",
    "cta.sub":
      "Runs locally; structured results land in JSONL on the server for review.",
    "common.loading": "Loading",
    "common.unknown": "Unknown",
    "overview.ready": "Ready",
    "overview.unavailable": "Unavailable",
    "overview.schedulerOn": "Scheduled search on (server)",
    "overview.schedulerOff": "Scheduled search off",
    "overview.codexBad": "Codex unavailable: {error}",
    "overview.routesCount": "{n} routes",
    "overview.interval": "Every {hours} h",
    "overview.skillName": "flight-hourly-web-search (skill)",
    "summary.noRun": "No completed run yet.",
    "summary.waitFirst": "Waiting for the first successful web search…",
    "summary.waitBody":
      "After the first run finishes, cards and summary will appear here.",
    "summary.headlineDefault": "This round’s fare snapshot",
    "summary.meta.ok": "Latest OK",
    "summary.meta.run": "Latest run",
    "summary.meta.slots": "{n} route slots",
    "summary.summaryEmpty": "No text summary.",
    "run.ok": "ok",
    "run.routesCount": "{n} routes · {rest}",
    "runs.empty": "No runs yet. They will appear after the first search.",
    "run.summaryFallback": "No structured summary",
    "airport.unknown": "Unknown airport",
    "airport.unmapped": "Unmapped airport ({code})",
    "finding.noNote": "No notes",
    "finding.source": "Source: {name}",
    "finding.linksEmpty":
      "No round-trip search links (missing airports or no AAA→BBB in route).",
    "finding.google": "Google Flights RT: {o}→{d}{hint}",
    "finding.google.hintDates": " · dates included",
    "finding.google.hintPick": " · pick dates on site",
    "finding.kayak": "Kayak RT: {o}-{d}",
    "finding.sky": "Skyscanner RT: {o}/{d}{suffix}",
    "finding.sky.dates": " · round-trip dates",
    "finding.linksAria": "Round-trip route search",
    "placeholder.route": "No more routes this round",
    "placeholder.dates": "Not enough verified results; slot reserved.",
    "placeholder.note":
      "Ten slots stay fixed like a departures wall so the layout doesn’t jump.",
    "placeholder.waitLink": "Waiting for the next fare in this round",
    "status.nextScheduled": " Next scheduled search: {time}.",
    "status.manualRunning": "Manual web search running on the server.{next}",
    "status.jobRunning": "Scheduled job running.{next}",
    "status.autoOk":
      "The server refreshes fares on an interval.{next}Use “Search fares now” for an extra run.",
    "status.schedulerOff": "Service loaded, but scheduled search is off.",
    "status.initFail": "Board failed to load: {error}",
    "status.healthError": "Error",
    "status.schedulerHint": "See status bar below",
    "status.manualStart": "Requesting an extra search on the server…",
    "status.manualDone":
      "Search accepted. This page will update when results are written (or refresh the browser).",
    "status.manualFail": "Manual search failed: {error}",
    "status.refreshFail": "Auto-refresh failed: {error}",
  },
};

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

function initLang() {
  const saved = localStorage.getItem(LANG_STORAGE_KEY);
  if (saved === "en" || saved === "zh") {
    state.lang = saved;
  } else {
    state.lang = "zh";
  }
}

function t(key, vars) {
  const table = I18N[state.lang] || I18N.zh;
  let s = table[key];
  if (s == null) s = I18N.zh[key] ?? key;
  if (vars && typeof s === "string") {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, String(v));
    }
  }
  return s;
}

function applyStaticI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key) el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = el.getAttribute("data-i18n-html");
    if (key) el.innerHTML = t(key);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    const key = el.getAttribute("data-i18n-aria");
    if (key) el.setAttribute("aria-label", t(key));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    const key = el.getAttribute("data-i18n-title");
    if (key) el.setAttribute("title", t(key));
  });
  document.title = t("doc.title");
  document.documentElement.lang = state.lang === "zh" ? "zh-Hans" : "en";

  document.querySelectorAll(".lang-switch__btn").forEach((btn) => {
    const lang = btn.getAttribute("data-lang");
    const active = lang === state.lang;
    btn.classList.toggle("lang-switch__btn--active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function setLang(lang) {
  if (lang !== "en" && lang !== "zh") return;
  state.lang = lang;
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  applyStaticI18n();
  setSearchButtonState(state.manualSearchRunning);
  refreshDashboard().catch(() => {});
}

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
  if (!raw) return t("airport.unknown");
  const norm = normalizeAirportToken(raw);
  const c = norm ? canonicalIata(norm) : "";
  if (!isValidIata(c)) {
    return raw ? t("airport.unmapped", { code: raw }) : t("airport.unknown");
  }
  const zh = AIRPORT_CITIES_ZH[c];
  const en = AIRPORT_CITIES_EN[c];
  if (state.lang === "en") {
    if (en) return `${en} (${c})`;
    return `${c}`;
  }
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
  const o = escapeHtml(canonicalIata(origin));
  const d = escapeHtml(canonicalIata(dest));
  const ol = canonicalIata(origin).toLowerCase();
  const dl = canonicalIata(dest).toLowerCase();
  const rows = [];
  if (g) {
    const hint = dep && ret ? t("finding.google.hintDates") : t("finding.google.hintPick");
    const label = t("finding.google", { o, d, hint });
    rows.push(
      `<a class="finding-link finding-link--primary" href="${escapeHtml(g)}" target="_blank" rel="noreferrer">${label}</a>`,
    );
  }
  if (k) {
    rows.push(
      `<a class="finding-link finding-link--secondary" href="${escapeHtml(k)}" target="_blank" rel="noreferrer">${t("finding.kayak", { o, d })}</a>`,
    );
  }
  if (sk) {
    const suffix = dep && ret ? t("finding.sky.dates") : "";
    rows.push(
      `<a class="finding-link finding-link--secondary" href="${escapeHtml(sk)}" target="_blank" rel="noreferrer">${t("finding.sky", { o: escapeHtml(ol), d: escapeHtml(dl), suffix })}</a>`,
    );
  }
  if (!rows.length) return "";
  return `<div class="finding-links" role="group" aria-label="${escapeHtml(t("finding.linksAria"))}">${rows.join("")}</div>`;
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
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setSearchButtonState(running) {
  state.manualSearchRunning = running;
  const button = document.getElementById("startSearchButton");
  if (!button) return;
  button.disabled = running;
  button.textContent = running ? t("hero.btnSearchRunning") : t("hero.btnSearch");
}

function formatStatusMoment(value) {
  if (!value) return t("common.unknown");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(state.lang === "zh" ? "zh-CN" : "en-CA");
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
  if (!value) return t("common.unknown");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(state.lang === "zh" ? "zh-CN" : "en-CA");
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
  const statusLabel = run.status === "ok" ? t("run.ok") : run.status;
  const rest = run.headline || run.narrative_summary || run.error || t("run.summaryFallback");
  const restEsc = escapeHtml(rest);
  el.innerHTML = `
    <div class="list-title">
      <span>${escapeHtml(run.run_id)}</span>
      <span class="pill ${run.status === "ok" ? "pill-ok" : "pill-bad"}">${escapeHtml(statusLabel)}</span>
    </div>
    <div class="list-meta">
      ${escapeHtml(formatRunMoment(run.finished_at || run.started_at))}<br>
      ${t("run.routesCount", { n: findingsCount, rest: restEsc })}
    </div>
  `;
  return el;
}

function renderRuns(runs) {
  const root = document.getElementById("runsList");
  root.innerHTML = "";
  if (!runs.length) {
    root.innerHTML = `<div class="empty-state">${escapeHtml(t("runs.empty"))}</div>`;
    return;
  }
  runs.forEach((run) => root.appendChild(renderRunCard(run)));
}

function renderFindingPlaceholder(index) {
  const card = document.createElement("article");
  card.className = "finding-card finding-card-empty";
  card.innerHTML = `
    <div class="finding-card__top">
      <div class="finding-route finding-route--hero">${escapeHtml(t("placeholder.route"))}</div>
      <span class="finding-rank finding-rank--badge" aria-hidden="true">#${index + 1}</span>
    </div>
    <div class="finding-price finding-price--muted">—</div>
    <div class="finding-dates">${escapeHtml(t("placeholder.dates"))}</div>
    <div class="finding-note">${escapeHtml(t("placeholder.note"))}</div>
    <div class="finding-link-stack finding-link-stack--footer">
      <span class="finding-link finding-link-placeholder">${escapeHtml(t("placeholder.waitLink"))}</span>
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
      `<div class="finding-links finding-links--empty" role="status">${escapeHtml(t("finding.linksEmpty"))}</div>`;
    const note = finding.note || t("finding.noNote");
    const sourceLabel = t("finding.source", { name: escapeHtml(finding.source_name) });
    card.innerHTML = `
      <div class="finding-card__top">
        <div class="finding-route finding-route--hero">${escapeHtml(routeLabel(finding))}</div>
        <span class="finding-rank finding-rank--badge" aria-hidden="true">#${index + 1}</span>
      </div>
      <div class="finding-price">${escapeHtml(finding.price_display)}</div>
      <div class="finding-dates">${escapeHtml(finding.date_range)}</div>
      <div class="finding-note">${escapeHtml(note)}</div>
      <div class="finding-link-stack finding-link-stack--footer">
        ${searchBlock}
        <a class="finding-link finding-link--source" href="${escapeHtml(finding.source_url)}" target="_blank" rel="noreferrer">${sourceLabel}</a>
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
  setText("healthValue", bootstrap.codex.available ? t("overview.ready") : t("overview.unavailable"));
  setText(
    "schedulerValue",
    scheduler.running ? t("overview.schedulerOn") : t("overview.schedulerOff"),
  );
  setText("hostName", bootstrap.codex.host || t("common.unknown"));
  setText(
    "codexStatus",
    bootstrap.codex.available
      ? bootstrap.codex.path
      : t("overview.codexBad", { error: bootstrap.codex.error }),
  );
  setText("originValue", (cfg.origin_airports || []).join(", "));
  setText("scopeValue", cfg.destination_scope);
  setText(
    "topNValue",
    t("overview.routesCount", { n: Math.max(FIXED_BOARD_ROUTE_COUNT, cfg.top_n || 0) }),
  );
  setText("intervalValue", t("overview.interval", { hours: cfg.interval_hours }));
  setText("configPath", bootstrap.paths.config);
  setText("promptPath", t("overview.skillName"));
}

function updateSummary(runs, config) {
  const run = latestUsefulRun(runs);
  if (!run) {
    setText("boardHeadline", t("summary.noRun"));
    setText("latestMeta", t("summary.waitFirst"));
    setText("summaryText", t("summary.waitBody"));
    renderFindings(null);
    return;
  }
  setText("boardHeadline", run.headline || t("summary.headlineDefault"));
  const statusPhrase = run.status === "ok" ? t("summary.meta.ok") : t("summary.meta.run");
  const slots = Math.max(FIXED_BOARD_ROUTE_COUNT, config?.top_n || 0);
  setText(
    "latestMeta",
    `${statusPhrase} · ${formatRunMoment(run.finished_at || run.started_at)} · ${t("summary.meta.slots", { n: slots })}`,
  );
  setText(
    "summaryText",
    run.narrative_summary || run.error || run.output || t("summary.summaryEmpty"),
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
    ? t("status.nextScheduled", { time: formatStatusMoment(scheduler.next_run_at) })
    : "";
  let statusMsg;
  if (searchStatus.manual_search?.running) {
    statusMsg = t("status.manualRunning", { next: nextRunText });
  } else if (scheduler.job_running) {
    statusMsg = t("status.jobRunning", { next: nextRunText });
  } else if (scheduler.running) {
    statusMsg = t("status.autoOk", { next: nextRunText });
  } else {
    statusMsg = t("status.schedulerOff");
  }
  setText("boardStatus", statusMsg);
}

async function triggerManualSearch() {
  if (state.manualSearchRunning) return;
  setSearchButtonState(true);
  setText("boardStatus", t("status.manualStart"));
  try {
    await fetchJson("/api/local/search-now", { method: "POST" });
    await refreshDashboard();
    setText("boardStatus", t("status.manualDone"));
  } catch (error) {
    setText("boardStatus", t("status.manualFail", { error: String(error) }));
  }
}

initLang();
applyStaticI18n();

document.getElementById("langZh")?.addEventListener("click", () => setLang("zh"));
document.getElementById("langEn")?.addEventListener("click", () => setLang("en"));

refreshDashboard().catch((error) => {
  setText("boardStatus", t("status.initFail", { error: String(error) }));
  setText("healthValue", t("status.healthError"));
  setText("schedulerValue", t("status.schedulerHint"));
});

document.getElementById("startSearchButton")?.addEventListener("click", () => {
  triggerManualSearch().catch((error) => {
    setText("boardStatus", t("status.manualFail", { error: String(error) }));
    setSearchButtonState(false);
  });
});

window.setInterval(() => {
  refreshDashboard().catch((error) => {
    setText("boardStatus", t("status.refreshFail", { error: String(error) }));
  });
}, 60000);
