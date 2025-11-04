// State Management (in-memory only)
const state = {
  queryHistory: [],
  networkLog: [],
  logs: [],
  apiBaseUrl: 'http://localhost:8000',
  verboseMode: false,
  currentRequest: null,
  currentResponse: null,
  retryAttempts: 0,
  maxRetries: 3
};

// Error suggestions
const errorSuggestions = {
  'ECONNREFUSED': "Vérifiez que les conteneurs Docker sont en cours d'exécution avec 'docker-compose ps'",
  'Failed to fetch': "Vérifiez que les conteneurs Docker sont en cours d'exécution avec 'docker-compose ps'",
  'NetworkError': "Vérifiez que les conteneurs Docker sont en cours d'exécution avec 'docker-compose ps'",
  'invalid_model': "Le modèle spécifié est invalide. Utilisez 'sonar' au lieu de 'sonar-small-chat'",
  '401': "Vérifiez que la variable PERPLEXITY_API_KEY est correctement définie",
  'timeout': "Le serveur met trop de temps à répondre. Vérifiez les logs avec 'docker-compose logs'"
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
  setupEventListeners();
  updateTimestamp();
  setInterval(updateTimestamp, 1000);
});

function initializeApp() {
  addLog('Application initialisée', 'success');
  
  // Load saved config from memory
  const apiUrlInput = document.getElementById('apiBaseUrl');
  if (apiUrlInput) {
    apiUrlInput.value = state.apiBaseUrl;
  }
  
  // Initial health check
  setTimeout(() => performHealthCheck(), 1000);
}

function setupEventListeners() {
  // Query submission
  const sendBtn = document.getElementById('sendQueryBtn');
  const queryInput = document.getElementById('queryInput');
  
  sendBtn.addEventListener('click', handleSendQuery);
  
  // Keyboard shortcut: Ctrl+Enter to send
  queryInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSendQuery();
    }
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      handleClear();
    }
  });
  
  // Clear button
  const clearBtn = document.getElementById('clearBtn');
  clearBtn.addEventListener('click', handleClear);
  
  // Health check button
  const healthCheckBtn = document.getElementById('healthCheckBtn');
  healthCheckBtn.addEventListener('click', performHealthCheck);
  
  // Quick queries
  const quickQueryBtns = document.querySelectorAll('.quick-query-btn');
  quickQueryBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.dataset.query;
      queryInput.value = query;
      showToast('Requête chargée', 'success');
    });
  });
  
  // Tabs
  const tabButtons = document.querySelectorAll('.tab-button');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      switchTab(tabId);
    });
  });
  
  // Configuration
  const apiUrlInput = document.getElementById('apiBaseUrl');
  apiUrlInput.addEventListener('change', (e) => {
    state.apiBaseUrl = e.target.value;
    updateEndpointDisplay();
    addLog(`URL de base API changée: ${state.apiBaseUrl}`, 'info');
  });
  
  const verboseCheckbox = document.getElementById('verboseMode');
  verboseCheckbox.addEventListener('change', (e) => {
    state.verboseMode = e.target.checked;
    addLog(`Mode verbose ${state.verboseMode ? 'activé' : 'désactivé'}`, 'info');
  });
  
  // Clear logs button
  const clearLogsBtn = document.getElementById('clearLogsBtn');
  clearLogsBtn.addEventListener('click', () => {
    state.logs = [];
    updateLogsDisplay();
    showToast('Logs effacés', 'success');
  });
}

