// Shared auth + sidebar logic — included on every protected page

function getToken()    { return localStorage.getItem('token'); }
function getUserName() { return localStorage.getItem('userName'); }
function getRole()     { return localStorage.getItem('role'); }
function getUserId()   { return localStorage.getItem('userId'); }

function requireAuth() {
  if (!getToken()) {
    window.location.href = '/frontend/index.html';
    return false;
  }
  return true;
}

function logout() {
  localStorage.clear();
  window.location.href = '/frontend/index.html';
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  };
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
    document.body.appendChild(container);
  }

  const colors = { success: '#16a34a', danger: '#dc2626', warning: '#f59e0b', info: '#4f46e5' };
  const icons  = { success: '✓', danger: '✕', warning: '⚠', info: 'ℹ' };

  const toast = document.createElement('div');
  toast.style.cssText = `
    background:#fff; border-left:4px solid ${colors[type]||colors.info};
    border-radius:10px; padding:14px 18px; min-width:260px; max-width:360px;
    box-shadow:0 4px 20px rgba(0,0,0,0.12); display:flex; align-items:center;
    gap:12px; font-size:13px; font-family:Poppins,sans-serif;
    animation:slideIn .25s ease; color:#1e293b;
  `;
  toast.innerHTML = `
    <span style="color:${colors[type]||colors.info};font-weight:700;font-size:16px">${icons[type]||icons.info}</span>
    <span style="flex:1">${message}</span>
    <span style="cursor:pointer;color:#94a3b8;font-size:16px" onclick="this.parentElement.remove()">×</span>
  `;

  if (!document.getElementById('toastStyle')) {
    const style = document.createElement('style');
    style.id = 'toastStyle';
    style.textContent = '@keyframes slideIn{from{transform:translateX(120%);opacity:0}to{transform:translateX(0);opacity:1}}';
    document.head.appendChild(style);
  }

  container.appendChild(toast);
  setTimeout(() => toast.style.opacity = '0', 3500);
  setTimeout(() => toast.remove(), 3800);
}

// ── Loading spinner ───────────────────────────────────────────────────────────
function showLoading(containerId, colSpan = 4) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<tr><td colspan="${colSpan}" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading…</td></tr>`;
}

function initSidebar() {
  const name = getUserName() || 'User';
  const role = getRole() || 'member';

  const avatarEl = document.getElementById('avatarInitial');
  const emailEl  = document.getElementById('sidebarEmail');
  const roleEl   = document.getElementById('sidebarRole');

  if (avatarEl) avatarEl.innerText = name[0].toUpperCase();
  if (emailEl)  emailEl.innerText  = name;
  if (roleEl)   roleEl.innerText   = role;

  if (role === 'admin') {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
  }

  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(a => {
    if (path.includes(a.getAttribute('href'))) a.classList.add('active');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initSidebar();
});
