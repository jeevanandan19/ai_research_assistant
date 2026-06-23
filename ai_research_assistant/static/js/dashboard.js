/**
 * Dashboard JavaScript
 * Handles all dashboard interactions: summary, keywords, Q&A, insights
 */

// ── State ────────────────────────────────────────────────────────
const SESSION_ID = document.getElementById('sessionId')?.value ||
                   sessionStorage.getItem('session_id') || '';

let chatHistory = [];
let statsQA = 0;

// ── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  if (!SESSION_ID) {
    window.location.href = '/upload';
    return;
  }

  await loadSessionInfo();
  await loadChatHistory();
  bindEvents();
});

// ── Session Info ─────────────────────────────────────────────────

async function loadSessionInfo() {
  try {
    const res = await fetch(`/api/session-info?session_id=${SESSION_ID}`);
    const data = await res.json();

    if (!data.has_session) {
      window.location.href = '/upload';
      return;
    }

    // Populate navbar doc name
    const navDocName = document.getElementById('navDocName');
    if (navDocName) navDocName.textContent = data.filename;

    // Populate stats
    const meta = data.metadata || {};
    setEl('statPages', meta.total_pages || '—');
    setEl('statChunks', meta.total_chunks || '—');
    setEl('statWords', meta.word_count ? meta.word_count.toLocaleString() : '—');
    setEl('statQA', data.chat_count || 0);
    statsQA = data.chat_count || 0;

    // Document info table
    buildInfoTable(data);

    // Show download button if summary cached
    if (data.has_summary) {
      document.getElementById('btnDownloadSummary')?.classList.remove('d-none');
    }
    if (data.has_keywords) {
      document.getElementById('btnExportKeywords')?.classList.remove('d-none');
    }

  } catch (err) {
    console.error('Failed to load session info:', err);
  }
}

function buildInfoTable(data) {
  const meta = data.metadata || {};
  const fileRows = [
    ['Filename', data.filename],
    ['File Size', meta.file_size_mb ? `${meta.file_size_mb} MB` : '—'],
    ['Total Pages', meta.total_pages || '—'],
    ['Word Count', meta.word_count ? meta.word_count.toLocaleString() : '—'],
    ['Character Count', meta.char_count ? meta.char_count.toLocaleString() : '—'],
  ];

  const procRows = [
    ['Total Chunks', meta.total_chunks || '—'],
    ['Avg Chunk Size', meta.avg_chunk_size ? `${meta.avg_chunk_size} chars` : '—'],
    ['Min Chunk Size', meta.min_chunk_size ? `${meta.min_chunk_size} chars` : '—'],
    ['Max Chunk Size', meta.max_chunk_size ? `${meta.max_chunk_size} chars` : '—'],
    ['Uploaded', data.created_at ? new Date(data.created_at).toLocaleString() : '—'],
  ];

  buildTable('fileInfoTable', fileRows);
  buildTable('processingInfoTable', procRows);
}

function buildTable(id, rows) {
  const tbody = document.getElementById(id);
  if (!tbody) return;
  tbody.innerHTML = rows.map(([k, v]) =>
    `<tr><td>${k}</td><td>${v}</td></tr>`
  ).join('');
}

// ── Event Bindings ────────────────────────────────────────────────

function bindEvents() {
  // Summary
  document.getElementById('btnGenerateSummary')?.addEventListener('click', generateSummary);
  document.getElementById('btnDownloadSummary')?.addEventListener('click', downloadSummary);

  // Keywords
  document.getElementById('btnExtractKeywords')?.addEventListener('click', extractKeywords);
  document.getElementById('btnExportKeywords')?.addEventListener('click', exportKeywords);

  // Insights
  document.getElementById('btnExtractInsights')?.addEventListener('click', extractInsights);

  // Q&A
  document.getElementById('btnAsk')?.addEventListener('click', askQuestion);
  document.getElementById('questionInput')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); askQuestion(); }
  });
  document.getElementById('btnClearChat')?.addEventListener('click', clearChat);

  // Suggested questions
  document.querySelectorAll('.suggested-q').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('questionInput').value = btn.textContent;
      askQuestion();
    });
  });
}

// ── Summary ──────────────────────────────────────────────────────

async function generateSummary() {
  showSection('summaryLoading', 'summaryPlaceholder', 'summaryContent');

  try {
    const data = await apiPost('/api/summarize', { session_id: SESSION_ID });

    hideLoading('summaryLoading');

    if (data.success) {
      const content = document.getElementById('summaryContent');
      content.innerHTML = markdownToHtml(data.summary);
      content.classList.remove('d-none');
      document.getElementById('btnDownloadSummary')?.classList.remove('d-none');
      if (data.cached) showToast('Summary loaded from cache', 'info');
    } else {
      showSectionError('summaryPlaceholder', data.error);
    }
  } catch (err) {
    hideLoading('summaryLoading');
    showSectionError('summaryPlaceholder', 'Failed to generate summary.');
    console.error(err);
  }
}

