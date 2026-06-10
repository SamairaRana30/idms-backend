// Chart.js global dark defaults
Chart.defaults.color           = '#94a3b8';
Chart.defaults.borderColor     = '#1a2a42';
Chart.defaults.font.family     = 'Poppins, sans-serif';
Chart.defaults.font.size       = 11;
Chart.defaults.plugins.legend.labels.boxWidth = 10;

const ACCENT   = '#0ea5e9';
const SUCCESS  = '#10b981';
const DANGER   = '#ef4444';
const WARNING  = '#f59e0b';
const INDIGO   = '#6366f1';
const MUTED_BG = 'rgba(255,255,255,0.04)';

async function initDashboard() {
    const res = await apiGetMe();
    if (res.success) {
        const u = res.data.user;
        localStorage.setItem('userName',  u.full_name || u.email);
        localStorage.setItem('userEmail', u.email);
        localStorage.setItem('role',      u.role);
        localStorage.setItem('userId',    u.id);

        const avatarEl = document.getElementById('avatarInitial');
        const emailEl  = document.getElementById('sidebarEmail');
        const roleEl   = document.getElementById('sidebarRole');
        if (avatarEl) avatarEl.innerText = (u.full_name || u.email)[0].toUpperCase();
        if (emailEl)  emailEl.innerText  = u.full_name || u.email;
        if (roleEl)   roleEl.innerText   = u.role;

        document.getElementById('welcome').innerText      = `Welcome back, ${u.full_name || 'User'}!`;
        document.getElementById('profileName').innerText  = u.full_name || '—';
        document.getElementById('profileEmail').innerText = u.email     || '—';
        document.getElementById('profileRole').innerText  = u.role      || '—';

        if (u.role === 'admin') {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = '');
            document.getElementById('usersCard').style.display    = 'block';
            document.getElementById('statsGrid').style.display    = 'grid';
            document.getElementById('chartsSection').style.display = 'block';
            loadAdminData();
        }
    } else {
        document.getElementById('welcome').innerText      = `Welcome back, ${getUserName() || 'User'}!`;
        document.getElementById('profileName').innerText  = getUserName()  || '—';
        document.getElementById('profileEmail').innerText = localStorage.getItem('userEmail') || '—';
        document.getElementById('profileRole').innerText  = getRole()      || '—';
    }
}

async function loadAdminData() {
    showLoading('usersTableBody', 4);
    const [statsRes, finRes, usersRes] = await Promise.all([
        apiGetUserStats(),
        apiGetFinanceReport(),
        apiGetUsers(1, 50)
    ]);

    if (statsRes.success) renderMemberStats(statsRes.data);
    if (finRes.success)   renderFinanceCharts(finRes.data);
    if (usersRes.success) renderUsersTable(usersRes.data);
}

function renderMemberStats(data) {
    document.getElementById('statTotal').innerText  = data.total  ?? '—';
    document.getElementById('statActive').innerText = data.active ?? '—';
    document.getElementById('statAdmins').innerText = data.admins ?? '—';

    // Member breakdown donut
    const donut = document.getElementById('memberDonut');
    if (!donut) return;
    new Chart(donut, {
        type: 'doughnut',
        data: {
            labels: ['Active', 'Inactive', 'Admins'],
            datasets: [{
                data: [data.active, data.inactive, data.admins],
                backgroundColor: [SUCCESS, DANGER, ACCENT],
                borderColor: '#0d1626',
                borderWidth: 3,
                hoverOffset: 6
            }]
        },
        options: {
            cutout: '72%',
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}` } }
            }
        }
    });

    document.getElementById('donutLegend').innerHTML = [
        { label: 'Active Members', color: SUCCESS, value: data.active },
        { label: 'Inactive', color: DANGER, value: data.inactive },
        { label: 'Admins', color: ACCENT, value: data.admins }
    ].map(i => `
        <div class="donut-legend-item">
          <div class="donut-legend-dot" style="background:${i.color}"></div>
          <span>${i.label}</span>
          <span style="margin-left:auto;font-weight:600;color:var(--text-primary)">${i.value}</span>
        </div>
    `).join('');

    // Member growth line chart
    if (data.growth && data.growth.length) {
        const growthEl = document.getElementById('growthChart');
        if (growthEl) {
            new Chart(growthEl, {
                type: 'line',
                data: {
                    labels: data.growth.map(d => fmtMonth(d.month)),
                    datasets: [{
                        label: 'New Members',
                        data: data.growth.map(d => d.new_members),
                        borderColor: ACCENT,
                        backgroundColor: 'rgba(14,165,233,0.12)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: ACCENT,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: chartOpts('Members')
            });
        }
    } else {
        const el = document.getElementById('growthChart');
        if (el) el.parentElement.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px 0">No growth data for the last 6 months</div>';
    }
}

function renderFinanceCharts(data) {
    const bd = (data.breakdown || []).slice().reverse().slice(0, 6);

    // Summary cards
    if (data.breakdown) {
        let totalIncome = 0, totalExpense = 0;
        data.breakdown.forEach(b => { totalIncome += b.income || 0; totalExpense += b.expense || 0; });
        const balance = totalIncome - totalExpense;
        document.getElementById('finIncome').innerText  = fmtCurrency(totalIncome);
        document.getElementById('finExpense').innerText = fmtCurrency(totalExpense);
        const balEl = document.getElementById('finBalance');
        balEl.innerText = fmtCurrency(balance);
        balEl.style.color = balance >= 0 ? SUCCESS : DANGER;
        document.getElementById('statBalance').innerText = fmtCurrency(balance);
        document.getElementById('statBalance').style.color = balance >= 0 ? SUCCESS : DANGER;
    }

    if (!bd.length) {
        const el = document.getElementById('financeChart');
        if (el) el.parentElement.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px 0">No finance data yet</div>';
        return;
    }

    const finEl = document.getElementById('financeChart');
    if (!finEl) return;
    new Chart(finEl, {
        type: 'bar',
        data: {
            labels: bd.map(d => fmtMonth(d.month)),
            datasets: [
                {
                    label: 'Income',
                    data: bd.map(d => d.income  || 0),
                    backgroundColor: 'rgba(16,185,129,0.7)',
                    borderColor: SUCCESS,
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Expenses',
                    data: bd.map(d => d.expense || 0),
                    backgroundColor: 'rgba(239,68,68,0.6)',
                    borderColor: DANGER,
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            ...chartOpts('Amount (£)'),
            plugins: {
                ...chartOpts('Amount (£)').plugins,
                legend: { display: true, position: 'top', labels: { color: '#94a3b8', boxWidth: 12, padding: 16 } }
            }
        }
    });
}

function renderUsersTable(data) {
    const { users, total } = data;
    document.getElementById('usersTableBody').innerHTML = users.map(u => `
        <tr>
            <td>${u.full_name || '—'}</td>
            <td>${u.email}</td>
            <td><span class="badge badge-${u.role}">${u.role}</span></td>
            <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
        </tr>
    `).join('');
}

function chartOpts(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: '#0d1626', borderColor: '#1a2a42', borderWidth: 1, titleColor: '#f1f5f9', bodyColor: '#94a3b8', padding: 10 }
        },
        scales: {
            x: { grid: { color: '#1a2a42' }, ticks: { color: '#475569' } },
            y: { grid: { color: '#1a2a42' }, ticks: { color: '#475569' }, title: { display: false } }
        }
    };
}

function fmtMonth(str) {
    if (!str) return '';
    const [y, m] = str.split('-');
    return new Date(y, m - 1).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' });
}

function fmtCurrency(val) {
    return '£' + Number(val).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

initDashboard();
