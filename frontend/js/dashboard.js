// dashboard.js — runs after api.js and main.js are loaded

document.getElementById('welcome').innerText = `Welcome back, ${getUserName() || 'User'}!`;

const nameEl  = document.getElementById('profileName');
const emailEl = document.getElementById('profileEmail');
const roleEl  = document.getElementById('profileRole');

if (nameEl)  nameEl.innerText  = getUserName() || '—';
if (emailEl) emailEl.innerText = localStorage.getItem('userEmail') || '—';
if (roleEl)  roleEl.innerText  = getRole() || '—';

if (getRole() === 'admin') {
  document.getElementById('usersCard').style.display  = 'block';
  document.getElementById('statsGrid').style.display  = 'grid';

  apiGetUsers().then(data => {
    if (!data.success) return;
    const users = data.users;

    document.getElementById('statTotal').innerText   = users.length;
    document.getElementById('statActive').innerText  = users.filter(u => u.is_active).length;
    document.getElementById('statAdmins').innerText  = users.filter(u => u.role === 'admin').length;

    document.getElementById('usersTableBody').innerHTML = users.map(u => `
      <tr>
        <td>${u.full_name || '—'}</td>
        <td>${u.email}</td>
        <td><span class="badge badge-${u.role}">${u.role}</span></td>
        <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
      </tr>
    `).join('');
  });
}
