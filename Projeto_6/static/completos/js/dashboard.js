/**
 * dashboard.js
 * Responsável por:
 *  - Relógio em tempo real
 *  - Contadores de logs e alertas
 *  - Consumo do SSE (/stream)
 *  - Atualização dinâmica das tabelas e painel de fix
 */

// ── Constantes ──────────────────────────────────────────────
const MAX_TABLE_ROWS = 30;

// ── Estado inicial injetado pelo servidor via Jinja2 ────────
let logCount   = window.INITIAL_LOG_COUNT   || 0;
let alertCount = window.INITIAL_ALERT_COUNT || 0;

// ── Referências DOM ─────────────────────────────────────────
const clockEl     = document.getElementById('clock');
const logCountEl  = document.getElementById('log-count');
const alertCountEl= document.getElementById('alert-count');
const logBody     = document.getElementById('log-body');
const alertBody   = document.getElementById('alert-body');
const fixArea     = document.getElementById('fix-area');
const fixBadge    = document.getElementById('fix-badge');

// ============================================================
// Relógio
// ============================================================
function tick() {
  clockEl.textContent = new Date().toLocaleTimeString('pt-BR');
}
tick();
setInterval(tick, 1000);

// ============================================================
// Utilitários
// ============================================================

/**
 * Atualiza o texto de um badge de contagem.
 * @param {HTMLElement} el - Elemento do badge
 * @param {number} n - Valor atual
 * @param {string} singular - Label no singular
 * @param {string} plural - Label no plural
 */
function updateBadge(el, n, singular, plural) {
  el.textContent = `${n} ${n === 1 ? singular : plural}`;
}

/**
 * Insere uma linha no topo de uma tbody e limita o total de linhas.
 * @param {HTMLElement} tbody
 * @param {string} html - innerHTML da <tr>
 */
function prependRow(tbody, html) {
  const tr = document.createElement('tr');
  tr.innerHTML = html;
  tbody.insertBefore(tr, tbody.firstChild);
  while (tbody.rows.length > MAX_TABLE_ROWS) {
    tbody.deleteRow(tbody.rows.length - 1);
  }
}

/**
 * Escapa caracteres HTML para exibição segura de código.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ============================================================
// Inicialização dos badges com estado do servidor
// ============================================================
updateBadge(logCountEl,   logCount,   'evento',  'eventos');
updateBadge(alertCountEl, alertCount, 'alerta',  'alertas');

// ============================================================
// Handlers de evento SSE
// ============================================================

/**
 * Processa um pacote do tipo LOG recebido via SSE.
 * @param {Object} d - Dados do log
 */
function handleLog(d) {
  const msg = d.raw_log || d.message || '';
  prependRow(logBody, `
    <td class="ts">${d.timestamp || '--'}</td>
    <td class="src">${d.source   || ''}</td>
    <td class="msg">${msg}</td>
  `);
  logCount++;
  updateBadge(logCountEl, logCount, 'evento', 'eventos');
}

/**
 * Processa um pacote do tipo ALERT recebido via SSE.
 * @param {Object} d - Dados do alerta
 */
function handleAlert(d) {
  const t   = d.triage      || {};
  const rem = d.remediation || null;
  const sev = t.severity    || 'LOW';

  // Insere linha na tabela de alertas
  prependRow(alertBody, `
    <td class="ts">${d.received_at || '--'}</td>
    <td><span class="sev sev-${sev}">${sev}</span></td>
    <td class="src">${t.category  || ''}</td>
    <td class="msg">${(t.reasoning || '').substring(0, 80)}</td>
  `);

  alertCount++;
  updateBadge(alertCountEl, alertCount, 'alerta', 'alertas');

  // Atualiza contador de severidade no card do topo
  const sevCountEl = document.getElementById(`cnt-${sev}`);
  if (sevCountEl) {
    sevCountEl.textContent = parseInt(sevCountEl.textContent || '0') + 1;
  }

  // Atualiza o painel de fix
  updateFixPanel(sev, rem);
}

/**
 * Atualiza o painel inferior de AI Auto-Fix.
 * @param {string} sev - Severidade da ameaça
 * @param {Object|null} rem - Objeto de remediação (ou null)
 */
function updateFixPanel(sev, rem) {
  if (rem) {
    // ── Fix automático disponível ──
    fixBadge.textContent        = '✓ fix gerado';
    fixBadge.style.background   = 'rgba(0,255,136,.12)';
    fixBadge.style.color        = 'var(--green)';
    fixBadge.style.borderColor  = 'rgba(0,255,136,.3)';
    fixArea.className = 'fix-content';
    fixArea.innerHTML = `
      <div class="fix-block">
        <div class="fix-section">
          <label>📋 Plano de Ação</label>
          <p>${rem.action_plan || ''}</p>
        </div>
        <div class="fix-section">
          <label>💻 Comando / Código</label>
          <div class="code-block">${escapeHtml(rem.code_fix)}</div>
        </div>
      </div>`;
  } else {
    // ── Revisão manual necessária ──
    const borderClass = ['HIGH', 'CRITICAL'].includes(sev) ? 'crit' : 'medium';
    fixBadge.textContent        = '⚠ revisão manual';
    fixBadge.style.background   = 'rgba(255,136,0,.12)';
    fixBadge.style.color        = 'var(--orange)';
    fixBadge.style.borderColor  = 'rgba(255,136,0,.3)';
    fixArea.className = 'fix-content';
    fixArea.innerHTML = `
      <div class="manual-review ${borderClass}">
        <span>⚠</span>
        <span>Ameaça detectada (${sev}) — Nenhum fix automático disponível para esta categoria.
        Revisão manual necessária.</span>
      </div>`;
  }
}

// ============================================================
// Server-Sent Events
// ============================================================
const evtSource = new EventSource('/stream');

evtSource.addEventListener('log', e => {
  try {
    handleLog(JSON.parse(e.data));
  } catch (err) {
    console.error('[SSE] Erro ao processar log:', err);
  }
});

evtSource.addEventListener('alert', e => {
  try {
    handleAlert(JSON.parse(e.data));
  } catch (err) {
    console.error('[SSE] Erro ao processar alerta:', err);
  }
});

evtSource.onerror = () => {
  console.warn('[SSE] Conexão perdida — tentando reconectar...');
};