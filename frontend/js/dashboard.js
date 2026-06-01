async function initDashboard() {
    // Load live profile from API instead of relying on stale localStorage
    const res = await apiGetMe();
    if (res.success) {
        const u = res.data.user;

        // Refresh localStorage so sidebar/other pages stay in sync
        localStorage.setItem('userName',  u.full_name || u.email);
        localStorage.setItem('userEmail', u.email);
        localStorage.setItem('role',      u.role);
        localStorage.setItem('userId',    u.id);

        // Update sidebar
        const avatarEl = document.getElementById('avatarInitial');
        const emailEl  = document.getElementById('sidebarEmail');
        const roleEl   = document.getElementById('sidebarRole');
        if (avatarEl) avatarEl.innerText = (u.full_name || u.email)[0].toUpperCase();
        if (emailEl)  emailEl.innerText  = u.full_name || u.email;
        if (roleEl)   roleEl.innerText   = u.role;

        // Welcome + profile card
        document.getElementById('welcome').innerText     = `Welcome back, ${u.full_name || 'User'}!`;
        document.getElementById('profileName').innerText  = u.full_name || '—';
        document.getElementById('profileEmail').innerText = u.email     || '—';
        document.getElementById('profileRole').innerText  = u.role      || '—';

        // Admin section
        if (u.role === 'admin') {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
            document.getElementById('usersCard').style.display  = 'block';
            document.getElementById('statsGrid').style.display  = 'grid';
            loadAdminStats();
        }
    } else {
        // Fallback to localStorage if API call fails
        document.getElementById('welcome').innerText     = `Welcome back, ${getUserName() || 'User'}!`;
        document.getElementById('profileName').innerText  = getUserName()  || '—';
        document.getElementById('profileEmail').innerText = localStorage.getItem('userEmail') || '—';
        document.getElementById('profileRole').innerText  = getRole()      || '—';
    }
}

async function loadAdminStats() {
    showLoading('usersTableBody', 4);
    const res = await apiGetUsers();
    if (!res.success) return;

    const { users, total } = res.data;
    document.getElementById('statTotal').innerText  = total;
    document.getElementById('statActive').innerText = users.filter(u => u.is_active).length;
    document.getElementById('statAdmins').innerText = users.filter(u => u.role === 'admin').length;

    document.getElementById('usersTableBody').innerHTML = users.map(u => `
        <tr>
            <td>${u.full_name || '—'}</td>
            <td>${u.email}</td>
            <td><span class="badge badge-${u.role}">${u.role}</span></td>
            <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
        </tr>
    `).join('');
}

initDashboard();
