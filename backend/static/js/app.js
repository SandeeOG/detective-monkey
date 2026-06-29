/* Detective Monkey — single-page web app (vanilla JS). */
'use strict';

const App = (() => {
  const state = {
    token: localStorage.getItem('dm_token') || null,
    user: JSON.parse(localStorage.getItem('dm_user') || 'null'),
  };

  /* ---------- API ---------- */
  async function api(path, { method = 'GET', body } = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const res = await fetch(`/api${path}`, {
      method, headers, body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401) { logout(); throw new Error('Session expired. Please log in again.'); }
    let data = null;
    try { data = await res.json(); } catch (_) { /* no body */ }
    if (!res.ok) throw new Error((data && data.detail) || `Request failed (${res.status})`);
    return data;
  }

  /* ---------- helpers ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function toast(msg, type = '') {
    const box = $('#toast');
    const t = el(`<div class="toast ${type}">${esc(msg)}</div>`);
    box.appendChild(t);
    setTimeout(() => t.remove(), 3500);
  }

  function scoreColor(score) {
    if (score >= 78) return '#16a34a';
    if (score >= 60) return '#0ea5e9';
    if (score >= 45) return '#d97706';
    return '#9ca3af';
  }
  function confBadge(c) {
    const cls = c === 'High' ? 'success' : c === 'Medium' ? 'warning' : 'muted';
    return `<span class="badge ${cls}">${esc(c)} confidence</span>`;
  }

  /* ---------- auth ---------- */
  function setSession(data) {
    state.token = data.token; state.user = data.user;
    localStorage.setItem('dm_token', data.token);
    localStorage.setItem('dm_user', JSON.stringify(data.user));
  }
  function logout() {
    state.token = null; state.user = null;
    localStorage.removeItem('dm_token'); localStorage.removeItem('dm_user');
    location.hash = '#/login';
    renderAuth();
  }

  function renderAuth() {
    const app = $('#app');
    app.innerHTML = '';
    const card = el(`
      <div class="auth-wrap"><div class="card auth-card">
        <div class="brand"><span class="logo">🐵</span> Detective Monkey</div>
        <p class="muted small">AI-powered career intelligence for students. Discover careers that fit who you are.</p>
        <div class="tabs">
          <button data-tab="login" class="active">Log in</button>
          <button data-tab="register">Create account</button>
        </div>
        <form id="authForm"></form>
      </div></div>`);
    app.appendChild(card);
    let tab = 'login';
    const renderForm = () => {
      const f = $('#authForm', card);
      f.innerHTML = tab === 'register' ? `
        <div class="field"><label>Full name</label><input name="full_name" required placeholder="Alex Student" /></div>
        <div class="field"><label>Email</label><input name="email" type="email" required placeholder="you@example.com" /></div>
        <div class="field"><label>Password</label><input name="password" type="password" minlength="6" required placeholder="At least 6 characters" /></div>
        <button class="btn block" type="submit">Create account</button>`
        : `
        <div class="field"><label>Email</label><input name="email" type="email" required placeholder="you@example.com" /></div>
        <div class="field"><label>Password</label><input name="password" type="password" required /></div>
        <button class="btn block" type="submit">Log in</button>`;
    };
    card.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
      tab = b.dataset.tab;
      card.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('active', x === b));
      renderForm();
    });
    renderForm();
    $('#authForm', card).onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target).entries());
      const btn = e.target.querySelector('button');
      btn.disabled = true; btn.textContent = 'Please wait…';
      try {
        const data = await api(tab === 'register' ? '/auth/register' : '/auth/login', { method: 'POST', body: fd });
        setSession(data);
        toast(`Welcome${tab === 'register' ? '' : ' back'}, ${data.user.full_name.split(' ')[0]}!`, 'success');
        location.hash = '#/dashboard';
        renderShell();
      } catch (err) { toast(err.message, 'error'); btn.disabled = false; renderForm(); }
    };
  }

  /* ---------- shell ---------- */
  const NAV = [
    { path: 'dashboard', label: 'Dashboard', icon: '🏠' },
    { path: 'assessment', label: 'Assessment', icon: '📝' },
    { path: 'recommendations', label: 'Recommendations', icon: '⭐' },
    { path: 'careers', label: 'Explore Careers', icon: '🧭' },
    { path: 'coach', label: 'AI Coach', icon: '💬' },
    { path: 'report', label: 'Report', icon: '📄' },
    { sep: true },
    { path: 'profile', label: 'Profile', icon: '👤' },
    { path: 'feedback', label: 'Feedback', icon: '🗣️' },
  ];

  function renderShell() {
    const app = $('#app');
    app.innerHTML = `
      <div class="shell">
        <aside class="sidebar" id="sidebar">
          <div class="brand"><span class="logo">🐵</span> Detective Monkey</div>
          <nav class="nav" id="nav"></nav>
          <div class="userbox">
            <div>${esc(state.user?.full_name || '')}</div>
            <div class="muted small">${esc(state.user?.email || '')}</div>
            <button class="btn secondary sm block" id="logoutBtn" style="margin-top:.6rem">Log out</button>
          </div>
        </aside>
        <div class="main">
          <div class="topbar">
            <button class="menu-toggle" id="menuToggle">☰</button>
            <div class="brand" style="font-size:1rem"><span class="logo">🐵</span> Detective Monkey</div>
            <span class="muted small">Guidance, not prediction</span>
          </div>
          <div class="content" id="content"><div class="spinner"></div></div>
        </div>
      </div>`;
    $('#logoutBtn').onclick = logout;
    $('#menuToggle').onclick = () => $('#sidebar').classList.toggle('open');
    router();
    window.onhashchange = router;
  }

  function renderNav(active) {
    const nav = $('#nav');
    if (!nav) return;
    nav.innerHTML = '';
    NAV.forEach(item => {
      if (item.sep) { nav.appendChild(el('<div class="sep"></div>')); return; }
      const a = el(`<a href="#/${item.path}" class="${item.path === active ? 'active' : ''}">
        <span class="nav-icon">${item.icon}</span> ${item.label}</a>`);
      a.onclick = () => $('#sidebar').classList.remove('open');
      nav.appendChild(a);
    });
  }

  /* ---------- router ---------- */
  const routes = {};
  async function router() {
    if (!state.token) { renderAuth(); return; }
    if (!$('#content')) { renderShell(); return; }
    let path = (location.hash.replace('#/', '') || 'dashboard');
    const [base, param] = path.split('/');
    renderNav(base);
    const content = $('#content');
    content.innerHTML = '<div class="spinner"></div>';
    const handler = routes[base] || routes.dashboard;
    try { await handler(content, param); }
    catch (err) { content.innerHTML = `<div class="empty"><div class="ico">⚠️</div>${esc(err.message)}</div>`; }
  }

  /* ---------- pages ---------- */
  routes.dashboard = async (c) => {
    const [status, profile] = await Promise.all([
      api('/assessment/status'), api('/profile'),
    ]);
    let recs = { recommendations: [] };
    if (status.completed) { try { recs = await api('/recommendations'); } catch (_) {} }
    const first = (state.user.full_name || 'there').split(' ')[0];
    const done = status.completed;
    const topRec = recs.recommendations[0];

    c.innerHTML = `
      <div class="page-head"><h1>Welcome, ${esc(first)} 👋</h1>
        <p class="muted">Your personalised career journey at a glance.</p></div>
      <div class="grid cols-3" style="margin-bottom:1.2rem">
        <div class="card"><div class="muted small">Assessment</div>
          <div class="stat">${done ? '✓' : '0%'}</div>
          <div class="muted small">${done ? 'Completed' : 'Not started'}</div></div>
        <div class="card"><div class="muted small">Recommendations</div>
          <div class="stat">${recs.recommendations.length}</div>
          <div class="muted small">careers matched</div></div>
        <div class="card"><div class="muted small">Top match</div>
          <div class="stat" style="font-size:1.2rem">${topRec ? esc(topRec.career.name) : '—'}</div>
          <div class="muted small">${topRec ? topRec.score + '% fit' : 'Complete assessment'}</div></div>
      </div>
      <div class="grid cols-2">
        <div class="card">
          <h3>Continue where you left off</h3>
          ${done
            ? `<p class="muted">Your assessment is complete. Explore your matches or chat with your AI coach.</p>
               <a class="btn" href="#/recommendations">View recommendations</a>`
            : `<p class="muted">Start with a ~10 minute assessment to unlock personalised career matches.</p>
               <a class="btn" href="#/assessment">Start assessment</a>`}
        </div>
        <div class="card">
          <h3>Your profile</h3>
          <p class="muted small">${esc(profile.grade || 'Grade not set')} · ${esc(profile.school || 'School not set')}</p>
          <p class="small">${profile.career_aspiration ? 'Aspiration: ' + esc(profile.career_aspiration) : 'Add your aspirations to personalise guidance.'}</p>
          <a class="btn secondary sm" href="#/profile">Edit profile</a>
        </div>
      </div>`;
  };

  routes.profile = async (c) => {
    const p = await api('/profile');
    c.innerHTML = `
      <div class="page-head"><h1>Your Profile</h1><p class="muted">Help us personalise your guidance.</p></div>
      <div class="card" style="max-width:640px">
        <form id="pf">
          <div class="field"><label>Full name</label><input value="${esc(p.full_name)}" disabled /></div>
          <div class="grid cols-2">
            <div class="field"><label>Grade</label>
              <select name="grade">${['', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12']
                .map(g => `<option ${g === (p.grade || '') ? 'selected' : ''}>${g}</option>`).join('')}</select></div>
            <div class="field"><label>School</label><input name="school" value="${esc(p.school || '')}" /></div>
          </div>
          <div class="field"><label>Favourite subjects (comma separated)</label>
            <input name="subjects" value="${esc((p.favourite_subjects || []).join(', '))}" placeholder="Maths, Physics, Art" /></div>
          <div class="field"><label>Career aspiration</label>
            <input name="career_aspiration" value="${esc(p.career_aspiration || '')}" placeholder="e.g. Doctor, Engineer, unsure" /></div>
          <div class="field"><label>Location</label><input name="location" value="${esc(p.location || '')}" /></div>
          <button class="btn">Save profile</button>
        </form>
      </div>`;
    $('#pf', c).onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target).entries());
      const body = {
        grade: fd.grade || null, school: fd.school || null,
        favourite_subjects: fd.subjects.split(',').map(s => s.trim()).filter(Boolean),
        career_aspiration: fd.career_aspiration || null, location: fd.location || null,
      };
      try { await api('/profile', { method: 'PUT', body }); toast('Profile saved', 'success'); }
      catch (err) { toast(err.message, 'error'); }
    };
  };

  routes.assessment = async (c) => {
    const status = await api('/assessment/status');
    const data = await api('/assessment/questions');
    const total = data.total;
    const answers = {}; // id -> value
    const LABELS = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree'];

    const head = `<div class="page-head"><h1>Self-Discovery Assessment</h1>
      <p class="muted">Answer honestly — there are no right or wrong answers. ~${Math.ceil(total / 6)} minutes.</p></div>
      ${status.completed ? '<p><span class="badge success">Previously completed</span> Retaking will refresh your results.</p>' : ''}
      <div class="card" style="position:sticky;top:70px;z-index:5;margin-bottom:1rem">
        <div class="bar-row"><span class="label">Progress</span>
          <div class="progress"><span id="abar" style="width:0%"></span></div>
          <span class="val" id="acount">0/${total}</span></div>
      </div>`;

    const groups = data.groups.map(g => `
      <div class="card" style="margin-bottom:1rem">
        <h3>${esc(g.domain)}</h3>
        ${g.questions.map(q => `
          <div class="q-block" data-qid="${q.id}">
            <div class="q-text">${esc(q.text)}</div>
            <div class="likert">
              ${[1, 2, 3, 4, 5].map(v => `
                <label data-v="${v}"><input type="radio" name="q${q.id}" value="${v}" /> ${LABELS[v - 1]}</label>`).join('')}
            </div>
          </div>`).join('')}
      </div>`).join('');

    c.innerHTML = head + groups +
      `<div class="card no-print" style="position:sticky;bottom:0">
        <button class="btn block" id="submitA" disabled>Answer all questions to submit</button>
      </div>`;

    const update = () => {
      const n = Object.keys(answers).length;
      $('#abar').style.width = `${Math.round(n / total * 100)}%`;
      $('#acount').textContent = `${n}/${total}`;
      const btn = $('#submitA');
      btn.disabled = n < total;
      btn.textContent = n < total ? `Answer all questions to submit (${total - n} left)` : 'Submit & see my matches';
    };
    c.querySelectorAll('.likert label').forEach(lab => {
      lab.onclick = () => {
        const block = lab.closest('.q-block');
        const qid = block.dataset.qid;
        block.querySelectorAll('.likert label').forEach(l => l.classList.remove('sel'));
        lab.classList.add('sel');
        answers[qid] = Number(lab.dataset.v);
        update();
      };
    });
    $('#submitA', c).onclick = async (e) => {
      e.target.disabled = true; e.target.textContent = 'Scoring your profile…';
      try {
        const body = { session_id: 0, responses: Object.entries(answers).map(([id, value]) => ({ question_id: Number(id), value })) };
        await api('/assessment/submit', { method: 'POST', body });
        await api('/recommendations/generate', { method: 'POST' });
        toast('Assessment complete! Recommendations ready.', 'success');
        location.hash = '#/recommendations';
      } catch (err) { toast(err.message, 'error'); e.target.disabled = false; update(); }
    };
    update();
  };

  routes.recommendations = async (c) => {
    const [recsRes, fvRes] = await Promise.all([api('/recommendations'), api('/assessment/feature-vector')]);
    const recs = recsRes.recommendations;
    if (!recs.length) {
      c.innerHTML = `<div class="empty"><div class="ico">⭐</div>
        <h3>No recommendations yet</h3>
        <p>Complete the assessment to unlock your personalised career matches.</p>
        <a class="btn" href="#/assessment">Start assessment</a></div>`;
      return;
    }
    const fv = (fvRes.feature_vector || []).sort((a, b) => b.score - a.score).slice(0, 8);
    c.innerHTML = `
      <div class="page-head"><h1>Your Career Matches</h1>
        <p class="muted">Ranked by how well each fits your assessed strengths and interests. These are options to explore — not predictions.</p></div>
      <div class="grid cols-2" id="recList"></div>
      <div class="card" style="margin-top:1.4rem">
        <h3>Your strongest traits</h3>
        <p class="muted small">From your assessment (0–100%).</p>
        <div id="fvBars"></div>
      </div>
      <div style="margin-top:1.2rem;display:flex;gap:.6rem;flex-wrap:wrap">
        <a class="btn" href="#/report">📄 View full report</a>
        <a class="btn secondary" href="#/coach">💬 Ask the AI coach</a>
        <button class="btn secondary" id="regen">↻ Regenerate</button>
      </div>`;
    const list = $('#recList', c);
    recs.forEach(r => {
      const card = el(`<div class="card rec-card">
        <div class="rec-head">
          <div>
            <div class="badge muted">#${r.rank} · ${esc(r.career.category)}</div>
            <h3 style="margin:.4rem 0 .1rem">${esc(r.career.name)}</h3>
            ${confBadge(r.confidence)}
          </div>
          <div class="score-ring" style="background:${scoreColor(r.score)}">${r.score}%</div>
        </div>
        <p class="small">${esc(r.explanation || '')}</p>
        <div class="chips">${(r.matched_constructs || []).map(m => `<span class="badge">${esc(m)}</span>`).join('')}</div>
        <a class="btn secondary sm" href="#/careers/${r.career.slug}">View career details →</a>
      </div>`);
      list.appendChild(card);
    });
    const bars = $('#fvBars', c);
    fv.forEach(f => {
      bars.appendChild(el(`<div class="bar-row">
        <span class="label">${esc(f.label)}</span>
        <div class="progress"><span style="width:${Math.round(f.score * 100)}%"></span></div>
        <span class="val">${Math.round(f.score * 100)}%</span></div>`));
    });
    $('#regen', c).onclick = async (e) => {
      e.target.disabled = true; e.target.textContent = 'Regenerating…';
      try { await api('/recommendations/generate', { method: 'POST' }); router(); }
      catch (err) { toast(err.message, 'error'); e.target.disabled = false; }
    };
  };

  routes.careers = async (c, slug) => {
    if (slug) return careerDetail(c, slug);
    const [{ categories }, { careers }] = await Promise.all([api('/careers/categories'), api('/careers')]);
    c.innerHTML = `
      <div class="page-head"><h1>Explore Careers</h1><p class="muted">Browse the career knowledge base.</p></div>
      <div class="toolbar">
        <input id="csearch" placeholder="🔍 Search by name, skill or keyword…" />
        <select id="ccat"><option value="">All categories</option>${categories.map(x => `<option>${esc(x)}</option>`).join('')}</select>
      </div>
      <div class="grid cols-3" id="clist"></div>`;
    const render = (items) => {
      const list = $('#clist', c);
      list.innerHTML = items.length ? '' : '<div class="empty">No careers match your search.</div>';
      items.forEach(cr => list.appendChild(el(`
        <a class="card" href="#/careers/${cr.slug}" style="display:block">
          <div class="badge muted">${esc(cr.category)}</div>
          <h3 style="margin:.5rem 0 .2rem">${esc(cr.name)}</h3>
          <p class="small muted">${esc(cr.description.slice(0, 110))}…</p>
          <div class="small">💰 ${esc(cr.salary_range)} · 📈 ${esc(cr.outlook)}</div>
        </a>`)));
    };
    render(careers);
    let timer;
    const reload = async () => {
      const q = $('#csearch').value, cat = $('#ccat').value;
      const params = new URLSearchParams();
      if (q) params.set('q', q); if (cat) params.set('category', cat);
      const { careers: items } = await api(`/careers?${params}`);
      render(items);
    };
    $('#csearch', c).oninput = () => { clearTimeout(timer); timer = setTimeout(reload, 250); };
    $('#ccat', c).onchange = reload;
  };

  async function careerDetail(c, slug) {
    const cr = await api(`/careers/${slug}`);
    c.innerHTML = `
      <a class="btn ghost sm" href="#/careers">← Back to explorer</a>
      <div class="page-head" style="margin-top:.6rem">
        <div class="badge muted">${esc(cr.category)}</div>
        <h1 style="margin-top:.4rem">${esc(cr.name)}</h1>
        <p class="muted">${esc(cr.description)}</p>
      </div>
      <div class="grid cols-2">
        <div class="card"><h3>Daily responsibilities</h3>
          <ul class="clean">${cr.responsibilities.map(r => `<li>${esc(r)}</li>`).join('')}</ul></div>
        <div class="card"><h3>Key skills</h3>
          <div class="chips">${cr.skills.map(s => `<span class="badge">${esc(s)}</span>`).join('')}</div>
          <h3 style="margin-top:1rem">Recommended subjects</h3>
          <div class="chips">${cr.subjects.map(s => `<span class="badge muted">${esc(s)}</span>`).join('')}</div></div>
      </div>
      <div class="card" style="margin-top:1rem"><h3>Education pathway</h3>
        <p>${esc(cr.education_pathway || '')}</p>
        <div class="grid cols-3" style="margin-top:.8rem">
          <div><div class="muted small">Work environment</div><strong>${esc(cr.work_environment || '—')}</strong></div>
          <div><div class="muted small">Salary range</div><strong>${esc(cr.salary_range || '—')}</strong></div>
          <div><div class="muted small">Outlook</div><strong>${esc(cr.outlook || '—')}</strong></div>
        </div></div>
      ${cr.related.length ? `<div class="card" style="margin-top:1rem"><h3>Related careers</h3>
        <div class="chips">${cr.related.map(r => `<a class="badge" href="#/careers/${r.slug}">${esc(r.name)} →</a>`).join('')}</div></div>` : ''}`;
  }

  routes.coach = async (c) => {
    const hist = await api('/chat/history');
    const latest = hist.conversations[0] || null;
    let convId = latest ? latest.id : null;
    c.innerHTML = `
      <div class="page-head"><h1>AI Career Coach</h1>
        <p class="muted">Ask about your results, compare careers, or plan next steps. Guidance only — always check with people who support you.</p></div>
      <div class="suggested">
        ${['Explain my recommendations', 'What should I learn next?', 'Compare my top two careers', 'What career suits me?']
          .map(s => `<button data-s="${esc(s)}">${esc(s)}</button>`).join('')}
      </div>
      <div class="card chat-wrap">
        <div class="chat-log" id="log"></div>
        <div class="chat-input">
          <input id="cinput" placeholder="Type your question…" />
          <button class="btn" id="csend">Send</button>
        </div>
      </div>
      ${hist.conversations.length ? '<button class="btn ghost sm" id="clearChat" style="margin-top:.6rem">Clear conversation history</button>' : ''}`;
    const log = $('#log', c);
    const addMsg = (role, content) => {
      log.appendChild(el(`<div class="msg ${role}">${esc(content)}</div>`));
      log.scrollTop = log.scrollHeight;
    };
    if (latest) latest.messages.forEach(m => addMsg(m.role, m.content));
    else addMsg('assistant', `Hi ${esc((state.user.full_name || '').split(' ')[0])}! I'm your career coach. Ask me anything about your results or careers you're curious about.`);

    const send = async (text) => {
      if (!text.trim()) return;
      addMsg('user', text);
      $('#cinput').value = '';
      const typing = el('<div class="msg assistant">…</div>'); log.appendChild(typing); log.scrollTop = log.scrollHeight;
      try {
        const res = await api('/chat', { method: 'POST', body: { message: text, conversation_id: convId } });
        convId = res.conversation_id; typing.remove(); addMsg('assistant', res.reply);
      } catch (err) { typing.remove(); addMsg('assistant', '⚠️ ' + err.message); }
    };
    $('#csend', c).onclick = () => send($('#cinput').value);
    $('#cinput', c).onkeydown = (e) => { if (e.key === 'Enter') send($('#cinput').value); };
    c.querySelectorAll('.suggested button').forEach(b => b.onclick = () => send(b.dataset.s));
    const clear = $('#clearChat', c);
    if (clear) clear.onclick = async () => { await api('/chat/history', { method: 'DELETE' }); router(); };
  };

  routes.report = async (c) => {
    let r;
    try { r = await api('/report'); }
    catch (err) {
      c.innerHTML = `<div class="empty"><div class="ico">📄</div><h3>Report not ready</h3>
        <p>${esc(err.message)}</p><a class="btn" href="#/assessment">Go to assessment</a></div>`;
      return;
    }
    const date = new Date(r.generated_at).toLocaleDateString();
    c.innerHTML = `
      <div class="page-head no-print" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem">
        <div><h1>Career Report</h1><p class="muted">A summary you can save or print as PDF.</p></div>
        <button class="btn" onclick="window.print()">⬇ Download / Print PDF</button>
      </div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);padding-bottom:.8rem;margin-bottom:1rem">
          <div class="brand">🐵 Detective Monkey</div><div class="muted small">Generated ${esc(date)}</div>
        </div>
        <h2>${esc(r.student.name)}</h2>
        <p class="muted small">${esc(r.student.grade || 'Grade —')} · ${esc(r.student.school || 'School —')}
          ${r.student.career_aspiration ? '· Aspiration: ' + esc(r.student.career_aspiration) : ''}</p>

        <h3 style="margin-top:1.4rem">Your strengths</h3>
        ${r.strengths.map(s => `<div class="bar-row"><span class="label">${esc(s.label)}</span>
          <div class="progress"><span style="width:${Math.round(s.score * 100)}%"></span></div>
          <span class="val">${Math.round(s.score * 100)}%</span></div>`).join('')}

        <h3 style="margin-top:1.4rem">Recommended careers</h3>
        ${r.recommendations.map(rec => `
          <div style="padding:.8rem 0;border-bottom:1px solid var(--border)">
            <div style="display:flex;justify-content:space-between"><strong>#${rec.rank} ${esc(rec.name)}</strong>
              <span class="badge" style="background:${scoreColor(rec.score)};color:#fff">${rec.score}% · ${esc(rec.confidence)}</span></div>
            <p class="small" style="margin:.4rem 0">${esc(rec.explanation || '')}</p>
            ${rec.skill_gaps.length ? `<div class="small muted">Develop: ${rec.skill_gaps.map(esc).join(', ')}</div>` : ''}
          </div>`).join('')}

        <h3 style="margin-top:1.4rem">Suggested next steps</h3>
        <ul class="clean">${r.next_steps.map(s => `<li>${esc(s)}</li>`).join('')}</ul>

        <p class="muted small" style="margin-top:1.4rem;border-top:1px solid var(--border);padding-top:.8rem">${esc(r.disclaimer)}</p>
      </div>`;
  };

  routes.feedback = async (c) => {
    c.innerHTML = `
      <div class="page-head"><h1>Share Feedback</h1><p class="muted">Help us improve your recommendations.</p></div>
      <div class="card" style="max-width:600px">
        <form id="fb">
          <div class="field"><label>What's this about?</label>
            <select name="kind"><option value="recommendation">My recommendations</option>
              <option value="assessment">The assessment</option><option value="general">General</option></select></div>
          <div class="field"><label>Rating</label>
            <select name="rating"><option value="5">⭐⭐⭐⭐⭐ Excellent</option><option value="4">⭐⭐⭐⭐ Good</option>
              <option value="3">⭐⭐⭐ Okay</option><option value="2">⭐⭐ Poor</option><option value="1">⭐ Very poor</option></select></div>
          <div class="field"><label>Comments</label><textarea name="comment" placeholder="Tell us what worked or what could be better…"></textarea></div>
          <button class="btn">Submit feedback</button>
        </form>
      </div>`;
    $('#fb', c).onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target).entries());
      try {
        await api('/feedback', { method: 'POST', body: { kind: fd.kind, rating: Number(fd.rating), comment: fd.comment || null } });
        toast('Thanks for your feedback!', 'success');
        e.target.reset();
      } catch (err) { toast(err.message, 'error'); }
    };
  };

  /* ---------- boot ---------- */
  function start() { state.token ? renderShell() : renderAuth(); }
  return { start };
})();

document.addEventListener('DOMContentLoaded', App.start);
