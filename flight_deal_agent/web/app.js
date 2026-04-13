const state = {
  bootstrap: null,
  scheduler: null,
  manualSearchRunning: false,
};

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
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
  button.textContent = running ? "Searching..." : "Start search";
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
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function latestUsefulRun(runs) {
  return runs.find((run) => run.status === "ok" && Array.isArray(run.findings) && run.findings.length) || runs[0] || null;
}

function renderRunCard(run) {
  const findingsCount = Array.isArray(run.findings) ? run.findings.length : 0;
  const el = document.createElement("div");
  el.className = "list-item";
  el.innerHTML = `
    <div class="list-title">
      <span>${escapeHtml(run.run_id)}</span>
      <span class="pill ${run.status === "ok" ? "pill-ok" : "pill-bad"}">${escapeHtml(run.status)}</span>
    </div>
    <div class="list-meta">
      ${escapeHtml(formatRunMoment(run.finished_at || run.started_at))}<br>
      ${findingsCount} routes · ${escapeHtml(run.headline || run.narrative_summary || run.error || "No structured summary")}
    </div>
  `;
  return el;
}

function renderRuns(runs) {
  const root = document.getElementById("runsList");
  root.innerHTML = "";
  if (!runs.length) {
    root.innerHTML = `<div class="empty-state">No server runs yet.</div>`;
    return;
  }
  runs.forEach((run) => root.appendChild(renderRunCard(run)));
}

function renderFindingPlaceholder(index) {
  const card = document.createElement("article");
  card.className = "finding-card finding-card-empty";
  card.innerHTML = `
    <div class="finding-rank">#${index + 1}</div>
    <div class="finding-link finding-link-placeholder">Waiting for another indexed fare</div>
    <div class="finding-route">No additional route captured</div>
    <div class="finding-price">Pending</div>
    <div class="finding-dates">This hour did not surface enough verified results to fill this slot.</div>
    <div class="finding-note">The board still reserves all requested Top 10 positions so the dashboard shape stays stable.</div>
  `;
  return card;
}

function renderFindings(run, targetCount) {
  const root = document.getElementById("findingsGrid");
  root.innerHTML = "";
  if (!run || !Array.isArray(run.findings) || !run.findings.length) {
    root.innerHTML = `<div class="empty-state">No structured top-route results yet. The server will populate this board after the next successful hourly run.</div>`;
    return;
  }
  const displayCount = Math.max(targetCount || 0, run.findings.length);
  run.findings.slice(0, displayCount).forEach((finding, index) => {
    const card = document.createElement("article");
    card.className = "finding-card";
    card.innerHTML = `
      <div class="finding-rank">#${index + 1}</div>
      <a class="finding-link" href="${escapeHtml(finding.source_url)}" target="_blank" rel="noreferrer">Open fare source: ${escapeHtml(finding.source_name)}</a>
      <div class="finding-route">${escapeHtml(finding.route)}</div>
      <div class="finding-price">${escapeHtml(finding.price_display)}</div>
      <div class="finding-dates">${escapeHtml(finding.date_range)}</div>
      <div class="finding-note">${escapeHtml(finding.note || "No extra note")}</div>
    `;
    root.appendChild(card);
  });
  for (let index = run.findings.length; index < displayCount; index += 1) {
    root.appendChild(renderFindingPlaceholder(index));
  }
}

function updateOverview(bootstrap, scheduler) {
  const cfg = bootstrap.config;
  setText("healthValue", bootstrap.codex.available ? "ONLINE" : "BLOCKED");
  setText("schedulerValue", scheduler.running ? "Hourly worker active on server" : "Hourly worker not running");
  setText("hostName", bootstrap.codex.host || "unknown");
  setText(
    "codexStatus",
    bootstrap.codex.available
      ? bootstrap.codex.path
      : `codex unavailable: ${bootstrap.codex.error}`,
  );
  setText("originValue", (cfg.origin_airports || []).join(", "));
  setText("scopeValue", cfg.destination_scope);
  setText("topNValue", `${cfg.top_n} routes`);
  setText("intervalValue", `${cfg.interval_hours} hour(s)`);
  setText("configPath", bootstrap.paths.config);
  setText("promptPath", "flight-hourly-web-search skill");
}

function updateSummary(runs, config) {
  const run = latestUsefulRun(runs);
  if (!run) {
    setText("boardHeadline", "No hourly run has completed yet.");
    setText("latestMeta", "Waiting for the first successful server-side search run.");
    setText("summaryText", "The board will populate automatically after the server finishes a run.");
    renderFindings(null);
    return;
  }
  setText("boardHeadline", run.headline || "Latest server-side flight snapshot");
  setText(
    "latestMeta",
    `${run.status === "ok" ? "Latest success" : "Latest run"} · ${formatRunMoment(run.finished_at || run.started_at)} · ${Array.isArray(run.findings) ? run.findings.length : 0} routes`,
  );
  setText("summaryText", run.narrative_summary || run.error || run.output || "No summary available.");
  renderFindings(run, config?.top_n || 10);
}

async function refreshDashboard() {
  const [bootstrap, scheduler] = await Promise.all([
    fetchJson("/api/gui/bootstrap"),
    fetchJson("/api/local/scheduler/status"),
  ]);
  state.bootstrap = bootstrap;
  state.scheduler = scheduler;

  updateOverview(bootstrap, scheduler);
  renderRuns(bootstrap.recent_runs || []);
  updateSummary(bootstrap.recent_runs || [], bootstrap.config || {});
  setText(
    "boardStatus",
    scheduler.running
      ? "This board refreshes hourly on the server host. Use Start search only when you want one extra server-side run for testing."
      : "Server loaded, but the hourly worker is not running.",
  );
}

async function triggerManualSearch() {
  if (state.manualSearchRunning) return;
  setSearchButtonState(true);
  setText("boardStatus", "Starting one server-side search run...");
  try {
    await fetchJson("/api/local/search-now", { method: "POST" });
    await refreshDashboard();
    setText("boardStatus", "Manual search completed on the server host.");
  } catch (error) {
    setText("boardStatus", `Manual search failed: ${error}`);
  } finally {
    setSearchButtonState(false);
  }
}

refreshDashboard().catch((error) => {
  setText("boardStatus", `Bootstrap failed: ${error}`);
  setText("healthValue", "ERROR");
  setText("schedulerValue", "See board status");
});

document.getElementById("startSearchButton")?.addEventListener("click", () => {
  triggerManualSearch().catch((error) => {
    setText("boardStatus", `Manual search failed: ${error}`);
    setSearchButtonState(false);
  });
});

window.setInterval(() => {
  refreshDashboard().catch((error) => {
    setText("boardStatus", `Refresh failed: ${error}`);
  });
}, 60000);
