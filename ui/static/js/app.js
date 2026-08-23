/* ============================================================
   REVERIE — Application Logic
   Clean modular JS for the glassmorphism chat UI.
   ============================================================ */

/* ---- 1. SVG Icon Library ---- */
const ICON = {
  chat:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  trash:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
  sparkle:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>`,
  globe:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  code:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  zap:      `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  brain:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/></svg>`,
  file:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>`,
};

/* ---- 2. DOM References ---- */
const $ = (s) => document.querySelector(s);
const DOM = {
  sidebar:       $('#sidebar'),
  toggleBtn:     $('#sidebar-toggle-btn'),
  threadList:    $('#thread-list'),
  newChatBtns:   document.querySelectorAll('.new-chat-btn'),
  searchInput:   $('#search-input'),
  welcomeScreen: $('#welcome-screen'),
  chatArea:      $('#chat-area'),
  chatTitle:     $('#chat-title'),
  chatContainer: $('#chat-container'),
  inputWrapper:  $('#input-wrapper'),
  chatInput:     $('#chat-input'),
  sendBtn:       $('#send-btn'),
};

/* ---- 3. State ---- */
let currentThreadId = null;
let allThreads      = [];
let isSending       = false;

/* ---- 4. Initialisation ---- */
function init() {
  setupListeners();
  setupResizers();
  loadThreads().then(() => {
    const match = window.location.pathname.match(/^\/chat\/(.+)$/);
    if (match && match[1] !== 'null' && match[1] !== 'undefined') {
      loadThreadMessages(match[1], false);
    } else {
      window.history.replaceState({}, '', '/');
    }
  });
}

function setupListeners() {
  const toggleSidebar = () => {
    if (DOM.sidebar) {
      DOM.sidebar.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed', DOM.sidebar.classList.contains('collapsed'));
    }
  };

  if (DOM.toggleBtn) {
    DOM.toggleBtn.addEventListener('click', toggleSidebar);
  }
  const innerToggle = document.getElementById('sidebar-toggle-btn-inner');
  if (innerToggle) {
    innerToggle.addEventListener('click', toggleSidebar);
  }
  
  if (DOM.newChatBtns) {
    DOM.newChatBtns.forEach(btn => btn.addEventListener('click', createNewThread));
  }
  


  // Expand Button Logic
  const expandBtn = document.getElementById('expand-btn');
  if (expandBtn && DOM.inputWrapper) {
    expandBtn.addEventListener('click', () => {
      DOM.inputWrapper.classList.toggle('expanded');
      autoResize(DOM.chatInput);
      if (DOM.inputWrapper.classList.contains('expanded')) {
        DOM.chatInput.focus();
        // Change icon to collapse
        expandBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>`;
      } else {
        // Change icon back to expand
        expandBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>`;
      }
    });
  }

  // Ctrl+K or Cmd+K for new chat
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      createNewThread();
    }
  });

  // History popstate
  window.addEventListener('popstate', (e) => {
    if (e.state && e.state.threadId) {
      loadThreadMessages(e.state.threadId, false);
    } else {
      // Check URL path
      const match = window.location.pathname.match(/^\/chat\/(.+)$/);
      if (match && match[1] !== 'null' && match[1] !== 'undefined') {
        loadThreadMessages(match[1], false);
      } else {
        currentThreadId = null;
        showWelcome(true);
        window.history.replaceState({}, '', '/');
      }
    }
  });

  if (DOM.sendBtn) DOM.sendBtn.addEventListener('click', sendMessage);

  document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('.file-link-btn');
    if (btn) {
      e.preventDefault();
      const path = btn.getAttribute('data-path');
      const name = btn.getAttribute('data-name');
      if (typeof openFilePreview === 'function') {
        openFilePreview(path, name);
      }
    }
  });

  if (DOM.chatInput) {
    DOM.chatInput.addEventListener('input', () => {
      autoResize(DOM.chatInput);
      if (DOM.sendBtn) DOM.sendBtn.disabled = DOM.chatInput.value.trim() === '' || isSending;
    });

    DOM.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (DOM.sendBtn && !DOM.sendBtn.disabled) sendMessage();
      }
    });
  }

  if (DOM.searchInput) {
    DOM.searchInput.addEventListener('input', filterThreads);
  }

  // Quick action & suggestion cards
  document.querySelectorAll('.quick-card, .suggestion-card').forEach(card => {
    card.addEventListener('click', () => {
      const prompt = card.dataset.prompt;
      if (prompt) {
        DOM.chatInput.value = prompt;
        DOM.chatInput.focus();
        // Place cursor at the end for easy editing
        DOM.chatInput.setSelectionRange(prompt.length, prompt.length);
        autoResize(DOM.chatInput);
        DOM.sendBtn.disabled = false;
      }
    });
  });
}

