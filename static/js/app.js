/**
 * ============================================================
 * SMART CAMPUS ATTENDANCE SYSTEM — app.js
 * Handles: Login, Navigation, GPS, Attendance, Tables, Charts,
 *          Modals, Toasts, Clock, Search, and all UI interactions
 * ============================================================
 */

'use strict';

/* ============================================================
   1. APPLICATION STATE
   ============================================================ */
const App = {
  currentRole: 'student',
  currentScreen: '',
  attendanceMarked: true,
  isCheckedIn: true,
  campusTimerSec: 3 * 3600 + 22 * 60 + 14,
  clockInterval: null,
  campusTimerInterval: null,
  gpsInterval: null,
  toastTimeout: null,
  students: [],
  attendance: [],
  entryLogs: [],
};

/* ============================================================
   2. DEMO DATA
   ============================================================ */
const DATA = {
  history: [
    { day: 'Mon', date: '9 Jun',  cin: '08:42 AM', cout: '—',       dur: 'Active',  present: true,  gps: true  },
    { day: 'Fri', date: '6 Jun',  cin: '08:55 AM', cout: '05:18 PM', dur: '8h 23m', present: true,  gps: true  },
    { day: 'Thu', date: '5 Jun',  cin: '09:10 AM', cout: '04:45 PM', dur: '7h 35m', present: true,  gps: true  },
    { day: 'Wed', date: '4 Jun',  cin: '08:30 AM', cout: '05:00 PM', dur: '8h 30m', present: true,  gps: true  },
    { day: 'Tue', date: '3 Jun',  cin: '—',        cout: '—',        dur: '—',       present: false, gps: false },
    { day: 'Mon', date: '2 Jun',  cin: '09:05 AM', cout: '04:50 PM', dur: '7h 45m', present: true,  gps: true  },
    { day: 'Fri', date: '30 May', cin: '08:48 AM', cout: '05:12 PM', dur: '8h 24m', present: true,  gps: true  },
    { day: 'Thu', date: '29 May', cin: '—',        cout: '—',        dur: '—',       present: false, gps: false },
    { day: 'Wed', date: '28 May', cin: '08:55 AM', cout: '04:35 PM', dur: '7h 40m', present: true,  gps: true  },
  ],

  students: [
    { name: 'Alex Kumar',      id: 'CS2401', email: 'alex.kumar@campus.edu',    att: 87, active: true,  last: 'Today 08:42' },
    { name: 'Priya Reddy',     id: 'CS2402', email: 'priya.reddy@campus.edu',   att: 92, active: true,  last: 'Today 12:04' },
    { name: 'Suresh Mehta',    id: 'CS2403', email: 'suresh.m@campus.edu',      att: 76, active: true,  last: 'Today 08:55' },
    { name: 'Nisha Patel',     id: 'CS2404', email: 'nisha.p@campus.edu',       att: 95, active: true,  last: 'Today 08:38' },
    { name: 'Rahul Krishnan',  id: 'CS2405', email: 'rahul.k@campus.edu',       att: 58, active: false, last: 'Fri 6 Jun'   },
    { name: 'Maya Singh',      id: 'CS2406', email: 'maya.s@campus.edu',        att: 68, active: false, last: 'Thu 5 Jun'   },
    { name: 'Vijay Rao',       id: 'CS2407', email: 'vijay.r@campus.edu',       att: 81, active: false, last: 'Today 09:12' },
    { name: 'Anita Thomas',    id: 'CS2408', email: 'anita.t@campus.edu',       att: 72, active: false, last: 'Fri 6 Jun'   },
    { name: 'Deepak Nair',     id: 'CS2409', email: 'deepak.n@campus.edu',      att: 88, active: true,  last: 'Today 08:50' },
    { name: 'Kavitha Rao',     id: 'CS2410', email: 'kavitha.r@campus.edu',     att: 79, active: true,  last: 'Today 09:02' },
  ],

  entryLogs: [
    { name: 'Alex Kumar',   ein: '08:42 AM', eout: '—',       dur: 'Active',  egps: '17.4486°N, 78.3908°E', xgps: '—',                          onCampus: true  },
    { name: 'Priya Reddy',  ein: '12:04 PM', eout: '—',       dur: 'Active',  egps: '17.4491°N, 78.3912°E', xgps: '—',                          onCampus: true  },
    { name: 'Suresh Mehta', ein: '08:55 AM', eout: '11:52 AM', dur: '2h 57m', egps: '17.4488°N, 78.3910°E', xgps: '17.4495°N, 78.3906°E',       onCampus: false },
    { name: 'Nisha Patel',  ein: '08:38 AM', eout: '—',       dur: 'Active',  egps: '17.4482°N, 78.3914°E', xgps: '—',                          onCampus: true  },
    { name: 'Vijay Rao',    ein: '09:12 AM', eout: '—',       dur: 'Active',  egps: '17.4490°N, 78.3909°E', xgps: '—',                          onCampus: true  },
    { name: 'Ravi Kumar',   ein: '08:45 AM', eout: '04:30 PM', dur: '7h 45m', egps: '17.4487°N, 78.3911°E', xgps: '17.4493°N, 78.3907°E',       onCampus: false },
  ],

  attTrend: [1, 1, 0, 1, 1, 1, 1],
  attBarHeights: [38, 42, 0, 40, 44, 36, 14],

  calendarPresent: [2, 3, 5, 6, 7, 9],
  calendarAbsent:  [4, 8],
};

