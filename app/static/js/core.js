/* Marketing OS — lõi giao diện: gọi API, phiên đăng nhập, điều hướng, thông báo, hộp thoại. */
(function () {
  'use strict';

  const App = (window.App = window.App || {});
  App.views = {};
  App.state = { user: null, status: null, context: null, tasks: null };

  const TOKEN_KEY = 'mos_token';

  // ---------------------------------------------------------------- tiện ích
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  App.esc = esc;
  App.$ = (sel, root = document) => root.querySelector(sel);
  App.$$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  App.money = (v) => {
    if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) return '—';
    return Math.round(Number(v)).toLocaleString('vi-VN') + ' đ';
  };
  App.num = (v, digits = 0) => {
    if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) return '—';
    return Number(v).toLocaleString('vi-VN', { maximumFractionDigits: digits, minimumFractionDigits: 0 });
  };
  App.compact = (v) => {
    const n = Number(v) || 0;
    const a = Math.abs(n);
    if (a >= 1e9) return App.num(n / 1e9, 1) + ' tỷ';
    if (a >= 1e6) return App.num(n / 1e6, 1) + ' tr';
    if (a >= 1e3) return App.num(n / 1e3, 0) + 'k';
    return App.num(n);
  };
  App.pct = (v) => (v === null || v === undefined ? '—' : App.num(v, 1) + '%');
  App.today = () => {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  };
  App.month = () => App.today().slice(0, 7);
  App.dateVi = (iso) => {
    if (!iso) return '';
    const s = String(iso).slice(0, 10).split('-');
    return s.length === 3 ? `${s[2]}/${s[1]}/${s[0]}` : iso;
  };
  // Thời điểm lưu trong CSDL (CURRENT_TIMESTAMP của SQLite) là giờ UTC, dạng "YYYY-MM-DD HH:MM:SS": đổi sang giờ máy người xem.
  App.dt = (ts, dateOnly = false) => {
    if (!ts) return '';
    const s = String(ts);
    if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$/.test(s)) {
      const d = new Date(s.replace(' ', 'T') + 'Z');
      if (!Number.isNaN(d.getTime())) {
        const opts = dateOnly ? { day: '2-digit', month: '2-digit', year: 'numeric' }
          : { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' };
        return d.toLocaleString('vi-VN', opts);
      }
    }
    return s;
  };
  App.weekday = (iso) => ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'][new Date(iso + 'T00:00:00').getDay()];

  let purifyHooked = false;
  App.md = (text) => {
    if (!window.marked || !window.DOMPurify) return `<pre class="whitespace-pre-wrap">${esc(text)}</pre>`;
    if (!purifyHooked) {
      // Liên kết trong kết quả AI luôn mở tab mới và không lộ trang nguồn
      window.DOMPurify.addHook('afterSanitizeAttributes', (node) => {
        if (node.tagName === 'A' && node.getAttribute('href')) {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      });
      purifyHooked = true;
    }
    return window.DOMPurify.sanitize(window.marked.parse(String(text || '')));
  };

  App.copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      App.toast('Đã sao chép.');
    } catch (e) {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); App.toast('Đã sao chép.'); } catch (_) { App.toast('Trình duyệt chặn sao chép.', 'bad'); }
      ta.remove();
    }
  };

  App.download = (filename, content, type = 'text/plain;charset=utf-8') => {
    const blob = content instanceof Blob ? content : new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };

  // ---------------------------------------------------------------- API
  App.token = () => { try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; } };
  App.setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch (e) { /* bỏ qua */ } };

  class ApiError extends Error {
    constructor(message, status, data) { super(message); this.status = status; this.data = data; }
  }
  App.ApiError = ApiError;

  App.api = async (method, url, body, opts = {}) => {
    const headers = { Accept: 'application/json' };
    const token = App.token();
    if (token) headers.Authorization = 'Bearer ' + token;
    const init = { method, headers };
    if (body !== undefined && body !== null) {
      headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(body);
    }
    let res;
    try {
      res = await fetch(url, init);
    } catch (e) {
      throw new ApiError('Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.', 0);
    }
    if (res.status === 401 && !opts.allow401) {
      App.setToken('');
      App.showAuth('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      throw new ApiError('Cần đăng nhập lại.', 401);
    }
    if (opts.raw) {
      if (!res.ok) throw new ApiError(`Lỗi HTTP ${res.status}`, res.status);
      return res;
    }
    let data = null;
    const ctype = res.headers.get('content-type') || '';
    if (ctype.includes('application/json')) {
      try { data = await res.json(); } catch (e) { data = null; }
    } else {
      data = await res.text();
    }
    if (!res.ok) {
      let msg = (data && data.detail) || `Lỗi HTTP ${res.status}`;
      if (Array.isArray(msg)) msg = msg.map((d) => d.msg || JSON.stringify(d)).join('; ');
      throw new ApiError(String(msg), res.status, data);
    }
    return data;
  };
  App.get = (u, o) => App.api('GET', u, undefined, o);
  App.post = (u, b, o) => App.api('POST', u, b || {}, o);
  App.patch = (u, b) => App.api('PATCH', u, b || {});
  App.put = (u, b) => App.api('PUT', u, b || {});
  App.del = (u, b) => App.api('DELETE', u, b);

  App.downloadApi = async (url, fallbackName) => {
    try {
      const res = await App.api('GET', url, undefined, { raw: true });
      const blob = await res.blob();
      const cd = res.headers.get('content-disposition') || '';
      const m = cd.match(/filename=([^;]+)/);
      App.download(m ? m[1].replace(/"/g, '') : fallbackName, blob);
    } catch (e) {
      App.toast(e.message, 'bad');
    }
  };

  // ---------------------------------------------------------------- thông báo
  App.toast = (msg, kind = 'ok') => {
    const root = document.getElementById('toast');
    const el = document.createElement('div');
    const icon = { ok: 'fa-circle-check text-emerald-400', bad: 'fa-circle-exclamation text-rose-400', warn: 'fa-triangle-exclamation text-amber-400', info: 'fa-circle-info text-sky-400' }[kind] || 'fa-circle-info text-sky-400';
    el.className = 'toast';
    el.setAttribute('role', kind === 'bad' ? 'alert' : 'status');
    el.innerHTML = `<i class="fa-solid ${icon} mt-0.5"></i><div class="flex-1">${esc(msg)}</div>`;
    root.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, kind === 'bad' ? 6000 : 3500);
    setTimeout(() => el.remove(), kind === 'bad' ? 6400 : 3900);
  };

  // ---------------------------------------------------------------- hộp thoại
  App.modal = ({ title, body, actions = [], wide = false, onMount }) => {
    const root = document.getElementById('modal-root');
    const wrap = document.createElement('div');
    wrap.className = 'modal-backdrop';
    wrap.innerHTML = `<div class="modal ${wide ? 'sm:max-w-5xl' : ''}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
      <div class="sticky top-0 bg-slate-900 border-b border-slate-800 px-5 py-3 flex items-center gap-3 z-10">
        <h3 class="font-bold flex-1 truncate">${esc(title)}</h3>
        <button type="button" data-close class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-sm" aria-label="Đóng"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <div class="p-5 flex-1" data-body></div>
      ${actions.length ? '<div class="flex flex-wrap gap-2 justify-end" data-actions></div>' : ''}
    </div>`;
    const bodyEl = wrap.querySelector('[data-body]');
    if (typeof body === 'string') bodyEl.innerHTML = body; else if (body) bodyEl.appendChild(body);
    const close = () => { wrap.remove(); document.removeEventListener('keydown', onKey); };
    const onKey = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    wrap.addEventListener('click', (e) => { if (e.target === wrap || e.target.closest('[data-close]')) close(); });
    const actEl = wrap.querySelector('[data-actions]');
    actions.forEach((a) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = a.cls || 'btn-ghost';
      b.innerHTML = a.label;
      b.addEventListener('click', async () => {
        if (!a.onClick) return close();
        try {
          App.busy(b, true);
          const keep = await a.onClick({ close, body: bodyEl });
          if (keep !== true) close();
        } catch (e) {
          App.toast(e.message || String(e), 'bad');
        } finally {
          App.busy(b, false);
        }
      });
      actEl.appendChild(b);
    });
    root.appendChild(wrap);
    if (onMount) onMount(bodyEl, close);
    const first = wrap.querySelector('input, textarea, select');
    if (first) setTimeout(() => first.focus(), 30);
    return { close, body: bodyEl };
  };

  App.confirm = (message, { title = 'Xác nhận', okLabel = 'Đồng ý', danger = false } = {}) => new Promise((resolve) => {
    let done = false;
    const m = App.modal({
      title,
      body: `<p class="text-sm text-slate-300 leading-relaxed">${esc(message)}</p>`,
      actions: [
        { label: 'Hủy', onClick: () => { done = true; resolve(false); } },
        { label: okLabel, cls: danger ? 'btn-danger' : 'btn-primary', onClick: () => { done = true; resolve(true); } },
      ],
    });
    const obs = new MutationObserver(() => { if (!document.body.contains(m.body)) { obs.disconnect(); if (!done) resolve(false); } });
    obs.observe(document.getElementById('modal-root'), { childList: true });
  });

  App.busy = (btn, on, label) => {
    if (!btn) return;
    if (on) {
      btn.dataset.label = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> ${esc(label || 'Đang xử lý…')}`;
    } else {
      btn.disabled = false;
      if (btn.dataset.label) btn.innerHTML = btn.dataset.label;
    }
  };

  // Gắn sự kiện theo data-act trong một vùng
  App.on = (root, handlers) => {
    root.addEventListener('click', async (e) => {
      const el = e.target.closest('[data-act]');
      if (!el || !root.contains(el)) return;
      const fn = handlers[el.dataset.act];
      if (!fn) return;
      e.preventDefault();
      try {
        await fn(el, e);
      } catch (err) {
        if (err && err.status !== 401) App.toast(err.message || String(err), 'bad');
      }
    });
  };

  // ---------------------------------------------------------------- điều hướng
  App.NAV = [
    { group: 'TỔNG QUAN' },
    { id: 'home', label: 'Tổng quan', icon: 'fa-gauge-high' },
    { id: 'context', label: 'Hồ sơ bối cảnh', icon: 'fa-id-card' },

    { group: 'CƠ HỘI SEO & THỊ TRƯỜNG' },
    { id: 'seo_tools', label: 'AI Market Radar', icon: 'fa-radar', badge: 'AI' },
    { id: 'research', label: 'Nghiên cứu & Đối thủ', icon: 'fa-magnifying-glass-chart' },
    { id: 'local', label: 'Local SEO & AI search', icon: 'fa-location-dot' },

    { group: 'NỘI DUNG & SEO' },
    { id: 'humanize', label: 'Viết lại & Humanize AI', icon: 'fa-wand-magic-sparkles', badge: 'Bypass 99%' },
    { id: 'studio', label: 'Skill Studio AI', icon: 'fa-robot', badge: 'HOT' },
    { id: 'content', label: 'Kho nội dung bài viết', icon: 'fa-pen-nib' },
    { id: 'calendar', label: 'Kế hoạch nội dung', icon: 'fa-calendar-days' },
    { id: 'media', label: 'Media: Ảnh & Video', icon: 'fa-photo-film' },
    { id: 'compliance', label: 'Kiểm duyệt nội dung', icon: 'fa-shield-halved' },

    { group: 'KHÁCH HÀNG & TĂNG TRƯỞNG' },
    { id: 'leads', label: 'Khách hàng (CRM 6 tầng)', icon: 'fa-users' },
    { id: 'growth', label: 'Growth Console', icon: 'fa-chart-pie' },

    { group: 'HỆ THỐNG' },
    { id: 'settings', label: 'Cài đặt AI & Website', icon: 'fa-gear' },
  ];
  App.BOTTOM = ['home', 'humanize', 'studio', 'content', 'leads'];

  App.parseHash = () => {
    const raw = (location.hash || '#/home').replace(/^#\/?/, '');
    const [path, query] = raw.split('?');
    const parts = path.split('/').filter(Boolean).map(decodeURIComponent);
    const params = Object.fromEntries(new URLSearchParams(query || ''));
    return { view: parts[0] || 'home', args: parts.slice(1), params };
  };

  App.go = (view, ...args) => {
    const hash = '#/' + [view, ...args].map(encodeURIComponent).join('/');
    if (location.hash === hash) App.render(); else location.hash = hash;
  };

  App.render = async () => {
    if (!App.state.user) return;
    const { view, args, params } = App.parseHash();
    const def = App.views[view] || App.views.home;
    const name = App.views[view] ? view : 'home';
    App.$$('[data-nav]').forEach((a) => a.classList.toggle('active', a.dataset.nav === name));
    const navDef = App.NAV.find((n) => n.id === name);
    document.getElementById('view-title').textContent = navDef ? navDef.label : 'Marketing OS';
    document.title = (navDef ? navDef.label + ' · ' : '') + 'Marketing OS';
    const el = document.getElementById('view');
    el.innerHTML = '<div class="space-y-3"><div class="skeleton h-24"></div><div class="skeleton h-48"></div></div>';
    document.getElementById('drawer').classList.add('hidden');
    const token = (App._renderToken = (App._renderToken || 0) + 1);
    try {
      const fresh = document.createElement('div');
      await def.render(fresh, args, params);
      if (token !== App._renderToken) return;
      el.innerHTML = '';
      el.appendChild(fresh);
      window.scrollTo(0, 0);
    } catch (e) {
      if (token !== App._renderToken) return;
      if (e && e.status === 401) return;
      el.innerHTML = `<div class="card text-rose-300"><i class="fa-solid fa-circle-exclamation"></i> ${esc(e.message || e)}</div>`;
    }
  };

  App.buildNav = () => {
    const make = (n) => {
      if (n.group) return `<div class="nav-group">${esc(n.group)}</div>`;
      const b = n.badge
        ? `<span class="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded ${n.badge.includes('99%') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : n.badge === 'HOT' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'}">${esc(n.badge)}</span>`
        : '';
      return `<a href="#/${n.id}" data-nav="${n.id}" class="nav-item"><i class="fa-solid ${n.icon} w-4 text-center"></i><span class="truncate">${esc(n.label)}</span>${b}</a>`;
    };
    const html = App.NAV.map(make).join('');
    document.getElementById('nav').innerHTML = html;
    document.getElementById('drawer-nav').innerHTML = html;
    const short = { home: 'Tổng quan', humanize: 'Humanize', studio: 'Studio', content: 'Nội dung', leads: 'Khách' };
    document.getElementById('bottom-nav').innerHTML = App.BOTTOM.map((id) => {
      const n = App.NAV.find((x) => x.id === id);
      return `<a href="#/${id}" data-nav="${id}" class="bnav-item"><i class="fa-solid ${n.icon} text-base"></i><span class="truncate max-w-full">${esc(short[id] || n.label)}</span></a>`;
    }).join('');
  };

  App.showSearchPalette = () => {
    const items = [
      { id: 'humanize', title: 'Viết lại & Humanize AI', cat: 'Nội dung & SEO', icon: 'fa-wand-magic-sparkles', desc: 'Bypass 99% AI Detector, giữ nguyên từ khóa' },
      { id: 'seo_tools', title: 'AI Market Radar & Cơ hội SEO', cat: 'Cơ hội SEO', icon: 'fa-radar', desc: 'Quét xu hướng tìm kiếm, phát hiện ăn thịt từ khóa' },
      { id: 'studio', title: 'Skill Studio AI (18 Tác vụ)', cat: 'Nội dung & SEO', icon: 'fa-robot', desc: 'Nghiên cứu thị trường, bài viết, kịch bản, quảng cáo' },
      { id: 'research', title: 'Nghiên cứu & Đối thủ cạnh tranh', cat: 'Chiến lược', icon: 'fa-magnifying-glass-chart', desc: 'Rà soát đối thủ có nguồn & dossier trung thực' },
      { id: 'content', title: 'Kho bài viết & Quản lý nội dung', cat: 'Nội dung & SEO', icon: 'fa-pen-nib', desc: 'Biên tập, lưu trữ và xuất bản đa kênh' },
      { id: 'calendar', title: 'Kế hoạch nội dung theo ngày thật', cat: 'Nội dung & SEO', icon: 'fa-calendar-days', desc: 'Lập lịch ngày thật và ngày lễ Việt Nam' },
      { id: 'leads', title: 'Khách hàng CRM (6 tầng phễu)', cat: 'Tăng trưởng', icon: 'fa-users', desc: 'Quản lý lead, phễu chuyển đổi và doanh số' },
      { id: 'growth', title: 'Growth Console & Chỉ số đo lường', cat: 'Tăng trưởng', icon: 'fa-chart-pie', desc: 'Theo dõi AARRR, CAC, LTV và phễu bán hàng' },
      { id: 'compliance', title: 'Kiểm duyệt nội dung & Tuân thủ', cat: 'An toàn', icon: 'fa-shield-halved', desc: 'Chống quảng cáo láo, kiểm tra Luật 75/91' },
      { id: 'settings', title: 'Cài đặt Gemini AI & Hệ thống', cat: 'Hệ thống', icon: 'fa-gear', desc: 'API key, model AI và cấu hình workspace' },
    ];

    const bodyHtml = `
      <div class="space-y-3">
        <div class="relative">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500"></i>
          <input id="palette-input" class="inp pl-10 py-2.5 text-sm" placeholder="Nhập tên tính năng, từ khóa hoặc lệnh AI (ví dụ: humanize, đối thủ, bài viết)..." autocomplete="off">
        </div>
        <div id="palette-list" class="max-h-80 overflow-y-auto space-y-1 divide-y divide-slate-800/40">
          ${items.map((it) => `
            <a href="#/${it.id}" class="palette-item block p-2.5 rounded-xl hover:bg-slate-800 transition flex items-center justify-between gap-3 text-xs" data-cat="${esc(it.cat)}">
              <div class="flex items-center gap-3">
                <span class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-sky-400 text-sm"><i class="fa-solid ${it.icon}"></i></span>
                <div>
                  <div class="font-bold text-slate-200 text-sm">${esc(it.title)}</div>
                  <div class="text-slate-400 text-[11px]">${esc(it.desc)}</div>
                </div>
              </div>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">${esc(it.cat)}</span>
            </a>
          `).join('')}
        </div>
      </div>
    `;

    const m = App.modal({
      title: 'Tìm kiếm nhanh (Command Palette)',
      body: bodyHtml,
      wide: false,
      onMount: (bodyEl, close) => {
        const inp = bodyEl.querySelector('#palette-input');
        const listEl = bodyEl.querySelector('#palette-list');
        inp.focus();

        inp.addEventListener('input', () => {
          const q = inp.value.trim().toLowerCase();
          const filtered = items.filter((it) => it.title.toLowerCase().includes(q) || it.desc.toLowerCase().includes(q) || it.cat.toLowerCase().includes(q));
          if (!filtered.length) {
            listEl.innerHTML = '<div class="p-4 text-center text-slate-500 text-xs">Không tìm thấy tính năng phù hợp.</div>';
            return;
          }
          listEl.innerHTML = filtered.map((it) => `
            <a href="#/${it.id}" class="palette-item block p-2.5 rounded-xl hover:bg-slate-800 transition flex items-center justify-between gap-3 text-xs" data-cat="${esc(it.cat)}">
              <div class="flex items-center gap-3">
                <span class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-sky-400 text-sm"><i class="fa-solid ${it.icon}"></i></span>
                <div>
                  <div class="font-bold text-slate-200 text-sm">${esc(it.title)}</div>
                  <div class="text-slate-400 text-[11px]">${esc(it.desc)}</div>
                </div>
              </div>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">${esc(it.cat)}</span>
            </a>
          `).join('');
        });

        listEl.addEventListener('click', (e) => {
          const a = e.target.closest('a');
          if (a) close();
        });
      }
    });
  };

  // ---------------------------------------------------------------- đăng nhập
  let authMode = 'login';
  App.showAuth = (message) => {
    App.state.user = null;
    document.getElementById('app').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
    const err = document.getElementById('auth-error');
    if (message) { err.textContent = message; err.classList.remove('hidden'); } else { err.classList.add('hidden'); }
    App.setAuthMode(authMode);
  };

  App.setAuthMode = (mode) => {
    authMode = mode;
    App.$$('.auth-tab').forEach((t) => t.classList.toggle('active', t.dataset.authTab === mode));
    document.getElementById('auth-name-row').classList.toggle('hidden', mode !== 'register');
    document.getElementById('auth-pw-hint').classList.toggle('hidden', mode !== 'register');
    document.getElementById('auth-submit').textContent = mode === 'register' ? 'Tạo tài khoản' : 'Đăng nhập';
    document.getElementById('auth-password').setAttribute('autocomplete', mode === 'register' ? 'new-password' : 'current-password');
  };

  App.afterLogin = async (data) => {
    App.setToken(data.token);
    App.state.user = data.user;
    await App.boot();
  };

  App.initAuth = async () => {
    App.$$('.auth-tab').forEach((t) => t.addEventListener('click', () => App.setAuthMode(t.dataset.authTab)));
    document.getElementById('auth-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('auth-submit');
      const err = document.getElementById('auth-error');
      err.classList.add('hidden');
      const email = document.getElementById('auth-email').value.trim();
      const password = document.getElementById('auth-password').value;
      const name = document.getElementById('auth-name').value.trim();
      if (!email || !password) { err.textContent = 'Nhập email và mật khẩu.'; err.classList.remove('hidden'); return; }
      App.busy(btn, true, authMode === 'register' ? 'Đang tạo…' : 'Đang đăng nhập…');
      try {
        const data = await App.api('POST', '/api/auth/' + (authMode === 'register' ? 'register' : 'login'), { email, password, name }, { allow401: true });
        document.getElementById('auth-password').value = '';
        await App.afterLogin(data);
      } catch (e2) {
        err.textContent = e2.message;
        err.classList.remove('hidden');
      } finally {
        App.busy(btn, false);
      }
    });
    try {
      const cfg = await App.api('GET', '/api/auth/config', undefined, { allow401: true });
      if (!cfg.allow_registration) document.querySelector('[data-auth-tab="register"]').classList.add('hidden');
      if (cfg.google_client_id) App.initGoogle(cfg.google_client_id);
    } catch (e) { /* vẫn đăng nhập bằng mật khẩu được */ }
  };

  App.initGoogle = (clientId) => {
    const s = document.createElement('script');
    s.src = 'https://accounts.google.com/gsi/client';
    s.async = true;
    s.onload = () => {
      if (!window.google || !google.accounts) return;
      google.accounts.id.initialize({
        client_id: clientId,
        callback: async (resp) => {
          try {
            const data = await App.api('POST', '/api/auth/google', { credential: resp.credential }, { allow401: true });
            await App.afterLogin(data);
          } catch (e) {
            const err = document.getElementById('auth-error');
            err.textContent = e.message;
            err.classList.remove('hidden');
          }
        },
      });
      google.accounts.id.renderButton(document.getElementById('google-btn'), { theme: 'filled_black', size: 'large', text: 'continue_with', locale: 'vi' });
      document.getElementById('google-login').classList.remove('hidden');
    };
    document.head.appendChild(s);
  };

  App.logout = async () => {
    try { await App.api('POST', '/api/auth/logout', {}, { allow401: true }); } catch (e) { /* vẫn đăng xuất phía máy */ }
    App.setToken('');
    App.state = { user: null, status: null, context: null, tasks: null };
    App.showAuth();
  };

  // ---------------------------------------------------------------- trạng thái chung
  App.refreshStatus = async () => {
    const st = await App.get('/api/system/status');
    App.state.status = st;
    const badge = document.getElementById('ai-badge');
    const ai = st.ai || {};
    if (ai.has_key || ai.server_key_available) {
      badge.className = 'hidden sm:inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border chip-ok';
      badge.innerHTML = `<i class="fa-solid fa-circle text-[7px]"></i> Gemini ${esc(ai.model || 'tự chọn model')}`;
    } else {
      badge.className = 'hidden sm:inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border chip-warn';
      badge.innerHTML = '<i class="fa-solid fa-key"></i> Chưa có Gemini key';
    }
    const banner = document.getElementById('banner');
    if (st.ephemeral_storage) {
      banner.className = 'bg-amber-500/10 border-b border-amber-500/30 text-amber-200 text-xs px-4 md:px-6 py-2';
      banner.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Máy chủ đang dùng ổ đĩa tạm: dữ liệu sẽ mất khi dịch vụ khởi động lại. Hãy đặt DATA_DIR vào ổ đĩa bền (xem DEPLOY_TO_CLOUD.md) và thường xuyên tải bản sao lưu trong Cài đặt.';
    } else {
      banner.className = 'hidden';
    }
    return st;
  };

  App.loadContext = async (force = false) => {
    if (App.state.context && !force) return App.state.context;
    const data = await App.get('/api/context');
    App.state.context = data;
    const name = (data.context.brand && data.context.brand.name) || 'Chưa đặt tên';
    document.getElementById('side-brand').textContent = name;
    return data;
  };

  App.loadTasks = async () => {
    if (App.state.tasks) return App.state.tasks;
    App.state.tasks = await App.get('/api/skills');
    return App.state.tasks;
  };

  App.boot = async () => {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    document.getElementById('side-user').textContent = App.state.user.email;
    App.buildNav();
    try {
      await Promise.all([App.refreshStatus(), App.loadContext(true)]);
    } catch (e) {
      if (e.status === 401) return;
      App.toast(e.message, 'bad');
    }
    App.render();
  };
})();