/* ---- 5. Thread Management ---- */
async function loadThreads() {
  try {
    const res = await fetch('/api/threads');
    allThreads = await res.json();
    renderThreadList(allThreads);
  } catch (err) {
    console.error('Failed to load threads:', err);
  }
}

function renderThreadList(threads) {
  DOM.threadList.innerHTML = '';

  if (threads.length === 0) {
    DOM.threadList.innerHTML = `
      <div class="empty-threads">
        ${ICON.chat}
        <span>No conversations yet</span>
      </div>`;
    return;
  }

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;
  const last7Days = today - 7 * 86400000;

  const groups = { 'Today': [], 'Yesterday': [], 'Previous 7 Days': [], 'Older': [] };

  threads.forEach(t => {
    const ts = t.updated_at ? t.updated_at * 1000 : Date.now();
    if (ts >= today) groups['Today'].push(t);
    else if (ts >= yesterday) groups['Yesterday'].push(t);
    else if (ts >= last7Days) groups['Previous 7 Days'].push(t);
    else groups['Older'].push(t);
  });

  for (const [groupName, groupThreads] of Object.entries(groups)) {
    if (groupThreads.length === 0) continue;

    const header = document.createElement('div');
    header.className = 'thread-group-header';
    header.textContent = groupName;
    DOM.threadList.appendChild(header);

    groupThreads.forEach(t => {
      const div = document.createElement('div');
      div.className = 'thread-item' + (t.thread_id === currentThreadId ? ' active' : '');
      div.innerHTML = `
        <span class="thread-title">${escapeHtml(t.title || 'Unnamed Chat')}</span>
        <div class="thread-actions">
          <button class="thread-action thread-rename" title="Rename"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
          <button class="thread-action thread-delete" title="Delete">${ICON.trash}</button>
        </div>
      `;
      div.addEventListener('click', (e) => {
        if (e.target.closest('.thread-action')) return;
        loadThreadMessages(t.thread_id);
      });
      div.querySelector('.thread-rename').addEventListener('click', (e) => {
        e.stopPropagation();
        const newTitle = prompt("Enter new thread name:", t.title || "");
        if (newTitle !== null && newTitle.trim() !== "") {
          renameThread(t.thread_id, newTitle.trim());
        }
      });
      div.querySelector('.thread-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteThread(t.thread_id);
      });
      DOM.threadList.appendChild(div);
    });
  }
}

async function createNewThread() {
  if (DOM.welcomeScreen && !DOM.welcomeScreen.classList.contains('hidden')) {
    return; // Already in a new chat
  }
  try {
    const res  = await fetch('/api/threads/new', { method: 'POST' });
    const data = await res.json();
    currentThreadId = data.thread_id;

    DOM.chatContainer.innerHTML = '';
    showWelcome(true);
    loadThreads();
    DOM.chatInput.focus();
    window.history.pushState({ threadId: currentThreadId }, '', '/chat/' + currentThreadId);
  } catch (e) {
    console.error(e);
  }
}

async function loadThreadMessages(threadId, pushUrl = true) {
  currentThreadId = threadId;
  DOM.chatContainer.innerHTML = '';

  if (pushUrl) {
    window.history.pushState({ threadId: threadId }, '', '/chat/' + threadId);
  }

  try {
    const res  = await fetch(`/api/threads/${threadId}/messages`);
    const data = await res.json();

    if (data.messages && data.messages.length > 0) {
      showWelcome(false);
      data.messages.forEach(m => appendMessage(m.role, m.content));

      // Update title
      const thread = allThreads.find(t => t.thread_id === threadId);
      if (thread) DOM.chatTitle.textContent = thread.title || '';
    } else {
      showWelcome(true);
    }
    scrollToBottom();
    loadThreads(); // refresh active states
    
    // Check for active stream (resume if reloading page during generation)
    try {
      const attachRes = await fetch(`/api/chat/${threadId}/stream`);
      if (attachRes.status === 200) {
        isSending = true;
        if (DOM.sendBtn) DOM.sendBtn.disabled = true;
        
        const reader = attachRes.body.getReader();
        const decoder = new TextDecoder("utf-8");
        
        const assistantDiv = document.createElement('div');
        assistantDiv.className = 'message assistant-message';
        DOM.chatContainer.appendChild(assistantDiv);
        scrollToBottom();
        
        let accumulated = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          accumulated += chunk;
          
          let processed = processFileTags(accumulated);
          processed = parseThinkBlocks(processed);
          
          assistantDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(processed) : processed;
          
          assistantDiv.querySelectorAll('pre code').forEach((el) => {
            if (typeof hljs !== 'undefined') hljs.highlightElement(el);
          });
          scrollToBottom();
        }
        addCopyButtons(assistantDiv);
        isSending = false;
        if (DOM.chatInput) {
          DOM.chatInput.focus();
          if (DOM.sendBtn) DOM.sendBtn.disabled = DOM.chatInput.value.trim() === '';
        }
        loadThreads(); // reload to get any updated title
      }
    } catch (e) {
      console.error("Failed to attach to stream", e);
    }
    
  } catch (e) {
    console.error(e);
  }
}

