const API_BASE = 'http://127.0.0.1:8000/api';

const SUPPORTED_HOSTS = [
  'chatgpt.com',
  'chat.openai.com',
  'gemini.google.com',
  'claude.ai',
  'perplexity.ai'
];

function isSupportedUrl(url) {
  if (!url) return false;
  return SUPPORTED_HOSTS.some(h => url.includes(h));
}

document.addEventListener('DOMContentLoaded', async () => {
  const statusBadge = document.getElementById('statusBadge');
  const pairingSection = document.getElementById('pairingSection');
  const mainSection = document.getElementById('mainSection');
  const currentTabProvider = document.getElementById('currentTabProvider');
  const monitoringStatus = document.getElementById('monitoringStatus');
  const btnToggleMonitoring = document.getElementById('btnToggleMonitoring');
  const btnCapture = document.getElementById('btnCapture');

  // Load token and pause state
  const settings = await chrome.storage.local.get(['token', 'monitoringPaused']);
  const token = settings.token;

  if (!token) {
    pairingSection.style.display = 'block';
    mainSection.style.display = 'none';
    statusBadge.innerText = 'Unpaired';
  } else {
    pairingSection.style.display = 'none';
    mainSection.style.display = 'block';
    statusBadge.innerText = 'Paired & Local';
  }

  // Active tab inspection
  let activeTab = null;
  let isSupported = false;
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs.length > 0) {
      activeTab = tabs[0];
      const url = activeTab.url || '';
      isSupported = isSupportedUrl(url);

      if (url.includes('chatgpt.com') || url.includes('openai.com')) currentTabProvider.innerText = 'ChatGPT';
      else if (url.includes('gemini.google.com')) currentTabProvider.innerText = 'Gemini';
      else if (url.includes('claude.ai')) currentTabProvider.innerText = 'Claude';
      else if (url.includes('perplexity.ai')) currentTabProvider.innerText = 'Perplexity';
      else currentTabProvider.innerText = 'Unsupported Page';
    }
  } catch (err) {
    currentTabProvider.innerText = 'Tab Unavailable';
  }

  // Monitoring status display
  const paused = settings.monitoringPaused === true;
  monitoringStatus.innerText = paused ? 'Paused' : 'Active';
  monitoringStatus.style.color = paused ? '#d97706' : '#059669';
  btnToggleMonitoring.innerText = paused ? 'Resume Monitoring' : 'Pause Monitoring';

  // 1. Pairing Handler
  document.getElementById('btnPair').addEventListener('click', async () => {
    const code = document.getElementById('pairingCodeInput').value.trim();
    if (!code) {
      alert('Please enter your 8-character pairing code from the NEXUS web dashboard.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/extension/pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pairing_code: code })
      });
      const data = await res.json();
      if (res.ok && data.token) {
        await chrome.storage.local.set({ token: data.token });
        // Request background service worker to flush queue
        chrome.runtime.sendMessage({ type: 'FLUSH_QUEUE' }, () => {
          if (chrome.runtime.lastError) {
            // Background wake/ignore
          }
        });
        window.location.reload();
      } else {
        alert(data.detail || 'Pairing failed. Ensure code matches dashboard.');
      }
    } catch (e) {
      alert('Could not contact NEXUS server on 127.0.0.1:8000. Ensure NEXUS is running.');
    }
  });

  // 2. Open dashboard
  document.getElementById('btnOpenDashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://127.0.0.1:8000' });
  });

  // 3. Robust Capture Selected Text
  btnCapture.addEventListener('click', async () => {
    if (!activeTab || !activeTab.id) {
      alert('No active browser tab found.');
      return;
    }

    if (!isSupported) {
      alert(`Text capture is only available on supported AI websites:\nChatGPT, Gemini, Claude, and Perplexity.`);
      return;
    }

    // Safely send message with runtime.lastError handling and script reinjection if needed
    const sendMessageToTab = (tabId) => {
      chrome.tabs.sendMessage(tabId, { action: 'get_selected_text' }, async (response) => {
        if (chrome.runtime.lastError) {
          // If receiving end does not exist, inject content script dynamically and retry once
          try {
            await chrome.scripting.executeScript({
              target: { tabId: tabId },
              files: ['content.js']
            });
            // Retry message after injection
            chrome.tabs.sendMessage(tabId, { action: 'get_selected_text' }, (retryResp) => {
              if (chrome.runtime.lastError || !retryResp) {
                alert('Could not communicate with tab. Please refresh the page and select text.');
                return;
              }
              handleCaptureResponse(retryResp);
            });
          } catch (injectErr) {
            alert('Cannot access text on this tab. Ensure the page is completely loaded.');
          }
          return;
        }

        handleCaptureResponse(response);
      });
    };

    const handleCaptureResponse = async (response) => {
      if (!response || !response.text || response.text.trim().length === 0) {
        alert('No text is currently selected.\n\nPlease highlight text in your conversation first, then click "Capture Selected Text".');
        return;
      }

      const token = (await chrome.storage.local.get(['token'])).token;
      if (!token) {
        alert('Extension is unpaired. Please pair with NEXUS first.');
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/capture`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Nexus-Token': token
          },
          body: JSON.stringify({
            title: response.title || 'Selected Chat Excerpt',
            url: response.url || activeTab.url,
            content: response.text,
            provider: currentTabProvider.innerText
          })
        });

        if (res.ok) {
          alert('Selection captured and safely stored in NEXUS local database!');
        } else {
          alert('Capture failed: Local server rejected request.');
        }
      } catch (err) {
        alert('Server unreachable on 127.0.0.1:8000. Is NEXUS running?');
      }
    };

    sendMessageToTab(activeTab.id);
  });

  // 4. Toggle pause
  btnToggleMonitoring.addEventListener('click', async () => {
    const isPaused = !(await chrome.storage.local.get(['monitoringPaused'])).monitoringPaused;
    await chrome.storage.local.set({ monitoringPaused: isPaused });
    monitoringStatus.innerText = isPaused ? 'Paused' : 'Active';
    monitoringStatus.style.color = isPaused ? '#d97706' : '#059669';
    btnToggleMonitoring.innerText = isPaused ? 'Resume Monitoring' : 'Pause Monitoring';
  });
});