function updateTimestamp() {
  const timeEl = document.getElementById('currentTime');
  const now = new Date();
  timeEl.textContent = now.toLocaleString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function updateEndpointDisplay() {
  const endpointEl = document.getElementById('currentEndpoint');
  const target = document.getElementById('targetSelect').value;
  let endpoint = `${state.apiBaseUrl}/query`;
  if (target !== 'all') {
    endpoint += `?target=${target}`;
  }
  endpointEl.textContent = endpoint;
}

async function handleSendQuery() {
  const queryInput = document.getElementById('queryInput');
  const query = queryInput.value.trim();
  
  if (!query) {
    showToast('Veuillez entrer une requête', 'error');
    return;
  }
  
  const target = document.getElementById('targetSelect').value;
  
  // Add to history
  addToHistory(query);
  
  // Show loading state
  setLoadingState(true);
  
  // Prepare request
  const requestData = {
    query: query,
    target: target !== 'all' ? target : undefined
  };
  
  const startTime = Date.now();
  
  try {
    addLog(`Envoi de la requête: ${query}`, 'info');
    
    const response = await fetchWithRetry(`${state.apiBaseUrl}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    });
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    const responseData = await response.json();
    
    // Store request/response
    state.currentRequest = {
      method: 'POST',
      url: `${state.apiBaseUrl}/query`,
      headers: { 'Content-Type': 'application/json' },
      body: requestData,
      timestamp: new Date().toISOString()
    };
    
    state.currentResponse = {
      status: response.status,
      statusText: response.ok ? 'OK' : 'Error',
      data: responseData,
      duration: duration,
      timestamp: new Date().toISOString()
    };
    
    // Add to network log
    addNetworkLogEntry({
      endpoint: '/query',
      status: response.status,
      duration: duration,
      success: response.ok
    });
    
    // Update displays
    updateRequestDisplay();
    updateResponseDisplay();
    displayResponse(responseData, duration, response.status);
    
    if (response.ok) {
      addLog('Requête réussie', 'success');
      showToast('Réponse reçue avec succès', 'success');
      updateServiceStatus('mcp', true);
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
  } catch (error) {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    addLog(`Erreur: ${error.message}`, 'error');
    
    // Add to network log
    addNetworkLogEntry({
      endpoint: '/query',
      status: 0,
      duration: duration,
      success: false,
      error: error.message
    });
    
    displayError(error, duration);
    updateServiceStatus('mcp', false);
    showToast(`Erreur: ${error.message}`, 'error');
  } finally {
    setLoadingState(false);
    state.retryAttempts = 0;
  }
}

async function fetchWithRetry(url, options, attempt = 0) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout
    
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    return response;
    
  } catch (error) {
    if (attempt < state.maxRetries && error.name !== 'AbortError') {
      const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
      addLog(`Tentative ${attempt + 1}/${state.maxRetries} échouée. Nouvelle tentative dans ${delay}ms...`, 'warning');
      
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, attempt + 1);
    }
    throw error;
  }
}

function displayResponse(data, duration, statusCode) {
  // Switch to aggregated tab
  switchTab('aggregated');
  
  // Display aggregated response
  const aggregatedContainer = document.getElementById('response-aggregated');
  aggregatedContainer.innerHTML = createResponseHTML(
    data.response || data.message || JSON.stringify(data, null, 2),
    duration,
    statusCode,
    'Réponse Agrégée'
  );
  
  // Try to parse individual agent responses
  if (data.response) {
    const agentResponses = parseAgentResponses(data.response);
    
    // Display Agent A response
    const agentAContainer = document.getElementById('response-agent-a');
    agentAContainer.innerHTML = createResponseHTML(
      agentResponses.agentA || 'Aucune réponse',
      duration,
      statusCode,
      'Agent A'
    );
    
    // Display Agent B response
    const agentBContainer = document.getElementById('response-agent-b');
    agentBContainer.innerHTML = createResponseHTML(
      agentResponses.agentB || 'Aucune réponse',
      duration,
      statusCode,
      'Agent B'
    );
    
    // Display Agent C response
    const agentCContainer = document.getElementById('response-agent-c');
    agentCContainer.innerHTML = createResponseHTML(
      agentResponses.agentC || 'Aucune réponse',
      duration,
      statusCode,
      'Agent C'
    );
  }
  
  // Display raw JSON
  const rawContainer = document.getElementById('response-raw');
  rawContainer.innerHTML = createResponseHTML(
    JSON.stringify(data, null, 2),
    duration,
    statusCode,
    'JSON Brut',
    true
  );
}

function parseAgentResponses(responseText) {
  const responses = {
    agentA: '',
    agentB: '',
    agentC: ''
  };
  
  // Try to parse format: "AgentA: message\nAgentB: message\nAgentC: message"
  const lines = responseText.split('\n');
  
  lines.forEach(line => {
    if (line.startsWith('AgentA:') || line.startsWith('Agent A:')) {
      responses.agentA = line.replace(/^Agent\s*A:\s*/i, '').trim();
    } else if (line.startsWith('AgentB:') || line.startsWith('Agent B:')) {
      responses.agentB = line.replace(/^Agent\s*B:\s*/i, '').trim();
    } else if (line.startsWith('AgentC:') || line.startsWith('Agent C:')) {
      responses.agentC = line.replace(/^Agent\s*C:\s*/i, '').trim();
    }
  });
  
  // If no parsing succeeded, return empty
  if (!responses.agentA && !responses.agentB && !responses.agentC) {
    return {
      agentA: responseText,
      agentB: '',
      agentC: ''
    };
  }
  
  return responses;
}

function createResponseHTML(content, duration, statusCode, title, isJson = false) {
  const copyBtn = `<button class="copy-btn" onclick="copyToClipboard('${escapeHtml(content)}', event)">📋 Copier</button>`;
  
  return `
    <div class="response-item">
      <div class="response-header">
        <div class="response-meta">
          <span><strong>${title}</strong></span>
          <span>⏱️ ${duration}ms</span>
          <span class="status-code ${statusCode >= 200 && statusCode < 300 ? 'success' : 'error'}">${statusCode}</span>
        </div>
        ${copyBtn}
      </div>
      <div class="response-content ${isJson ? 'json' : ''}">${escapeHtml(content)}</div>
    </div>
  `;
}

function displayError(error, duration) {
  switchTab('aggregated');
  
  const suggestion = findErrorSuggestion(error.message);
  const errorHTML = `
    <div class="response-item response-error">
      <div class="response-header">
        <div class="response-meta">
          <span><strong>❌ Erreur</strong></span>
          <span>⏱️ ${duration}ms</span>
        </div>
      </div>
      <div class="response-content">
        <strong>Message d'erreur:</strong>\n${escapeHtml(error.message)}\n\n
        ${error.stack ? `<strong>Stack trace:</strong>\n${escapeHtml(error.stack)}\n\n` : ''}
        ${suggestion ? `<strong>💡 Suggestion:</strong>\n${escapeHtml(suggestion)}` : ''}
      </div>
    </div>
  `;
  
  document.getElementById('response-aggregated').innerHTML = errorHTML;
  document.getElementById('response-agent-a').innerHTML = '<div class="empty-state">Erreur lors de la requête</div>';
  document.getElementById('response-agent-b').innerHTML = '<div class="empty-state">Erreur lors de la requête</div>';
  document.getElementById('response-agent-c').innerHTML = '<div class="empty-state">Erreur lors de la requête</div>';
  document.getElementById('response-raw').innerHTML = errorHTML;
}

function findErrorSuggestion(errorMessage) {
  for (const [key, suggestion] of Object.entries(errorSuggestions)) {
    if (errorMessage.includes(key)) {
      return suggestion;
    }
  }
  return null;
}

function updateRequestDisplay() {
  const requestDetails = document.getElementById('requestDetails');
  
  if (!state.currentRequest) {
    requestDetails.innerHTML = '<div class="empty-state">Aucune requête envoyée</div>';
    return;
  }
  
  const req = state.currentRequest;
  requestDetails.innerHTML = `
    <div class="detail-item">
      <div class="detail-label">Méthode:</div>
      <div class="detail-value">${req.method}</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">URL:</div>
      <div class="detail-value">${req.url}</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Headers:</div>
      <div class="detail-value">${JSON.stringify(req.headers, null, 2)}</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Body:</div>
      <div class="detail-value">${JSON.stringify(req.body, null, 2)}</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Timestamp:</div>
      <div class="detail-value">${new Date(req.timestamp).toLocaleString('fr-FR')}</div>
    </div>
  `;
}

function updateResponseDisplay() {
  const responseDetails = document.getElementById('responseDetails');
  
  if (!state.currentResponse) {
    responseDetails.innerHTML = '<div class="empty-state">Aucune réponse reçue</div>';
    return;
  }
  
  const res = state.currentResponse;
  responseDetails.innerHTML = `
    <div class="detail-item">
      <div class="detail-label">Status Code:</div>
      <div class="detail-value">
        <span class="status-code ${res.status >= 200 && res.status < 300 ? 'success' : 'error'}">${res.status} ${res.statusText}</span>
      </div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Temps de réponse:</div>
      <div class="detail-value">${res.duration}ms</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Content-Type:</div>
      <div class="detail-value">application/json</div>
    </div>
    <div class="detail-item">
      <div class="detail-label">Timestamp:</div>
      <div class="detail-value">${new Date(res.timestamp).toLocaleString('fr-FR')}</div>
    </div>
  `;
}

function addNetworkLogEntry(entry) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    ...entry
  };
  
  state.networkLog.unshift(logEntry);
  if (state.networkLog.length > 20) {
    state.networkLog = state.networkLog.slice(0, 20);
  }
  
  updateNetworkLogDisplay();
}

function updateNetworkLogDisplay() {
  const networkLog = document.getElementById('networkLog');
  
  if (state.networkLog.length === 0) {
    networkLog.innerHTML = '<div class="empty-state">Aucune activité réseau</div>';
    return;
  }
  
  networkLog.innerHTML = state.networkLog.map(entry => {
    const time = new Date(entry.timestamp).toLocaleTimeString('fr-FR');
    const statusClass = entry.success ? 'success' : 'error';
    return `
      <div class="log-entry ${statusClass}">
        <span class="log-time">${time}</span>
        <strong>${entry.endpoint}</strong> - 
        Status: ${entry.status} - 
        ${entry.duration}ms
        ${entry.error ? `<br/>❌ ${entry.error}` : ''}
      </div>
    `;
  }).join('');
}

function addToHistory(query) {
  state.queryHistory.unshift(query);
  if (state.queryHistory.length > 10) {
    state.queryHistory = state.queryHistory.slice(0, 10);
  }
  updateHistoryDisplay();
}

function updateHistoryDisplay() {
  const historySection = document.getElementById('queryHistorySection');
  const historyContainer = document.getElementById('queryHistory');
  
  if (state.queryHistory.length === 0) {
    historySection.style.display = 'none';
    return;
  }
  
  historySection.style.display = 'block';
  historyContainer.innerHTML = state.queryHistory.map(query => `
    <div class="history-item" onclick="loadQueryFromHistory('${escapeHtml(query)}')">
      ${escapeHtml(query.substring(0, 100))}${query.length > 100 ? '...' : ''}
    </div>
  `).join('');
}

function loadQueryFromHistory(query) {
  document.getElementById('queryInput').value = query;
  showToast('Requête chargée depuis l\'historique', 'success');
}

function switchTab(tabId) {
  // Update buttons
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  
  // Update panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });
}

function handleClear() {
  document.getElementById('queryInput').value = '';
  showToast('Champ de requête effacé', 'success');
}

function setLoadingState(loading) {
  const sendBtn = document.getElementById('sendQueryBtn');
  const btnText = sendBtn.querySelector('.btn-text');
  const btnLoader = sendBtn.querySelector('.btn-loader');
  
  if (loading) {
    sendBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
  } else {
    sendBtn.disabled = false;
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
  }
}

async function performHealthCheck() {
  addLog('Vérification de la santé des services...', 'info');
  
  const services = [
    { id: 'mcp', url: `${state.apiBaseUrl}/health`, name: 'MCP Server' },
    // Note: Direct agent checks won't work from browser due to CORS
    // These would need to be proxied through the MCP server
  ];
  
  for (const service of services) {
    const healthItem = document.querySelector(`.health-item[data-service="${service.id}"]`);
    const statusSpan = healthItem.querySelector('.health-status');
    
    statusSpan.textContent = '⏳';
    
    try {
      const response = await fetch(service.url, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        statusSpan.textContent = '✅';
        updateServiceStatus(service.id, true);
        addLog(`${service.name} est en ligne`, 'success');
      } else {
        statusSpan.textContent = '❌';
        updateServiceStatus(service.id, false);
        addLog(`${service.name} a retourné le statut ${response.status}`, 'error');
      }
    } catch (error) {
      statusSpan.textContent = '❌';
      updateServiceStatus(service.id, false);
      addLog(`${service.name} est hors ligne: ${error.message}`, 'error');
    }
  }
  
  showToast('Vérification de santé terminée', 'info');
}

function updateServiceStatus(serviceId, isConnected) {
  const indicator = document.querySelector(`.status-indicator[data-service="${serviceId}"]`);
  if (indicator) {
    indicator.classList.toggle('connected', isConnected);
    indicator.classList.toggle('error', !isConnected);
  }
}

function addLog(message, type = 'info') {
  const logEntry = {
    timestamp: new Date().toISOString(),
    message,
    type
  };
  
  state.logs.unshift(logEntry);
  if (state.logs.length > 50) {
    state.logs = state.logs.slice(0, 50);
  }
  
  if (state.verboseMode) {
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
  
  updateLogsDisplay();
}

function updateLogsDisplay() {
  const logsContainer = document.getElementById('logsContainer');
  
  if (state.logs.length === 0) {
    logsContainer.innerHTML = '<div class="empty-state">Aucun log</div>';
    return;
  }
  
  logsContainer.innerHTML = state.logs.map(log => {
    const time = new Date(log.timestamp).toLocaleTimeString('fr-FR');
    return `
      <div class="log-message ${log.type}">
        <span style="color: var(--color-text-secondary);">[${time}]</span> ${escapeHtml(log.message)}
      </div>
    `;
  }).join('');
}

function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function copyToClipboard(text, event) {
  event.stopPropagation();
  
  // Create a temporary textarea
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  
  try {
    document.execCommand('copy');
    showToast('Copié dans le presse-papiers', 'success');
  } catch (err) {
    showToast('Erreur lors de la copie', 'error');
  }
  
  document.body.removeChild(textarea);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Update endpoint display when target changes
document.addEventListener('DOMContentLoaded', () => {
  const targetSelect = document.getElementById('targetSelect');
  if (targetSelect) {
    targetSelect.addEventListener('change', updateEndpointDisplay);
    updateEndpointDisplay();
  }
});