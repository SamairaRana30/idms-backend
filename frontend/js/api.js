const API = '/api/v1';

function authHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function authHeadersNoContent() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
}

// ── Auth ──────────────────────────────────────────────────────────────────────
async function apiRegister(full_name, email, password) {
    const r = await fetch(`${API}/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name, email, password })
    });
    return r.json();
}

async function apiLogin(email, password) {
    const r = await fetch(`${API}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    return r.json();
}

async function apiProfile() {
    const r = await fetch(`${API}/auth/profile`, { headers: authHeaders() });
    return r.json();
}

// ── Users ─────────────────────────────────────────────────────────────────────
async function apiGetMe() {
    const r = await fetch(`${API}/users/me`, { headers: authHeaders() });
    return r.json();
}

async function apiUpdateMe(data) {
    const r = await fetch(`${API}/users/me`, {
        method: 'PUT', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

async function apiGetUsers(page = 1, limit = 20) {
    const r = await fetch(`${API}/users?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

async function apiUpdateUser(userId, data) {
    const r = await fetch(`${API}/users/${userId}`, {
        method: 'PUT', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

async function apiDeleteUser(userId) {
    const r = await fetch(`${API}/users/${userId}`, {
        method: 'DELETE', headers: authHeaders()
    });
    return r.json();
}

// ── Migration ─────────────────────────────────────────────────────────────────
async function apiMigrationPreview(formData) {
    const r = await fetch(`${API}/migration/upload`, {
        method: 'POST', headers: authHeadersNoContent(), body: formData
    });
    return r.json();
}

async function apiMigrationImport(formData) {
    const r = await fetch(`${API}/migration/import`, {
        method: 'POST', headers: authHeadersNoContent(), body: formData
    });
    return r.json();
}

// ── Documents ─────────────────────────────────────────────────────────────────
async function apiUploadDocument(formData) {
    const r = await fetch(`${API}/documents/upload`, {
        method: 'POST', headers: authHeadersNoContent(), body: formData
    });
    return r.json();
}

async function apiGetDocuments(page = 1, limit = 20, category = '') {
    const params = new URLSearchParams({ page, limit });
    if (category) params.set('category', category);
    const r = await fetch(`${API}/documents?${params}`, { headers: authHeaders() });
    return r.json();
}

async function apiSearchDocuments(q) {
    const r = await fetch(`${API}/documents/search?q=${encodeURIComponent(q)}`, { headers: authHeaders() });
    return r.json();
}

async function apiDownloadDocument(docId) {
    const r = await fetch(`${API}/documents/${docId}/download`, { headers: authHeaders() });
    return r.json();
}

async function apiDeleteDocument(docId) {
    const r = await fetch(`${API}/documents/${docId}`, {
        method: 'DELETE', headers: authHeaders()
    });
    return r.json();
}

// ── Voting ────────────────────────────────────────────────────────────────────
async function apiGetBallots(page = 1, limit = 20) {
    const r = await fetch(`${API}/ballots?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

async function apiGetBallot(ballotId) {
    const r = await fetch(`${API}/ballots/${ballotId}`, { headers: authHeaders() });
    return r.json();
}

async function apiCreateBallot(data) {
    const r = await fetch(`${API}/ballots`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

async function apiOpenBallot(ballotId) {
    const r = await fetch(`${API}/ballots/${ballotId}/open`, {
        method: 'PUT', headers: authHeaders()
    });
    return r.json();
}

async function apiCloseBallot(ballotId) {
    const r = await fetch(`${API}/ballots/${ballotId}/close`, {
        method: 'PUT', headers: authHeaders()
    });
    return r.json();
}

async function apiCastVote(ballotId, optionId) {
    const r = await fetch(`${API}/ballots/${ballotId}/vote`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({ option_id: optionId })
    });
    return r.json();
}

async function apiDeleteBallot(ballotId) {
    const r = await fetch(`${API}/ballots/${ballotId}`, {
        method: 'DELETE', headers: authHeaders()
    });
    return r.json();
}

async function apiGetBallotResults(ballotId) {
    const r = await fetch(`${API}/ballots/${ballotId}/results`, { headers: authHeaders() });
    return r.json();
}

// ── Meetings ──────────────────────────────────────────────────────────────────
async function apiGetMeetings(page = 1, limit = 50, status = '') {
    const params = new URLSearchParams({ page, limit });
    if (status) params.set('status', status);
    const r = await fetch(`${API}/meetings?${params}`, { headers: authHeaders() });
    return r.json();
}

async function apiGetMeeting(meetingId) {
    const r = await fetch(`${API}/meetings/${meetingId}`, { headers: authHeaders() });
    return r.json();
}

async function apiCreateMeeting(data) {
    const r = await fetch(`${API}/meetings`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

async function apiSaveMinutes(meetingId, minutes) {
    const r = await fetch(`${API}/meetings/${meetingId}/minutes`, {
        method: 'PUT', headers: authHeaders(), body: JSON.stringify({ minutes })
    });
    return r.json();
}

async function apiCompleteMeeting(meetingId) {
    const r = await fetch(`${API}/meetings/${meetingId}/complete`, {
        method: 'PUT', headers: authHeaders()
    });
    return r.json();
}

async function apiArchiveMeeting(meetingId) {
    const r = await fetch(`${API}/meetings/${meetingId}/archive`, {
        method: 'PUT', headers: authHeaders()
    });
    return r.json();
}

async function apiSendInvitations(meetingId) {
    const r = await fetch(`${API}/meetings/${meetingId}/invite`, {
        method: 'POST', headers: authHeaders()
    });
    return r.json();
}

async function apiDeleteMeeting(meetingId) {
    const r = await fetch(`${API}/meetings/${meetingId}`, {
        method: 'DELETE', headers: authHeaders()
    });
    return r.json();
}

// ── Notifications ─────────────────────────────────────────────────────────────
async function apiGetNotifications(page = 1, limit = 20) {
    const r = await fetch(`${API}/notifications?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

async function apiSendNotification(data) {
    const r = await fetch(`${API}/notifications`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

// ── Finances ──────────────────────────────────────────────────────────────────
async function apiGetFinances(page = 1, limit = 20) {
    const r = await fetch(`${API}/finances?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

async function apiAddFinanceRecord(data) {
    const r = await fetch(`${API}/finances`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}

async function apiDeleteFinanceRecord(recordId) {
    const r = await fetch(`${API}/finances/${recordId}`, {
        method: 'DELETE', headers: authHeaders()
    });
    return r.json();
}

// ── Audit ─────────────────────────────────────────────────────────────────────
async function apiGetAuditLog(page = 1, limit = 20) {
    const r = await fetch(`${API}/audit?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

// ── Analytics ─────────────────────────────────────────────────────────────────
async function apiGetAnalytics(page = 1, limit = 20) {
    const r = await fetch(`${API}/analytics?page=${page}&limit=${limit}`, { headers: authHeaders() });
    return r.json();
}

async function apiUploadAnalytics(data) {
    const r = await fetch(`${API}/analytics`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
    });
    return r.json();
}
