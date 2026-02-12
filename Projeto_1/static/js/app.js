// Estado da aplicação
const state = {
    sessionId: null,
    fileName: null,
    isProcessing: false
};

// Elementos do DOM
const elements = {
    fileInput: document.getElementById('file-input'),
    fileInfo: document.getElementById('file-info'),
    fileName: document.getElementById('file-name'),
    removeFile: document.getElementById('remove-file'),
    uploadBtn: document.getElementById('upload-btn'),
    uploadStatus: document.getElementById('upload-status'),
    uploadSection: document.getElementById('upload-section'),
    chatSection: document.getElementById('chat-section'),
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    newDocumentBtn: document.getElementById('new-document-btn'),
    documentName: document.getElementById('document-name'),
    loadingOverlay: document.getElementById('loading-overlay')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    autoResizeTextarea();
});

// Configurar event listeners
function setupEventListeners() {
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.removeFile.addEventListener('click', handleFileRemove);
    elements.uploadBtn.addEventListener('click', handleFileUpload);
    elements.sendBtn.addEventListener('click', handleSendMessage);
    elements.chatInput.addEventListener('input', handleInputChange);
    elements.chatInput.addEventListener('keydown', handleKeyPress);
    elements.newDocumentBtn.addEventListener('click', handleNewDocument);
}

// Handle file selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    
    if (!file) return;
    
    // Verificar tipo de arquivo
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatus('Apenas arquivos PDF são permitidos', 'error');
        elements.fileInput.value = '';
        return;
    }
    
    // Verificar tamanho (16MB)
    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
        showStatus('Arquivo muito grande. Tamanho máximo: 16MB', 'error');
        elements.fileInput.value = '';
        return;
    }
    
    // Mostrar informações do arquivo
    elements.fileName.textContent = file.name;
    elements.fileInfo.classList.remove('hidden');
    elements.uploadBtn.classList.remove('hidden');
    elements.uploadStatus.classList.add('hidden');
}

// Handle file removal
function handleFileRemove() {
    elements.fileInput.value = '';
    elements.fileInfo.classList.add('hidden');
    elements.uploadBtn.classList.add('hidden');
    elements.uploadStatus.classList.add('hidden');
}

// Handle file upload
async function handleFileUpload() {
    const file = elements.fileInput.files[0];
    
    if (!file) {
        showStatus('Nenhum arquivo selecionado', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        state.isProcessing = true;
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            state.sessionId = data.session_id;
            state.fileName = data.filename;
            
            showStatus(data.message, 'success');
            
            // Aguardar 1 segundo e mostrar chat
            setTimeout(() => {
                showChatSection();
            }, 1000);
        } else {
            showStatus(data.error || 'Erro ao processar arquivo', 'error');
        }
    } catch (error) {
        console.error('Erro no upload:', error);
        showStatus('Erro de conexão. Tente novamente.', 'error');
    } finally {
        showLoading(false);
        state.isProcessing = false;
    }
}

// Mostrar seção de chat
function showChatSection() {
    elements.uploadSection.classList.add('hidden');
    elements.chatSection.classList.remove('hidden');
    elements.documentName.textContent = state.fileName;
    elements.chatInput.focus();
}

// Handle input changes
function handleInputChange() {
    const hasText = elements.chatInput.value.trim().length > 0;
    elements.sendBtn.disabled = !hasText || state.isProcessing;
}

// Handle key press
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!elements.sendBtn.disabled) {
            handleSendMessage();
        }
    }
}

// Handle send message
async function handleSendMessage() {
    const message = elements.chatInput.value.trim();
    
    if (!message || state.isProcessing) return;
    
    // Limpar input
    elements.chatInput.value = '';
    handleInputChange();
    
    // Adicionar mensagem do usuário
    addMessage('user', message);
    
    try {
        state.isProcessing = true;
        elements.sendBtn.disabled = true;
        
        // Adicionar indicador de digitação
        const typingId = addTypingIndicator();
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remover indicador de digitação
        removeTypingIndicator(typingId);
        
        if (response.ok && data.success) {
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', `❌ ${data.error || 'Erro ao processar mensagem'}`, true);
        }
    } catch (error) {
        console.error('Erro no chat:', error);
        removeTypingIndicator();
        addMessage('assistant', '❌ Erro de conexão. Tente novamente.', true);
    } finally {
        state.isProcessing = false;
        handleInputChange();
    }
}

// Adicionar mensagem ao chat
function addMessage(role, content, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const now = new Date();
    const time = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    
    const avatar = role === 'user' ? 'U' : '🤖';
    const roleName = role === 'user' ? 'Você' : 'Assistente';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-role">${roleName}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text ${isError ? 'error' : ''}">${escapeHtml(content)}</div>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Adicionar indicador de digitação
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-role">Assistente</span>
            </div>
            <div class="message-text">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;
    
    elements.chatMessages.appendChild(typingDiv);
    scrollToBottom();
    
    return 'typing-indicator';
}

// Remover indicador de digitação
function removeTypingIndicator(id = 'typing-indicator') {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

// Handle new document
async function handleNewDocument() {
    if (!confirm('Deseja carregar um novo documento? O chat atual será perdido.')) {
        return;
    }
    
    try {
        showLoading(true);
        
        await fetch('/api/clear', {
            method: 'POST'
        });
        
        // Reset state
        state.sessionId = null;
        state.fileName = null;
        state.isProcessing = false;
        
        // Reset UI
        elements.fileInput.value = '';
        elements.fileInfo.classList.add('hidden');
        elements.uploadBtn.classList.add('hidden');
        elements.uploadStatus.classList.add('hidden');
        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <h3>👋 Olá!</h3>
                <p>Seu documento foi processado com sucesso. Faça perguntas sobre o conteúdo e receba respostas precisas baseadas no texto.</p>
            </div>
        `;
        
        elements.chatSection.classList.add('hidden');
        elements.uploadSection.classList.remove('hidden');
    } catch (error) {
        console.error('Erro ao limpar sessão:', error);
        alert('Erro ao limpar sessão. Recarregue a página.');
    } finally {
        showLoading(false);
    }
}

// Mostrar status
function showStatus(message, type) {
    elements.uploadStatus.textContent = message;
    elements.uploadStatus.className = `status-message ${type}`;
    elements.uploadStatus.classList.remove('hidden');
}

// Mostrar/ocultar loading overlay
function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Scroll para o final do chat
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Auto-resize textarea
function autoResizeTextarea() {
    elements.chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// CSS adicional para typing indicator
const style = document.createElement('style');
style.textContent = `
    .typing-indicator .message-text {
        display: flex;
        gap: 4px;
        padding: 0.75rem 1rem;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-tertiary);
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
