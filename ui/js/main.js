// Constantes
const API_URL = 'http://orchestrator:8000';

// État global
let isProcessing = false;

// Éléments du DOM
const elements = {
    form: document.getElementById('queryForm'),
    textarea: document.getElementById('query'),
    submitButton: document.getElementById('submitBtn'),
    responseContainer: document.getElementById('response'),
    errorContainer: document.getElementById('errorContainer')
};

// Gestionnaires d'événements
document.addEventListener('DOMContentLoaded', () => {
    elements.form.addEventListener('submit', handleSubmit);
    elements.textarea.addEventListener('input', handleTextareaInput);
});

// Gestion de la soumission du formulaire
async function handleSubmit(event) {
    event.preventDefault();
    
    if (isProcessing) return;
    
    const query = elements.textarea.value.trim();
    if (!query) {
        showError('Veuillez entrer une question');
        return;
    }
    
    try {
        setLoading(true);
        const result = await sendQuery(query);
        displayResponse(result);
        elements.textarea.value = '';
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

// Envoi de la requête à l'API
async function sendQuery(query) {
    try {
        const response = await fetch(`${API_URL}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        throw new Error('Erreur de communication avec le serveur');
    }
}

// Affichage de la réponse
function displayResponse(data) {
    const responseHtml = `
        <div class="response-card">
            <div class="synthesized-response">
                <h2 class="text-xl font-semibold mb-4">Réponse Synthétisée</h2>
                <div class="whitespace-pre-wrap">${escapeHtml(data.synthesized_response)}</div>
            </div>
            
            <h3 class="text-lg font-semibold mb-3">Réponses des Agents</h3>
            <div class="space-y-4">
                ${data.agent_responses.map(agent => createAgentResponseHtml(agent)).join('')}
            </div>
        </div>
    `;

    elements.responseContainer.insertAdjacentHTML('afterbegin', responseHtml);
}

// Création du HTML pour la réponse d'un agent
function createAgentResponseHtml(agent) {
    return `
        <div class="agent-response">
            <div class="agent-header">
                <span class="agent-name">${escapeHtml(agent.agent_name)}</span>
                <span class="agent-specialty">${escapeHtml(agent.specialty)}</span>
            </div>
            <div class="confidence-badge">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Confiance: ${(agent.confidence * 100).toFixed(0)}%
            </div>
            <div class="mt-3 whitespace-pre-wrap">${escapeHtml(agent.response)}</div>
            ${createSourcesHtml(agent.sources)}
        </div>
    `;
}

// Création du HTML pour les sources
function createSourcesHtml(sources) {
    if (!sources || sources.length === 0) return '';
    
    return `
        <div class="sources-accordion">
            <button class="sources-button" onclick="toggleSources(this)">
                <svg class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
                Sources (${sources.length})
            </button>
            <div class="sources-content hidden">
                ${sources.map(source => `
                    <div class="source-item">
                        <span class="w-2 h-2 rounded-full bg-primary"></span>
                        <span>${escapeHtml(source.content)}</span>
                        <span class="ml-auto text-sm">${(source.similarity * 100).toFixed(0)}%</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Gestion des états de chargement
function setLoading(loading) {
    isProcessing = loading;
    elements.submitButton.disabled = loading;
    
    if (loading) {
        elements.submitButton.innerHTML = `
            <span class="loading-spinner"></span>
            <span>Traitement en cours...</span>
        `;
    } else {
        elements.submitButton.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
            <span>Envoyer</span>
        `;
    }
}

// Gestion des erreurs
function showError(message) {
    const errorHtml = `
        <div class="error-message">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            ${escapeHtml(message)}
        </div>
    `;
    
    elements.errorContainer.innerHTML = errorHtml;
    setTimeout(() => {
        elements.errorContainer.innerHTML = '';
    }, 5000);
}

// Gestion du textarea
function handleTextareaInput(event) {
    const textarea = event.target;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Toggle des sources
function toggleSources(button) {
    const content = button.nextElementSibling;
    const arrow = button.querySelector('svg');
    
    content.classList.toggle('hidden');
    arrow.style.transform = content.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
}

// Utilitaires
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}