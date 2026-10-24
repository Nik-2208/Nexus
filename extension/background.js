// NEXUS Companion Background Service Worker (Manifest V3)
const NEXUS_API_BASE = 'http://127.0.0.1:8000/api';

const SUPPORTED_DOMAINS = {
  'chatgpt.com': 'ChatGPT',
  'chat.openai.com': 'ChatGPT',
  'gemini.google.com': 'Gemini',
  'claude.ai': 'Claude',
  'perplexity.ai': 'Perplexity'
};

// Register runtime message listener at startup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === 'PING') {
    sendResponse({ status: 'PONG', time: Date.now() });
    return false;
  }
  if (message && message.type === 'FLUSH_QUEUE') {
    flushPendingEvents().then((count) => {
      sendResponse({ status: 'FLUSHED', count: count });
    });
    return true; // Async response
  }
  return false;
});

// Event-driven navigation observer
chrome.webNavigation.onCommitted.addListener((details) => {
  if (details.frameId !== 0) return; // Top-level frame only
  detectAndRecordSession(details.url, details.tabId);
});

// Single-Page-App URL updates (e.g. chat route changes)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url) {
    detectAndRecordSession(changeInfo.url, tabId, tab.title);
  }
});

function detectProvider(url) {
  try {
    const parsed = new URL(url);
    for (const domain in SUPPORTED_DOMAINS) {
      if (parsed.hostname.includes(domain)) {
        return SUPPORTED_DOMAINS[domain];
      }
    }
  } catch (e) {}
  return null;
}

async function detectAndRecordSession(url, tabId, title = '') {
  const provider = detectProvider(url);
  if (!provider) return;

  // Retrieve current tab title if missing
  if (!title && tabId) {
    try {
      const tab = await chrome.tabs.get(tabId);
      title = tab.title || '';
    } catch (e) {}
  }

  const sessionPayload = {
    provider: provider,
    url: url,
    title: title || `${provider} Conversation`,
    event_type: 'navigation'
  };

  // Queue and transmit to local server
  await transmitOrQueueEvent(sessionPayload);
}

async function flushPendingEvents() {
  const settings = await chrome.storage.local.get(['token', 'pendingQueue']);
  const token = settings.token;
  const queue = settings.pendingQueue || [];
  if (!token || queue.length === 0) return 0;

  let successCount = 0;
  const remaining = [];
  for (const item of queue) {
    try {
      const res = await fetch(`${NEXUS_API_BASE}/extension/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Nexus-Token': token },
        body: JSON.stringify(item)
      });
      if (res.ok) successCount++;
      else remaining.push(item);
    } catch (e) {
      remaining.push(item);
    }
  }
  await chrome.storage.local.set({ pendingQueue: remaining });
  return successCount;
}

async function transmitOrQueueEvent(payload) {
  const settings = await chrome.storage.local.get(['token', 'monitoringPaused', 'pendingQueue']);
  if (settings.monitoringPaused) return;

  const token = settings.token;
  const queue = settings.pendingQueue || [];

  if (!token) {
    queue.push(payload);
    await chrome.storage.local.set({ pendingQueue: queue.slice(-50) });
    return;
  }

  try {
    const res = await fetch(`${NEXUS_API_BASE}/extension/event`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Nexus-Token': token
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      if (queue.length > 0) {
        await flushPendingEvents();
      }
    } else {
      queue.push(payload);
      await chrome.storage.local.set({ pendingQueue: queue.slice(-50) });
    }
  } catch (err) {
    queue.push(payload);
    await chrome.storage.local.set({ pendingQueue: queue.slice(-50) });
  }
}
