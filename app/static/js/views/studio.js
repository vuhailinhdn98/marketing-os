/* Skill Studio: danh mục tác vụ theo skill marketing, chạy tác vụ, xem kết quả, lưu kết quả vào đúng nơi dùng. */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;
  const LAST_KEY = 'mos_last_inputs';

  const GROUP_ICON = {
    'Chiến lược': 'fa-chess-knight', 'Ưu đãi & Nội dung': 'fa-pen-nib', 'Quảng cáo': 'fa-bullhorn',
    'Khách hàng & Bán hàng': 'fa-handshake', 'Giữ chân': 'fa-heart', 'SEO & Local': 'fa-magnifying-glass-location',
    'PR & KOL': 'fa-microphone', 'Đo lường': 'fa-chart-line',
  };

  const loadLast = (taskId) => { try { return JSON.parse(localStorage.getItem(LAST_KEY) || '{}')[taskId] || null; } catch (e) { return null; } };
  const saveLast = (taskId, inputs) => {
    try {
      const all = JSON.parse(localStorage.getItem(LAST_KEY) || '{}');
      all[taskId] = inputs;
      localStorage.setItem(LAST_KEY, JSON.stringify(all));
    } catch (e) { /* bộ nhớ trình duyệt bị chặn: bỏ qua */ }
  };

  function getPath(obj, path) {
    return path.split('.').reduce((o, k) => (o && typeof o === 'object' ? o[k] : undefined), obj);
  }
  function filled(v) {
    if (v === null || v === undefined) return false;
    if (Array.isArray(v)) return v.length > 0;
    return String(v).trim() !== '';
  }
  function missingFor(task) {
    const ctx = (App.state.context && App.state.context.context) || {};
    return (task.required_context || []).filter((p) => !filled(getPath(ctx, p)));
  }

  // ------------------------------------------------------------------ danh mục
  async function renderCatalog(el) {
    const [cat, runs] = await Promise.all([App.loadTasks(), App.get('/api/skills/runs'), App.loadContext()]);
    el.innerHTML = `
      <div class="space-y-5">
        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center gap-3">
            <div class="flex-1">
              <h1 class="text-lg font-bold">Skill Studio</h1>
              <p class="text-sm text-slate-400 mt-1">${cat.tasks.length} tác vụ dựng từ bộ skill marketing. Mỗi tác vụ đọc Hồ sơ bối cảnh, trả kết quả có cấu trúc, ghi nguồn và qua cổng tuân thủ.</p>
            </div>
            <div class="md:w-72 relative">
              <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm"></i>
              <input class="inp pl-9" data-search placeholder="Tìm tác vụ… (vd: quảng cáo, KOL)" aria-label="Tìm tác vụ">
            </div>
          </div>
        </div>
        <div class="grid lg:grid-cols-4 gap-5">
          <div class="lg:col-span-3 space-y-6" data-groups>
            ${cat.groups.map((g) => {
              const tasks = cat.tasks.filter((t) => t.group === g);
              if (!tasks.length) return '';
              return `<section data-group>
                <h2 class="text-sm font-bold text-slate-300 mb-2 flex items-center gap-2"><i class="fa-solid ${GROUP_ICON[g] || 'fa-circle'} text-sky-400"></i>${esc(g)}</h2>
                <div class="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
                  ${tasks.map((t) => {
                    const miss = missingFor(t);
                    return `<a href="#/studio/${esc(t.id)}" class="card-tight hover:border-sky-500/60 block" data-task data-text="${esc((t.title + ' ' + t.description + ' ' + t.group).toLowerCase())}">
                      <div class="flex items-start gap-2"><div class="font-semibold text-sm flex-1">${esc(t.title)}</div>${t.grounded ? '<span class="chip chip-ok shrink-0" title="Tìm kiếm Google, có nguồn"><i class="fa-brands fa-google"></i></span>' : ''}</div>
                      <p class="text-xs text-slate-400 mt-1 leading-relaxed">${esc(t.description)}</p>
                      ${miss.length ? `<div class="mt-2"><span class="chip chip-warn"><i class="fa-solid fa-circle-question"></i> Cần thêm ${miss.length} thông tin hồ sơ</span></div>` : ''}
                    </a>`;
                  }).join('')}
                </div></section>`;
            }).join('')}
            <p class="hidden text-sm text-slate-400" data-noresult>Không tìm thấy tác vụ phù hợp.</p>
          </div>
          <aside class="card h-fit">
            <h2 class="font-bold mb-3">Lịch sử chạy</h2>
            ${runsList(runs.runs.slice(0, 15))}
          </aside>
        </div>
      </div>`;
    const search = el.querySelector('[data-search]');
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      let any = false;
      App.$$('[data-group]', el).forEach((sec) => {
        let shown = 0;
        App.$$('[data-task]', sec).forEach((a) => {
          const ok = !q || a.dataset.text.includes(q);
          a.classList.toggle('hidden', !ok);
          if (ok) shown += 1;
        });
        sec.classList.toggle('hidden', !shown);
        any = any || shown > 0;
      });
      el.querySelector('[data-noresult]').classList.toggle('hidden', any);
    });
  }

  function runsList(runs) {
    if (!runs.length) return '<p class="text-sm text-slate-400">Chưa có lần chạy nào.</p>';
    return `<ul class="space-y-1">${runs.map((r) => `<li><a href="#/studio/run/${r.id}" class="block rounded-lg px-2 py-1.5 hover:bg-slate-800">
      <div class="text-sm truncate">${esc(r.title)}</div><div class="text-[11px] text-slate-500">${esc(App.dt(r.created_at))}</div></a></li>`).join('')}</ul>`;
  }

  // ------------------------------------------------------------------ một tác vụ
  async function renderTask(el, taskId, params) {
    const [cat, runs] = await Promise.all([App.loadTasks(), App.get('/api/skills/runs?task=' + encodeURIComponent(taskId)), App.loadContext()]);
    const task = cat.tasks.find((t) => t.id === taskId);
    if (!task) {
      el.innerHTML = ui.empty('fa-circle-question', 'Không tìm thấy tác vụ', 'Tác vụ này không tồn tại.', '<a href="#/studio" class="btn-primary btn-sm">Về Skill Studio</a>');
      return;
    }
    const prefill = (App.state.prefill && App.state.prefill.task === taskId) ? App.state.prefill.inputs : null;
    App.state.prefill = null;
    const last = prefill || loadLast(taskId) || {};
    const values = { ...last };
    Object.keys(params || {}).forEach((k) => { values[k] = params[k]; });
    task.inputs.forEach((spec) => {
      if (values[spec.name] === undefined && spec.name === 'month') values[spec.name] = App.month();
    });

    el.innerHTML = `
      <div class="space-y-5">
        <a href="#/studio" class="text-sm text-slate-400 hover:text-sky-300"><i class="fa-solid fa-arrow-left"></i> Skill Studio</a>
        <div class="grid lg:grid-cols-5 gap-5">
          <div class="lg:col-span-2 space-y-5">
            <form class="card space-y-4" data-form novalidate>
              <div>
                <div class="flex items-center gap-2 flex-wrap"><span class="chip chip-mute">${esc(task.group)}</span>${task.grounded ? '<span class="chip chip-ok"><i class="fa-brands fa-google"></i> Tìm kiếm có nguồn</span>' : ''}</div>
                <h1 class="text-lg font-bold mt-2">${esc(task.title)}</h1>
                <p class="text-sm text-slate-400 mt-1">${esc(task.description)}</p>
              </div>
              ${task.inputs.map((spec) => ui.inputHtml(spec, values[spec.name])).join('')}
              <button type="submit" class="btn-primary w-full justify-center" data-run><i class="fa-solid fa-wand-magic-sparkles"></i> Chạy tác vụ</button>
              <p class="text-[11px] text-slate-500">Kết quả dựa trên Hồ sơ bối cảnh hiện tại. AI không được bịa số liệu; thông tin chưa có sẽ được liệt kê ở mục "Cần bổ sung".</p>
            </form>
            <div class="card">
              <h2 class="font-bold mb-2 text-sm">Các lần chạy trước</h2>
              <div data-history>${runsList(runs.runs.slice(0, 10))}</div>
            </div>
          </div>
          <div class="lg:col-span-3" data-result>
            ${ui.empty('fa-wand-magic-sparkles', 'Kết quả sẽ hiện ở đây', task.grounded ? 'Tác vụ có tìm kiếm Google nên thường mất 30–90 giây.' : 'Thường mất 10–40 giây tùy độ dài.')}
          </div>
        </div>
      </div>`;

    const form = el.querySelector('[data-form]');
    const resultEl = el.querySelector('[data-result]');
    const run = async () => {
      const btn = form.querySelector('[data-run]');
      const inputs = ui.readFields(form);
      const missingReq = task.inputs.filter((s) => s.required && s.type !== 'checkbox' && (inputs[s.name] === '' || inputs[s.name] === undefined || (Array.isArray(inputs[s.name]) && !inputs[s.name].length)));
      App.$$('[data-field]', form).forEach((f) => f.removeAttribute('aria-invalid'));
      if (missingReq.length) {
        missingReq.forEach((s) => { const f = form.querySelector(`[data-field="${s.name}"]`); if (f) f.setAttribute('aria-invalid', 'true'); });
        App.toast('Điền các ô bắt buộc: ' + missingReq.map((s) => s.label).join(', '), 'warn');
        return;
      }
      saveLast(task.id, inputs);
      App.busy(btn, true, 'Đang chạy…');
      const started = Date.now();
      resultEl.innerHTML = `<div class="card"><div class="flex items-center gap-3"><i class="fa-solid fa-circle-notch fa-spin text-sky-400"></i>
        <div><div class="font-semibold">Đang chạy “${esc(task.title)}”…</div><div class="text-xs text-slate-400" data-elapsed>0 giây</div></div></div>
        <div class="space-y-2 mt-4"><div class="skeleton h-4 w-2/3"></div><div class="skeleton h-4"></div><div class="skeleton h-4 w-5/6"></div><div class="skeleton h-32"></div></div></div>`;
      const timer = setInterval(() => {
        const e = resultEl.querySelector('[data-elapsed]');
        if (e) e.textContent = Math.round((Date.now() - started) / 1000) + ' giây' + (task.grounded ? ' · đang tìm kiếm và đối chiếu nguồn' : '');
      }, 1000);
      try {
        const res = await App.post(`/api/skills/${encodeURIComponent(task.id)}/run`, { inputs });
        clearInterval(timer);
        renderOutcome(resultEl, res, task, run);
        if (res.status === 'ok') {
          const h = await App.get('/api/skills/runs?task=' + encodeURIComponent(task.id));
          el.querySelector('[data-history]').innerHTML = runsList(h.runs.slice(0, 10));
        }
        if (window.innerWidth < 1024) resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } catch (e) {
        clearInterval(timer);
        resultEl.innerHTML = `<div class="card text-rose-300"><i class="fa-solid fa-circle-exclamation"></i> ${esc(e.message)}</div>`;
      } finally {
        App.busy(btn, false);
      }
    };
    form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  }

  function renderOutcome(resultEl, res, task, rerun) {
    resultEl.innerHTML = '';
    if (res.status === 'needs_context') {
      resultEl.appendChild(ui.missingContextForm(res.missing, rerun));
      return;
    }
    if (res.status === 'invalid_input') {
      resultEl.innerHTML = `<div class="card border-amber-500/40"><div class="font-semibold text-amber-300 mb-2"><i class="fa-solid fa-triangle-exclamation"></i> Ô nhập chưa hợp lệ</div>
        <ul class="list-disc ml-5 text-sm space-y-1">${(res.errors || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>`;
      return;
    }
    if (res.status !== 'ok') {
      resultEl.innerHTML = ui.provenance(res.provenance || { status: 'not_generated', error: res.message });
      return;
    }
    renderRun(resultEl, {
      id: res.run_id, task: res.task, output: res.output, provenance: res.provenance, guardrails: res.guardrails,
      notes: res.notes, markdown: res.markdown, inputs: res.inputs, extras: res.extras,
    }, task);
  }

  // ------------------------------------------------------------------ hiển thị kết quả
  function extrasHtml(run) {
    const ex = run.extras || {};
    let html = '';
    if (ex.site_error) html += `<div class="rounded-xl border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-200"><i class="fa-solid fa-globe"></i> Không tải được website đối thủ: ${esc(ex.site_error)}</div>`;
    if (ex.holidays_in_range && ex.holidays_in_range.length) {
      html += `<div class="text-xs text-slate-400">Dịp lễ trong khoảng lịch: ${ex.holidays_in_range.map((h) => `<span class="chip chip-info mr-1 mb-1">${esc(App.dateVi(h.date))} ${esc(h.name)}</span>`).join('')}</div>`;
    }
    if (ex.funnel && ex.funnel.steps) {
      html += `<div class="card-tight"><div class="text-xs font-semibold text-slate-400 mb-2">Phễu khách hàng thực tế (từ CRM)</div>
        <div class="scroll-x"><table class="tbl"><thead><tr><th>Từ → Đến</th><th class="num">Số khách</th><th class="num">Tỉ lệ</th></tr></thead><tbody>
        ${ex.funnel.steps.map((s) => `<tr${ex.funnel.bottleneck && ex.funnel.bottleneck.from === s.from ? ' class="text-amber-300"' : ''}><td>${esc(s.from)} → ${esc(s.to)}</td><td class="num">${s.from_count} → ${s.to_count}</td><td class="num">${s.rate_pct === null ? '—' : App.pct(s.rate_pct)}</td></tr>`).join('')}
        </tbody></table></div>${ex.funnel.note ? `<p class="help">${esc(ex.funnel.note)}</p>` : ''}</div>`;
    }
    return html;
  }

  function actionsFor(run) {
    const out = run.output || {};
    const a = [];
    switch (run.task) {
      case 'copy_studio':
        (out.variants || []).forEach((v, i) => a.push(`<button type="button" class="btn-soft btn-sm" data-act="to-content" data-variant="${i}"><i class="fa-solid fa-box-archive"></i> Lưu phương án ${i + 1}${i === out.recommended ? ' (đề xuất)' : ''} vào kho</button>`));
        if (out.visual_brief) a.push('<button type="button" class="btn-ghost btn-sm" data-act="to-media" data-field="visual_brief"><i class="fa-solid fa-image"></i> Tạo ảnh từ gợi ý</button>');
        break;
      case 'content_package':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-content"><i class="fa-solid fa-box-archive"></i> Lưu vào kho nội dung</button>');
        if (out.image_prompt) a.push('<button type="button" class="btn-ghost btn-sm" data-act="to-media" data-field="image_prompt"><i class="fa-solid fa-image"></i> Tạo ảnh từ prompt</button>');
        break;
      case 'copy_edit':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-content"><i class="fa-solid fa-box-archive"></i> Lưu bản cuối vào kho</button>');
        break;
      case 'content_calendar':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-calendar"><i class="fa-solid fa-calendar-plus"></i> Lưu vào lịch nội dung</button>');
        break;
      case 'budget_plan':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-budget"><i class="fa-solid fa-coins"></i> Lưu vào ngân sách tháng</button>');
        break;
      case 'weekly_loop':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-experiment"><i class="fa-solid fa-flask"></i> Tạo thử nghiệm tuần tới</button>');
        break;
      case 'competitor_discovery':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-competitors"><i class="fa-solid fa-users-viewfinder"></i> Lưu vào danh sách đối thủ</button>');
        break;
      case 'competitor_dossier':
        a.push('<button type="button" class="btn-soft btn-sm" data-act="to-competitors"><i class="fa-solid fa-users-viewfinder"></i> Lưu hồ sơ đối thủ</button>');
        break;
      default:
        break;
    }
    return a.join('');
  }

  function vocPicker(run) {
    const quotes = (run.output && run.output.verbatim_quotes) || [];
    if (run.task !== 'voc_extract' || !quotes.length) return '';
    return `<div class="card-tight" data-voc>
      <div class="text-sm font-semibold mb-2">Đưa câu nguyên văn vào Hồ sơ (mục Ngôn ngữ khách)</div>
      <div class="space-y-1.5 max-h-64 overflow-y-auto">${quotes.map((q, i) => `<label class="flex gap-2 text-sm"><input type="checkbox" class="accent-sky-500 mt-1" value="${i}" checked><span>“${esc(q.quote)}” <span class="text-xs text-slate-500">(dòng ${esc(q.line)})</span></span></label>`).join('')}</div>
      <button type="button" class="btn-soft btn-sm mt-3" data-act="to-context"><i class="fa-solid fa-id-card"></i> Thêm câu đã chọn vào hồ sơ</button></div>`;
  }

  function renderRun(container, run, task) {
    const notes = run.notes || (run.guardrails && run.guardrails.notes) || [];
    container.innerHTML = `
      <div class="card space-y-4">
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex-1 min-w-0">${ui.provenance(run.provenance)}</div>
          <div class="flex gap-1.5">
            <button type="button" class="btn-ghost btn-sm" data-act="copy" title="Sao chép Markdown"><i class="fa-regular fa-copy"></i><span class="hidden sm:inline">Sao chép</span></button>
            <button type="button" class="btn-ghost btn-sm" data-act="download" title="Tải file .md"><i class="fa-solid fa-download"></i><span class="hidden sm:inline">.md</span></button>
            <button type="button" class="btn-ghost btn-sm" data-act="delete" title="Xóa kết quả"><i class="fa-regular fa-trash-can"></i></button>
          </div>
        </div>
        ${ui.guardrails(run.guardrails, notes)}
        ${extrasHtml(run)}
        ${actionsFor(run) ? `<div class="flex flex-wrap gap-2">${actionsFor(run)}</div>` : ''}
        ${vocPicker(run)}
        <article class="md">${App.md(run.markdown)}</article>
      </div>`;

    App.on(container, {
      copy: () => App.copy(run.markdown),
      download: () => App.downloadApi(`/api/skills/runs/${run.id}/markdown`, `marketing-os-${run.task}-${run.id}.md`),
      delete: async () => {
        if (!(await App.confirm('Xóa kết quả này khỏi lịch sử?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del(`/api/skills/runs/${run.id}`);
        App.toast('Đã xóa.');
        App.go('studio', run.task);
      },
      'to-content': async (btn) => {
        App.busy(btn, true, 'Đang lưu…');
        try {
          const body = btn.dataset.variant !== undefined ? { variant: Number(btn.dataset.variant) } : {};
          const r = await App.post(`/api/skills/runs/${run.id}/to-content`, body);
          const blockers = (r.item.guardrails && r.item.guardrails.blockers) || [];
          App.toast(blockers.length ? `Đã lưu bản nháp #${r.item.id}. Còn ${blockers.length} lỗi tuân thủ cần sửa trước khi duyệt.` : `Đã lưu bản nháp #${r.item.id} vào kho nội dung.`, blockers.length ? 'warn' : 'ok');
          btn.outerHTML = `<a href="#/content?open=${r.item.id}" class="btn-soft btn-sm"><i class="fa-solid fa-check"></i> Đã lưu · mở bản nháp #${r.item.id}</a>`;
        } catch (e) {
          App.busy(btn, false);
          throw e;
        }
      },
      'to-calendar': async (btn) => {
        const ok = await App.confirm('Lịch mới sẽ thay các dòng lịch cũ trong cùng khoảng ngày. Tiếp tục?', { okLabel: 'Lưu lịch' });
        if (!ok) return;
        const r = await App.post(`/api/skills/runs/${run.id}/to-calendar`);
        App.toast(`Đã lưu ${r.saved} dòng vào lịch nội dung.`);
        btn.outerHTML = '<a href="#/calendar" class="btn-soft btn-sm"><i class="fa-solid fa-calendar-days"></i> Mở lịch nội dung</a>';
      },
      'to-budget': async (btn) => {
        const r = await App.post(`/api/skills/runs/${run.id}/to-budget`);
        App.toast(`Đã thêm ${r.saved} hạng mục vào ngân sách tháng ${r.month}.`);
        btn.outerHTML = `<a href="#/growth/budget?month=${esc(r.month)}" class="btn-soft btn-sm"><i class="fa-solid fa-coins"></i> Mở ngân sách ${esc(r.month)}</a>`;
      },
      'to-experiment': async (btn) => {
        await App.post(`/api/skills/runs/${run.id}/to-experiment`);
        App.toast('Đã tạo thử nghiệm (trạng thái: Kế hoạch).');
        btn.outerHTML = '<a href="#/growth/experiments" class="btn-soft btn-sm"><i class="fa-solid fa-flask"></i> Mở danh sách thử nghiệm</a>';
      },
      'to-competitors': async (btn) => {
        const r = await App.post(`/api/skills/runs/${run.id}/to-competitors`);
        App.toast(r.saved !== undefined ? `Đã lưu ${r.saved} đối thủ.` : 'Đã lưu hồ sơ đối thủ.');
        btn.outerHTML = '<a href="#/research" class="btn-soft btn-sm"><i class="fa-solid fa-users-viewfinder"></i> Mở danh sách đối thủ</a>';
      },
      'to-context': async (btn) => {
        const idx = App.$$('[data-voc] input:checked', container).map((c) => Number(c.value));
        if (!idx.length) { App.toast('Chọn ít nhất một câu.', 'warn'); return; }
        const r = await App.post(`/api/skills/runs/${run.id}/to-context`, { indexes: idx });
        await App.loadContext(true);
        App.toast(r.added ? `Đã thêm ${r.added} câu vào hồ sơ.` : 'Các câu này đã có trong hồ sơ.');
        btn.disabled = true;
      },
      'to-media': (btn) => {
        const prompt = (run.output || {})[btn.dataset.field] || '';
        App.state.mediaPrompt = String(prompt);
        App.go('media');
      },
    });
  }

  async function renderSavedRun(el, runId) {
    const [run, cat] = await Promise.all([App.get('/api/skills/runs/' + encodeURIComponent(runId)), App.loadTasks()]);
    const task = cat.tasks.find((t) => t.id === run.task);
    const inputRows = Object.entries(run.inputs || {}).filter(([, v]) => v !== '' && v !== null && !(Array.isArray(v) && !v.length));
    el.innerHTML = `
      <div class="space-y-5">
        <a href="#/studio/${esc(run.task)}" class="text-sm text-slate-400 hover:text-sky-300"><i class="fa-solid fa-arrow-left"></i> ${esc(task ? task.title : run.task)}</a>
        <div class="card">
          <h1 class="text-lg font-bold">${esc(run.title)}</h1>
          <p class="text-xs text-slate-400 mt-1">Tạo lúc ${esc(App.dt(run.created_at))}</p>
          ${inputRows.length ? `<details class="mt-3"><summary class="text-sm text-sky-300 cursor-pointer">Đầu vào đã dùng</summary>
            <dl class="mt-2 grid sm:grid-cols-2 gap-2 text-sm">${inputRows.map(([k, v]) => {
              const spec = task && task.inputs.find((s) => s.name === k);
              return `<div class="card-tight"><dt class="text-xs text-slate-400">${esc(spec ? spec.label : k)}</dt><dd class="whitespace-pre-wrap break-words">${esc(Array.isArray(v) ? v.join(', ') : typeof v === 'boolean' ? (v ? 'Có' : 'Không') : v)}</dd></div>`;
            }).join('')}</dl></details>` : ''}
          ${task ? '<button type="button" class="btn-ghost btn-sm mt-3" data-act="rerun"><i class="fa-solid fa-rotate"></i> Chạy lại với đầu vào này</button>' : ''}
        </div>
        <div data-result></div>
      </div>`;
    renderRun(el.querySelector('[data-result]'), { ...run, notes: (run.guardrails || {}).notes }, task);
    App.on(el.querySelector('.card'), {
      rerun: () => { App.state.prefill = { task: run.task, inputs: run.inputs }; App.go('studio', run.task); },
    });
  }

  App.views.studio = {
    render: async (el, args, params) => {
      if (!args.length) return renderCatalog(el);
      if (args[0] === 'run' && args[1]) return renderSavedRun(el, args[1]);
      return renderTask(el, args[0], params);
    },
  };
})();
