let allMembers = [];
let filtered   = [];
let currentPage = 1;
const PAGE_SIZE  = 20;
let editingId    = null;
let pendingToggleId     = null;
let pendingToggleActive = true;

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadMembers() {
  const tbody = document.getElementById('membersBody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading…</td></tr>';

  const res = await apiGetUsers(1, 1000);
  if (!res.success) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">${res.error || 'Failed to load members'}</td></tr>`;
    return;
  }

  allMembers = res.data.users || [];
  applyFilter();
}

// ── Filter + Render ───────────────────────────────────────────────────────────

function applyFilter() {
  const q = ((document.getElementById('searchInput') || {}).value || '').toLowerCase().trim();
  filtered = q
    ? allMembers.filter(m =>
        (m.full_name || '').toLowerCase().includes(q) ||
        (m.email     || '').toLowerCase().includes(q) ||
        (m.role      || '').toLowerCase().includes(q)
      )
    : [...allMembers];
  currentPage = 1;
  renderTable();
  renderPagination();
}

function filterTable(q) {
  applyFilter();
}

function renderTable() {
  const tbody = document.getElementById('membersBody');
  if (!tbody) return;
  const start = (currentPage - 1) * PAGE_SIZE;
  const page  = filtered.slice(start, start + PAGE_SIZE);

  if (!page.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No members found</td></tr>';
    return;
  }

  tbody.innerHTML = page.map(m => `
    <tr>
      <td>${esc(m.full_name || '—')}</td>
      <td style="word-break:break-all">${esc(m.email || '—')}</td>
      <td><span class="badge badge-${m.role}">${m.role}</span></td>
      <td><span class="badge badge-${m.is_active ? 'active' : 'inactive'}">${m.is_active ? 'Active' : 'Inactive'}</span></td>
      <td>${m.created_at ? new Date(m.created_at).toLocaleDateString('en-GB') : '—'}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary me-1"
          onclick="openEdit('${m.id}','${escAttr(m.full_name)}','${m.role}','${m.is_active}')">Edit</button>
        <button class="btn btn-sm ${m.is_active ? 'btn-outline-danger' : 'btn-outline-success'}"
          onclick="confirmToggle('${m.id}','${escAttr(m.full_name)}',${m.is_active})">
          ${m.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </td>
    </tr>
  `).join('');
}

function renderPagination() {
  const el = document.getElementById('paginationControls');
  if (!el) return;
  const total = filtered.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  if (pages <= 1) { el.innerHTML = ''; return; }

  const from = Math.min((currentPage - 1) * PAGE_SIZE + 1, total);
  const to   = Math.min(currentPage * PAGE_SIZE, total);
  let html = `<span class="text-muted me-2" style="font-size:12px">Showing ${from}–${to} of ${total}</span>`;
  html += '<div class="btn-group btn-group-sm">';
  html += `<button class="btn btn-outline-secondary" onclick="goPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>‹</button>`;
  for (let p = Math.max(1, currentPage - 2); p <= Math.min(pages, currentPage + 2); p++) {
    html += `<button class="btn btn-outline-secondary${p === currentPage ? ' active' : ''}" onclick="goPage(${p})">${p}</button>`;
  }
  html += `<button class="btn btn-outline-secondary" onclick="goPage(${currentPage + 1})" ${currentPage === pages ? 'disabled' : ''}>›</button>`;
  html += '</div>';
  el.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PAGE_SIZE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderTable();
  renderPagination();
}

// ── Edit modal ────────────────────────────────────────────────────────────────

function openEdit(id, name, role, isActive) {
  editingId = id;
  document.getElementById('editName').value    = name;
  document.getElementById('editRole').value    = role;
  document.getElementById('editActive').checked = (isActive === 'true' || isActive === true);
  new bootstrap.Modal(document.getElementById('editModal')).show();
}

async function saveEdit() {
  const data = {
    full_name: document.getElementById('editName').value.trim(),
    role:      document.getElementById('editRole').value,
    is_active: document.getElementById('editActive').checked
  };
  if (!data.full_name) { showToast('Name is required', 'danger'); return; }
  const res = await apiUpdateUser(editingId, data);
  if (res.success) {
    bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
    showToast('Member updated');
    loadMembers();
  } else {
    showToast(res.error || 'Update failed', 'danger');
  }
}

// ── Toggle active ─────────────────────────────────────────────────────────────

function confirmToggle(id, name, isActive) {
  pendingToggleId     = id;
  pendingToggleActive = (isActive === true || isActive === 'true');
  const action = pendingToggleActive ? 'deactivate' : 'activate';
  const body   = document.getElementById('deleteModalBody');
  if (body) body.innerHTML = `Are you sure you want to <strong>${action}</strong> <strong>${esc(name)}</strong>?`;
  new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

async function deleteConfirmed() {
  bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
  let res;
  if (pendingToggleActive) {
    res = await apiDeleteUser(pendingToggleId);
  } else {
    res = await apiUpdateUser(pendingToggleId, { is_active: true });
  }
  if (res.success) {
    showToast(pendingToggleActive ? 'Member deactivated' : 'Member activated');
    loadMembers();
  } else {
    showToast(res.error || 'Action failed', 'danger');
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escAttr(s) {
  return String(s).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// ── Boot ──────────────────────────────────────────────────────────────────────
loadMembers();
