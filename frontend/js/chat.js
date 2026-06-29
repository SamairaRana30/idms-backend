let currentChannel  = null;
let currentUser     = null;
let replyTo         = null;
let pollInterval    = null;
let lastMessageId   = 0;

async function initChat() {
  const meRes = await apiGetMe();
  if (meRes.success) currentUser = meRes.data.user;
  await loadChannels();
}

async function loadChannels() {
  const res = await apiGetChannels();
  const list = document.getElementById('channelList');
  if (!res.success) {
    list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px">Failed to load channels</div>';
    return;
  }
  const channels = res.data.channels;
  if (!channels.length) {
    list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px">No channels yet</div>';
    return;
  }
  const isAdmin = getRole() === 'admin';
  list.innerHTML = channels.map(c => `
    <div class="channel-item${currentChannel && currentChannel.id === c.id ? ' active' : ''}"
         onclick="selectChannel(${JSON.stringify(c).replace(/"/g,'&quot;')})">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:4px">
        <div class="channel-name"># ${c.name}</div>
        ${isAdmin && c.name !== 'general' ? `<span style="color:var(--text-muted);font-size:13px;cursor:pointer;padding:0 4px;opacity:.5" title="Delete channel"
          onclick="event.stopPropagation();deleteChannel(${c.id},'${c.name}')">✕</span>` : ''}
      </div>
      ${c.description ? `<div class="channel-preview">${c.description}</div>` : ''}
    </div>
  `).join('');
  if (!currentChannel && channels.length) selectChannel(channels[0]);
}

function selectChannel(channel) {
  currentChannel = channel;
  lastMessageId  = 0;
  replyTo        = null;
  if (pollInterval) clearInterval(pollInterval);

  document.querySelectorAll('.channel-item').forEach(el => el.classList.remove('active'));
  const items = document.querySelectorAll('.channel-item');
  items.forEach(el => { if (el.querySelector('.channel-name')?.innerText === `# ${channel.name}`) el.classList.add('active'); });

  renderChatArea();
  loadMessages();
  pollInterval = setInterval(pollMessages, 5000);
}

function renderChatArea() {
  const area = document.getElementById('chatArea');
  area.innerHTML = `
    <div class="chat-header">
      <div>
        <h5># ${currentChannel.name}</h5>
        ${currentChannel.description ? `<small>${currentChannel.description}</small>` : ''}
      </div>
    </div>
    <div class="chat-messages" id="chatMessages"></div>
    <div class="chat-input-area">
      <div id="replyBanner" style="display:none;background:var(--bg-elevated);border-left:2px solid var(--accent);padding:6px 12px;border-radius:4px;margin-bottom:8px;font-size:12px;color:var(--text-muted);display:flex;align-items:center;justify-content:space-between;gap:8px">
        <span id="replyBannerText"></span>
        <button onclick="cancelReply()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;line-height:1">&times;</button>
      </div>
      <div class="chat-input-wrap">
        <textarea id="chatInput" rows="1" placeholder="Message #${currentChannel.name}"
                  onkeydown="handleInputKey(event)" oninput="autoResize(this)"></textarea>
        <button class="send-btn" onclick="sendMessage()"><i class="bi bi-send"></i></button>
      </div>
    </div>
  `;
}

async function loadMessages() {
  if (!currentChannel) return;
  const res = await apiGetMessages(currentChannel.id);
  const container = document.getElementById('chatMessages');
  if (!container) return;
  if (!res.success) { container.innerHTML = '<div style="text-align:center;color:var(--danger);font-size:13px;padding:20px">Failed to load messages</div>'; return; }
  const messages = res.data.messages;
  if (!messages.length) { container.innerHTML = '<div class="empty-chat"><i class="bi bi-chat-dots"></i><p>No messages yet — say hello!</p></div>'; return; }
  container.innerHTML = messages.map(renderMessage).join('');
  if (messages.length) lastMessageId = Math.max(...messages.map(m => m.id));
  scrollToBottom();
}

async function pollMessages() {
  if (!currentChannel) return;
  const res = await apiGetMessages(currentChannel.id, lastMessageId);
  if (!res.success || !res.data.messages.length) return;
  const container = document.getElementById('chatMessages');
  if (!container) return;
  const emptyState = container.querySelector('.empty-chat');
  if (emptyState) container.innerHTML = '';
  res.data.messages.forEach(m => {
    container.insertAdjacentHTML('beforeend', renderMessage(m));
    if (m.id > lastMessageId) lastMessageId = m.id;
  });
  scrollToBottom();
}

