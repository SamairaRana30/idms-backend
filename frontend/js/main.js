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

function initSidebar() {
  const name = getUserName() || 'User';
  const role = getRole() || 'member';

  const avatarEl    = document.getElementById('avatarInitial');
  const emailEl     = document.getElementById('sidebarEmail');
  const roleEl      = document.getElementById('sidebarRole');

  if (avatarEl)  avatarEl.innerText  = name[0].toUpperCase();
  if (emailEl)   emailEl.innerText   = name;
  if (roleEl)    roleEl.innerText    = role;

  // Show admin-only nav items
  if (role === 'admin') {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
  }

  // Mark active nav item by current path
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(a => {
    if (path.includes(a.getAttribute('href'))) {
      a.classList.add('active');
    }
  });
}

// Run on every page load
document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initSidebar();
});
