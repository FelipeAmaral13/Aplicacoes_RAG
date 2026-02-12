// Application State
const state = {
    analyzedCount: 0,
    threatsCount: 0,
    isAnalyzing: false
};

// DOM Elements
const elements = {
    logInput: document.getElementById('logInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    loadSampleBtn: document.getElementById('loadSampleBtn'),
    charCount: document.getElementById('charCount'),
    resultsSection: document.getElementById('resultsSection'),
    cleanedLogs: document.getElementById('cleanedLogs'),
    analysisReport: document.getElementById('analysisReport'),
    retrievedContext: document.getElementById('retrievedContext'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    analyzedCountEl: document.getElementById('analyzedCount'),
    threatsCountEl: document.getElementById('threatsCount'),
    suspiciousCount: document.getElementById('suspiciousCount'),
    copyReportBtn: document.getElementById('copyReportBtn'),
    downloadReportBtn: document.getElementById('downloadReportBtn'),
    contextHeader: document.getElementById('contextHeader'),
    contextBody: document.getElementById('contextBody')
};

// Toast Notification System
class ToastManager {
    constructor() {
        this.container = document.getElementById('toastContainer');
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getIcon(type);
        
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-message">${message}</div>
        `;
        
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            info: 'ℹ',
            warning: '⚠'
        };
        return icons[type] || icons.info;
    }
}

const toast = new ToastManager();

// Markdown Parser (Simple)
function parseMarkdown(text) {
    if (!text) return '';
    
    let html = text
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code blocks
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // Inline code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Lists
        .replace(/^\- (.+)$/gim, '<li>$1</li>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Wrap in paragraphs
    html = '<p>' + html + '</p>';
    
    return html;
}

// API Calls
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            elements.statusDot.style.background = 'var(--success)';
            elements.statusText.textContent = 'Online';
            return true;
        }
    } catch (error) {
        elements.statusDot.style.background = 'var(--danger)';
        elements.statusText.textContent = 'Offline';
        console.error('Health check failed:', error);
        return false;
    }
}

async function loadSampleLogs() {
    try {
        const response = await fetch('/api/sample');
        const data = await response.json();
        elements.logInput.value = data.sample_logs;
        updateCharCount();
        toast.show('Sample logs loaded successfully', 'success');
    } catch (error) {
        console.error('Error loading sample:', error);
        toast.show('Failed to load sample logs', 'error');
    }
}

async function analyzeLogs() {
    const logs = elements.logInput.value.trim();
    
    if (!logs) {
        toast.show('Please enter some logs to analyze', 'warning');
        return;
    }
    
    if (state.isAnalyzing) {
        toast.show('Analysis already in progress', 'warning');
        return;
    }
    
    state.isAnalyzing = true;
    elements.loadingOverlay.style.display = 'flex';
    elements.analyzeBtn.disabled = true;
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ logs })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }
        
        displayResults(data.results);
        updateStats();
        toast.show('Analysis completed successfully', 'success');
        
    } catch (error) {
        console.error('Analysis error:', error);
        toast.show(error.message || 'Failed to analyze logs', 'error');
    } finally {
        state.isAnalyzing = false;
        elements.loadingOverlay.style.display = 'none';
        elements.analyzeBtn.disabled = false;
    }
}

function displayResults(results) {
    // Show results section
    elements.resultsSection.style.display = 'block';
    
    // Scroll to results
    setTimeout(() => {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // Display cleaned logs
    elements.cleanedLogs.textContent = results.cleaned_logs || 'No suspicious activity detected.';
    
    // Count suspicious lines
    const lines = results.cleaned_logs.split('\n').filter(line => line.trim()).length;
    elements.suspiciousCount.textContent = `${lines} events`;
    
    // Display analysis report with markdown parsing
    elements.analysisReport.innerHTML = parseMarkdown(results.analysis_report);
    
    // Display retrieved context
    elements.retrievedContext.textContent = results.retrieved_context || 'No context retrieved.';
    
    // Update threat count
    state.threatsCount += lines;
}

function updateStats() {
    state.analyzedCount++;
    elements.analyzedCountEl.textContent = state.analyzedCount;
    elements.threatsCountEl.textContent = state.threatsCount;
}

function updateCharCount() {
    const count = elements.logInput.value.length;
    elements.charCount.textContent = count.toLocaleString();
}

function copyReport() {
    const reportText = elements.analysisReport.innerText;
    
    navigator.clipboard.writeText(reportText)
        .then(() => {
            toast.show('Report copied to clipboard', 'success');
        })
        .catch(err => {
            console.error('Copy failed:', err);
            toast.show('Failed to copy report', 'error');
        });
}

function downloadReport() {
    const reportText = elements.analysisReport.innerText;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `threat-analysis-${timestamp}.txt`;
    
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.show('Report downloaded successfully', 'success');
}

function toggleContext() {
    const contextCard = elements.contextHeader.parentElement;
    const isCollapsed = contextCard.classList.contains('collapsed');
    
    if (isCollapsed) {
        contextCard.classList.remove('collapsed');
        elements.contextBody.style.display = 'block';
    } else {
        contextCard.classList.add('collapsed');
        elements.contextBody.style.display = 'none';
    }
}

// Event Listeners
elements.analyzeBtn.addEventListener('click', analyzeLogs);
elements.loadSampleBtn.addEventListener('click', loadSampleLogs);
elements.logInput.addEventListener('input', updateCharCount);
elements.copyReportBtn.addEventListener('click', copyReport);
elements.downloadReportBtn.addEventListener('click', downloadReportBtn);
elements.contextHeader.addEventListener('click', toggleContext);

// Keyboard shortcuts
elements.logInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        analyzeLogs();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    updateCharCount();
    
    // Check health periodically
    setInterval(checkHealth, 30000); // Every 30 seconds
    
    // Add some visual feedback
    console.log('%c🛡️ ThreatRAG Sentinel', 'font-size: 24px; color: #667eea; font-weight: bold;');
    console.log('%cSecurity Log Analyzer Initialized', 'color: #a0a0b8;');
});

// Add typing effect for better UX
let typingTimer;
elements.logInput.addEventListener('input', () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        const lineCount = elements.logInput.value.split('\n').filter(l => l.trim()).length;
        if (lineCount > 0) {
            console.log(`📝 ${lineCount} log entries ready for analysis`);
        }
    }, 1000);
});

// Export for debugging
window.app = {
    state,
    elements,
    toast,
    analyzeLogs,
    loadSampleLogs,
    checkHealth
};
