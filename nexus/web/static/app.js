var networkInstance = null;
var currentReport = null;
let activeAIProvider = 'local_gemma';

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    activeAIProvider = data.active_provider;

    // Sync select dropdowns
    const headerSel = document.getElementById('headerProviderToggle');
    if (headerSel) headerSel.value = activeAIProvider;
    const settingsSel = document.getElementById('settingsProviderToggle');
    if (settingsSel) settingsSel.value = activeAIProvider;

    document.getElementById('runtimeStatus').innerText = data.model_status;

    // Model summary on Overview
    const activeInfo = activeAIProvider === 'gemini' ? data.gemini : data.local_gemma;
    const isConn = activeInfo && activeInfo.is_connected;
    document.getElementById('modelSummary').innerText = isConn ? `Connected (${activeInfo.discovered_model || activeAIProvider})` : 'Offline / Error';
    document.getElementById('modelSummary').style.color = isConn ? 'var(--accent-success)' : 'var(--accent-critical)';

    if (isConn) {
      document.getElementById('runtimeDot').className = 'status-dot';
    } else {
      document.getElementById('runtimeDot').className = 'status-dot warning';
    }

    // Locality indicator
    document.getElementById('localityStatus').innerText = activeAIProvider === 'gemini' ? 'Gemini Remote' : 'Local-First';
  } catch (e) {
    console.error('Status fetch error:', e);
  }
}

async function switchAIProvider(providerName) {
  try {
    const res = await fetch('/api/provider', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: providerName })
    });
    const data = await res.json();
    if (res.ok) {
      activeAIProvider = data.active_provider;
      const headerSel = document.getElementById('headerProviderToggle');
      if (headerSel) headerSel.value = activeAIProvider;
      const settingsSel = document.getElementById('settingsProviderToggle');
      if (settingsSel) settingsSel.value = activeAIProvider;
      await fetchStatus();
    } else {
      alert(data.detail || 'Failed to switch provider');
    }
  } catch (e) {
    alert('Server communication error: ' + e);
  }
}

async function loadCounts() {
  try {
    const sessRes = await fetch('/api/sessions');
    const sessions = await sessRes.json();
    document.getElementById('countSessions').innerText = sessions.length;

    const convRes = await fetch('/api/conversations');
    const convs = await convRes.json();
    document.getElementById('countConversations').innerText = convs.length;
  } catch (e) {}
}

async function runAnalysis() {
  try {
    const res = await fetch('/api/run_analysis', { method: 'POST' });
    const data = await res.json();
    currentReport = data;
    renderReport(data);
  } catch (e) {
    alert('Analysis failed: ' + e);
  }
}

function renderReport(report) {
  if (!report) return;

  document.getElementById('countFindings').innerText = report.findings.length;

  const overviewContainer = document.getElementById('overviewFindings');
  const analysisContainer = document.getElementById('analysisFindings');
  overviewContainer.innerHTML = '';
  analysisContainer.innerHTML = '';

  report.findings.forEach(f => {
    const sevClass = f.severity === 'critical' ? 'critical' : (f.severity === 'high' ? 'high' : 'info');
    const cardHtml = `
      <div class="finding-card ${sevClass}">
        <div class="finding-header">
          <span class="finding-module">[${f.module}]</span>
          <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">${f.severity}</span>
        </div>
        <div class="finding-title">${f.title}</div>
        <div class="finding-desc">${f.description}</div>
        ${f.remediation_suggestion ? `<div class="finding-remediation"><strong>Remediation:</strong> ${f.remediation_suggestion}</div>` : ''}
      </div>
    `;
    overviewContainer.insertAdjacentHTML('beforeend', cardHtml);
    analysisContainer.insertAdjacentHTML('beforeend', cardHtml);
  });

  renderGraph(report.nodes, report.edges);
}

let rawNodesList = [];
let rawEdgesList = [];

function fitGraph() {
  if (networkInstance) {
    networkInstance.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
  }
}