/* ============================================================
   3. UTILITY FUNCTIONS
   ============================================================ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function initials(name) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase();
}

function attColor(pct) {
  if (pct >= 85) return 'var(--success)';
  if (pct >= 75) return 'var(--warn)';
  return 'var(--danger)';
}

function zeroPad(n) {
  return String(n).padStart(2, '0');
}

function formatDuration(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${zeroPad(h)}:${zeroPad(m)}:${zeroPad(s)}`;
}

function avatarHTML(name, size = 30, extraStyle = '') {
  return `<div style="width:${size}px;height:${size}px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:${Math.floor(size*0.38)}px;font-weight:700;flex-shrink:0;${extraStyle}">${initials(name)}</div>`;
}

function progressBarHTML(pct, color) {
  return `<div style="display:flex;align-items:center;gap:.5rem">
    <div style="width:60px;height:6px;background:var(--bg3);border-radius:3px;overflow:hidden">
      <div style="width:${pct}%;height:100%;background:${color};border-radius:3px;transition:width .8s ease"></div>
    </div>
    <span style="font-size:12px;font-weight:700;color:${color}">${pct}%</span>
  </div>`;
}

/* ============================================================
   4. TOAST NOTIFICATION
   ============================================================ */
function showToast(icon, msg, duration = 3500) {
  const toast = $('#toast');
  if (!toast) return;

  clearTimeout(App.toastTimeout);
  toast.classList.remove('show', 'hide');

  $('#toast-icon').textContent = icon;
  $('#toast-msg').textContent = msg;

  toast.classList.add('show');

  App.toastTimeout = setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.classList.remove('show', 'hide'), 300);
  }, duration);
}

/* ============================================================
   5. LOGIN
   ============================================================ */
