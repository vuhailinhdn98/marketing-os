/* Thành phần giao diện dùng chung: nguồn gốc kết quả, cổng tuân thủ, bài học, ô nhập, hồ sơ thiếu. */
(function () {
  'use strict';
  const App = window.App;
  const esc = App.esc;
  const ui = (App.ui = {});

  ui.empty = (icon, title, text, action = '') => `
    <div class="card text-center py-10">
      <div class="w-12 h-12 rounded-2xl bg-slate-800 mx-auto flex items-center justify-center text-slate-300 text-lg mb-3"><i class="fa-solid ${icon}"></i></div>
      <h3 class="font-semibold">${esc(title)}</h3>
      <p class="text-sm text-slate-400 mt-1 max-w-md mx-auto">${esc(text)}</p>
      ${action ? `<div class="mt-4 flex justify-center gap-2 flex-wrap">${action}</div>` : ''}
    </div>`;

  ui.kpi = (label, value, sub = '', tone = '') => `
    <div class="card-tight">
      <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">${esc(label)}</div>
      <div class="text-xl font-bold mt-1 ${tone}">${value}</div>
      ${sub ? `<div class="text-[11px] text-slate-500 mt-0.5">${sub}</div>` : ''}
    </div>`;

  // Chỉ tạo liên kết cho http/https; địa chỉ khác hiển thị dạng chữ
  ui.safeLink = (url, label, cls = 'text-sky-400 hover:underline break-all') => (/^https?:\/\//i.test(String(url || ''))
    ? `<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`
    : `<span class="break-all">${esc(label)}</span>`);

  ui.sources = (sources) => {
    if (!sources || !sources.length) return '';
    return `<div class="mt-4"><div class="text-xs font-semibold text-slate-400 mb-1">Nguồn (${sources.length})</div>
      <ol class="text-xs space-y-1 list-decimal ml-5">${sources.map((s) => `<li>${ui.safeLink(s.url, s.title || s.url)}</li>`).join('')}</ol></div>`;
  };

  ui.provenance = (prov) => {
    if (!prov) return '';
    if (prov.status === 'not_generated') {
      const hint = ['no_key', 'invalid_key', 'forbidden'].includes(prov.error_code)
        ? '<a href="#/settings" class="underline">Mở Cài đặt AI</a>'
        : (prov.error_code === 'quota' ? 'Thử lại sau hoặc đổi model trong Cài đặt.' : 'Thử lại sau ít phút.');
      return `<div class="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm">
        <div class="font-semibold text-rose-300"><i class="fa-solid fa-circle-xmark"></i> Chưa tạo được</div>
        <div class="text-rose-200/90 mt-1">${esc(prov.error || 'AI không trả kết quả.')}</div>
        <div class="text-xs text-slate-400 mt-2">Hệ thống không thay bằng nội dung mẫu để tránh số liệu tự chế. ${hint}</div>
      </div>`;
    }
    if (prov.status === 'manual') return '<span class="chip chip-mute"><i class="fa-solid fa-user-pen"></i> Nhập tay</span>';
    const chips = [];
    if (prov.model) chips.push(`<span class="chip chip-info"><i class="fa-solid fa-microchip"></i> ${esc(prov.model)}</span>`);
    chips.push(prov.grounded
      ? `<span class="chip chip-ok"><i class="fa-solid fa-magnifying-glass"></i> Có tìm kiếm Google · ${(prov.sources || []).length} nguồn</span>`
      : '<span class="chip chip-mute"><i class="fa-solid fa-ban"></i> Không tìm kiếm web</span>');
    if (prov.context_version) chips.push(`<span class="chip chip-mute">Hồ sơ v${esc(prov.context_version)}</span>`);
    if (prov.generated_at) chips.push(`<span class="chip chip-mute">${esc(prov.generated_at)}</span>`);
    if (prov.key_source === 'server') chips.push('<span class="chip chip-warn">Key máy chủ</span>');
    return `<div class="flex flex-wrap gap-1.5">${chips.join('')}</div>`;
  };

  ui.guardrails = (guard, notes) => {
    guard = guard || {};
    const blockers = guard.blockers || [];
    const warnings = guard.warnings || [];
    notes = notes || guard.notes || [];
    if (!blockers.length && !warnings.length && !notes.length) {
      return '<div class="rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-4 py-2.5 text-sm text-emerald-300"><i class="fa-solid fa-shield-halved"></i> Qua cổng tuân thủ G01–G11: không phát hiện vấn đề.</div>';
    }
    const item = (x, tone) => `<li class="flex gap-2"><span class="chip ${tone} shrink-0">${esc(x.code)}</span><span>${esc(x.message)}${x.excerpt ? `<span class="block text-xs text-slate-400 mt-0.5">“${esc(x.excerpt)}”</span>` : ''}</span></li>`;
    let html = '<div class="rounded-xl border border-slate-700 bg-slate-900/60 p-4 space-y-3 text-sm">';
    if (blockers.length) html += `<div><div class="font-semibold text-rose-300 mb-1.5"><i class="fa-solid fa-hand"></i> Phải sửa trước khi duyệt/đăng (${blockers.length})</div><ul class="space-y-1.5">${blockers.map((b) => item(b, 'chip-bad')).join('')}</ul></div>`;
    if (warnings.length) html += `<div><div class="font-semibold text-amber-300 mb-1.5"><i class="fa-solid fa-triangle-exclamation"></i> Nên xem lại (${warnings.length})</div><ul class="space-y-1.5">${warnings.map((w) => item(w, 'chip-warn')).join('')}</ul></div>`;
    if (notes.length) html += `<div><div class="font-semibold text-sky-300 mb-1.5"><i class="fa-solid fa-calculator"></i> Hệ thống đã kiểm/tính lại</div><ul class="space-y-1.5">${notes.map((n) => item(n, 'chip-info')).join('')}</ul></div>`;
    return html + '</div>';
  };

  ui.lessons = (lessons) => {
    if (!lessons || !lessons.length) return '';
    return `<div class="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 text-sm">
      <div class="font-semibold text-indigo-300 mb-1.5"><i class="fa-solid fa-graduation-cap"></i> Bài học</div>
      <ul class="space-y-1 list-disc ml-5 text-slate-300">${lessons.map((l) => `<li>${esc(l)}</li>`).join('')}</ul></div>`;
  };

  // ---------------------------------------------------------------- chuyển đổi kiểu dữ liệu hồ sơ
  const SEP = ' | ';
  ui.toText = (kind, value) => {
    if (value === null || value === undefined) return '';
    switch (kind) {
      case 'list': return (value || []).join('\n');
      case 'price_list': return (value || []).map((x) => `${x.name || ''}${SEP}${x.price_vnd ?? ''}`).join('\n');
      case 'pair_list': return (value || []).map((x) => `${x.objection || ''}${SEP}${x.answer || ''}`).join('\n');
      case 'quote_list': return (value || []).map((x) => `${x.quote || ''}${SEP}${x.source || ''}`).join('\n');
      case 'proof_list': return (value || []).map((x) => [x.type || '', x.text || '', x.source || '', x.permission ? 'có' : 'không'].join(SEP)).join('\n');
      case 'faq_list': return (value || []).map((x) => `${x.q || ''}${SEP}${x.a || ''}`).join('\n');
      case 'number': return value === 0 || value ? String(value) : '';
      default: return String(value);
    }
  };

  const splitLine = (line) => line.split('|').map((s) => s.trim());
  ui.fromText = (kind, text, prev) => {
    const lines = String(text || '').split('\n').map((l) => l.trim()).filter(Boolean);
    const prevQuotes = {};
    (Array.isArray(prev) ? prev : []).forEach((x) => { if (x && x.quote) prevQuotes[String(x.quote).trim().toLowerCase()] = x; });
    switch (kind) {
      case 'list': return lines;
      case 'price_list': return lines.map((l) => { const [name, price] = splitLine(l); return { name, price_vnd: Number(String(price || '').replace(/[^\d]/g, '')) || 0 }; });
      case 'pair_list': return lines.map((l) => { const [objection, answer] = splitLine(l); return { objection, answer: answer || '' }; });
      case 'quote_list': return lines.map((l) => {
        const [quote, source] = splitLine(l);
        const before = prevQuotes[String(quote).toLowerCase()];
        return { quote, source: source || '', date: (before && before.date) || App.today() };
      });
      case 'proof_list': return lines.map((l, i) => { const [type, text, source, perm] = splitLine(l); return { id: 'P' + (i + 1), type: type || 'khác', text: text || '', source: source || '', permission: /^(có|co|yes|true|x|đồng ý)$/i.test(perm || '') }; });
      case 'faq_list': return lines.map((l) => { const [q, a] = splitLine(l); return { q, a: a || '' }; });
      case 'number': return text === '' ? null : String(text).trim();
      default: return String(text || '').trim();
    }
  };

  // ---------------------------------------------------------------- ô nhập
  let uid = 0;
  ui.inputHtml = (spec, value) => {
    const id = 'f' + (++uid);
    const req = spec.required ? '<span class="text-rose-400">*</span>' : '';
    const label = `<label class="lbl" for="${id}">${esc(spec.label)} ${req}</label>`;
    const help = spec.help ? `<p class="help">${esc(spec.help)}</p>` : '';
    const ph = spec.placeholder ? ` placeholder="${esc(spec.placeholder)}"` : '';
    const v = value ?? spec.default ?? '';
    const data = `data-field="${esc(spec.name)}" data-type="${esc(spec.type)}"`;
    let control;
    switch (spec.type) {
      case 'textarea':
        control = `<textarea id="${id}" class="txt" ${data}${ph}>${esc(v)}</textarea>`;
        break;
      case 'number':
        control = `<input id="${id}" type="number" min="0" step="any" inputmode="decimal" class="inp" ${data} value="${esc(v)}"${ph}>`;
        break;
      case 'date':
        control = `<input id="${id}" type="date" class="inp" ${data} value="${esc(v || App.today())}">`;
        break;
      case 'checkbox':
        return `<label class="flex items-center gap-2 text-sm text-slate-300 py-1"><input type="checkbox" class="w-4 h-4 accent-sky-500" ${data} ${v ? 'checked' : ''}> ${esc(spec.label)}</label>${help}`;
      case 'select': {
        const opts = (spec.options || []).map((o) => `<option value="${esc(o)}" ${o === v ? 'selected' : ''}>${esc(o)}</option>`).join('');
        control = `<select id="${id}" class="sel" ${data}>${opts}</select>`;
        break;
      }
      case 'multiselect': {
        const options = spec.options === 'channels' ? ((App.state.context && App.state.context.context.channels_active) || []) : (spec.options || []);
        if (!options.length) {
          control = `<div class="text-sm text-amber-300">Chưa có kênh trong hồ sơ. <a class="underline" href="#/context">Thêm kênh đang dùng</a>.</div>`;
        } else {
          const chosen = Array.isArray(v) ? v : [];
          control = `<div class="flex flex-wrap gap-2" ${data}>${options.map((o) => `<label class="chip chip-mute cursor-pointer"><input type="checkbox" class="accent-sky-500" value="${esc(o)}" ${chosen.includes(o) || (!chosen.length && spec.required) ? 'checked' : ''}> ${esc(o)}</label>`).join('')}</div>`;
        }
        break;
      }
      default:
        control = `<input id="${id}" class="inp" ${data} value="${esc(v)}"${ph}>`;
    }
    return `<div>${label}${control}${help}</div>`;
  };

  ui.readFields = (root) => {
    const out = {};
    App.$$('[data-field]', root).forEach((el) => {
      const name = el.dataset.field;
      const type = el.dataset.type;
      if (type === 'checkbox') out[name] = el.checked;
      else if (type === 'multiselect') out[name] = App.$$('input:checked', el).map((c) => c.value);
      else if (type === 'number') out[name] = el.value === '' ? '' : Number(el.value);
      else out[name] = el.value;
    });
    return out;
  };

  // ---------------------------------------------------------------- hồ sơ còn thiếu
  ui.missingContextForm = (missing, onSaved) => {
    const box = document.createElement('div');
    box.className = 'rounded-xl border border-amber-500/40 bg-amber-500/5 p-4';
    box.innerHTML = `<div class="font-semibold text-amber-300"><i class="fa-solid fa-circle-question"></i> Cần thêm thông tin trước khi chạy</div>
      <p class="text-xs text-slate-400 mt-1 mb-3">Skill marketing yêu cầu "bối cảnh trước, chiến thuật sau". Trả lời ${missing.length} câu dưới đây; câu trả lời được lưu vào Hồ sơ bối cảnh.</p>
      <div class="space-y-3" data-q></div>
      <div class="mt-3 flex gap-2"><button type="button" class="btn-primary btn-sm" data-save><i class="fa-solid fa-floppy-disk"></i> Lưu và chạy lại</button>
      <a href="#/context" class="btn-ghost btn-sm">Mở toàn bộ hồ sơ</a></div>`;
    const q = box.querySelector('[data-q]');
    missing.forEach((m) => {
      const multi = m.kind !== 'text' && m.kind !== 'number';
      const id = 'mq' + (++uid);
      q.insertAdjacentHTML('beforeend', `<div><label class="lbl" for="${id}">${esc(m.question)}</label>
        ${multi ? `<textarea id="${id}" class="txt" data-path="${esc(m.path)}" data-kind="${esc(m.kind)}" placeholder="${esc(m.hint || '')}"></textarea>`
          : `<input id="${id}" class="inp" data-path="${esc(m.path)}" data-kind="${esc(m.kind)}" placeholder="${esc(m.hint || '')}">`}
        ${m.hint ? `<p class="help">${esc(m.hint)}</p>` : ''}</div>`);
    });
    box.querySelector('[data-save]').addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const patch = {};
      App.$$('[data-path]', box).forEach((el) => {
        const val = ui.fromText(el.dataset.kind, el.value);
        if ((Array.isArray(val) && val.length) || (!Array.isArray(val) && val !== null && val !== '')) patch[el.dataset.path] = val;
      });
      if (!Object.keys(patch).length) { App.toast('Hãy trả lời ít nhất một câu.', 'warn'); return; }
      App.busy(btn, true, 'Đang lưu…');
      try {
        await App.patch('/api/context', { patch, note: 'Trả lời khi chạy tác vụ' });
        await App.loadContext(true);
        App.toast('Đã lưu vào hồ sơ bối cảnh.');
        if (onSaved) await onSaved();
      } catch (err) {
        App.toast(err.message, 'bad');
      } finally {
        App.busy(btn, false);
      }
    });
    return box;
  };

  // ---------------------------------------------------------------- biểu đồ
  const charts = new WeakMap();
  ui.chart = (canvas, config, tries = 0) => {
    // Khung nhìn được dựng ngoài DOM rồi mới gắn vào: chờ canvas gắn vào trang để Chart.js đo đúng kích thước
    if (!canvas.isConnected) {
      if (tries < 40) setTimeout(() => ui.chart(canvas, config, tries + 1), 25);
      return null;
    }
    if (!window.Chart) { canvas.replaceWith(Object.assign(document.createElement('div'), { className: 'text-xs text-slate-500', textContent: 'Không tải được thư viện biểu đồ.' })); return null; }
    const old = charts.get(canvas);
    if (old) old.destroy();
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = '#1e293b';
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    const c = new Chart(canvas, config);
    charts.set(canvas, c);
    return c;
  };
})();