// ── Keywords ─────────────────────────────────────────────────────

async function extractKeywords() {
  showSection('keywordsLoading', 'keywordsPlaceholder', 'keywordsContent');

  try {
    const data = await apiPost('/api/keywords', { session_id: SESSION_ID });
    hideLoading('keywordsLoading');

    if (data.success) {
      renderKeywords(data.keywords);
      document.getElementById('keywordsContent').classList.remove('d-none');
      document.getElementById('btnExportKeywords')?.classList.remove('d-none');
      if (data.cached) showToast('Keywords loaded from cache', 'info');
    } else {
      showSectionError('keywordsPlaceholder', data.error);
    }
  } catch (err) {
    hideLoading('keywordsLoading');
    showSectionError('keywordsPlaceholder', 'Failed to extract keywords.');
    console.error(err);
  }
}

function renderKeywords(kwData) {
  const cat = kwData.categorized || {};

  renderCloud('primaryKeywords', cat.primary_keywords || [], 'primary');
  renderCloud('technicalMethods', cat.technical_methods || [], 'method');
  renderCloud('datasetsMetrics', cat.datasets_and_metrics || [], 'data');
  renderCloud('domainConcepts', cat.domain_concepts || [], 'domain');
  renderCloud('allKeywords', kwData.all_keywords || [], 'all');
}

function renderCloud(containerId, keywords, cssClass) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!keywords || keywords.length === 0) {
    container.innerHTML = '<span class="text-muted small">None detected</span>';
    return;
  }

  container.innerHTML = keywords.map(kw =>
    `<span class="keyword-tag ${cssClass}">${escapeHtml(kw)}</span>`
  ).join('');
}

// ── Insights ─────────────────────────────────────────────────────

async function extractInsights() {
  document.getElementById('insightsPlaceholder')?.classList.add('d-none');
  document.getElementById('noveltyPlaceholder')?.classList.add('d-none');
  document.getElementById('insightsLoading')?.classList.remove('d-none');

  try {
    const data = await apiPost('/api/insights', { session_id: SESSION_ID });
    document.getElementById('insightsLoading')?.classList.add('d-none');

    if (data.success) {
      const insights = data.insights;

      const insightsEl = document.getElementById('insightsContent');
      insightsEl.innerHTML = markdownToHtml(insights.insights || '');
      insightsEl.classList.remove('d-none');

      const noveltyEl = document.getElementById('noveltyContent');
      noveltyEl.innerHTML = markdownToHtml(insights.novelty || '');
      noveltyEl.classList.remove('d-none');

      if (data.cached) showToast('Insights loaded from cache', 'info');
    } else {
      document.getElementById('insightsPlaceholder')?.classList.remove('d-none');
      showToast(data.error || 'Insight extraction failed', 'danger');
    }
  } catch (err) {
    document.getElementById('insightsLoading')?.classList.add('d-none');
    document.getElementById('insightsPlaceholder')?.classList.remove('d-none');
    showToast('Failed to extract insights', 'danger');
    console.error(err);
  }
}

// ── Q&A ──────────────────────────────────────────────────────────

async function askQuestion() {
  const input = document.getElementById('questionInput');
  const question = input.value.trim();

  if (!question) return;

  // Clear welcome message on first question
  const welcome = document.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Add user bubble
  appendChatBubble('user', question);
  input.value = '';

  // Show typing indicator
  const typingId = showTyping();

  // Clear context panel
  document.getElementById('contextPlaceholder')?.classList.add('d-none');
  document.getElementById('contextContent')?.classList.add('d-none');

  try {
    const data = await apiPost('/api/ask', {
      session_id: SESSION_ID,
      question: question,
    });

    removeTyping(typingId);

    if (data.success) {
      appendChatBubble('assistant', data.answer, data.num_sources);
      renderContext(data.retrieved_context || []);

      // Update QA counter
      statsQA++;
      setEl('statQA', statsQA);
    } else {
      appendChatBubble('assistant', `⚠️ ${data.error || 'An error occurred.'}`);
    }

  } catch (err) {
    removeTyping(typingId);
    appendChatBubble('assistant', '⚠️ Network error. Please try again.');
    console.error(err);
  }
}