function setRole(role, btn) {
  App.currentRole = role;
  $$('.role-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const emailInput = $('#login-email');
  if (emailInput) {
    emailInput.value = role === 'admin' ? 'admin@campus.edu' : 'alex.kumar@campus.edu';
  }
}

function quickLogin(role) {
  App.currentRole = role;
  $$('.role-btn').forEach((b, i) => {
    b.classList.toggle('active', (role === 'student' && i === 0) || (role === 'admin' && i === 1));
  });
  doLogin();
}

function doLogin() {
  const loginPage = $('#page-login');
  const appPage = $('#page-app');
  if (!loginPage || !appPage) return;

  // Simulate brief loading
  const submitBtn = loginPage.querySelector('.btn-primary');
  if (submitBtn) {
    submitBtn.textContent = 'Signing in...';
    submitBtn.disabled = true;
  }

  setTimeout(() => {
    if (submitBtn) {
      submitBtn.textContent = 'Sign In →';
      submitBtn.disabled = false;
    }

    loginPage.classList.remove('active');
    appPage.classList.add('active');

    const role = App.currentRole;

    if (role === 'admin') {
      $('#nav-student').style.display = 'none';
      $('#nav-admin').style.display = 'block';
      $('#sb-name').textContent = 'Dr. S. Sharma';
      $('#sb-role').textContent = 'Administrator';
      $('#sb-avatar').textContent = 'SS';
      showScreen('a-dashboard', $('#nav-admin .nav-item'));
    } else {
      $('#nav-student').style.display = 'block';
      $('#nav-admin').style.display = 'none';
      $('#sb-name').textContent = 'Alex Kumar';
      $('#sb-role').textContent = 'Student · CS-A';
      $('#sb-avatar').textContent = 'AK';
      showScreen('s-dashboard', $('#nav-student .nav-item'));
    }

    initAllData();
    startLiveClock();
    startCampusTimer();
    startGPSAnimation();
    showToast('👋', `Welcome back, ${role === 'admin' ? 'Dr. Sharma' : 'Alex'}!`);
  }, 600);
}

function doLogout() {
  // Stop intervals
  clearInterval(App.clockInterval);
  clearInterval(App.campusTimerInterval);
  clearInterval(App.gpsInterval);

  const appPage = $('#page-app');
  const loginPage = $('#page-login');

  appPage.classList.remove('active');
  loginPage.classList.add('active');
}

/* ============================================================
   6. NAVIGATION
   ============================================================ */
const SCREEN_META = {
  's-dashboard': { title: 'Dashboard',       crumb: 'Student / Dashboard'    },
  's-mark':      { title: 'Mark Attendance', crumb: 'Student / Mark'         },
  's-history':   { title: 'My Attendance',   crumb: 'Student / History'      },
  's-entryexit': { title: 'Entry / Exit Log',crumb: 'Student / Entry-Exit'   },
  'a-dashboard': { title: 'Admin Dashboard', crumb: 'Admin / Dashboard'      },
  'a-students':  { title: 'Students',        crumb: 'Admin / Students'       },
  'a-attendance':{ title: 'Attendance',      crumb: 'Admin / Attendance'     },
  'a-reports':   { title: 'Reports',         crumb: 'Admin / Reports'        },
  'a-entryexit': { title: 'Entry-Exit Logs', crumb: 'Admin / Entry-Exit'     },
};

function showScreen(id, navItem) {
  $$('.screen').forEach(s => s.classList.remove('active'));
  $$('.nav-item').forEach(n => n.classList.remove('active'));

  const el = $(`#screen-${id}`);
  if (el) el.classList.add('active');
  if (navItem) navItem.classList.add('active');

  App.currentScreen = id;

  const meta = SCREEN_META[id] || { title: 'Dashboard', crumb: '' };
  const titleEl = $('#topbar-title');
  const crumbEl = $('#topbar-crumb');
  if (titleEl) titleEl.textContent = meta.title;
  if (crumbEl) crumbEl.textContent = meta.crumb;

  // Trigger lazy builds for specific screens
  const builders = {
    's-dashboard': () => { buildCalendar(); buildMiniChart(); },
    's-history':   () => buildHistoryTable(),
    'a-students':  () => buildStudentsTable(),
    'a-attendance':() => buildAttMonitor(),
    'a-reports':   () => buildReports(),
    'a-entryexit': () => buildAdminEntry(),
  };
  builders[id]?.();
}

/* ============================================================
   7. LIVE CLOCK
   ============================================================ */
function startLiveClock() {
  clearInterval(App.clockInterval);

  function tick() {
    const d = new Date();
    const clockEl = $('#live-clock');
    if (clockEl) {
      clockEl.textContent = d.toLocaleTimeString('en-IN', { hour12: false });
    }
    const verifiedEl = $('#last-verified');
    if (verifiedEl) {
      verifiedEl.textContent = 'Just now · ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    const dateBadge = $('#mark-date-badge');
    if (dateBadge) {
      dateBadge.textContent = d.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    }
  }

  tick();
  App.clockInterval = setInterval(tick, 1000);
}

/* ============================================================
   8. CAMPUS TIMER
   ============================================================ */
function startCampusTimer() {
  clearInterval(App.campusTimerInterval);

  App.campusTimerInterval = setInterval(() => {
    App.campusTimerSec++;
    const el = $('#campus-timer');
    if (el) el.textContent = formatDuration(App.campusTimerSec);
  }, 1000);
}

/* ============================================================
   9. GPS ANIMATION (simulated coordinate drift)
   ============================================================ */
function startGPSAnimation() {
  clearInterval(App.gpsInterval);

  const baseLat = 17.4486;
  const baseLon = 78.3908;

  App.gpsInterval = setInterval(() => {
    const latEl  = $('#gps-lat');
    const lonEl  = $('#gps-lon');
    if (!latEl || !lonEl) return;

    const jitter = 0.0002;
    const lat = (baseLat + (Math.random() - 0.5) * jitter).toFixed(4);
    const lon = (baseLon + (Math.random() - 0.5) * jitter).toFixed(4);

    latEl.textContent = `${lat}°N`;
    lonEl.textContent = `${lon}°E`;
  }, 3000);
}

/* ============================================================
   10. MARK ATTENDANCE
   ============================================================ */
function markAttendance() {
  const btn = $('#mark-btn');
  if (!btn || btn.disabled) return;

  if (btn.classList.contains('success-state')) {
    // Check-out flow
    btn.innerHTML = '🔄 Recording check-out...';
    btn.disabled = true;

    setTimeout(() => {
      btn.disabled = false;
      btn.classList.remove('success-state');
      btn.innerHTML = '📍 Mark Attendance';
      App.isCheckedIn = false;
      App.campusTimerSec = 0;
      showToast('✅', 'Checked out! Session of 3h 22m recorded.');
    }, 1600);

  } else {
    // Check-in flow — simulate GPS verification
    const statusBox = $('#gps-status-box');
    const campusBox = $('#gps-campus-box');

    btn.innerHTML = '<span class="status-dot-anim" style="background:#fff"></span> Verifying GPS location...';
    btn.disabled = true;
    btn.style.background = 'var(--warn)';

    if (statusBox) {
      statusBox.className = 'gps-status scanning';
      statusBox.innerHTML = '<div class="status-dot-anim"></div><span>Acquiring GPS signal...</span>';
    }

    setTimeout(() => {
      if (statusBox) {
        statusBox.className = 'gps-status found';
        statusBox.innerHTML = '<div class="status-dot-anim"></div><span>GPS acquired · Accuracy: ±8m</span>';
      }
    }, 800);

    setTimeout(() => {
      if (campusBox) {
        campusBox.className = 'gps-status inside';
        campusBox.innerHTML = '<span>✅</span><span>Location verified — within campus boundary</span>';
      }
    }, 1400);

    setTimeout(() => {
      btn.disabled = false;
      btn.style.background = '';
      btn.classList.add('success-state');
      btn.innerHTML = '✅ Attendance Marked — Check Out';
      App.isCheckedIn = true;
      showToast('✅', 'Attendance marked! GPS verified — within campus.');
    }, 2200);
  }
}

/* ============================================================
   11. CALENDAR BUILD
   ============================================================ */
function buildCalendar() {
  const grid = $('#cal-grid');
  if (!grid) return;

  const days = ['S','M','T','W','T','F','S'];
  let html = days.map(d => `<div class="cal-header">${d}</div>`).join('');

  // June 2025 starts on Sunday (index 0) — no offset needed
  for (let d = 1; d <= 30; d++) {
    let cls = 'cal-day';
    if (d === 9) {
      cls += ' today';
    } else if (DATA.calendarPresent.includes(d)) {
      cls += ' present';
    } else if (DATA.calendarAbsent.includes(d)) {
      cls += ' absent';
    } else if (d < 9) {
      cls += ' other';
    }
    html += `<div class="${cls}" title="${d} June">${d}</div>`;
  }

  grid.innerHTML = html;
}

/* ============================================================
   12. MINI CHART (7-DAY TREND)
   ============================================================ */
function buildMiniChart() {
  const container = $('#mini-chart');
  if (!container) return;

  const labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  container.innerHTML = DATA.attTrend.map((present, i) => {
    const h = DATA.attBarHeights[i] || 12;
    const cls = present ? 'present' : 'absent';
    return `<div class="mini-bar ${cls}" style="height:${h}px" title="${labels[i]}: ${present ? 'Present' : 'Absent'}"></div>`;
  }).join('');
}

/* ============================================================
   13. HISTORY TABLE
   ============================================================ */
function buildHistoryTable(filter = '') {
  const tb = $('#history-tbody');
  if (!tb) return;

  const rows = filter
    ? DATA.history.filter(r => r.date.toLowerCase().includes(filter.toLowerCase()))
    : DATA.history;

  if (rows.length === 0) {
    tb.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text3);padding:2rem">No records found</td></tr>`;
    return;
  }

  tb.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${r.date}</strong></td>
      <td style="color:var(--text3)">${r.day}</td>
      <td style="font-family:var(--mono);font-size:12px;color:${r.cin === '—' ? 'var(--text3)' : 'var(--success)'}">${r.cin}</td>
      <td style="font-family:var(--mono);font-size:12px;color:${r.cout === '—' ? 'var(--text3)' : 'var(--danger)'}">${r.cout}</td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--accent2)">${r.dur}</td>
      <td>${r.present
        ? '<span class="badge badge-green">Present</span>'
        : '<span class="badge badge-red">Absent</span>'}</td>
      <td>${r.gps
        ? '<span class="badge badge-blue">✓ GPS</span>'
        : '<span class="badge badge-neutral">—</span>'}</td>
    </tr>
  `).join('');
}

/* ============================================================
   14. STUDENTS TABLE (Admin)
   ============================================================ */
function buildStudentsTable(filter = '') {
  const tb = $('#students-tbody');
  if (!tb) return;

  const filtered = filter
    ? DATA.students.filter(s =>
        s.name.toLowerCase().includes(filter.toLowerCase()) ||
        s.email.toLowerCase().includes(filter.toLowerCase()) ||
        s.id.toLowerCase().includes(filter.toLowerCase())
      )
    : DATA.students;

  if (filtered.length === 0) {
    tb.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text3);padding:2rem">No students found</td></tr>`;
    return;
  }

  tb.innerHTML = filtered.map(s => {
    const color = attColor(s.att);
    return `
      <tr>
        <td>
          <div style="display:flex;align-items:center;gap:.6rem">
            ${avatarHTML(s.name, 30)}
            <strong>${s.name}</strong>
          </div>
        </td>
        <td style="font-family:var(--mono);font-size:12px">${s.id}</td>
        <td style="color:var(--text3)">${s.email}</td>
        <td>${progressBarHTML(s.att, color)}</td>
        <td>${s.active
          ? '<span class="badge badge-green"><span class="badge-dot"></span>On Campus</span>'
          : '<span class="badge badge-red">Absent</span>'}</td>
        <td style="font-family:var(--mono);font-size:12px;color:var(--text3)">${s.last}</td>
        <td>
          <div class="action-menu">
            <button class="btn btn-sm btn-outline">Actions ▾</button>
            <div class="action-dropdown">
              <span class="action-item" onclick="showToast('👁','Viewing ${s.name}')">👁 View Profile</span>
              <span class="action-item" onclick="openEditModal('${s.id}')">✏️ Edit</span>
              <span class="action-item" onclick="exportStudentReport('${s.name}')">📊 Report</span>
              <span class="action-item danger" onclick="confirmRemove('${s.name}')">🗑 Remove</span>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterStudents(val) {
  buildStudentsTable(val);
}

/* ============================================================
   15. ATTENDANCE MONITOR (Admin)
   ============================================================ */
function buildAttMonitor() {
  const tb = $('#att-monitor-tbody');
  if (!tb) return;

  const checkins = ['08:42', '08:55', '09:10', '08:38', '—', '—', '09:12', '—', '08:50', '09:02'];
  const checkouts = ['—', '—', '11:52', '—', '—', '—', '—', '—', '—', '—'];
  const durations = ['Active', 'Active', '2h 57m', 'Active', '—', '—', 'Active', '—', 'Active', 'Active'];

  tb.innerHTML = DATA.students.map((s, i) => `
    <tr>
      <td>
        <div style="display:flex;align-items:center;gap:.6rem">
          ${avatarHTML(s.name, 28)}
          <strong>${s.name}</strong>
        </div>
      </td>
      <td style="font-family:var(--mono);font-size:12px;color:${checkins[i] === '—' ? 'var(--text3)' : 'var(--success)'}">${checkins[i]}</td>
      <td style="font-family:var(--mono);font-size:12px;color:${checkouts[i] === '—' ? 'var(--text3)' : 'var(--danger)'}">${checkouts[i]}</td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--accent2)">${durations[i]}</td>
      <td>${checkins[i] !== '—'
        ? '<span class="badge badge-blue">✓ GPS Verified</span>'
        : '<span class="badge badge-neutral">—</span>'}</td>
      <td>${s.active
        ? '<span class="badge badge-green">Present</span>'
        : '<span class="badge badge-red">Absent</span>'}</td>
    </tr>
  `).join('');
}

/* ============================================================
   16. REPORTS TABLE (Admin)
   ============================================================ */
function buildReports() {
  const tb = $('#reports-tbody');
  if (!tb) return;

  tb.innerHTML = DATA.students.map(s => {
    const color   = attColor(s.att);
    const present = Math.round(9 * s.att / 100);
    const absent  = 9 - present;
    const avgH    = Math.floor(6 + Math.random() * 2);
    const avgM    = Math.floor(Math.random() * 55);
    const avg     = `${avgH}h ${zeroPad(avgM)}m`;

    let statusBadge;
    if (s.att >= 75)      statusBadge = '<span class="badge badge-green">Good</span>';
    else if (s.att >= 60) statusBadge = '<span class="badge badge-warn">At Risk</span>';
    else                  statusBadge = '<span class="badge badge-red">Critical</span>';

    return `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td style="text-align:center">9</td>
        <td style="text-align:center;color:var(--success)">${present}</td>
        <td style="text-align:center;color:var(--danger)">${absent}</td>
        <td><span style="font-weight:700;color:${color}">${s.att}%</span></td>
        <td style="font-family:var(--mono);font-size:12px">${avg}</td>
        <td>${statusBadge}</td>
      </tr>
    `;
  }).join('');
}

/* ============================================================
   17. ADMIN ENTRY/EXIT TABLE
   ============================================================ */
function buildAdminEntry(filter = '') {
  const tb = $('#admin-entry-tbody');
  if (!tb) return;

  const rows = filter
    ? DATA.entryLogs.filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
    : DATA.entryLogs;

  tb.innerHTML = rows.map(r => `
    <tr>
      <td>
        <div style="display:flex;align-items:center;gap:.6rem">
          ${avatarHTML(r.name, 28)}
          <strong>${r.name}</strong>
        </div>
      </td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--success)">${r.ein}</td>
      <td style="font-family:var(--mono);font-size:12px;color:${r.eout === '—' ? 'var(--text3)' : 'var(--danger)'}">${r.eout}</td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--accent2)">${r.dur}</td>
      <td style="font-family:var(--mono);font-size:10px;color:var(--text3)">${r.egps}</td>
      <td style="font-family:var(--mono);font-size:10px;color:var(--text3)">${r.xgps}</td>
      <td>${r.onCampus
        ? '<span class="badge badge-green"><span class="badge-dot"></span>On Campus</span>'
        : '<span class="badge badge-teal">Exited</span>'}</td>
    </tr>
  `).join('');
}

/* ============================================================
   18. INIT ALL DATA
   ============================================================ */
function initAllData() {
  buildCalendar();
  buildMiniChart();
  buildHistoryTable();
  buildStudentsTable();
  buildAttMonitor();
  buildReports();
  buildAdminEntry();
}

/* ============================================================
   19. MODAL HANDLERS
   ============================================================ */
function openModal(id) {
  const el = $(`#${id}`);
  if (el) {
    el.classList.add('open');
    // Focus first input
    setTimeout(() => {
      const firstInput = el.querySelector('input, select, textarea');
      if (firstInput) firstInput.focus();
    }, 100);
  }
}

