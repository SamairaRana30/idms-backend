// Centralised API helpers — import or include before page-specific scripts

const API = '/api/v1';

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  };
}

// ── Auth ─────────────────────────────────────────────────────────────────────
async function apiRegister(full_name, email, password) {
  const r = await fetch(`${API}/auth/register`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ full_name, email, password })
  });
  return r.json();
}

async function apiLogin(email, password) {
  const r = await fetch(`${API}/auth/login`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ email, password })
  });
  return r.json();
}

async function apiProfile() {
  const r = await fetch(`${API}/auth/profile`, { headers: authHeaders() });
  return r.json();
}

// ── Users ─────────────────────────────────────────────────────────────────────
async function apiGetUsers() {
  const r = await fetch(`${API}/users`, { headers: authHeaders() });
  return r.json();
}

async function apiUpdateUser(userId, data) {
  const r = await fetch(`${API}/users/${userId}`, {
    method: 'PATCH', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}

async function apiDeleteUser(userId) {
  const r = await fetch(`${API}/users/${userId}`, {
    method: 'DELETE', headers: authHeaders()
  });
  return r.json();
}

// ── Documents ─────────────────────────────────────────────────────────────────
async function apiGetDocuments() {
  const r = await fetch(`${API}/documents`, { headers: authHeaders() });
  return r.json();
}

async function apiCreateDocument(data) {
  const r = await fetch(`${API}/documents`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}

async function apiDeleteDocument(docId) {
  const r = await fetch(`${API}/documents/${docId}`, {
    method: 'DELETE', headers: authHeaders()
  });
  return r.json();
}

// ── Voting ────────────────────────────────────────────────────────────────────
async function apiGetBallots() {
  const r = await fetch(`${API}/voting/ballots`, { headers: authHeaders() });
  return r.json();
}

async function apiGetBallot(ballotId) {
  const r = await fetch(`${API}/voting/ballots/${ballotId}`, { headers: authHeaders() });
  return r.json();
}

async function apiCreateBallot(data) {
  const r = await fetch(`${API}/voting/ballots`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}

async function apiCastVote(ballotId, optionId) {
  const r = await fetch(`${API}/voting/ballots/${ballotId}/vote`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify({ option_id: optionId })
  });
  return r.json();
}

async function apiUpdateBallotStatus(ballotId, status) {
  const r = await fetch(`${API}/voting/ballots/${ballotId}/status`, {
    method: 'PATCH', headers: authHeaders(), body: JSON.stringify({ status })
  });
  return r.json();
}

// ── Meetings ──────────────────────────────────────────────────────────────────
async function apiGetMeetings() {
  const r = await fetch(`${API}/meetings`, { headers: authHeaders() });
  return r.json();
}

async function apiCreateMeeting(data) {
  const r = await fetch(`${API}/meetings`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}

async function apiUpdateMeeting(meetingId, data) {
  const r = await fetch(`${API}/meetings/${meetingId}`, {
    method: 'PATCH', headers: authHeaders(), body: JSON.stringify(data)
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
async function apiGetNotifications() {
  const r = await fetch(`${API}/notifications`, { headers: authHeaders() });
  return r.json();
}

async function apiSendNotification(data) {
  const r = await fetch(`${API}/notifications`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}

// ── Finances ──────────────────────────────────────────────────────────────────
async function apiGetFinances() {
  const r = await fetch(`${API}/finances`, { headers: authHeaders() });
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

// ── Analytics ─────────────────────────────────────────────────────────────────
async function apiGetAnalytics() {
  const r = await fetch(`${API}/analytics`, { headers: authHeaders() });
  return r.json();
}

async function apiUploadAnalytics(data) {
  const r = await fetch(`${API}/analytics`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  return r.json();
}
