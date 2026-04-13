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

function formValue(id) {
  return document.getElementById(id).value.trim();
}

function renderRunCard(run) {
  const el = document.createElement("div");
  el.className = "list-item";
  el.innerHTML = `
    <div class="list-title">
      <span>${run.run_id}</span>
      <span>${run.status}</span>
    </div>
    <div class="list-meta">
      ${run.started_at}<br>
      ${run.output ? run.output.slice(0, 180) : (run.error || "No output")}
    </div>
  `;
  return el;
}

function renderRuns(runs) {
  const root = document.getElementById("runsList");
  root.innerHTML = "";
  if (!runs.length) {
    root.innerHTML = `<div class="empty-state">No local runs yet.</div>`;
    document.getElementById("latestRun").textContent = "No local run yet.";
    return;
  }
  runs.forEach((run) => root.appendChild(renderRunCard(run)));
  const latest = runs[0];
  document.getElementById("latestRun").textContent = latest.output || latest.error || "No output";
}

async function refreshDashboard() {
  const [bootstrap, scheduler] = await Promise.all([
    fetchJson("/api/gui/bootstrap"),
    fetchJson("/api/local/scheduler/status"),
  ]);
  state.bootstrap = bootstrap;
  state.config = bootstrap.config;

  setText("healthValue", bootstrap.codex.available ? "READY" : "BLOCKED");
  setText("schedulerValue", scheduler.running ? "Hourly scheduler running" : "Hourly scheduler stopped");
  setText("configPath", bootstrap.paths.config);
  setText("promptPath", bootstrap.paths.prompt_template);
  setText(
    "codexStatus",
    bootstrap.codex.available
      ? `codex ok · ${bootstrap.codex.path}`
      : `codex missing · ${bootstrap.codex.error}`,
  );

  document.getElementById("origin_airport").value = state.config.origin_airport;
  document.getElementById("destination_scope").value = state.config.destination_scope;
  document.getElementById("top_n").value = state.config.top_n;
  document.getElementById("interval_hours").value = state.config.interval_hours;
  document.getElementById("notes").value = state.config.notes || "";

  renderRuns(bootstrap.recent_runs || []);
  setText("setupStatus", "GUI now drives the local Codex web-search flow only. No API key is required.");
}

async function saveSetup() {
  const payload = {
    origin_airport: formValue("origin_airport").toUpperCase(),
    destination_scope: formValue("destination_scope"),
    top_n: Number(formValue("top_n")),
    interval_hours: Number(formValue("interval_hours")),
    notes: formValue("notes"),
    model: "gpt-5.4",
    reasoning_effort: "medium",
  };

  const result = await fetchJson("/api/setup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setText(
    "setupStatus",
    `Saved local search config. Interval now ${result.scheduler_interval}. Config written to ${result.config_path}.`,
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

document.getElementById("runNowBtn").addEventListener("click", () => runAction("/api/local/run", "Running local Codex search"));
document.getElementById("startSchedulerBtn").addEventListener("click", () => runAction("/api/local/scheduler/start", "Starting hourly scheduler"));
document.getElementById("stopSchedulerBtn").addEventListener("click", () => runAction("/api/local/scheduler/stop", "Stopping hourly scheduler"));

refreshDashboard().catch((error) => {
  setText("setupStatus", `Bootstrap failed: ${error}`);
  setText("healthValue", "ERROR");
  setText("schedulerValue", "See setup status");
});