async function deleteThread(threadId) {
  try {
    await fetch(`/api/threads/${threadId}`, { method: 'DELETE' });
    if (currentThreadId === threadId) {
      currentThreadId = null;
      showWelcome(true);
      window.history.pushState({}, '', '/');
    }
    loadThreads();
  } catch (e) {
    console.error(e);
  }
}

async function renameThread(threadId, newTitle) {
  try {
    await fetch(`/api/threads/${threadId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle })
    });
    loadThreads();
  } catch (e) {
    console.error(e);
  }
}

function filterThreads() {
  const q = DOM.searchInput.value.toLowerCase().trim();
  if (!q) return renderThreadList(allThreads);
  const filtered = allThreads.filter(t =>
    (t.title || t.thread_id).toLowerCase().includes(q)
  );
  renderThreadList(filtered);
}

/* ---- 6. View Helpers ---- */
function showWelcome(visible) {
  DOM.welcomeScreen.classList.toggle('hidden', !visible);
  DOM.chatArea.classList.toggle('hidden', visible);
  if (visible && DOM.chatTitle) {
    DOM.chatTitle.textContent = '';
  }
  
  // Disable new chat button if on welcome screen
  if (DOM.newChatBtns) {
    DOM.newChatBtns.forEach(btn => {
      btn.disabled = visible;
      if (visible) {
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
      } else {
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
      }
    });
  }
}

/* ---- 7. Message Rendering ---- */
function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}-message`;

  let processed = content || '';
  processed = processFileTags(processed);

  if (role === 'assistant') {
    div.innerHTML = marked.parse(processThinkTags(processed));
  } else {
    div.innerHTML = marked.parse(processed);
  }
  convertFileNodesToButtons(div);
  DOM.chatContainer.appendChild(div);
  scrollToBottom();
  return div;
}

/* ---- 8. Think-Block & Tool Processing ---- */
function processThinkTags(text) {
  if (!text) return text;
  
  // 1. First pass: Extract and remove all completed tool results
  const results = {};
  let processed = text.replace(/<think>\s*✅ tool_call_results id: ([^\n]+)\nResult:\n([\s\S]*?)<\/think>/g, (match, id, res) => {
    results[id.trim()] = res.trim();
    return ''; // Remove from text completely
  });

  // 2. Second pass: Replace remaining completed think blocks
  processed = processed.replace(/<think>([\s\S]*?)<\/think>/g, (match, inner) => {
    const trimmed = inner.trim();
    if (!trimmed) return '';
    
    // A. Tool Call
    const callMatch = trimmed.match(/🚀 tool_call name: ([^\n]+)\nid: ([^\n]+)\nArguments:\n([\s\S]*)/);
    if (callMatch) {
      const name = callMatch[1].trim();
      const id   = callMatch[2].trim();
      const args = callMatch[3].trim();
      
      let content  = `**Arguments:**\n${args}`;
      let label    = `Tool: ${name}`;
      let openAttr = '';
      let icon     = ICON.zap;
      
      if (results[id]) {
        content += `\n\n**Result:**\n${results[id]}`;
        label = `${name}`; // Clean label when done
      } else {
        content += `\n\n*Running...*`;
        openAttr = 'open';
      }
      
      const parsed = typeof marked !== 'undefined' ? marked.parse(content) : content;
      return `<details class="think-block" ${openAttr}><summary>${icon} ${label}</summary><div class="think-content">${parsed}</div></details>`;
    }
    
    // B. Memory Update
    if (trimmed.startsWith('🧠')) {
      const parsed = typeof marked !== 'undefined' ? marked.parse(trimmed) : trimmed;
      return `<details class="think-block"><summary>${ICON.brain} Memory Update</summary><div class="think-content">${parsed}</div></details>`;
    }
    
    // C. Tool Prep (transient)
    if (trimmed.startsWith('⏳')) {
       const parsed = typeof marked !== 'undefined' ? marked.parse(trimmed) : trimmed;
       return `<details class="think-block" open><summary>${ICON.zap} Preparing Tool…</summary><div class="think-content">${parsed}</div></details>`;
    }
    
    // D. Normal Thinking
    const parsed = typeof marked !== 'undefined' ? marked.parse(trimmed) : trimmed;
    return `<details class="think-block"><summary>${ICON.sparkle} Thought Process</summary><div class="think-content">${parsed}</div></details>`;
  });
  
  // 3. Third pass: Handle unclosed <think> that is still streaming
  const openIdx = processed.lastIndexOf('<think>');
  if (openIdx !== -1) {
    const before   = processed.slice(0, openIdx);
    const thinking = processed.slice(openIdx + 7).trim();
    
    let label = 'Thinking…';
    let icon  = ICON.sparkle;
    
    // Might be an unclosed tool result streaming in
    if (thinking.match(/✅ tool_call_results/)) {
      label = 'Receiving Result…';
      icon  = ICON.zap;
    } 
    // Might be an unclosed tool call streaming in
    else if (thinking.match(/🚀 tool_call name: ([^\n]+)/)) {
      const nameMatch = thinking.match(/🚀 tool_call name: ([^\n]+)/);
      label = `Tool: ${nameMatch[1].trim()}…`;
      icon  = ICON.zap;
    }
    
    const parsed = typeof marked !== 'undefined' ? marked.parse(thinking) : thinking;
    processed = before + `<details class="think-block" open><summary>${icon} ${label}</summary><div class="think-content">${parsed}</div></details>`;
  }

  return processed;
}

/* ---- 9. Send Message (Streaming) ---- */
async function sendMessage() {
  let text = DOM.chatInput.value.trim();
  if (!text) return;
  if (isSending) return;

  if (!currentThreadId || currentThreadId === 'null' || currentThreadId === 'undefined') {
    try {
      const res = await fetch('/api/threads/new', { method: 'POST' });
      const data = await res.json();
      currentThreadId = data.thread_id;
      window.history.pushState({ threadId: currentThreadId }, '', '/chat/' + currentThreadId);
    } catch (e) {
      console.error("Failed to create thread", e);
      return;
    }
  }

  isSending = true;
  DOM.chatInput.value = '';
  DOM.chatInput.style.height = 'auto';
  if (DOM.inputWrapper && DOM.inputWrapper.classList.contains('expanded')) {
    DOM.inputWrapper.classList.remove('expanded');
    const expandBtn = document.getElementById('expand-btn');
    if (expandBtn) expandBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>`;
  }
  
  DOM.sendBtn.disabled = true;
  showWelcome(false);

  appendMessage('user', text);

  // Create assistant placeholder with typing dots
  const assistantDiv = document.createElement('div');
  assistantDiv.className = 'message assistant-message';
  assistantDiv.innerHTML = `<div class="typing-indicator">
    <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
  </div>`;
  DOM.chatContainer.appendChild(assistantDiv);
  scrollToBottom();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, thread_id: currentThreadId }),
    });

    if (!response.ok) throw new Error(`Server ${response.status}`);
    if (!response.body) throw new Error('ReadableStream unavailable');

    const reader  = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullText  = '';
    let raf       = false;

    function updateDOM() {
      if (fullText) {
        let text = processFileTags(fullText);
        assistantDiv.innerHTML = marked.parse(processThinkTags(text));
        convertFileNodesToButtons(assistantDiv);
      }
      scrollToBottom();
      raf = false;
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
      if (!raf) { raf = true; requestAnimationFrame(updateDOM); }
    }

    // Final render
    if (fullText) {
      let text = processFileTags(fullText);
      assistantDiv.innerHTML = marked.parse(processThinkTags(text));
      convertFileNodesToButtons(assistantDiv);
    } else {
      assistantDiv.innerHTML = '<span style="color:var(--t3);font-style:italic">[No response]</span>';
    }

    scrollToBottom();
    loadThreads();
  } catch (err) {
    console.error('Streaming error:', err);
    assistantDiv.innerHTML = `<p style="color:var(--danger);font-weight:600">Error: ${escapeHtml(err.message)}</p>`;
    scrollToBottom();
  } finally {
    isSending = false;
    DOM.sendBtn.disabled = DOM.chatInput.value.trim() === '';
  }
}

/* ---- 10. File Panel Integration ---- */
const filePanel = {
  container: $('#file-panel'),
  name:      $('#file-panel-name'),
  code:      $('#file-panel-code'),
  closeBtn:  $('#file-panel-close')
};

if (filePanel.closeBtn) {
  filePanel.closeBtn.addEventListener('click', () => {
    filePanel.container.classList.add('hidden');
  });
}

function processFileTags(text) {
  if (!text) return text;
  
  // 1. Temporarily extract and protect multi-line triple-backtick code blocks
  const codeBlocks = [];
  let processed = text.replace(/```[\s\S]*?```/g, match => {
    codeBlocks.push(match);
    return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
  });

  // 2. Explicit [/display{path}/display] tags (with optional emoji, backticks, bold)
  processed = processed.replace(/(?:[📄📁📝📎💾📊📑📜✨🔹🔸]\s*)?(?:\*\*|\*|__|_)?`?\[\/display\{?(.*?)\}?\/display\]`?(?:\*\*|\*|__|_)?/g, (match, path) => {
    const cleanPath = escapeHtml(path.trim());
    const fileName = cleanPath.split('/').pop() || cleanPath;
    return `<button type="button" class="file-link-btn" data-path="${cleanPath}" data-name="${fileName}">${ICON.file} ${fileName}</button>`;
  });

  // 3. Markdown links pointing to local files: [Report](report.md) or [file.md](file.md)
  processed = processed.replace(/(?:[📄📁📝📎💾📊📑📜✨🔹🔸]\s*)?\[([^\]]+)\]\(([^)"]+\.(?:md|py|txt|json|js|ts|jsx|tsx|css|html|sh|yml|yaml|csv|log|sql|pdf|toml|env|lock|png|jpg|jpeg|svg))\)/gi, (match, label, path) => {
    if (path.startsWith('http://') || path.startsWith('https://')) return match;
    const cleanPath = escapeHtml(path.trim());
    const cleanLabel = escapeHtml(label.trim());
    return `<button type="button" class="file-link-btn" data-path="${cleanPath}" data-name="${cleanLabel}">${ICON.file} ${cleanLabel}</button>`;
  });

  // 4. Any file reference wrapped in emoji, bold/italic, backticks, or standalone:
  // Matches: 📄 **`filename.md`**, **`filename.md`**, `filename.md`, **filename.md**, etc.
  const fileExts = 'md|py|txt|json|js|ts|jsx|tsx|css|html|sh|yml|yaml|csv|log|sql|pdf|toml|env|lock|png|jpg|jpeg|svg';
  const masterFileRegex = new RegExp(
    '(?:[📄📁📝📎💾📊📑📜✨🔹🔸]\\s*)?' +                     // Optional emoji & space
    '(?:\\*\\*|\\*|__|_)?' +                                   // Optional opening bold/italic
    '`?' +                                                     // Optional opening backtick
    '([a-zA-Z0-9_\\-\\.\\/]+\\.(?:' + fileExts + '))' +        // Filename with extension (Group 1)
    '`?' +                                                     // Optional closing backtick
    '(?:\\*\\*|\\*|__|_)?'                                     // Optional closing bold/italic
  , 'gi');

  processed = processed.replace(masterFileRegex, (match, path, offset, string) => {
    // If inside an existing HTML tag or attribute, don't replace
    const before = string.slice(0, offset);
    if (before.lastIndexOf('<') > before.lastIndexOf('>')) return match;
    // If it was already replaced into a button
    if (match.includes('file-link-btn') || match.includes('data-path')) return match;

    const cleanPath = escapeHtml(path.trim());
    const fileName = cleanPath.split('/').pop() || cleanPath;
    return `<button type="button" class="file-link-btn" data-path="${cleanPath}" data-name="${fileName}">${ICON.file} ${fileName}</button>`;
  });

  // 5. Restore multi-line triple-backtick code blocks
  processed = processed.replace(/__CODE_BLOCK_(\d+)__/g, (match, idx) => codeBlocks[idx]);

  return processed;
}

// DOM Post-Processor: Converts any remaining <code> or <strong> nodes containing filenames into buttons
function convertFileNodesToButtons(container) {
  if (!container) return;
  const fileExtRegex = /^([a-zA-Z0-9_\-\.\/]+\.(?:md|py|txt|json|js|ts|jsx|tsx|css|html|sh|yml|yaml|csv|log|sql|pdf|toml|env|lock|png|jpg|jpeg|svg))$/i;
  
  const candidateEls = container.querySelectorAll('code, strong, em, a:not(.file-link-btn)');
  candidateEls.forEach(el => {
    if (el.closest('pre') || el.closest('.file-link-btn')) return;
    const text = el.textContent.trim().replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}📄📁📝📎💾📊📑📜✨🔹🔸?\s]+/u, '').replace(/^`|`$/g, '').trim();
    const m = text.match(fileExtRegex);
    if (m) {
      const cleanPath = m[1];
      const fileName = cleanPath.split('/').pop() || cleanPath;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'file-link-btn';
      btn.setAttribute('data-path', cleanPath);
      btn.setAttribute('data-name', fileName);
      btn.innerHTML = `${ICON.file} ${fileName}`;
      
      // If the parent is a strong/em wrapping this code tag, replace the highest wrapper
      let targetToReplace = el;
      if (el.parentElement && (el.parentElement.tagName === 'STRONG' || el.parentElement.tagName === 'EM' || el.parentElement.tagName === 'CODE')) {
        targetToReplace = el.parentElement;
      }

      const parentEl = targetToReplace.parentElement;
      targetToReplace.replaceWith(btn);

      // Clean up any stray emoji text or question mark glyphs in the parent paragraph
      if (parentEl) {
        parentEl.childNodes.forEach(node => {
          if (node.nodeType === Node.TEXT_NODE) {
            node.textContent = node.textContent.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}📄📁📝📎💾📊📑📜✨🔹🔸?]/gu, '').trim();
          }
        });
      }
    }
  });

  // Also clean any orphan emojis/question marks directly in paragraphs containing file buttons
  container.querySelectorAll('.file-link-btn').forEach(btn => {
    const parent = btn.parentElement;
    if (parent && (parent.tagName === 'P' || parent.tagName === 'DIV')) {
      parent.childNodes.forEach(node => {
        if (node.nodeType === Node.TEXT_NODE) {
          node.textContent = node.textContent.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}📄📁📝📎💾📊📑📜✨🔹🔸?]/gu, '').trim();
        }
      });
    }
  });
}