function renderGraph(nodes, edges) {
  rawNodesList = nodes || [];
  rawEdgesList = edges || [];
  const container = document.getElementById('graphCanvas');
  if (!container || typeof vis === 'undefined') return;

  const typeColors = {
    goal: '#2563eb',
    constraint: '#0891b2',
    claim: '#475569',
    assumption: '#d97706',
    decision: '#3b82f6',
    action: '#dc2626',
    artifact: '#059669',
    evidence: '#7c3aed'
  };

  const visNodes = new vis.DataSet(
    rawNodesList.map(n => ({
      id: n.id,
      label: n.label,
      title: `${n.type.toUpperCase()}: ${n.description}`,
      color: {
        background: typeColors[n.type] || '#475569',
        border: '#ffffff',
        highlight: { background: '#1e293b', border: '#38bdf8' }
      },
      font: { color: '#ffffff', face: 'Inter', size: 12, bold: true },
      shape: 'box',
      margin: 10,
      shadow: true
    }))
  );

  const visEdges = new vis.DataSet(
    rawEdgesList.map(e => ({
      id: `${e.source}->${e.target}`,
      from: e.source,
      to: e.target,
      label: e.relation,
      arrows: { to: { enabled: true, scaleFactor: 0.8 } },
      font: { align: 'middle', size: 10, color: '#71717a', strokeWidth: 2, strokeColor: '#ffffff' },
      color: { color: '#cbd5e1', highlight: '#0284c7' },
      smooth: { type: 'cubicBezier', roundness: 0.2 }
    }))
  );

  const data = { nodes: visNodes, edges: visEdges };
  const options = {
    autoResize: true,
    height: '100%',
    width: '100%',
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -50,
        centralGravity: 0.01,
        springLength: 100,
        springConstant: 0.08
      },
      stabilization: { iterations: 150 }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      navigationButtons: true,
      keyboard: true
    }
  };

  if (networkInstance) {
    try { networkInstance.destroy(); } catch (e) {}
  }

  networkInstance = new vis.Network(container, data, options);

  // Click inspection handler
  networkInstance.on('click', function(params) {
    const inspector = document.getElementById('nodeInspectorPanel');
    if (params.nodes && params.nodes.length > 0) {
      const selectedId = params.nodes[0];
      const found = rawNodesList.find(n => n.id === selectedId);
      if (found && inspector) {
        inspector.style.display = 'block';
        document.getElementById('inspectNodeTitle').innerText = found.label;
        document.getElementById('inspectNodeType').innerText = `Type: ${found.type.toUpperCase()} | Provenance: ${found.provenance || 'deterministic_rule'}`;
        document.getElementById('inspectNodeDesc').innerText = found.description;
      }
    }
  });

  // Fit automatically after stabilization
  networkInstance.once('stabilizationIterationsDone', function() {
    networkInstance.fit();
  });
}

// Activity Timeline
async function loadTimeline() {
  const container = document.getElementById('timelineContainer');
  try {
    const res = await fetch('/api/events');
    const events = await res.json();
    if (events.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">No browser events recorded yet. Pair the extension and browse supported AI services (ChatGPT, Gemini, Claude, Perplexity).</div>';
      return;
    }
    container.innerHTML = '';
    events.forEach(evt => {
      container.insertAdjacentHTML('beforeend', `
        <div class="finding-card info">
          <div class="finding-header">
            <span class="finding-module">${evt.provider}</span>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${evt.timestamp}</span>
          </div>
          <div class="finding-title">${evt.event_type.toUpperCase()}: ${evt.url}</div>
        </div>
      `);
    });
  } catch (e) {}
}

// Conversation Library
async function loadLibrary() {
  const container = document.getElementById('libraryContainer');
  try {
    const res = await fetch('/api/conversations');
    const convs = await res.json();
    if (convs.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">No conversations imported or captured yet. Paste a transcript above or capture text via the browser extension.</div>';
      return;
    }
    container.innerHTML = '';
    convs.forEach(c => {
      container.insertAdjacentHTML('beforeend', `
        <div class="finding-card">
          <div class="finding-header">
            <span class="finding-module">${c.provider} (${c.import_method})</span>
            <button onclick="deleteConv('${c.id}')" style="background: none; border: none; color: var(--accent-critical); cursor: pointer; font-size: 0.8rem;">Delete</button>
          </div>
          <div class="finding-title">${c.title}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">Created: ${c.created_at} | Size: ${c.content_len} characters</div>
          <button class="btn-primary" style="font-size: 0.8rem; padding: 4px 8px;" onclick="viewConversation('${c.id}')">View Full Transcript</button>
        </div>
      `);
    });
  } catch (e) {}
}

async function viewConversation(cid) {
  try {
    const res = await fetch(`/api/conversations/${cid}`);
    const data = await res.json();
    alert(`[${data.provider}] ${data.title}\n\n${data.content.slice(0, 800)}...`);
  } catch (e) {}
}

async function deleteConv(cid) {
  if (!confirm('Delete this conversation record?')) return;
  await fetch(`/api/conversations/${cid}`, { method: 'DELETE' });
  loadLibrary();
  loadCounts();
}

