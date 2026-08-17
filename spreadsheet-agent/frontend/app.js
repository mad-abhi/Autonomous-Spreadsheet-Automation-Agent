let ws;
let currentExcelPath = null;

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/agent`);

  ws.onopen = () => {
    document.getElementById('connection-status').innerHTML = `
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Connected
    `;
    document.getElementById('connection-status').className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs glass-card border-slate-700 text-emerald-400";
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleAgentEvent(data);
  };

  ws.onclose = () => {
    document.getElementById('connection-status').innerHTML = `
      <span class="w-2 h-2 rounded-full bg-rose-500"></span> Disconnected
    `;
    document.getElementById('connection-status').className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs glass-card border-rose-900/50 text-rose-400";
    setTimeout(connectWebSocket, 2000);
  };
}

function appendLog(text, color = "text-slate-300") {
  const terminal = document.getElementById("terminal");
  const p = document.createElement("p");
  p.className = `${color} font-mono`;
  p.textContent = `> ${text}`;
  terminal.appendChild(p);
  terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
  document.getElementById("terminal").innerHTML = "";
}

function highlightStep(stepId, state = "active") {
  const el = document.getElementById(stepId);
  const icon = el.querySelector(".step-icon");
  if (state === "active") {
    el.classList.add("border-indigo-500/50", "bg-indigo-950/20");
    icon.className = "w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-semibold text-xs animate-pulse step-icon";
  } else if (state === "done") {
    el.classList.remove("border-indigo-500/50", "bg-indigo-950/20");
    el.classList.add("border-emerald-500/40", "bg-emerald-950/10");
    icon.className = "w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-semibold text-xs step-icon";
    icon.innerHTML = '<i class="fa-solid fa-check"></i>';
  }
}

function renderTablePreview(records) {
  if (!records || records.length === 0) return;
  
  const headers = Object.keys(records[0]);
  const thead = document.getElementById("preview-thead");
  const tbody = document.getElementById("preview-tbody");
  
  thead.innerHTML = `<tr>${headers.map(h => `<th class="p-3 font-semibold uppercase tracking-wider text-[11px]">${h.replace('_', ' ')}</th>`).join('')}</tr>`;
  tbody.innerHTML = records.map((row, idx) => `
    <tr class="${idx % 2 === 0 ? 'bg-slate-900/20' : ''} hover:bg-slate-800/30">
      ${headers.map(h => `<td class="p-3 text-slate-300">${row[h] !== undefined ? row[h] : ''}</td>`).join('')}
    </tr>
  `).join('');

  document.getElementById("row-count-badge").innerText = `${records.length} records`;
}

function handleAgentEvent(event) {
  switch (event.type) {
    case "thought":
      highlightStep("step-reason", "active");
      appendLog(`[THOUGHT] ${event.message}`, "text-indigo-400");
      break;

    case "action":
      appendLog(`[TOOL CALL] Executing: ${event.tool}`, "text-amber-400");
      if (event.tool === "generate_dataset") {
        highlightStep("step-reason", "done");
        highlightStep("step-data", "active");
      } else if (event.tool === "create_styled_excel") {
        highlightStep("step-excel", "active");
      } else if (event.tool === "upload_to_google_sheets") {
        highlightStep("step-gsheet", "active");
      }
      break;

    case "data_generated":
      highlightStep("step-data", "done");
      renderTablePreview(event.data);
      appendLog(`[DATA] Successfully generated ${event.data.length} records`, "text-emerald-400");
      break;

    case "excel_created":
      highlightStep("step-excel", "done");
      currentExcelPath = event.path;
      const excelBtn = document.getElementById("open-excel-btn");
      excelBtn.disabled = false;
      excelBtn.className = "w-full py-3 px-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 font-medium text-sm flex items-center justify-between cursor-pointer hover:bg-emerald-900/40 transition";
      appendLog(`[EXCEL] Saved locally to: ${event.path}`, "text-emerald-400");
      break;

    case "gsheet_created":
      highlightStep("step-gsheet", "done");
      const gsheetBtn = document.getElementById("open-gsheet-btn");
      gsheetBtn.href = event.url;
      gsheetBtn.classList.remove("opacity-40", "pointer-events-none");
      gsheetBtn.className = "w-full py-3 px-4 rounded-xl bg-indigo-950/40 border border-indigo-500/40 text-indigo-300 font-medium text-sm flex items-center justify-between hover:bg-indigo-900/40 transition";
      appendLog(`[GSHEET] Published to: ${event.url}`, "text-indigo-400");
      break;

    case "completed":
      document.getElementById("summary-box").innerText = event.summary || "Agent task completed successfully.";
      document.getElementById("run-btn").disabled = false;
      document.getElementById("run-btn").innerHTML = '<i class="fa-solid fa-play text-xs"></i> Run Agent';
      appendLog(`[COMPLETE] Task execution finished.`, "text-emerald-300");
      break;

    case "error":
      appendLog(`[ERROR] ${event.message}`, "text-rose-400");
      document.getElementById("run-btn").disabled = false;
      document.getElementById("run-btn").innerHTML = '<i class="fa-solid fa-play text-xs"></i> Run Agent';
      break;
  }
}

function runAgent() {
  const promptInput = document.getElementById("prompt-input");
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  // Reset UI Steppers
  ["step-reason", "step-data", "step-excel", "step-gsheet"].forEach(s => {
    const el = document.getElementById(s);
    el.className = "glass-card p-4 rounded-xl flex items-center gap-3 border-slate-800 transition duration-300";
    const icon = el.querySelector(".step-icon");
    icon.className = "w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 font-semibold text-xs step-icon";
    icon.textContent = s.includes("reason") ? "1" : s.includes("data") ? "2" : s.includes("excel") ? "3" : "4";
  });

  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin text-xs"></i> Running...';

  ws.send(JSON.stringify({ prompt: prompt }));
}

async function openExcelLocally() {
  if (!currentExcelPath) return;
  await fetch("/api/open-local", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: currentExcelPath })
  });
}

// Initialize WebSocket on page load
connectWebSocket();