async function openFilePreview(path, name) {
  if (filePanel.name) filePanel.name.textContent = name;
  if (filePanel.code) {
    filePanel.code.parentElement.style.display = 'block';
    const contentContainer = document.querySelector('.file-panel-content');
    if (contentContainer) {
      const oldMd = contentContainer.querySelector('.markdown-preview');
      if (oldMd) oldMd.remove();
      contentContainer.querySelectorAll('.html-preview').forEach(el => el.remove());
    }
    filePanel.code.textContent = 'Loading...';
    filePanel.code.style.color = 'var(--t1)';
  }
  if (filePanel.container) filePanel.container.classList.remove('hidden');
  
  try {
    const url = `/api/files?path=${encodeURIComponent(path)}&thread_id=${encodeURIComponent(currentThreadId || '')}`;
    const res = await fetch(url);
    const data = await res.json();
    const contentContainer = document.querySelector('.file-panel-content');
    const oldMd = contentContainer.querySelector('.markdown-preview');
    if (oldMd) oldMd.remove();
    contentContainer.querySelectorAll('.html-preview').forEach(el => el.remove());
    
    // Reset container layout in case it was modified by a previous file (like HTML)
    contentContainer.style.display = 'block';
    contentContainer.style.flexDirection = '';
    contentContainer.style.padding = '';

    if (!filePanel.code) return;
    if (data.error) {
      filePanel.code.parentElement.style.display = 'block';
      filePanel.code.textContent = `Error: ${data.error}`;
      filePanel.code.style.color = 'var(--danger)';
    } else {
      const content = data.content || '(Empty file)';
      if (name.toLowerCase().endsWith('.md')) {
        filePanel.code.parentElement.style.display = 'none';
        const mdDiv = document.createElement('div');
        mdDiv.className = 'markdown-preview message';
        mdDiv.style.background = 'transparent';
        mdDiv.style.border = 'none';
        mdDiv.style.padding = '0';
        mdDiv.style.margin = '0';
        mdDiv.style.maxWidth = '100%';
        mdDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(content) : content;
        contentContainer.appendChild(mdDiv);
      } else if (name.toLowerCase().endsWith('.html')) {
        filePanel.code.parentElement.style.display = 'none';
        
        // Ensure contentContainer acts as a flex column so tabsContainer can fill it
        contentContainer.style.display = 'flex';
        contentContainer.style.flexDirection = 'column';
        
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'html-preview tabs-container';
        tabsContainer.style.display = 'flex';
        tabsContainer.style.flexDirection = 'column';
        tabsContainer.style.flex = '1';
        tabsContainer.style.height = '100%';
        tabsContainer.style.minHeight = '500px';

        const tabsHeader = document.createElement('div');
        tabsHeader.style.display = 'flex';
        tabsHeader.style.gap = '8px';
        tabsHeader.style.marginBottom = '12px';
        tabsHeader.style.borderBottom = '1px solid var(--border-color)';
        tabsHeader.style.paddingBottom = '8px';
        tabsHeader.style.flexShrink = '0';

        const previewTab = document.createElement('button');
        previewTab.textContent = 'Preview';
        previewTab.className = 'file-tab-btn active';
        previewTab.style.padding = '6px 16px';
        previewTab.style.background = 'var(--bg2)';
        previewTab.style.color = 'var(--t1)';
        previewTab.style.border = '1px solid var(--border-color)';
        previewTab.style.borderRadius = '6px';
        previewTab.style.cursor = 'pointer';

        const codeTab = document.createElement('button');
        codeTab.textContent = 'Code';
        codeTab.className = 'file-tab-btn';
        codeTab.style.padding = '6px 16px';
        codeTab.style.background = 'transparent';
        codeTab.style.color = 'var(--t2)';
        codeTab.style.border = '1px solid transparent';
        codeTab.style.borderRadius = '6px';
        codeTab.style.cursor = 'pointer';

        tabsHeader.appendChild(previewTab);
        tabsHeader.appendChild(codeTab);

        const previewContainer = document.createElement('div');
        previewContainer.style.flex = '1';
        previewContainer.style.display = 'flex';
        previewContainer.style.flexDirection = 'column';
        previewContainer.style.overflow = 'hidden';

        const codeContainer = document.createElement('div');
        codeContainer.style.flex = '1';
        codeContainer.style.display = 'none';
        codeContainer.style.overflow = 'auto';
        codeContainer.style.background = 'var(--bg2)';
        codeContainer.style.padding = '12px';
        codeContainer.style.borderRadius = '8px';
        codeContainer.style.border = '1px solid var(--border-color)';

        const pre = document.createElement('pre');
        pre.style.margin = '0';
        const codeEl = document.createElement('code');
        codeEl.textContent = content;
        pre.appendChild(codeEl);
        codeContainer.appendChild(pre);
        
        let viewContent = content;
        if (viewContent.includes('markmap-autoloader')) {
            // Inject a style tag to completely override any layout restrictions
            const injectStyle = `
                <style>
                    body { margin: 0 !important; padding: 0 !important; background: transparent !important; }
                    .markmap { border: none !important; box-shadow: none !important; border-radius: 0 !important; padding: 0 !important; margin: 0 !important; }
                    h2 { display: none !important; }
                </style>
            `;
            viewContent = viewContent.replace('</head>', injectStyle + '</head>');
        }
        
        let pendingIframeSrcdoc = null;
        let iframeEl = null;

        if (content.trim().startsWith('<div class="markmap"><svg') || content.trim().startsWith('<svg')) {
            previewContainer.innerHTML = content;
            const svgEl = previewContainer.querySelector('svg');
            if (svgEl) {
                svgEl.style.width = '100%';
                svgEl.style.height = '100%';
                svgEl.style.flex = '1';
            }
        } else {
            iframeEl = document.createElement('iframe');
            iframeEl.style.flex = '1';
            iframeEl.style.width = '100%';
            iframeEl.style.height = '100%';
            iframeEl.style.border = 'none';
            iframeEl.style.borderRadius = '8px';
            iframeEl.style.backgroundColor = '#fff';
            pendingIframeSrcdoc = viewContent;
            previewContainer.appendChild(iframeEl);
        }

        tabsContainer.appendChild(tabsHeader);
        tabsContainer.appendChild(previewContainer);
        tabsContainer.appendChild(codeContainer);

        previewTab.addEventListener('click', () => {
            previewTab.style.background = 'var(--bg2)';
            previewTab.style.color = 'var(--t1)';
            previewTab.style.border = '1px solid var(--border-color)';
            codeTab.style.background = 'transparent';
            codeTab.style.color = 'var(--t2)';
            codeTab.style.border = '1px solid transparent';
            previewContainer.style.display = 'flex';
            codeContainer.style.display = 'none';
        });

        codeTab.addEventListener('click', () => {
            codeTab.style.background = 'var(--bg2)';
            codeTab.style.color = 'var(--t1)';
            codeTab.style.border = '1px solid var(--border-color)';
            previewTab.style.background = 'transparent';
            previewTab.style.color = 'var(--t2)';
            previewTab.style.border = '1px solid transparent';
            previewContainer.style.display = 'none';
            codeContainer.style.display = 'block';
        });

        contentContainer.insertBefore(tabsContainer, filePanel.code.parentElement);

        if (iframeEl && pendingIframeSrcdoc) {
            // Assign srcdoc only after it's in the DOM so markmap sees real dimensions
            iframeEl.srcdoc = pendingIframeSrcdoc;
        }
      } else {
        filePanel.code.parentElement.style.display = 'block';
        filePanel.code.textContent = content;
        filePanel.code.style.color = 'var(--t1)';
      }
    }
  } catch (err) {
    if (filePanel.code) {
      filePanel.code.parentElement.style.display = 'block';
      filePanel.code.textContent = `Error: ${err.message}`;
      filePanel.code.style.color = 'var(--danger)';
    }
  }
}

