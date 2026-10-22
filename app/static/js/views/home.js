/* Tổng quan + Hồ sơ bối cảnh (12 mục, phiên bản, phỏng vấn nhanh). */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;

  // ------------------------------------------------------------------ TỔNG QUAN
  const WORKFLOW = [
    { n: 1, title: 'Điền hồ sơ bối cảnh', text: 'Sản phẩm, khách, giá, biên lãi, kênh. Mọi tác vụ đọc từ đây.', href: '#/context', icon: 'fa-id-card' },
    { n: 2, title: 'Chốt trụ cột nội dung', text: '3–5 trụ cột theo phễu, tránh đăng ngẫu hứng.', href: '#/studio/content_pillars', icon: 'fa-layer-group' },
    { n: 3, title: 'Lên lịch nội dung', text: 'Lịch có ngày lễ Việt Nam và âm lịch, mỗi bài có mục tiêu đo.', href: '#/studio/content_calendar', icon: 'fa-calendar-days' },
    { n: 4, title: 'Ghi khách vào CRM', text: 'Theo 6 tầng phễu, có ghi nhận đồng ý tiếp thị.', href: '#/leads', icon: 'fa-users' },
    { n: 5, title: 'Nhập số liệu tuần', text: 'Chi phí, doanh thu, đơn, khách mới → MER, CAC, ROAS hòa vốn.', href: '#/growth', icon: 'fa-chart-pie' },
    { n: 6, title: 'Vòng lặp tuần', text: 'Tìm nút thắt phễu, chọn 1 thử nghiệm cho tuần sau.', href: '#/studio/weekly_loop', icon: 'fa-rotate' },
  ];

  const LOG_TONE = { SUCCESS: 'chip-ok', DONE: 'chip-ok', FAILED: 'chip-bad', SKIPPED: 'chip-warn', RUNNING: 'chip-info' };

  function upcoming(holidays, days = 60) {
    const now = new Date(App.today() + 'T00:00:00');
    const end = new Date(now.getTime() + days * 86400000);
    return holidays.filter((h) => {
      const d = new Date(h.date + 'T00:00:00');
      return d >= now && d <= end;
    }).sort((a, b) => a.date.localeCompare(b.date));
  }

  function prepDate(h) {
    const d = new Date(h.date + 'T00:00:00');
    d.setDate(d.getDate() - (h.prep_days || 14));
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  async function renderHome(el) {
    const year = new Date().getFullYear();
    const [ctx, auto, runs, h1, h2] = await Promise.all([
      App.loadContext(true), App.get('/api/autopilot/status'), App.get('/api/skills/runs'),
      App.get('/api/holidays?year=' + year), App.get('/api/holidays?year=' + (year + 1)),
    ]);
    const comp = ctx.completeness;
    const c = auto.counts;
    const brand = (ctx.context.brand && ctx.context.brand.name) || '';
    const hol = upcoming([...h1.holidays, ...h2.holidays]).slice(0, 6);
    const hasKey = App.state.status && App.state.status.ai && (App.state.status.ai.has_key || App.state.status.ai.server_key_available);
    const tone = comp.score >= 75 ? 'bg-emerald-500' : comp.score >= 40 ? 'bg-amber-500' : 'bg-rose-500';

    el.innerHTML = `
      <div class="space-y-5">
        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center gap-4">
            <div class="flex-1 min-w-0">
              <h1 class="text-xl font-bold">${brand ? 'Xin chào, ' + esc(brand) : 'Chào mừng đến Marketing OS'}</h1>
              <p class="text-sm text-slate-400 mt-1">Bối cảnh trước, chiến thuật sau. Mọi kết quả đều ghi rõ nguồn, model và bị kiểm tuân thủ trước khi đăng.</p>
            </div>
            <div class="md:w-72">
              <div class="flex justify-between text-xs mb-1"><span class="text-slate-400">Hồ sơ bối cảnh</span><span class="font-bold">${comp.score}%</span></div>
              <div class="bar"><span class="${tone}" style="width:${Math.max(3, comp.score)}%"></span></div>
              <div class="flex gap-2 mt-3">
                <button type="button" class="btn-primary btn-sm" data-act="interview"><i class="fa-solid fa-comments"></i> Trả lời nhanh</button>
                <a href="#/context" class="btn-ghost btn-sm">Mở hồ sơ</a>
              </div>
            </div>
          </div>
          ${comp.missing_core.length ? `<div class="mt-4 text-xs text-slate-400">Còn thiếu thông tin cốt lõi: ${comp.missing_core.map((m) => `<span class="chip chip-warn mr-1 mb-1">${esc(m.label)}</span>`).join('')}</div>` : ''}
          ${!hasKey ? '<div class="mt-4 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200"><i class="fa-solid fa-key"></i> Chưa có Gemini API key nên các tác vụ AI chưa chạy được. <a href="#/settings" class="underline font-semibold">Thêm key trong Cài đặt</a> (miễn phí tại aistudio.google.com).</div>' : ''}
        </div>

        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          ${ui.kpi('Nội dung', App.num(c.content), '<a class="text-sky-400" href="#/content">Kho nội dung</a>')}
          ${ui.kpi('Lịch sắp tới', App.num(c.calendar), '<a class="text-sky-400" href="#/calendar">Lịch</a>')}
          ${ui.kpi('Khách hàng', App.num(c.leads), '<a class="text-sky-400" href="#/leads">CRM</a>')}
          ${ui.kpi('Đối thủ', App.num(c.competitors), '<a class="text-sky-400" href="#/research">Đối thủ</a>')}
          ${ui.kpi('Lần chạy AI', App.num(c.runs), '<a class="text-sky-400" href="#/studio">Studio</a>')}
        </div>

        <div class="grid lg:grid-cols-3 gap-5">
          <div class="lg:col-span-2 space-y-5">
            <div class="card">
              <div class="flex items-center justify-between gap-3 mb-3">
                <h2 class="font-bold">Quy trình làm marketing mỗi tuần</h2>
                <button type="button" class="btn-soft btn-sm" data-act="quickstart"><i class="fa-solid fa-bolt"></i> Khởi động nhanh</button>
              </div>
              <p class="text-xs text-slate-400 mb-3">Khởi động nhanh chạy nền 3 tác vụ: trụ cột nội dung → lịch 14 ngày → ý tưởng marketing. Cần hồ sơ có sản phẩm, khách mua và kênh.</p>
              <ol class="grid sm:grid-cols-2 gap-3">
                ${WORKFLOW.map((w) => `<li><a href="${w.href}" class="flex gap-3 p-3 rounded-xl border border-slate-800 hover:border-sky-500/60 bg-slate-950/40 h-full">
                  <span class="w-8 h-8 shrink-0 rounded-lg bg-slate-800 flex items-center justify-center text-sky-300"><i class="fa-solid ${w.icon}"></i></span>
                  <span><span class="text-sm font-semibold block">${w.n}. ${esc(w.title)}</span><span class="text-xs text-slate-400">${esc(w.text)}</span></span></a></li>`).join('')}
              </ol>
            </div>

            <div class="card">
              <div class="flex items-center justify-between mb-3"><h2 class="font-bold">Kết quả gần đây</h2><a href="#/studio" class="text-xs text-sky-400">Tất cả</a></div>
              ${runs.runs.length ? `<ul class="divide-y divide-slate-800">${runs.runs.slice(0, 6).map((r) => `<li class="py-2 flex items-center gap-3">
                <a class="flex-1 min-w-0 text-sm truncate hover:text-sky-300" href="#/studio/run/${r.id}">${esc(r.title)}</a>
                <span class="text-xs text-slate-500 shrink-0">${esc(App.dt(r.created_at, true))}</span></li>`).join('')}</ul>`
                : '<p class="text-sm text-slate-400">Chưa chạy tác vụ nào. Bắt đầu từ Skill Studio.</p>'}
            </div>
          </div>

          <div class="space-y-5">
            <div class="card">
              <h2 class="font-bold mb-3">Dịp sắp tới (60 ngày)</h2>
              ${hol.length ? `<ul class="space-y-2.5">${hol.map((h) => {
                const prep = prepDate(h);
                const late = prep <= App.today();
                return `<li class="flex gap-3"><div class="w-12 text-center shrink-0 rounded-lg bg-slate-800 py-1"><div class="text-[10px] text-slate-400">${App.weekday(h.date)}</div><div class="text-sm font-bold">${esc(App.dateVi(h.date).slice(0, 5))}</div></div>
                  <div class="min-w-0"><div class="text-sm font-semibold truncate">${esc(h.name)}</div>
                  <div class="text-[11px] ${late ? 'text-amber-300' : 'text-slate-400'}">${esc(h.type)} · ${late ? 'Nên chuẩn bị ngay' : 'Chuẩn bị từ ' + esc(App.dateVi(prep))}</div></div></li>`;
              }).join('')}</ul>` : '<p class="text-sm text-slate-400">Không có dịp lớn trong 60 ngày tới.</p>'}
            </div>
            <div class="card">
              <div class="flex items-center justify-between mb-3"><h2 class="font-bold">Nhật ký hệ thống</h2><button type="button" class="text-xs text-sky-400" data-act="reload">Làm mới</button></div>
              <div data-logs>${renderLogs(auto.logs)}</div>
            </div>
          </div>
        </div>
      </div>`;

    App.on(el, {
      interview: () => openInterview(),
      reload: () => App.render(),
      quickstart: async (btn) => {
        const ok = await App.confirm('Chạy nền 3 tác vụ AI (trụ cột nội dung, lịch 14 ngày từ hôm nay, ý tưởng marketing). Lịch mới sẽ thay lịch cũ trong cùng khoảng ngày. Tiếp tục?', { okLabel: 'Chạy' });
        if (!ok) return;
        App.busy(btn, true, 'Đang chạy…');
        try {
          const r = await App.post('/api/autopilot/run');
          App.toast(r.message, 'info');
          pollLogs(el, btn);
        } catch (e) {
          App.busy(btn, false);
          throw e;
        }
      },
    });
  }

  function renderLogs(logs) {
    if (!logs || !logs.length) return '<p class="text-sm text-slate-400">Chưa có hoạt động.</p>';
    return `<ul class="space-y-2 max-h-80 overflow-y-auto pr-1">${logs.map((l) => `<li class="text-xs">
      <div class="flex items-center gap-2"><span class="chip ${LOG_TONE[l.status] || 'chip-mute'}">${esc(l.status)}</span><span class="font-semibold truncate">${esc(l.task_name)}</span></div>
      <div class="text-slate-400 mt-0.5 break-words">${esc(l.details || '')}</div>
      <div class="text-slate-600">${esc(App.dt(l.created_at))}</div></li>`).join('')}</ul>`;
  }

  function pollLogs(el, btn) {
    let n = 0;
    const tick = async () => {
      n += 1;
      if (!document.body.contains(el)) return;
      try {
        const st = await App.get('/api/autopilot/status');
        const box = el.querySelector('[data-logs]');
        if (box) box.innerHTML = renderLogs(st.logs);
        const last = (st.logs || [])[0];
        if (last && last.task_code === 'QUICKSTART' && last.status === 'DONE') {
          App.busy(btn, false);
          App.toast('Khởi động nhanh đã xong. Xem nhật ký để biết từng bước.');
          return;
        }
      } catch (e) { /* thử lại lần sau */ }
      if (n < 90) setTimeout(tick, 4000); else App.busy(btn, false);
    };
    setTimeout(tick, 2500);
  }

  // ------------------------------------------------------------------ PHỎNG VẤN NHANH
  async function openInterview(focus) {
    const q = await App.get('/api/context/questions?limit=5' + (focus ? '&focus=' + encodeURIComponent(focus) : ''));
    if (!q.questions.length) { App.toast('Hồ sơ đã đủ các câu hỏi quan trọng.', 'info'); return; }
    const body = document.createElement('div');
    body.innerHTML = `<p class="text-xs text-slate-400 mb-4">Trả lời bằng lời của bạn, ngắn gọn. Câu nào chưa biết thì bỏ trống — hệ thống sẽ không tự đoán.</p><div class="space-y-4" data-q></div>`;
    const box = body.querySelector('[data-q]');
    q.questions.forEach((x, i) => {
      const multi = !['text', 'number'].includes(x.kind);
      box.insertAdjacentHTML('beforeend', `<div><label class="lbl" for="iq${i}">${i + 1}. ${esc(x.question)}</label>
        ${multi ? `<textarea id="iq${i}" class="txt" data-path="${esc(x.path)}" data-kind="${esc(x.kind)}"></textarea>` : `<input id="iq${i}" class="inp" data-path="${esc(x.path)}" data-kind="${esc(x.kind)}">`}
        ${x.hint ? `<p class="help">${esc(x.hint)}</p>` : ''}</div>`);
    });
    App.modal({
      title: 'Phỏng vấn hồ sơ bối cảnh',
      body,
      actions: [
        { label: 'Để sau' },
        {
          label: '<i class="fa-solid fa-floppy-disk"></i> Lưu câu trả lời', cls: 'btn-primary',
          onClick: async () => {
            const patch = {};
            App.$$('[data-path]', body).forEach((inpEl) => {
              const v = ui.fromText(inpEl.dataset.kind, inpEl.value);
              if ((Array.isArray(v) && v.length) || (!Array.isArray(v) && v !== null && v !== '')) patch[inpEl.dataset.path] = v;
            });
            if (!Object.keys(patch).length) { App.toast('Chưa có câu trả lời nào.', 'warn'); return true; }
            await App.patch('/api/context', { patch, note: 'Phỏng vấn nhanh' });
            await App.loadContext(true);
            App.toast('Đã lưu vào hồ sơ.');
            App.render();
            return false;
          },
        },
      ],
    });
  }
  App.openInterview = openInterview;

  // ------------------------------------------------------------------ HỒ SƠ BỐI CẢNH
  const SECTIONS = [
    { title: 'Thương hiệu & liên hệ', icon: 'fa-store', match: (p) => p.startsWith('brand.') },
    { title: 'Sản phẩm, giá & kinh tế đơn vị', icon: 'fa-tags', match: (p) => p.startsWith('product.') || p.startsWith('unit_economics.') },
    { title: 'Khách hàng & vấn đề', icon: 'fa-user-group', match: (p) => p.startsWith('customers.') || p.startsWith('problem.') || p === 'anti_persona' },
    { title: '4 lực chuyển đổi & lời từ chối', icon: 'fa-scale-balanced', match: (p) => p.startsWith('forces.') || p === 'objections' },
    { title: 'Cạnh tranh & khác biệt', icon: 'fa-chess', match: (p) => p.startsWith('competitors.') || p.startsWith('differentiation.') },
    { title: 'Ngôn ngữ khách & giọng thương hiệu', icon: 'fa-quote-left', match: (p) => p.startsWith('customer_language.') || p.startsWith('brand_voice.') },
    { title: 'Bằng chứng & câu hỏi thường gặp', icon: 'fa-certificate', match: (p) => p === 'proof' || p === 'faq' },
    { title: 'Mục tiêu, kênh & thị trường', icon: 'fa-bullseye', match: (p) => p.startsWith('goals.') || p === 'channels_active' || p.startsWith('market.') },
  ];
  const PRIO = { 1: '<span class="chip chip-bad">Cốt lõi</span>', 2: '<span class="chip chip-info">Quan trọng</span>', 3: '' };

  function getPath(obj, path) {
    return path.split('.').reduce((o, k) => (o && typeof o === 'object' ? o[k] : undefined), obj);
  }

  function fieldHtml(f, value) {
    const id = 'ctx-' + f.path.replace(/\./g, '-');
    const text = ui.toText(f.kind, value);
    const multi = f.kind !== 'text' && f.kind !== 'number';
    const control = f.kind === 'number'
      ? `<input id="${id}" class="inp" inputmode="decimal" data-path="${esc(f.path)}" data-kind="number" value="${esc(text)}" placeholder="${esc(f.hint || '')}">`
      : `<textarea id="${id}" class="txt ${multi ? '' : 'txt-sm'}" rows="${multi ? 4 : 2}" data-path="${esc(f.path)}" data-kind="${esc(f.kind)}" placeholder="${esc(f.hint || '')}">${esc(text)}</textarea>`;
    return `<div><label class="lbl flex items-center gap-2 flex-wrap" for="${id}">${esc(f.label)} ${PRIO[f.priority] || ''}</label>
      <p class="text-xs text-slate-400 mb-1.5">${esc(f.question)}</p>${control}
      ${multi ? `<p class="help">${esc(f.hint || 'Mỗi dòng một ý.')}</p>` : ''}</div>`;
  }

  async function renderContext(el) {
    const data = await App.loadContext(true);
    const ctx = data.context;
    const fields = data.fields;
    const comp = data.completeness;
    const tone = comp.score >= 75 ? 'bg-emerald-500' : comp.score >= 40 ? 'bg-amber-500' : 'bg-rose-500';
    const used = new Set();
    const sectionHtml = SECTIONS.map((s, si) => {
      const fs = fields.filter((f) => !used.has(f.path) && s.match(f.path));
      fs.forEach((f) => used.add(f.path));
      if (!fs.length) return '';
      const filled = fs.filter((f) => ui.toText(f.kind, getPath(ctx, f.path)).trim()).length;
      return `<details class="card group" data-section="${si}" ${si === 0 || filled < fs.length ? 'open' : ''}>
        <summary class="flex items-center gap-3 cursor-pointer list-none">
          <span class="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-sky-300 shrink-0"><i class="fa-solid ${s.icon}"></i></span>
          <span class="flex-1 font-bold">${esc(s.title)}</span>
          <span class="chip ${filled === fs.length ? 'chip-ok' : 'chip-mute'}">${filled}/${fs.length}</span>
          <i class="fa-solid fa-chevron-down text-slate-500 group-open:rotate-180 transition-transform"></i>
        </summary>
        <div class="mt-4 grid md:grid-cols-2 gap-4">${fs.map((f) => fieldHtml(f, getPath(ctx, f.path))).join('')}</div>
        <div class="mt-4 flex flex-col sm:flex-row gap-2 sm:items-center">
          <input class="inp sm:max-w-sm" data-note placeholder="Vì sao thay đổi? (ghi vào nhật ký hồ sơ, không bắt buộc)">
          <button type="button" class="btn-primary btn-sm justify-center" data-act="save" data-section="${si}"><i class="fa-solid fa-floppy-disk"></i> Lưu mục này</button>
        </div>
      </details>`;
    }).join('');

    el.innerHTML = `
      <div class="space-y-4">
        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center gap-4">
            <div class="flex-1">
              <h1 class="text-lg font-bold">Hồ sơ bối cảnh <span class="chip chip-mute ml-1">v${esc(ctx.version || 1)}</span></h1>
              <p class="text-sm text-slate-400 mt-1">Nguồn sự thật duy nhất cho mọi tác vụ AI. Chỉ ghi điều có thật; mục nào chưa biết cứ để trống, AI sẽ hỏi lại thay vì tự đoán.</p>
            </div>
            <div class="md:w-64">
              <div class="flex justify-between text-xs mb-1"><span class="text-slate-400">Độ đầy đủ</span><span class="font-bold">${comp.score}%</span></div>
              <div class="bar"><span class="${tone}" style="width:${Math.max(3, comp.score)}%"></span></div>
            </div>
          </div>
          <div class="flex flex-wrap gap-2 mt-4">
            <button type="button" class="btn-soft btn-sm" data-act="interview"><i class="fa-solid fa-comments"></i> Phỏng vấn nhanh 5 câu</button>
            <button type="button" class="btn-ghost btn-sm" data-act="history"><i class="fa-solid fa-clock-rotate-left"></i> Nhật ký thay đổi</button>
            <button type="button" class="btn-ghost btn-sm" data-act="export"><i class="fa-solid fa-download"></i> Tải JSON</button>
          </div>
        </div>
        ${sectionHtml}
      </div>`;

    App.on(el, {
      interview: () => openInterview(),
      export: () => App.downloadApi('/api/context/export', 'ho-so-boi-canh.json'),
      history: () => openHistory(ctx),
      save: async (btn) => {
        const sec = el.querySelector(`details[data-section="${btn.dataset.section}"]`);
        const patch = {};
        App.$$('[data-path]', sec).forEach((inpEl) => {
          const f = fields.find((x) => x.path === inpEl.dataset.path);
          const before = getPath(ctx, f.path);
          if (inpEl.value.trim() === ui.toText(f.kind, before).trim()) return;
          let v = ui.fromText(f.kind, inpEl.value, before);
          if (f.kind === 'number' && v === null) v = '';
          patch[f.path] = v === '' && f.kind === 'number' ? null : v;
        });
        if (!Object.keys(patch).length) { App.toast('Không có thay đổi.', 'info'); return; }
        App.busy(btn, true, 'Đang lưu…');
        try {
          await App.patch('/api/context', { patch, note: sec.querySelector('[data-note]').value });
          App.toast('Đã lưu hồ sơ.');
          await App.render();
        } finally {
          App.busy(btn, false);
        }
      },
    });
  }

  async function openHistory(ctx) {
    const v = await App.get('/api/context/versions');
    const log = ctx.changelog || [];
    App.modal({
      title: 'Nhật ký thay đổi hồ sơ',
      body: `${log.length ? `<ol class="space-y-3">${log.map((c) => `<li class="border-l-2 border-sky-500/50 pl-3">
          <div class="text-xs text-slate-400">${esc(c.date)} · v${esc(c.version)}</div>
          <div class="text-sm">${esc(c.change)}</div>${c.why ? `<div class="text-xs text-slate-400 mt-0.5">Lý do: ${esc(c.why)}</div>` : ''}</li>`).join('')}</ol>`
        : '<p class="text-sm text-slate-400">Chưa có thay đổi.</p>'}
        <p class="text-xs text-slate-500 mt-4">Hệ thống giữ ${v.versions.length} bản chụp gần nhất (tối đa 30) để đối chiếu khi cần.</p>`,
    });
  }

  App.views.home = { render: renderHome };
  App.views.context = { render: renderContext };
})();
