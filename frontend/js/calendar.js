let currentDate = new Date();
let allEvents   = [];
let selectedDay = null;

const DAY_LABELS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

// Use LOCAL date string (YYYY-MM-DD) to avoid UTC-shift mismatches
function localStr(date) {
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
}

async function loadEvents() {
  try {
    const [meetRes, ballotRes] = await Promise.all([
      apiGetMeetings(1, 100),
      apiGetBallots(1, 100)
    ]);
    allEvents = [];
    if (meetRes.success) {
      allEvents.push(...meetRes.data.meetings.map(m => ({
        id: m.id, title: m.title,
        date: m.scheduled_at ? localStr(new Date(m.scheduled_at)) : null,
        time: m.scheduled_at ? new Date(m.scheduled_at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'}) : '',
        type: 'meeting', status: m.status,
        location: m.location || ''
      })));
    }
    if (ballotRes.success) {
      allEvents.push(...ballotRes.data.ballots.flatMap(b => {
        const evs = [];
        if (b.start_date) evs.push({ id:b.id, title:`Vote opens: ${b.title}`, date:localStr(new Date(b.start_date)), time:'', type:'voting', status:b.status });
        if (b.end_date)   evs.push({ id:b.id, title:`Vote closes: ${b.title}`, date:localStr(new Date(b.end_date)),   time:'', type:'voting', status:b.status });
        return evs;
      }));
    }
    renderCalendar();
    renderMonthList();
    renderListView();
  } catch(e) { console.error(e); }
}

function renderCalendar() {
  const y = currentDate.getFullYear();
  const m = currentDate.getMonth();
  document.getElementById('calMonthLabel').innerText = `${MONTHS[m]} ${y}`;

  const grid = document.getElementById('calGrid');
  grid.innerHTML = DAY_LABELS.map(d => `<div class="cal-day-label">${d}</div>`).join('');

  const firstDay = new Date(y, m, 1).getDay();
  const daysInMonth = new Date(y, m+1, 0).getDate();
  const today = localStr(new Date());

  // Cells from previous month
  for (let i = 0; i < firstDay; i++) {
    const d = new Date(y, m, -(firstDay - i - 1));
    grid.appendChild(makeCell(d, true));
  }

  // Current month cells
  for (let day = 1; day <= daysInMonth; day++) {
    const d = new Date(y, m, day);
    const cell = makeCell(d, false);
    if (localStr(d) === today) cell.classList.add('today');
    if (selectedDay && localStr(d) === selectedDay) cell.classList.add('selected');
    grid.appendChild(cell);
  }

  // Fill remaining cells
  const total = firstDay + daysInMonth;
  const remaining = total % 7 === 0 ? 0 : 7 - (total % 7);
  for (let i = 1; i <= remaining; i++) {
    grid.appendChild(makeCell(new Date(y, m+1, i), true));
  }
}

function makeCell(date, otherMonth) {
  const dateStr = localStr(date);
  const dayEvents = allEvents.filter(e => e.date === dateStr);
  const cell = document.createElement('div');
  cell.className = 'cal-cell' + (otherMonth ? ' other-month' : '');
  cell.innerHTML = `<div class="cal-date">${date.getDate()}</div>` +
    dayEvents.slice(0,3).map(e => `<div class="cal-event ${e.type}" title="${e.title}">${e.title}</div>`).join('') +
    (dayEvents.length > 3 ? `<div style="font-size:10px;color:var(--text-muted);margin-top:2px">+${dayEvents.length-3} more</div>` : '');
  cell.onclick = () => selectDay(dateStr);
  return cell;
}

function selectDay(dateStr) {
  selectedDay = dateStr;
  renderCalendar();
  const dayEvents = allEvents.filter(e => e.date === dateStr);
  const label = document.getElementById('selectedDateLabel');
  const container = document.getElementById('selectedDayEvents');
  label.innerText = new Date(dateStr+'T00:00:00').toLocaleDateString('en-GB',{weekday:'long',month:'long',day:'numeric'});
  if (!dayEvents.length) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:12px 0">No events</div>';
    return;
  }
  container.innerHTML = dayEvents.map(e => `
    <div class="event-item">
      <div style="display:flex;align-items:flex-start;gap:8px">
        <div class="event-dot" style="background:${e.type==='meeting'?'var(--success)':e.type==='voting'?'var(--warning)':'var(--accent)'}"></div>
        <div>
          <div class="event-item-title">${e.title}</div>
          <div class="event-item-meta">
            ${e.time ? `<span><i class="bi bi-clock"></i> ${e.time}</span>` : ''}
            ${e.location ? `<span><i class="bi bi-geo-alt"></i> ${e.location}</span>` : ''}
            <span class="badge badge-${e.status}" style="font-size:10px">${e.status}</span>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

function renderMonthList() {
  const y = currentDate.getFullYear();
  const m = currentDate.getMonth();
  const monthStr = `${y}-${String(m+1).padStart(2,'0')}`;
  const monthEvents = allEvents.filter(e => e.date && e.date.startsWith(monthStr))
    .sort((a,b) => a.date.localeCompare(b.date));

  const container = document.getElementById('monthEventsList');
  if (!monthEvents.length) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:12px 0">No events this month</div>';
    return;
  }
  container.innerHTML = monthEvents.slice(0,8).map(e => `
    <div class="event-item" style="cursor:pointer" onclick="selectDay('${e.date}')">
      <div class="event-item-title">${e.title}</div>
      <div class="event-item-meta">
        <span>${new Date(e.date+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short'})}</span>
        ${e.time ? `<span>${e.time}</span>` : ''}
      </div>
    </div>
  `).join('');
}

function renderListView() {
  const today = localStr(new Date());
  const upcoming = allEvents.filter(e => e.date >= today).sort((a,b) => a.date.localeCompare(b.date));
  const container = document.getElementById('listViewContent');
  if (!upcoming.length) {
    container.innerHTML = '<div class="empty-state"><p>No upcoming events</p></div>';
    return;
  }
  container.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Event</th><th>Type</th><th>Date</th><th>Time</th><th>Status</th></tr></thead>
      <tbody>
        ${upcoming.map(e => `
          <tr>
            <td>${e.title}</td>
            <td><span class="badge badge-${e.type==='meeting'?'scheduled':'draft'}">${e.type}</span></td>
            <td>${new Date(e.date+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'})}</td>
            <td>${e.time || '—'}</td>
            <td><span class="badge badge-${e.status}">${e.status}</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function changeMonth(dir) {
  currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + dir, 1);
  selectedDay = null;
  renderCalendar();
  renderMonthList();
}

function goToday() {
  currentDate = new Date();
  selectedDay = new Date().toISOString().slice(0,10);
  renderCalendar();
  renderMonthList();
  selectDay(selectedDay);
}

function setView(view, btn) {
  document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('monthView').style.display = view === 'month' ? 'block' : 'none';
  document.getElementById('listView').style.display  = view === 'list'  ? 'block' : 'none';
}

loadEvents();