function closeModal(id) {
  const el = $(`#${id}`);
  if (el) el.classList.remove('open');
}

function closeModalOut(event, id) {
  if (event.target === event.currentTarget) closeModal(id);
}

function addStudentDemo() {
  closeModal('modal-add-student');

  // Simulate adding a new student row
  const newStudent = {
    name: 'New Student',
    id: `CS24${String(DATA.students.length + 1).padStart(2,'0')}`,
    email: 'new.student@campus.edu',
    att: 0,
    active: false,
    last: 'Never',
  };
  DATA.students.push(newStudent);
  buildStudentsTable();

  showToast('✅', 'Student account created successfully!');
}

function openEditModal(id) {
  showToast('✏️', `Editing student ${id}`);
}

function confirmRemove(name) {
  if (confirm(`Remove ${name} from the system?`)) {
    const idx = DATA.students.findIndex(s => s.name === name);
    if (idx !== -1) {
      DATA.students.splice(idx, 1);
      buildStudentsTable();
      showToast('🗑', `${name} removed successfully.`);
    }
  }
}

function exportStudentReport(name) {
  showToast('📊', `Generating report for ${name}...`);
}

/* ============================================================
   20. REPORT GENERATION (Admin)
   ============================================================ */
function generateReport() {
  const btn = document.querySelector('[onclick="generateReport()"]');
  if (btn) {
    btn.textContent = '⏳ Generating...';
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = 'Generate Report';
      btn.disabled = false;
      buildReports();
      showToast('📊', 'Report generated for selected date range!');
    }, 1200);
  }
}