async function submitImport() {
  const title = document.getElementById('importTitle').value.trim() || 'Imported Chat Transcript';
  const provider = document.getElementById('importProvider').value;
  const content = document.getElementById('importContent').value.trim();

  if (!content) {
    alert('Please paste transcript content to import.');
    return;
  }

  const res = await fetch('/api/import_text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, provider, content })
  });

  if (res.ok) {
    document.getElementById('importContent').value = '';
    document.getElementById('importTitle').value = '';
    alert('Conversation saved into local database!');
    loadLibrary();
    loadCounts();
  }
}

// AI Chat (Local Gemma or Gemini API)
async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  const history = document.getElementById('chatHistory');
  history.insertAdjacentHTML('beforeend', `<div style="margin-bottom: 0.5rem;"><strong>You:</strong> ${msg}</div>`);
  input.value = '';

  const providerLabel = activeAIProvider === 'gemini' ? 'Gemini API' : 'Local Gemma';
  const loadingId = 'loading_' + Date.now();
  history.insertAdjacentHTML('beforeend', `<div id="${loadingId}" style="margin-bottom: 0.75rem; color: var(--text-soft); font-style: italic;"><strong>${providerLabel}:</strong> Thinking...</div>`);
  history.scrollTop = history.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();

    const sender = data.provider === 'gemini' ? 'Gemini API' : 'Local Gemma';
    const isError = !data.is_live_inference;
    const colorStyle = isError ? 'color: var(--accent-critical);' : 'color: var(--text-main);';
    history.insertAdjacentHTML('beforeend', `<div style="margin-bottom: 0.75rem; ${colorStyle}"><strong>${sender}:</strong> ${data.content}</div>`);

    // If diagnostics returned, render inline badge and refresh analysis
    if (data.diagnostics) {
      history.insertAdjacentHTML(
        'beforeend',
        `<div style="font-size: 0.75rem; color: var(--text-muted); background: var(--bg-elevated); padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 0.75rem;">
          🛡️ Diagnostics Evaluated: ${data.diagnostics.critical_violations} violations, ${data.diagnostics.findings_count} findings
        </div>`
      );
      loadCounts();
      runAnalysis();
    }
    history.scrollTop = history.scrollHeight;
  } catch (err) {
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();
    history.insertAdjacentHTML('beforeend', `<div style="margin-bottom: 0.75rem; color: var(--accent-critical);"><strong>Error:</strong> Failed to communicate with server: ${err}</div>`);
    history.scrollTop = history.scrollHeight;
  }
}

// Load Persistent Chat History
async function loadChatHistory() {
  const history = document.getElementById('chatHistory');
  try {
    const res = await fetch('/api/chat/messages');
    const msgs = await res.json();
    if (!msgs || msgs.length === 0) return;
    history.innerHTML = '';
    msgs.forEach(m => {
      const sender = m.role === 'user' ? 'You' : 'AI Assistant';
      history.insertAdjacentHTML('beforeend', `<div style="margin-bottom: 0.6rem;"><strong>${sender}:</strong> ${m.content}</div>`);
    });
    history.scrollTop = history.scrollHeight;
  } catch (e) {}
}

// Extension Pairing Code
async function refreshPairingCode() {
  const res = await fetch('/api/pairing_code');
  const data = await res.json();
  document.getElementById('pairingCodeDisplay').innerText = data.pairing_code;
}

function switchTab(tabId) {
  ['overview', 'timeline', 'library', 'analysis', 'graph', 'chat', 'settings'].forEach(id => {
    const el = document.getElementById('tab-' + id);
    if (el) el.style.display = (id === tabId) ? 'block' : 'none';
  });

  document.querySelectorAll('.nav-tab').forEach(b => {
    b.classList.remove('active');
    if (b.innerText.toLowerCase().includes(tabId)) b.classList.add('active');
  });

  if (tabId === 'timeline') loadTimeline();
  if (tabId === 'library') loadLibrary();
  if (tabId === 'chat') loadChatHistory();
  if (tabId === 'settings') refreshPairingCode();
  if (tabId === 'graph') {
    setTimeout(() => {
      if (!networkInstance && currentReport) {
        renderGraph(currentReport.nodes, currentReport.edges);
      } else if (networkInstance) {
        networkInstance.redraw();
        networkInstance.fit();
      }
    }, 50);
  }
}

// Initial load
fetchStatus();
loadCounts();
runAnalysis();
