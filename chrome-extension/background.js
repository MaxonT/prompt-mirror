// background.js
const API_BASE = "https://prompt-mirror-api.onrender.com";

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get("prompts", (res) => {
    if (!res.prompts) chrome.storage.local.set({ prompts: [] });
  });
});

// --- API Sync Helpers ---
async function getAuthToken() {
  const { authToken } = await chrome.storage.local.get("authToken");
  return authToken || null;
}

async function syncToAPI(newPrompts) {
  const token = await getAuthToken();
  if (!token || newPrompts.length === 0) return;

  const payload = newPrompts.map(p => ({
    text: p.text,
    source: p.src || "unknown",
    client_ts: p.ts || null,
  }));

  try {
    const resp = await fetch(`${API_BASE}/api/prompts/batch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ prompts: payload }),
    });
    if (resp.ok) {
      // Mark synced
      const { prompts = [] } = await chrome.storage.local.get("prompts");
      const syncedTexts = new Set(newPrompts.map(p => p.text));
      prompts.forEach(p => { if (syncedTexts.has(p.text)) p.synced = true; });
      await chrome.storage.local.set({ prompts });
    } else if (resp.status === 401) {
      // Token expired, clear it
      await chrome.storage.local.remove("authToken");
    }
  } catch {
    // Offline — prompts stay local, will sync next time
  }
}

// Save prompts locally and sync to API
async function saveAndSync(newItems) {
  const { prompts = [] } = await chrome.storage.local.get("prompts");
  const existing = new Set(prompts.map(p => p.text));
  const added = [];
  for (const item of newItems) {
    if (!existing.has(item.text)) {
      prompts.push(item);
      existing.add(item.text);
      added.push(item);
    }
  }
  await chrome.storage.local.set({ prompts });
  if (added.length > 0) syncToAPI(added);
}

// --- Content Script Message Handler ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "PROMPTS" && msg.texts?.length) {
    const host = sender.tab?.url ? new URL(sender.tab.url).hostname : "unknown";
    let src = "unknown";
    if (host.includes("claude")) src = "claude";
    else if (host.includes("gemini")) src = "gemini";
    else if (host.includes("openai") || host.includes("chatgpt")) src = "chatgpt";
    else if (host.includes("trae")) src = "trae";

    const items = msg.texts.map(t => ({ ts: Date.now(), text: t, src }));
    saveAndSync(items);
  }
  // Handle auth token save from popup
  if (msg.type === "SAVE_TOKEN") {
    chrome.storage.local.set({ authToken: msg.token });
  }
  // Handle full sync request from popup
  if (msg.type === "FULL_SYNC") {
    (async () => {
      const { prompts = [] } = await chrome.storage.local.get("prompts");
      const unsynced = prompts.filter(p => !p.synced);
      await syncToAPI(unsynced);
      sendResponse({ ok: true, count: unsynced.length });
    })();
    return true; // keep channel open for async response
  }
});

// --- Tab Update: Scrape on page load ---
chrome.tabs.onUpdated.addListener(async (tabId, change, tab) => {
  if (change.status !== "complete" || !tab.url) return;
  const supported = ["chat.openai.com", "chatgpt.com", "claude.ai", "gemini.google.com", "trae.ai"];
  if (!supported.some(h => tab.url.includes(h))) return;

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        const host = window.location.hostname;
        let sels = [];
        if (host.includes("claude")) sels = [".font-user-message", '[data-test-id="user-message"]'];
        else if (host.includes("gemini")) sels = ["user-query", '[data-message-author-role="user"]'];
        else sels = ['[data-message-author-role="user"]', ".request-data", '[data-role="user"]'];
        for (const sel of sels) {
          const els = document.querySelectorAll(sel);
          if (els.length) return [...els].map(e => e.innerText.trim()).filter(t => t && t.length > 2);
        }
        return [];
      }
    });
    const texts = results?.[0]?.result || [];
    if (texts.length === 0) return;

    let src = "unknown";
    if (tab.url.includes("claude")) src = "claude";
    else if (tab.url.includes("gemini")) src = "gemini";
    else if (tab.url.includes("openai") || tab.url.includes("chatgpt")) src = "chatgpt";
    else if (tab.url.includes("trae")) src = "trae";

    const items = texts.map(t => ({ ts: Date.now(), text: t, src }));
    await saveAndSync(items);
  } catch {}
});