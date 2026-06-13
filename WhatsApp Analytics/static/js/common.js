const CHART_COLORS = {
    primary: '#128c7e',
    primaryLight: 'rgba(37, 211, 102, 0.15)',
    gradient: ['#075e54', '#128c7e', '#25d366', '#34b7f1', '#ffc107'],
    pie: ['#25d366', '#128c7e', '#667781', '#34b7f1', '#ffc107'],
    bar: '#128c7e',
    barHover: '#075e54',
};

Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.color = '#667781';

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function getAuthHeaders() {
    const token = getCookie('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(url) {
    const response = await fetch(url, { credentials: 'same-origin', headers: getAuthHeaders() });
    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || 'Request failed');
    }
    return response.json();
}

function getSelectedGroupId() {
    const select = document.getElementById('groupSelect');
    return select ? select.value : null;
}

function onGroupChange(callback) {
    const select = document.getElementById('groupSelect');
    if (select) {
        select.addEventListener('change', callback);
        if (select.value) callback();
    }
}

function destroyChart(chart) {
    if (chart) chart.destroy();
}

function barChart(ctx, labels, data, label = 'Count') {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label,
                data,
                backgroundColor: CHART_COLORS.bar,
                hoverBackgroundColor: CHART_COLORS.barHover,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f0f2f5' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function pieChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: CHART_COLORS.pie,
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            cutout: '55%',
            plugins: {
                legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } }
            }
        }
    });
}

function lineChart(ctx, labels, data, label = 'Messages') {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label,
                data,
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.primaryLight,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: CHART_COLORS.primary,
                pointRadius: 4,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f0f2f5' } },
                x: { grid: { display: false } }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (toggle && sidebar && overlay) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        });
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
});
