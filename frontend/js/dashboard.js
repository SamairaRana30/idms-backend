document.getElementById('welcome').innerText = `Welcome back, ${getUserName() || 'User'}!`;

document.getElementById('profileName').innerText  = getUserName() || '—';
document.getElementById('profileEmail').innerText = localStorage.getItem('userEmail') || '—';
document.getElementById('profileRole').innerText  = getRole() || '—';

if (getRole() === 'admin') {
    document.getElementById('usersCard').style.display = 'block';
    document.getElementById('statsGrid').style.display = 'grid';

    apiGetUsers().then(res => {
        if (!res.success) return;
        const { users } = res.data;

        document.getElementById('statTotal').innerText  = res.data.total;
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
    });
}