/* ---- 11. Resizable Panels ---- */
function setupResizers() {
  // 1. Sidebar Resizer (Drag right edge of sidebar)
  const sidebar = $('#sidebar');
  const sidebarResizer = $('#sidebar-resizer');
  if (sidebar && sidebarResizer) {
    let isDragging = false;
    let startX = 0;
    let startWidth = 0;

    sidebarResizer.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      startWidth = sidebar.getBoundingClientRect().width;
      sidebar.classList.add('is-resizing');
      sidebarResizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const newWidth = Math.min(Math.max(startWidth + dx, 180), 600);
      sidebar.style.width = `${newWidth}px`;
      sidebar.style.minWidth = `${newWidth}px`;
      document.documentElement.style.setProperty('--sidebar-w', `${newWidth}px`);
    });

    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        sidebar.classList.remove('is-resizing');
        sidebarResizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });
  }

  // 2. File Panel Resizer (Drag left edge of file preview panel)
  const filePanelEl = $('#file-panel');
  const fileResizer = $('#file-panel-resizer');
  if (filePanelEl && fileResizer) {
    let isDragging = false;
    let startX = 0;
    let startWidth = 0;

    fileResizer.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      startWidth = filePanelEl.getBoundingClientRect().width;
      filePanelEl.classList.add('is-resizing');
      fileResizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = startX - e.clientX; // Moving mouse left increases file panel width
      const maxWidth = window.innerWidth * 0.88;
      const newWidth = Math.min(Math.max(startWidth + dx, 280), maxWidth);
      filePanelEl.style.width = `${newWidth}px`;
    });

    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        filePanelEl.classList.remove('is-resizing');
        fileResizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });
  }
}

