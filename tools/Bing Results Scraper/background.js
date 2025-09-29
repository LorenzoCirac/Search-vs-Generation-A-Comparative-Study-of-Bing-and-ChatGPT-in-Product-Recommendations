// Bing Search Results Scraper with Content Extraction - Background Script

console.log('Bing Search Scraper with Content Extraction - Background script loaded');

// Hardcoded values for timeout and delay
const CONTENT_TIMEOUT = 15000; // 15 seconds
const RATE_LIMIT_MS = 1000; // 1 second between requests to same domain

// Initialize sidepanel on extension install/startup
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed - Setting up sidepanel');
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('Extension started - Sidepanel ready');
});

// =============== CONTENT FETCHING ===============

async function fetchUrlContent(url, timeout = CONTENT_TIMEOUT) {
  try {
    console.log(`Background: Fetching content from ${url}`);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
      },
      signal: controller.signal,
      redirect: 'follow',
      mode: 'cors'
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      return {
        content: '',
        error: `HTTP ${response.status}: ${response.statusText}`
      };
    }
    
    // Check content type
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) {
      return {
        content: '',
        error: `Unsupported content type: ${contentType}`
      };
    }
    
    const html = await response.text();
    console.log(`Background: Successfully fetched ${html.length} characters from ${url}`);
    
    return {
      content: html,
      error: null
    };
    
  } catch (error) {
    console.warn(`Background: Failed to fetch ${url}:`, error.message);
    
    let errorMessage = error.message;
    
    // Provide more user-friendly error messages
    if (error.name === 'AbortError') {
      errorMessage = 'Request timeout';
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Network error or CORS blocked';
    } else if (error.message.includes('TypeError')) {
      errorMessage = 'Invalid URL or network error';
    }
    
    return {
      content: '',
      error: errorMessage
    };
  }
}

// =============== COMMUNICATION RELAY ===============
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.action, 'from:', sender.tab ? 'content script' : 'sidepanel');
  
  // Handle content fetching requests
  if (message.action === 'fetchContent') {
    console.log(`Background: Content fetch request for ${message.url}`);
    
    fetchUrlContent(message.url, message.timeout || CONTENT_TIMEOUT)
      .then(result => {
        console.log(`Background: Content fetch completed for ${message.url}`);
        sendResponse(result);
      })
      .catch(error => {
        console.error(`Background: Content fetch error for ${message.url}:`, error);
        sendResponse({
          content: '',
          error: error.message || 'Unknown error'
        });
      });
    
    return true; // Keep message channel open for async response
  }
  
  // content to sidepanel relay
  if (sender.tab && (
    message.action === 'scrapingComplete' ||
    message.action === 'scrapingError' ||
    message.action === 'progressUpdate' ||
    message.action === 'queryError'
  )) {
    console.log('Relaying message to sidepanel:', message.action);
    return false; // Let the message propagate normally
  }
  
  // Handle direct background script actions
  if (message.action === 'backgroundPing') {
    console.log('Background script ping received');
    sendResponse({ status: 'background active' });
    return true;
  }
  
  // Log unhandled messages
  if (message.action) {
    console.log('Unhandled message action:', message.action);
  }
  
  return false;
});

// Handle tab updates to ensure content script stays connected
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('bing.com')) {
    console.log('Bing tab updated and ready:', tabId);
  }
});

// Handle connection errors
chrome.runtime.onConnect.addListener((port) => {
  console.log('Extension connection established:', port.name);
  
  port.onDisconnect.addListener(() => {
    if (chrome.runtime.lastError) {
      console.log('Connection disconnected with error:', chrome.runtime.lastError.message);
    } else {
      console.log('Connection disconnected normally');
    }
  });
});

// Monitor extension health
setInterval(() => {
  chrome.tabs.query({ url: '*://www.bing.com/*' }, (tabs) => {
    if (tabs.length > 0) {
      console.log(`Health check: ${tabs.length} Bing tab(s) open`);
    }
  });
}, 60000); // Check every minute

// Handle extension errors
chrome.runtime.onSuspend.addListener(() => {
  console.log('Extension suspending...');
});

chrome.runtime.onSuspendCanceled.addListener(() => {
  console.log('Extension suspension canceled');
});

// Rate limiting for content fetching
const urlFetchHistory = new Map();

function canFetchUrl(url) {
  try {
    const domain = new URL(url).hostname;
    const lastFetch = urlFetchHistory.get(domain);
    const now = Date.now();
    
    if (!lastFetch || (now - lastFetch) >= RATE_LIMIT_MS) {
      urlFetchHistory.set(domain, now);
      return true;
    }
    
    return false;
  } catch (error) {
    return true; // Allow if URL parsing fails
  }
}

// Clean up old rate limit entries periodically
setInterval(() => {
  const now = Date.now();
  const cutoff = now - (60 * 60 * 1000); // 1 hour ago
  
  for (const [domain, timestamp] of urlFetchHistory.entries()) {
    if (timestamp < cutoff) {
      urlFetchHistory.delete(domain);
    }
  }
}, 10 * 60 * 1000); // Clean every 10 minutes

// Export for debugging
if (typeof window !== 'undefined') {
  window.backgroundScript = {
    version: '2.0.0',
    status: 'active',
    features: ['content-extraction', 'rate-limiting']
  };
}