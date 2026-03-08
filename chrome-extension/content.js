// content.js – 多平台 Prompt 抓取引擎
(() => {
  const getSelectors = () => {
    const host = window.location.hostname;
    
    if (host.includes('claude.ai')) {
      return ['.font-user-message', '[data-test-id="user-message"]'];
    }
    if (host.includes('gemini.google.com')) {
      return ['user-query', '[data-message-author-role="user"]', '.user-query'];
    }
    if (host.includes('openai.com') || host.includes('chatgpt.com')) {
      return ['[data-message-author-role="user"]', '.request-data'];
    }
    // Default / Generic
    return ['[data-role="user"]', '.user-message', '.human-message'];
  };

  const extract = () => {
    const selectors = getSelectors();
    let texts = [];
    
    // Strategy 1: CSS Selectors
    for (const sel of selectors) {
      const elements = document.querySelectorAll(sel);
      if (elements.length > 0) {
        texts = [...elements].map(el => el.innerText.trim());
        break; 
      }
    }
    
    // Strategy 2: Fallback (if specific selectors fail)
    if (texts.length === 0) {
        // Try looking for common "User" labels in accessibility attributes
        const userDivs = [...document.querySelectorAll('div[aria-label="User"], div[aria-label="You"]')]
        if (userDivs.length > 0) {
            texts = userDivs.map(d => d.innerText.trim());
        }
    }

    return texts.filter(t => t && t.length > 2); // Basic noise filter
  };

  // 初始抓一次
  chrome.runtime.sendMessage({ type: "PROMPTS", texts: extract() });
  
  // 监听 DOM 变化，持续抓 (Debounced)
  let timeout = null;
  new MutationObserver(() => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
        chrome.runtime.sendMessage({ type: "PROMPTS", texts: extract() });
    }, 2000); // 2秒防抖，避免频繁发送
  }).observe(document.body, { childList: true, subtree: true });
})();