/* ---- 12. Utilities ---- */
function scrollToBottom() {
  DOM.chatContainer.scrollTop = DOM.chatContainer.scrollHeight;
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  if (textarea.closest('#input-wrapper').classList.contains('expanded')) {
    textarea.style.height = '100%';
  } else {
    textarea.style.height = Math.min(textarea.scrollHeight, 400) + 'px';
  }
}

function escapeHtml(str) {
  const map = { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' };
  return str.replace(/[&<>"']/g, c => map[c]);
}

/* ---- 13. Theme System ---- */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle-btn');
  const currentTheme = localStorage.getItem('theme') || 'dark';
  
  if (currentTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      if (isLight) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
      }
    });
  }
}

/* ---- Boot ---- */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  init();
});

// ---- Settings Modal Logic ----
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = document.getElementById('settings-modal');
const settingsCloseBtn = document.getElementById('settings-close-btn');

const settingsName = document.getElementById('settings-name');
const settingsDob = document.getElementById('settings-dob');
const settingsPersona = document.getElementById('settings-persona');
const settingsProfileForm = document.getElementById('settings-profile-form');

const settingsBackupBtn = document.getElementById('settings-backup-btn');
const settingsDeleteChatsBtn = document.getElementById('settings-delete-chats-btn');
const settingsDeleteAccountBtn = document.getElementById('settings-delete-account-btn');

