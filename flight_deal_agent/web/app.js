const state = {
  config: null,
  bootstrap: null,
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

function fillSelect(el, options, value, labelKey = null) {
  el.innerHTML = "";
  options.forEach((item) => {
    const option = document.createElement("option");
    if (typeof item === "string") {
      option.value = item;
      option.textContent = item;
    } else {
      option.value = item.id;
      option.textContent = labelKey ? item[labelKey] : `${item.label} (${item.airport_count})`;
    }
    if (option.value === value) option.selected = true;
    el.appendChild(option);
  });
}

function formValue(id) {
  return document.getElementById(id).value.trim();
}

function optionalNumber(id) {
  const value = formValue(id);
  return value === "" ? null : Number(value);
}

function renderList(containerId, items, renderItem) {
  const root = document.getElementById(containerId);
  root.innerHTML = "";
  if (!items.length) {
    root.innerHTML = `<div class="empty-state">No data yet.</div>`;
    return;
  }
  items.forEach((item) => root.appendChild(renderItem(item)));
}

function quoteCard(quote) {
  const el = document.createElement("div");
  el.className = "list-item";
  const price = `${quote.currency} ${quote.total_price}`;
  el.innerHTML = `
    <div class="list-title">
      <span>${quote.origin} → ${quote.destination}</span>
      <span>${price}</span>
    </div>
    <div class="list-meta">
      ${quote.departure_date}${quote.return_date ? ` → ${quote.return_date}` : ""}<br>
      source=${quote.source}${quote.deep_link ? ` · <a href="${quote.deep_link}" target="_blank" rel="noreferrer">open</a>` : ""}
    </div>
  `;
  return el;
}

function runCard(run) {
  const el = document.createElement("div");
  el.className = "list-item";
  el.innerHTML = `
    <div class="list-title">
      <span>${run.run_id}</span>
      <span>${run.deal_count} deals</span>
    </div>
    <div class="list-meta">
      tasks=${run.task_count} · api_calls=${run.api_calls} · quotes=${run.quote_count}<br>
      started=${run.started_at}
    </div>
  `;
  return el;
}

async function refreshDashboard() {
  const [health, bootstrap, deals, runs, scheduler] = await Promise.all([
    fetchJson("/api/health"),
    fetchJson("/api/gui/bootstrap"),
    fetchJson("/api/deals?limit=8"),
    fetchJson("/api/runs?limit=8"),
    fetchJson("/api/scheduler/status"),
  ]);
  state.bootstrap = bootstrap;
  state.config = bootstrap.config;

  setText("healthValue", health.status.toUpperCase());
  setText("schedulerValue", scheduler.running ? "Scheduler running" : "Scheduler stopped");
  setText("configPath", bootstrap.paths.config);
  setText("envPath", bootstrap.paths.env);
  setText(
    "secretStatus",
    [
      bootstrap.secret_status.searchapi_api_key_set ? "SearchApi key set" : "SearchApi key missing",
      bootstrap.secret_status.amadeus_client_id_set ? "Amadeus id set" : "Amadeus id missing",
    ].join(" · "),
  );

  fillSelect(document.getElementById("provider"), bootstrap.provider_options, state.config.collector.provider);
  fillSelect(document.getElementById("target_region_id"), bootstrap.regions, state.config.target_region_id);
  document.getElementById("origin_airports").value = (state.config.origin_airports || []).join(", ");
  document.getElementById("timezone").value = state.config.app.timezone;
  document.getElementById("currency").value = state.config.currency;
  document.getElementById("lowest_n_per_run").value = state.config.thresholds.lowest_n_per_run ?? 5;
  document.getElementById("request_budget_per_run").value = state.config.collector.request_budget_per_run;
  document.getElementById("interval_hours").value = state.config.scheduler.interval_hours;
  document.getElementById("interval_minutes").value = state.config.scheduler.interval_minutes ?? "";
  document.getElementById("max_total_price").value = state.config.thresholds.max_total_price ?? "";
  document.getElementById("below_median_pct").value = state.config.thresholds.below_median_pct ?? "";
  document.getElementById("gl").value = state.config.searchapi.gl ?? "us";
  document.getElementById("hl").value = state.config.searchapi.hl ?? "en";

  renderList("dealsList", deals, quoteCard);
  renderList("runsList", runs, runCard);
  setText("setupStatus", "Setup loaded. Secrets are never read back into the page.");
}

async function saveSetup() {
  const payload = {
    provider: formValue("provider"),
    origin_airports: formValue("origin_airports")
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean),
    target_region_id: formValue("target_region_id"),
    timezone: formValue("timezone"),
    currency: formValue("currency").toUpperCase(),
    lowest_n_per_run: Number(formValue("lowest_n_per_run")),
    request_budget_per_run: Number(formValue("request_budget_per_run")),
    interval_hours: Number(formValue("interval_hours")),
    interval_minutes: optionalNumber("interval_minutes"),
    max_total_price: optionalNumber("max_total_price"),
    below_median_pct: optionalNumber("below_median_pct"),
    searchapi_api_key: formValue("searchapi_api_key"),
    amadeus_client_id: formValue("amadeus_client_id"),
    amadeus_client_secret: formValue("amadeus_client_secret"),
    gl: formValue("gl"),
    hl: formValue("hl"),
  };

  const result = await fetchJson("/api/setup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setText(
    "setupStatus",
    `Saved setup. Scheduler interval now ${result.scheduler_interval}. Config written to ${result.config_path}.`,
  );
  await refreshDashboard();
}

async function runAction(path, label) {
  const out = document.getElementById("actionOutput");
  out.textContent = `${label}…`;
  try {
    const result = await fetchJson(path, { method: "POST" });
    out.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    out.textContent = String(error);
  }
  await refreshDashboard();
}

document.getElementById("saveSetupBtn").addEventListener("click", async (event) => {
  event.preventDefault();
  try {
    await saveSetup();
  } catch (error) {
    setText("setupStatus", `Save failed: ${error}`);
  }
});

document.getElementById("runNowBtn").addEventListener("click", () => runAction("/api/run", "Running one scan"));
document.getElementById("startSchedulerBtn").addEventListener("click", () => runAction("/api/scheduler/start", "Starting scheduler"));
document.getElementById("stopSchedulerBtn").addEventListener("click", () => runAction("/api/scheduler/stop", "Stopping scheduler"));

refreshDashboard().catch((error) => {
  setText("setupStatus", `Bootstrap failed: ${error}`);
  setText("healthValue", "ERROR");
  setText("schedulerValue", "See setup status");
});