function renderMessage(m) {
  const isOwn = currentUser && m.user_id === currentUser.id;
  const name  = m.full_name || m.email || 'Unknown';
  const time  = new Date(m.created_at).toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit'});
  const wrapClass = isOwn ? 'msg-own' : 'msg-group';
  const bubbleClass = isOwn ? 'msg-bubble own' : 'msg-bubble';
  const replyHtml = m.reply_to_content ? `
    <div class="reply-preview">
      <strong>${m.reply_to_author || 'Unknown'}</strong>: ${m.reply_to_content}
    </div>` : '';
  return `
    <div class="${wrapClass}" data-msg-id="${m.id}">
      <div class="msg-header">
        <span class="msg-author">${isOwn ? 'You' : name}</span>
        <span class="msg-time">${time}</span>
        <button onclick="startReply(${m.id},'${(m.full_name || m.email || '').replace(/'/g,"\\'")}')"
                style="background:none;border:none;color:var(--text-muted);font-size:11px;cursor:pointer;opacity:0;transition:opacity .15s"
                class="reply-btn" title="Reply">
          <i class="bi bi-reply"></i> Reply
        </button>
      </div>
      ${replyHtml}
      <div class="${bubbleClass}">${escapeHtml(m.content)}</div>
    </div>
  `;
}

document.addEventListener('mouseover', e => {
  const group = e.target.closest('.msg-group, .msg-own');
  if (group) group.querySelectorAll('.reply-btn').forEach(b => b.style.opacity = '1');
});
document.addEventListener('mouseout', e => {
  const group = e.target.closest('.msg-group, .msg-own');
  if (group && !group.contains(e.relatedTarget)) group.querySelectorAll('.reply-btn').forEach(b => b.style.opacity = '0');
});

function startReply(msgId, authorName) {
  replyTo = msgId;
  const banner = document.getElementById('replyBanner');
  if (banner) {
    banner.style.display = 'flex';
    document.getElementById('replyBannerText').innerText = `Replying to ${authorName}`;
  }
  document.getElementById('chatInput')?.focus();
}

function cancelReply() {
  replyTo = null;
  const banner = document.getElementById('replyBanner');
  if (banner) banner.style.display = 'none';
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  if (!input) return;
  const content = input.value.trim();
  if (!content || !currentChannel) return;

  input.value = '';
  input.style.height = '';
  const res = await apiPostMessage(currentChannel.id, content, replyTo);
  if (res.success) {
    cancelReply();
    await pollMessages();
  } else {
    showToast('Failed to send message', 'danger');
    input.value = content;
  }
}

function handleInputKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function scrollToBottom() {
  const container = document.getElementById('chatMessages');
  if (container) container.scrollTop = container.scrollHeight;
}

function showNewChannelModal() {
  document.getElementById('newChannelName').value = '';
  document.getElementById('newChannelDesc').value = '';
  new bootstrap.Modal(document.getElementById('newChannelModal')).show();
}

async function deleteChannel(id, name) {
  if (!confirm(`Delete #${name} and all its messages? This cannot be undone.`)) return;
  const res = await fetch(`/api/v1/chat/channels/${id}`, {
    method: 'DELETE', headers: authHeaders()
  }).then(r => r.json());
  if (res.success) {
    if (currentChannel && currentChannel.id === id) currentChannel = null;
    showToast(`#${name} deleted`);
    await loadChannels();
  } else {
    showToast(res.error || 'Delete failed', 'danger');
  }
}

async function createChannel() {
  const name = document.getElementById('newChannelName').value.trim();
  const description = document.getElementById('newChannelDesc').value.trim();
  if (!name) { showToast('Channel name is required', 'danger'); return; }

  const res = await apiCreateChannel({ name, description });
  if (res.success) {
    bootstrap.Modal.getInstance(document.getElementById('newChannelModal')).hide();
    await loadChannels();
    showToast(`#${name} created`);
  } else {
    showToast(res.error || 'Failed to create channel', 'danger');
  }
}

function escapeHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

initChat();