async function openSettings() {
  settingsModal.classList.remove('hidden');
  try {
    const res = await fetch('/api/profile');
    if (res.ok) {
      const data = await res.json();
      if (data.name) settingsName.value = data.name;
      if (data.dob) settingsDob.value = data.dob;
      if (data.ai_persona) settingsPersona.value = data.ai_persona;
    }
  } catch (e) {
    console.error('Failed to load profile', e);
  }
}

function closeSettings() {
  settingsModal.classList.add('hidden');
}

if (settingsBtn) settingsBtn.addEventListener('click', openSettings);
if (settingsCloseBtn) settingsCloseBtn.addEventListener('click', closeSettings);
if (settingsModal) {
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeSettings();
  });
}

if (settingsProfileForm) {
  settingsProfileForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('name', settingsName.value);
    formData.append('dob', settingsDob.value);
    formData.append('ai_persona', settingsPersona.value);
    try {
      const res = await fetch('/api/save_profile', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        closeSettings();
      }
    } catch (e) {
      console.error('Failed to save profile', e);
    }
  });
}

if (settingsDeleteChatsBtn) {
  settingsDeleteChatsBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to delete all chats? This cannot be undone.')) {
      try {
        const res = await fetch('/api/chats', { method: 'DELETE' });
        if (res.ok) {
          window.location.reload();
        }
      } catch (e) {
        console.error('Failed to delete chats', e);
      }
    }
  });
}