function exportCSV() {
  const headers = ['Name', 'ID', 'Present Days', 'Absent Days', 'Attendance %'];
  const rows = DATA.students.map(s => {
    const present = Math.round(9 * s.att / 100);
    return [s.name, s.id, present, 9 - present, s.att + '%'].join(',');
  });
  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'attendance_report.csv';
  a.click();
  URL.revokeObjectURL(url);
  showToast('⬇', 'CSV exported successfully!');
}

/* ============================================================
   21. KEYBOARD SHORTCUTS
   ============================================================ */
document.addEventListener('keydown', (e) => {
  // Escape closes modals
  if (e.key === 'Escape') {
    $$('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});

/* ============================================================
   22. RESPONSIVE — MOBILE SIDEBAR TOGGLE
   ============================================================ */
function toggleSidebar() {
  const sidebar = $('#sidebar');
  if (sidebar) sidebar.classList.toggle('open');
}

// Close sidebar on outside click (mobile)
document.addEventListener('click', (e) => {
  const sidebar = $('#sidebar');
  if (!sidebar) return;
  if (window.innerWidth <= 768
      && sidebar.classList.contains('open')
      && !sidebar.contains(e.target)
      && !e.target.closest('[onclick="toggleSidebar()"]')) {
    sidebar.classList.remove('open');
  }
});

/* ============================================================
   23. INPUT VALIDATION (Login)
   ============================================================ */
function validateLogin(email, password) {
  const errors = [];
  if (!email || !email.includes('@')) errors.push('Invalid email address');
  if (!password || password.length < 6) errors.push('Password too short');
  return errors;
}

/* ============================================================
   24. SEARCH HANDLERS
   ============================================================ */
function searchAdminEntry(val) {
  buildAdminEntry(val);
}

/* ============================================================
   25. FILTER HANDLERS (Attendance Monitor)
   ============================================================ */
function filterByDate(dateStr) {
  showToast('📅', `Showing attendance for ${dateStr}`);
  buildAttMonitor();
}

/* ============================================================
   26. WINDOW RESIZE HANDLER
   ============================================================ */
window.addEventListener('resize', () => {
  // Re-render chart on resize if needed
  if (App.currentScreen === 's-dashboard') {
    buildMiniChart();
  }
});

/* ============================================================
   27. PAGE VISIBILITY (pause timers when tab hidden)
   ============================================================ */
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    clearInterval(App.clockInterval);
    clearInterval(App.campusTimerInterval);
  } else {
    if ($('#page-app')?.classList.contains('active')) {
      startLiveClock();
      startCampusTimer();
    }
  }
});

/* ============================================================
   28. MOBILE PWA — HAMBURGER SIDEBAR
   ============================================================ */
(function () {
  'use strict';

  // Close sidebar when a nav item is tapped on mobile
  document.querySelectorAll('.nav-item').forEach(function (item) {
    item.addEventListener('click', function () {
      if (window.innerWidth <= 768) {
        var sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('open');
      }
    });
  });

  // Close sidebar when tapping the overlay (outside sidebar)
  document.addEventListener('click', function (e) {
    var sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    if (sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        e.target.id !== 'menu-toggle') {
      sidebar.classList.remove('open');
    }
  });

  // Close sidebar on window resize to desktop
  window.addEventListener('resize', function () {
    if (window.innerWidth > 768) {
      var sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.classList.remove('open');
    }
  });
}());