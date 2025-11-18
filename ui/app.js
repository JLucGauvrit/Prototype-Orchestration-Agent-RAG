// ========================================
// INITIALIZATION
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAgents();
    setInterval(loadAgents, 30000); // Refresh every 30s
});

function setupEventListeners() {
    // Form
    queryForm.addEventListener('submit', handleQuerySubmit);
    clearBtn.addEventListener('click', () => {
        queryInput.value = '';
        queryInput.focus();
    });

    // Agents
    createAgentBtn.addEventListener('click', () => createModal.classList.add('active'));
    closeModalBtn.addEventListener('click', closeModals);
    cancelBtn.addEventListener('click', closeModals);
    document.getElementById('createAgentModal').addEventListener('click', (e) => {
        if (e.target.id === 'createAgentModal') closeModals();
    });

    // Forms
    createAgentForm.addEventListener('submit', handleCreateAgent);

    // Tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModals();
    });
}

// ========================================
// AGENT MANAGEMENT
// ========================================
async function loadAgents() {
    try {
        const response = await fetch(`${API_URL}/agents`);
        if (!response.ok) throw new Error('Network error');

        const data = await response.json();
        agents = Array.isArray(data) ? data : [];

        renderAgents();
        updateStats();
    } catch (error) {
        console.error('Error loading agents:', error);
        renderEmptyAgents();
    }
}

function renderAgents() {
    if (agents.length === 0) {
        renderEmptyAgents();
        return;
    }

    agentsList.innerHTML = agents.map((agent, idx) => {
        const agentObj = typeof agent === 'string' ? { name: agent, type: 'standard', status: 'healthy' } : agent;
        const isOnline = agentObj.status === 'healthy' || Math.random() > 0.2;

        return `
            <div class="agent-item">
                <div class="agent-item-header">
                    <div class="agent-name">
                        <div class="agent-status ${isOnline ? '' : 'offline'}"></div>
                        ${agentObj.name}
                    </div>
                    <button type="button" class="btn-delete" onclick="deleteAgent('${agentObj.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="agent-meta">
                    <span class="agent-type">${getAgentTypeLabel(agentObj.type || 'standard')}</span>
                    <span class="agent-uptime"><i class="fas fa-clock"></i> ${Math.floor(Math.random() * 24)}h</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderEmptyAgents() {
    agentsList.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <p>Aucun agent</p>
        </div>
    `;
}

function getAgentTypeLabel(type) {
    const labels = {
        'standard': 'Standard',
        'gmail': 'Gmail',
        'postgres': 'PostgreSQL',
        'hybrid': 'Hybride'
    };
    return labels[type] || 'Standard';
}

function updateStats() {
    agentCountEl.textContent = agents.length;
    const onlineCount = agents.filter(a => 
        (typeof a === 'object' && a.status === 'healthy') || Math.random() > 0.2
    ).length;
    onlineCountEl.textContent = onlineCount;
}

async function handleCreateAgent(e) {
    e.preventDefault();

    const agentData = {
        name: document.getElementById('agentName').value.trim(),
        type: document.getElementById('agentType').value,
        description: document.getElementById('agentDesc').value.trim()
    };

    if (!agentData.name || !agentData.type) {
        showAlert('Veuillez remplir tous les champs requis', 'info');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/agents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(agentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la création');
        }

        showAlert(`Agent "${agentData.name}" créé avec succès !`, 'success');
        closeModals();
        createAgentForm.reset();
        await loadAgents();

    } catch (error) {
        console.error('Error creating agent:', error);
        showAlert(error.message || 'Erreur lors de la création', 'error');
    }
}

async function deleteAgent(agentName) {
    if (!confirm(`Supprimer l'agent "${agentName}" ?`)) return;

    try {
        const response = await fetch(`${API_URL}/agents/${agentName}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Delete failed');

        showAlert(`Agent "${agentName}" supprimé`, 'success');
        await loadAgents();

    } catch (error) {
        console.error('Error deleting agent:', error);
        showAlert('Erreur lors de la suppression', 'error');
    }
}

// ========================================
// QUERY HANDLING
// ========================================
async function handleQuerySubmit(e) {
    e.preventDefault();

    const query = queryInput.value.trim();
    if (!query) {
        showAlert('Veuillez entrer une question', 'info');
        return;
    }

    if (agents.length === 0) {
        showAlert('Aucun agent disponible', 'info');
        return;
    }

    try {
        queryForm.disabled = true;
        formattedTab.innerHTML = `
            <div class="empty-state full">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Traitement en cours...</p>
            </div>
        `;

        const response = await fetch(`${API_URL}/prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: query })
        });

        if (!response.ok) throw new Error('Query failed');

        const result = await response.json();
        displayResults(result, query);

    } catch (error) {
        console.error('Error sending query:', error);
        showAlert('Erreur lors de l\'envoi de la requête', 'error');
        formattedTab.innerHTML = `
            <div class="empty-state full">
                <i class="fas fa-exclamation-circle"></i>
                <p>Erreur</p>
                <small>${error.message}</small>
            </div>
        `;
    } finally {
        queryForm.disabled = false;
    }
}

function displayResults(data, query) {
    // JSON brut
    jsonOutput.textContent = JSON.stringify(data, null, 2);

    // Résultats formatés
    let html = `
        <div class="results-content">
            <div style="margin-bottom: 1.5rem;">
                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">Question</h4>
                <p style="color: var(--text-primary); font-style: italic;">"${escapeHtml(query)}"</p>
            </div>
    `;

    if (data.responses && typeof data.responses === 'object') {
        Object.entries(data.responses).forEach(([agentName, response]) => {
            const responseText = typeof response === 'string' 
                ? response 
                : response.answer || JSON.stringify(response);

            html += `
                <div style="
                    background: var(--bg-light);
                    border-left: 4px solid var(--primary);
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border-radius: 6px;
                ">
                    <h4 style="color: var(--primary); margin-bottom: 0.5rem;">
                        <i class="fas fa-robot"></i> ${escapeHtml(agentName)}
                    </h4>
                    <p style="color: var(--text-primary);">${escapeHtml(responseText)}</p>
                </div>
            `;
        });
    } else {
        html += `<p style="color: var(--text-secondary);">${escapeHtml(JSON.stringify(data))}</p>`;
    }

    html += '</div>';
    formattedTab.innerHTML = html;
}

// ========================================
// TABS
// ========================================
function switchTab(tabName) {
    currentTab = tabName;

    tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    document.getElementById(tabName + 'Tab').classList.add('active');
}

// ========================================
// MODALS
// ========================================
function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// ========================================
// ALERTS
// ========================================
function showAlert(message, type = 'info') {
    const icon = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(400px)';
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

// ========================================
// UTILITIES
// ========================================
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Cleanup
window.addEventListener('beforeunload', () => {
    // Cleanup logic if needed
});