if (settingsDeleteAccountBtn) {
  settingsDeleteAccountBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to delete your account and all chats? This cannot be undone.')) {
      try {
        const res = await fetch('/api/account', { method: 'DELETE' });
        if (res.ok) {
          window.location.href = '/';
        }
      } catch (e) {
        console.error('Failed to delete account', e);
      }
    }
  });
}

if (settingsBackupBtn) {
  settingsBackupBtn.addEventListener('click', async () => {
    const originalText = settingsBackupBtn.innerHTML;
    settingsBackupBtn.innerHTML = '<span class="btn-text">Loading...</span>';
    settingsBackupBtn.disabled = true;
    try {
      const res = await fetch('/api/backup');
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'swara_chats_backup.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Failed to backup chats', e);
    } finally {
      settingsBackupBtn.innerHTML = originalText;
      settingsBackupBtn.disabled = false;
    }
  });
}

// ---- MAIN PRELOADER ----
const mainPreloader = document.getElementById('main-preloader');
const mainPrePct = document.getElementById('main-pre-pct');
if (mainPreloader && mainPrePct) {
  let val = 0;
  const duration = 1200; // ms
  const startTime = performance.now();
  
  function easeOutQuart(x) {
    return 1 - Math.pow(1 - x, 4);
  }

  function updatePreloader(time) {
    let progress = (time - startTime) / duration;
    if (progress > 1) progress = 1;
    
    val = easeOutQuart(progress);
    mainPrePct.textContent = String(Math.floor(val * 100)).padStart(3, '0');
    
    if (progress < 1) {
      requestAnimationFrame(updatePreloader);
    } else {
      setTimeout(() => {
        mainPreloader.style.opacity = '0';
        setTimeout(() => mainPreloader.remove(), 600);
      }, 200);
    }
  }
  requestAnimationFrame(updatePreloader);
}