function appendChatBubble(role, text, numSources) {
  const messages = document.getElementById('chatMessages');
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  let metaHtml = `<div class="bubble-meta">${time}`;
  if (role === 'assistant' && numSources) {
    metaHtml += ` · <i class="fas fa-search me-1"></i>${numSources} source${numSources !== 1 ? 's' : ''} retrieved`;
  }
  metaHtml += '</div>';

  const icon = role === 'user' ? '' : '<i class="fas fa-robot me-2 text-primary"></i>';

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = `
    <div class="bubble-content">${icon}${escapeHtml(text)}</div>
    ${metaHtml}
  `;

  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
  const messages = document.getElementById('chatMessages');
  const id = 'typing-' + Date.now();
  const el = document.createElement('div');
  el.id = id;
  el.className = 'chat-bubble assistant';
  el.innerHTML = `<div class="bubble-content typing-indicator">
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  </div>`;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

function renderContext(contextItems) {
  const container = document.getElementById('contextContent');
  if (!container) return;

  if (!contextItems || contextItems.length === 0) {
    document.getElementById('contextPlaceholder')?.classList.remove('d-none');
    container.classList.add('d-none');
    return;
  }

  container.innerHTML = contextItems.map(ctx => `
    <div class="context-chunk">
      <div class="chunk-header">
        <i class="fas fa-file-alt me-1"></i>
        Chunk ${ctx.chunk_index} · Page ${ctx.page}
      </div>
      <div>${escapeHtml(ctx.content.substring(0, 400))}${ctx.content.length > 400 ? '...' : ''}</div>
    </div>
  `).join('');

  container.classList.remove('d-none');
}

async function loadChatHistory() {
  try {
    const res = await fetch(`/api/chat-history?session_id=${SESSION_ID}`);
    const data = await res.json();

    if (data.success && data.history.length > 0) {
      const welcome = document.querySelector('.chat-welcome');
      if (welcome) welcome.remove();

      data.history.forEach(entry => {
        appendChatBubble('user', entry.question);
        appendChatBubble('assistant', entry.answer, entry.num_sources);
      });

      statsQA = data.count;
      setEl('statQA', statsQA);
    }
  } catch (err) {
    console.error('Failed to load chat history:', err);
  }
}

async function clearChat() {
  try {
    await apiPost('/api/chat-history/clear', { session_id: SESSION_ID });
    document.getElementById('chatMessages').innerHTML = `
      <div class="chat-welcome">
        <i class="fas fa-robot chat-welcome-icon"></i>
        <p>Chat history cleared. Ask me anything about the research paper.</p>
      </div>`;
    document.getElementById('contextContent').innerHTML = '';
    document.getElementById('contextContent')?.classList.add('d-none');
    document.getElementById('contextPlaceholder')?.classList.remove('d-none');
    statsQA = 0;
    setEl('statQA', 0);
    showToast('Chat history cleared', 'success');
  } catch (err) {
    console.error(err);
  }
}

// ── Download / Export ─────────────────────────────────────────────

async function downloadSummary() {
  try {
    const res = await fetch('/api/download-summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: SESSION_ID }),
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.error || 'Download failed', 'danger');
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research_analysis.pdf';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Summary downloaded!', 'success');

  } catch (err) {
    showToast('Download failed', 'danger');
    console.error(err);
  }
}

async function exportKeywords() {
  try {
    const res = await fetch('/api/export-keywords', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: SESSION_ID }),
    });

    if (!res.ok) {
      showToast('Export failed', 'danger');
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'keywords_export.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Keywords exported!', 'success');

  } catch (err) {
    showToast('Export failed', 'danger');
    console.error(err);
  }
}

// ── Helpers ──────────────────────────────────────────────────────

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function markdownToHtml(text) {
  if (!text) return '';
  return text
    // Headings
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Bullet points
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>(\n|$))+/g, '<ul>$&</ul>')
    // Numbered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Paragraphs (double newlines)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines to <br>
    .replace(/\n/g, '<br>')
    // Wrap in paragraph
    .replace(/^(.+)/, '<p>$1')
    .replace(/(.+)$/, '$1</p>');
}

function showSection(loadingId, placeholderId, contentId) {
  document.getElementById(placeholderId)?.classList.add('d-none');
  document.getElementById(contentId)?.classList.add('d-none');
  document.getElementById(loadingId)?.classList.remove('d-none');
}

function hideLoading(loadingId) {
  document.getElementById(loadingId)?.classList.add('d-none');
}

function showSectionError(placeholderId, message) {
  const el = document.getElementById(placeholderId);
  if (el) {
    el.classList.remove('d-none');
    el.innerHTML = `
      <i class="fas fa-exclamation-circle empty-icon text-danger"></i>
      <p class="text-danger small">${escapeHtml(message || 'An error occurred.')}</p>
    `;
  }
}

function showToast(message, type = 'success') {
  const toastEl = document.getElementById('toastMsg');
  const toastBody = document.getElementById('toastBody');

  if (!toastEl || !toastBody) return;

  toastBody.textContent = message;
  toastEl.className = 'toast align-items-center border-0 text-bg-' + type;

  const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3000 });
  toast.show();
}
