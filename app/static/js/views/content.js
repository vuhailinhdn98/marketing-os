/* Kho nội dung (quy trình 7 bước có cổng duyệt) + Lịch nội dung (ngày lễ dương/âm lịch). */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;

  const CHANNELS = ['Facebook', 'TikTok', 'Zalo OA', 'Instagram', 'YouTube', 'Email', 'SMS', 'Website/Blog', 'Landing page', 'Google Business Profile', 'Quảng cáo Facebook', 'Quảng cáo Google'];
  const FUNNEL = ['', 'Nhận biết', 'Cân nhắc', 'Quyết định', 'Sử dụng/Quay lại'];
  const STATUS_TONE = { ideas: 'chip-mute', draft: 'chip-mute', review: 'chip-warn', approved: 'chip-ok', scheduled: 'chip-info', published: 'chip-ok', measured: 'chip-info' };
  const INTENT = { findable: 'Tìm được (SEO)', shareable: 'Chia sẻ được', experiment: 'Thử nghiệm' };

  const matchOption = (options, value) => {
    const v = String(value || '').toLowerCase();
    if (!v) return '';
    return options.find((o) => o.toLowerCase() === v) || options.find((o) => o.toLowerCase().includes(v) || v.includes(o.toLowerCase().replace(/^(bài|tin|kịch bản)\s+/, ''))) || '';
  };

  const fullText = (item) => [item.hook, item.body, item.cta].filter((x) => x && String(x).trim()).join('\n\n');

  // ------------------------------------------------------------------ KHO NỘI DUNG
  async function renderContent(el, args, params) {
    const data = await App.get('/api/content');
    const statuses = data.statuses;
    let items = data.items;
    let query = '';

    el.innerHTML = `
      <div class="space-y-4">
        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center gap-3">
            <div class="flex-1">
              <h1 class="text-lg font-bold">Kho nội dung</h1>
              <p class="text-sm text-slate-400 mt-1">Ý tưởng → Nháp → Chờ duyệt → Đã duyệt → Lên lịch → Đã đăng → Đã đo. Nội dung còn lỗi tuân thủ không thể qua bước duyệt.</p>
            </div>
            <div class="flex gap-2">
              <input class="inp md:w-56" data-search placeholder="Tìm chủ đề, kênh…" aria-label="Tìm nội dung">
              <button type="button" class="btn-primary shrink-0" data-act="new"><i class="fa-solid fa-plus"></i><span class="hidden sm:inline">Thêm</span></button>
            </div>
          </div>
        </div>
        <div data-board></div>
      </div>`;

    const board = el.querySelector('[data-board]');
    const draw = () => {
      const list = items.filter((i) => !query || `${i.topic} ${i.channel} ${i.body} ${i.pillar}`.toLowerCase().includes(query));
      if (!items.length) {
        board.innerHTML = ui.empty('fa-pen-nib', 'Chưa có nội dung', 'Tạo bài từ Skill Studio (Viết quảng cáo/bài, Gói nội dung đa kênh) hoặc thêm tay.',
          '<a href="#/studio/copy_studio" class="btn-primary btn-sm"><i class="fa-solid fa-wand-magic-sparkles"></i> Viết bằng AI</a><button type="button" class="btn-ghost btn-sm" data-act="new">Thêm tay</button>');
        return;
      }
      board.innerHTML = `<div class="kanban">${statuses.map((s) => {
        const col = list.filter((i) => i.status === s.key);
        return `<div class="kcol"><div class="flex items-center justify-between mb-2 px-1"><span class="text-sm font-bold">${esc(s.label)}</span><span class="chip ${STATUS_TONE[s.key]}">${col.length}</span></div>
          <div class="space-y-2">${col.map(cardHtml).join('') || '<p class="text-xs text-slate-600 px-1">Trống</p>'}</div></div>`;
      }).join('')}</div>`;
    };
    const cardHtml = (i) => {
      const b = (i.guardrails && i.guardrails.blockers) || [];
      const w = (i.guardrails && i.guardrails.warnings) || [];
      return `<div class="kcard" role="button" tabindex="0" data-act="open" data-id="${i.id}">
        <div class="flex items-center gap-1.5 flex-wrap mb-1"><span class="chip chip-info">${esc(i.channel)}</span>
        ${b.length ? `<span class="chip chip-bad" title="Lỗi tuân thủ"><i class="fa-solid fa-hand"></i> ${b.length}</span>` : ''}
        ${w.length ? `<span class="chip chip-warn" title="Cần xem lại"><i class="fa-solid fa-triangle-exclamation"></i> ${w.length}</span>` : ''}
        ${i.provenance && i.provenance.model ? '<span class="chip chip-mute" title="Tạo bằng AI"><i class="fa-solid fa-robot"></i></span>' : ''}</div>
        <div class="text-sm font-semibold line-clamp-2">${esc(i.topic)}</div>
        ${i.publish_date ? `<div class="text-[11px] text-slate-400 mt-1"><i class="fa-regular fa-calendar"></i> ${esc(App.dateVi(i.publish_date))}</div>` : ''}
      </div>`;
    };
    draw();

    const reload = async () => { items = (await App.get('/api/content')).items; draw(); };
    el.querySelector('[data-search]').addEventListener('input', (e) => { query = e.target.value.trim().toLowerCase(); draw(); });
    board.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches('.kcard')) e.target.click(); });
    App.on(el, {
      new: () => openEditor(null, statuses, reload),
      open: (card) => openEditor(Number(card.dataset.id), statuses, reload),
    });
    if (params && params.open) openEditor(Number(params.open), statuses, reload);
  }

  function editorFields(item) {
    const v = item || {};
    const ch = v.channel || 'Facebook';
    const chOptions = CHANNELS.includes(ch) ? CHANNELS : [ch, ...CHANNELS];
    return `
      <div class="grid sm:grid-cols-3 gap-3">
        <div><label class="lbl" for="ce-channel">Kênh</label><select id="ce-channel" class="sel" data-f="channel">${chOptions.map((c) => `<option ${c === ch ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select></div>
        <div><label class="lbl" for="ce-date">Ngày đăng</label><input id="ce-date" type="date" class="inp" data-f="publish_date" value="${esc(v.publish_date || '')}"></div>
        <div><label class="lbl" for="ce-funnel">Giai đoạn phễu</label><select id="ce-funnel" class="sel" data-f="funnel_stage">${FUNNEL.map((f) => `<option value="${esc(f)}" ${f === (v.funnel_stage || '') ? 'selected' : ''}>${esc(f || '—')}</option>`).join('')}</select></div>
      </div>
      <div><label class="lbl" for="ce-topic">Chủ đề / tiêu đề <span class="text-rose-400">*</span></label><input id="ce-topic" class="inp" data-f="topic" maxlength="300" value="${esc(v.topic || '')}"></div>
      <div><label class="lbl" for="ce-hook">Hook (câu mở đầu)</label><input id="ce-hook" class="inp" data-f="hook" value="${esc(v.hook || '')}"></div>
      <div><label class="lbl" for="ce-body">Nội dung</label><textarea id="ce-body" class="txt" rows="9" data-f="body">${esc(v.body || '')}</textarea></div>
      <div><label class="lbl" for="ce-cta">Kêu gọi hành động (CTA)</label><input id="ce-cta" class="inp" data-f="cta" value="${esc(v.cta || '')}"></div>
      <details ${v.video_script || v.image_prompt ? 'open' : ''}><summary class="text-sm text-sky-300 cursor-pointer">Kịch bản video, prompt ảnh, trụ cột</summary>
        <div class="space-y-3 mt-3">
          <div><label class="lbl" for="ce-video">Kịch bản video</label><textarea id="ce-video" class="txt" rows="5" data-f="video_script">${esc(v.video_script || '')}</textarea></div>
          <div><label class="lbl" for="ce-img">Prompt ảnh</label><textarea id="ce-img" class="txt" rows="3" data-f="image_prompt">${esc(v.image_prompt || '')}</textarea></div>
          <div class="grid sm:grid-cols-2 gap-3">
            <div><label class="lbl" for="ce-pillar">Trụ cột nội dung</label><input id="ce-pillar" class="inp" data-f="pillar" value="${esc(v.pillar || '')}"></div>
            <div><label class="lbl" for="ce-format">Định dạng</label><input id="ce-format" class="inp" data-f="format" value="${esc(v.format || '')}" placeholder="Ảnh đơn, carousel, video ngắn…"></div>
          </div>
        </div></details>
      <div><label class="lbl" for="ce-scarcity">Bằng chứng giới hạn có thật (nếu bài nói “chỉ còn”, “hôm nay cuối”…)</label><input id="ce-scarcity" class="inp" data-f="scarcity_evidence" placeholder="vd: Kho còn 20 hộp theo phiếu kiểm kho 12/11"><p class="help">Không lưu vào bài; chỉ dùng để cổng tuân thủ G03 không chặn khan hiếm có thật.</p></div>`;
  }

  const readEditor = (root) => {
    const out = {};
    App.$$('[data-f]', root).forEach((f) => { out[f.dataset.f] = f.value; });
    return out;
  };

  async function openEditor(id, statuses, onChange) {
    let item = null;
    let checklist = [];
    if (id) {
      try {
        const r = await App.get('/api/content/' + id);
        item = r.item;
        checklist = r.promotion_checklist || [];
      } catch (e) {
        App.toast(e.message, 'bad');
        return;
      }
    }
    const body = document.createElement('div');
    const paint = () => {
      const variants = (item && item.variants) || [];
      body.innerHTML = `
        <div class="grid lg:grid-cols-5 gap-5">
          <div class="lg:col-span-3 space-y-3" data-editor>${editorFields(item)}</div>
          <div class="lg:col-span-2 space-y-4">
            ${item ? `<div class="card-tight space-y-2">
              <div class="flex items-center justify-between"><span class="text-xs text-slate-400">Trạng thái</span><span class="chip ${STATUS_TONE[item.status]}">${esc(item.status_label)}</span></div>
              <select class="sel" data-status aria-label="Chuyển trạng thái">${statuses.map((s) => `<option value="${s.key}" ${s.key === item.status ? 'selected' : ''}>${esc(s.label)}</option>`).join('')}</select>
              <button type="button" class="btn-ghost btn-sm w-full justify-center" data-act="status"><i class="fa-solid fa-arrow-right-arrow-left"></i> Chuyển trạng thái</button>
              ${['approved', 'scheduled', 'published'].includes(item.status) ? '<button type="button" class="btn-soft btn-sm w-full justify-center" data-act="publish"><i class="fa-solid fa-paper-plane"></i> Xuất bản qua webhook</button>' : ''}
              ${item.webhook_published_at ? `<p class="text-[11px] text-emerald-300">Đã gửi webhook lúc ${esc(App.dt(item.webhook_published_at))}</p>` : ''}
            </div>` : ''}
            <div data-guard>${item ? ui.guardrails(item.guardrails) : '<p class="text-xs text-slate-400">Cổng tuân thủ sẽ chạy khi bạn lưu.</p>'}</div>
            ${item ? `<div>${ui.provenance(item.provenance)}</div>` : ''}
            ${variants.length > 1 ? `<div class="card-tight"><div class="text-xs font-semibold text-slate-400 mb-2">Phương án khác từ AI</div>
              ${variants.map((v, i) => `<div class="border-t border-slate-800 pt-2 mt-2 first:border-0 first:pt-0 first:mt-0"><div class="text-sm font-semibold">${i + 1}. ${esc(v.headline || v.hook || '')}</div>
              <div class="text-xs text-slate-400 line-clamp-2">${esc(v.body || '')}</div><button type="button" class="text-xs text-sky-400 mt-1" data-act="use-variant" data-i="${i}">Dùng phương án này</button></div>`).join('')}</div>` : ''}
            ${item && ['published', 'measured', 'scheduled', 'approved'].includes(item.status) && checklist.length ? `<details class="card-tight" ${item.status === 'published' ? 'open' : ''}><summary class="text-sm font-semibold cursor-pointer">Checklist quảng bá sau khi đăng</summary>
              <ul class="mt-2 space-y-1.5 text-sm">${checklist.map((c, i) => `<li><label class="flex gap-2"><input type="checkbox" class="accent-sky-500 mt-1" id="pc${i}"><span>${esc(c)}</span></label></li>`).join('')}</ul></details>` : ''}
          </div>
        </div>`;
    };
    paint();

    const actions = [];
    if (item) {
      actions.push({ label: '<i class="fa-regular fa-trash-can"></i> Xóa', cls: 'btn-danger', onClick: async ({ close }) => {
        if (!(await App.confirm('Xóa nội dung này?', { danger: true, okLabel: 'Xóa' }))) return true;
        await App.del('/api/content/' + item.id);
        App.toast('Đã xóa.');
        close();
        onChange();
        return true;
      } });
      actions.push({ label: '<i class="fa-regular fa-copy"></i> Sao chép bài', onClick: () => { App.copy(fullText(readEditor(body))); return true; } });
      actions.push({ label: '<i class="fa-solid fa-wand-magic-sparkles"></i> Biên tập bằng AI', onClick: ({ close }) => {
        const v = readEditor(body);
        App.state.prefill = { task: 'copy_edit', inputs: { text: fullText(v), channel: '' } };
        close();
        App.go('studio', 'copy_edit');
        return true;
      } });
    }
    actions.push({ label: '<i class="fa-solid fa-floppy-disk"></i> ' + (item ? 'Lưu thay đổi' : 'Tạo bản nháp'), cls: 'btn-primary', onClick: async () => {
      const v = readEditor(body);
      if (!v.topic.trim()) { App.toast('Nhập chủ đề.', 'warn'); return true; }
      const wasGated = item && ['approved', 'scheduled'].includes(item.status);
      const r = item ? await App.put('/api/content/' + item.id, v) : await App.post('/api/content', { ...v, status: 'draft' });
      item = r.item;
      const g = await App.get('/api/content/' + item.id);
      checklist = g.promotion_checklist || [];
      paint();
      App.toast(wasGated && item.status === 'review' ? 'Đã lưu. Bài đã duyệt bị sửa nên quay về Chờ duyệt.' : 'Đã lưu.', wasGated && item.status === 'review' ? 'warn' : 'ok');
      onChange();
      return true;
    } });

    App.modal({ title: item ? `Nội dung #${item.id}` : 'Nội dung mới', body, actions, wide: true });

    App.on(body, {
      status: async (btn) => {
        const to = body.querySelector('[data-status]').value;
        if (to === item.status) return;
        App.busy(btn, true);
        try {
          item = (await App.patch(`/api/content/${item.id}/status`, { status: to })).item;
          const g = await App.get('/api/content/' + item.id);
          checklist = g.promotion_checklist || [];
          paint();
          App.toast('Đã chuyển sang “' + item.status_label + '”.');
          onChange();
        } catch (e) {
          App.busy(btn, false);
          throw e;
        }
      },
      publish: async (btn) => {
        if (!(await App.confirm('Gửi bài này tới webhook xuất bản (Zapier/Make/n8n) đã cấu hình trong Cài đặt?', { okLabel: 'Gửi' }))) return;
        App.busy(btn, true, 'Đang gửi…');
        try {
          const r = await App.post(`/api/content/${item.id}/publish`);
          item = r.item;
          App.toast(r.delivered ? 'Webhook đã nhận bài. Trạng thái: Đã đăng.' : 'Webhook không nhận: ' + r.message, r.delivered ? 'ok' : 'bad');
          paint();
          onChange();
        } finally {
          App.busy(btn, false);
        }
      },
      'use-variant': (btn) => {
        const v = item.variants[Number(btn.dataset.i)] || {};
        const set = (f, val) => { const x = body.querySelector(`[data-f="${f}"]`); if (x && val !== undefined) x.value = val; };
        set('topic', v.headline || item.topic);
        set('hook', v.hook);
        set('body', v.body);
        set('cta', v.cta);
        App.toast('Đã điền phương án vào ô soạn. Bấm “Lưu thay đổi” để lưu.', 'info');
      },
    });
  }

  // ------------------------------------------------------------------ LỊCH NỘI DUNG
  const addDays = (iso, n) => {
    const d = new Date(iso + 'T00:00:00');
    d.setDate(d.getDate() + n);
    const pad = (x) => String(x).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  };

  async function renderCalendar(el, args, params) {
    const start = /^\d{4}-\d{2}-\d{2}$/.test(params.start || '') ? params.start : addDays(App.today(), -3);
    const days = [14, 31, 60].includes(Number(params.days)) ? Number(params.days) : 31;
    const data = await App.get(`/api/calendar?start=${start}&days=${days}`);
    const end = addDays(start, days - 1);
    const byDate = {};
    data.items.forEach((r) => { (byDate[r.plan_date] = byDate[r.plan_date] || []).push(r); });
    const holByDate = {};
    data.holidays.forEach((h) => { (holByDate[h.date] = holByDate[h.date] || []).push(h); });
    const dates = Array.from(new Set([...Object.keys(byDate), ...Object.keys(holByDate)])).sort();
    const link = (s, d) => `#/calendar?start=${s}&days=${d}`;

    el.innerHTML = `
      <div class="space-y-4">
        <div class="card">
          <div class="flex flex-col lg:flex-row lg:items-center gap-3">
            <div class="flex-1">
              <h1 class="text-lg font-bold">Lịch nội dung</h1>
              <p class="text-sm text-slate-400 mt-1">${esc(App.dateVi(start))} – ${esc(App.dateVi(end))} · ${data.items.length} bài · ngày lễ dương lịch, âm lịch và mùa sale.</p>
            </div>
            <div class="flex flex-wrap gap-2 items-center">
              <a class="btn-ghost btn-sm" href="${link(addDays(start, -days), days)}" aria-label="Khoảng trước"><i class="fa-solid fa-chevron-left"></i></a>
              <input type="date" class="inp w-40" value="${esc(start)}" data-start aria-label="Từ ngày">
              <select class="sel w-28" data-days aria-label="Số ngày">${[14, 31, 60].map((d) => `<option value="${d}" ${d === days ? 'selected' : ''}>${d} ngày</option>`).join('')}</select>
              <a class="btn-ghost btn-sm" href="${link(addDays(start, days), days)}" aria-label="Khoảng sau"><i class="fa-solid fa-chevron-right"></i></a>
              <a class="btn-primary btn-sm" href="#/studio/content_calendar"><i class="fa-solid fa-wand-magic-sparkles"></i> Lập lịch bằng AI</a>
            </div>
          </div>
          ${data.legacy_rows ? `<div class="mt-3 rounded-xl border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-200 flex flex-col sm:flex-row sm:items-center gap-2">
            <span class="flex-1"><i class="fa-solid fa-clock-rotate-left"></i> Có ${data.legacy_rows} dòng lịch từ phiên bản cũ (không có ngày cụ thể, có thể chứa nội dung tự chế).</span>
            <button type="button" class="btn-danger btn-sm" data-act="clear-legacy">Xóa lịch cũ</button></div>` : ''}
        </div>
        ${dates.length ? `<div class="space-y-3">${dates.map((d) => dayHtml(d, byDate[d] || [], holByDate[d] || [])).join('')}</div>`
          : ui.empty('fa-calendar-days', 'Chưa có lịch trong khoảng này', 'Dùng tác vụ “Lịch nội dung” trong Skill Studio rồi bấm “Lưu vào lịch nội dung”.', '<a href="#/studio/content_calendar" class="btn-primary btn-sm">Lập lịch bằng AI</a>')}
      </div>`;

    const go = () => { location.hash = link(el.querySelector('[data-start]').value || start, el.querySelector('[data-days]').value); };
    el.querySelector('[data-start]').addEventListener('change', go);
    el.querySelector('[data-days]').addEventListener('change', go);
    const rowById = (id) => data.items.find((r) => String(r.id) === String(id));

    App.on(el, {
      'clear-legacy': async () => {
        if (!(await App.confirm(`Xóa ${data.legacy_rows} dòng lịch cũ không có ngày?`, { danger: true, okLabel: 'Xóa' }))) return;
        const r = await App.del('/api/calendar/legacy');
        App.toast(`Đã xóa ${r.deleted} dòng.`);
        App.render();
      },
      'make-post': async (btn) => {
        const r = rowById(btn.dataset.id);
        const res = await App.post('/api/content', {
          channel: r.channel || 'Facebook', topic: r.topic || 'Bài theo lịch', hook: r.hook, cta: r.cta, pillar: r.pillar,
          funnel_stage: r.funnel_stage, format: r.format, publish_date: r.plan_date, status: 'ideas',
        });
        App.toast(`Đã tạo ý tưởng #${res.item.id} trong kho nội dung.`);
        btn.outerHTML = `<a href="#/content?open=${res.item.id}" class="btn-soft btn-sm"><i class="fa-solid fa-check"></i> Mở #${res.item.id}</a>`;
      },
      'write-ai': (btn) => {
        const r = rowById(btn.dataset.id);
        App.state.prefill = { task: 'content_package', inputs: { topic: [r.topic, r.hook ? 'Hook gợi ý: ' + r.hook : '', r.cta ? 'CTA: ' + r.cta : ''].filter(Boolean).join('\n'), channel: matchOption(['Facebook', 'TikTok', 'Zalo OA', 'Instagram', 'YouTube Shorts'], r.channel) || 'Facebook' } };
        App.go('studio', 'content_package');
      },
      'del-row': async (btn) => {
        if (!(await App.confirm('Xóa dòng lịch này?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del('/api/calendar/' + btn.dataset.id);
        btn.closest('[data-row]').remove();
        App.toast('Đã xóa.');
      },
    });
  }

  function dayHtml(d, rows, hols) {
    const isToday = d === App.today();
    return `<div class="card-tight ${isToday ? 'border-sky-500/60' : ''}">
      <div class="flex items-center gap-3 flex-wrap">
        <div class="w-14 text-center rounded-lg ${isToday ? 'bg-sky-500/20 text-sky-200' : 'bg-slate-800'} py-1 shrink-0"><div class="text-[10px]">${App.weekday(d)}</div><div class="font-bold text-sm">${esc(App.dateVi(d).slice(0, 5))}</div></div>
        <div class="flex flex-wrap gap-1.5 flex-1">${hols.map((h) => `<span class="chip chip-warn"><i class="fa-solid fa-gift"></i> ${esc(h.name)}</span>`).join('')}${!rows.length ? '<span class="text-xs text-slate-500">Chưa có bài</span>' : ''}</div>
      </div>
      ${rows.length ? `<div class="mt-3 space-y-2">${rows.map((r) => `<div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3" data-row>
        <div class="flex flex-wrap items-center gap-1.5 mb-1">
          <span class="chip chip-info">${esc(r.channel || '—')}</span>
          ${r.funnel_stage ? `<span class="chip chip-mute">${esc(r.funnel_stage)}</span>` : ''}
          ${r.pillar ? `<span class="chip chip-mute">${esc(r.pillar)}</span>` : ''}
          ${r.intent ? `<span class="chip chip-mute">${esc(INTENT[r.intent] || r.intent)}</span>` : ''}
          ${r.format ? `<span class="text-[11px] text-slate-400">${esc(r.format)}</span>` : ''}
        </div>
        <div class="text-sm font-semibold">${esc(r.topic)}</div>
        ${r.hook ? `<div class="text-xs text-slate-300 mt-1"><span class="text-slate-500">Hook:</span> ${esc(r.hook)}</div>` : ''}
        ${r.cta ? `<div class="text-xs text-slate-300"><span class="text-slate-500">CTA:</span> ${esc(r.cta)}</div>` : ''}
        ${r.metric ? `<div class="text-xs text-slate-400"><span class="text-slate-500">Đo bằng:</span> ${esc(r.metric)}</div>` : ''}
        <div class="flex flex-wrap gap-2 mt-2">
          <button type="button" class="btn-soft btn-sm" data-act="write-ai" data-id="${r.id}"><i class="fa-solid fa-wand-magic-sparkles"></i> Viết bằng AI</button>
          <button type="button" class="btn-ghost btn-sm" data-act="make-post" data-id="${r.id}"><i class="fa-solid fa-plus"></i> Đưa vào kho</button>
          <button type="button" class="btn-ghost btn-sm ml-auto" data-act="del-row" data-id="${r.id}" aria-label="Xóa dòng"><i class="fa-regular fa-trash-can"></i></button>
        </div></div>`).join('')}</div>` : ''}
    </div>`;
  }

  App.views.content = { render: renderContent };
  App.views.calendar = { render: renderCalendar };
})();
