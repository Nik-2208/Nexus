// Content script: Enables explicit selection capture only when requested by user
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request && request.action === 'get_selected_text') {
    try {
      const selected = window.getSelection().toString().trim();
      sendResponse({
        ok: true,
        text: selected,
        title: document.title || 'Conversation Excerpt',
        url: window.location.href
      });
    } catch (err) {
      sendResponse({
        ok: false,
        error: err.message
      });
    }
  }
  return true; // Crucial for async response channels
});
