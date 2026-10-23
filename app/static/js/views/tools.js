/* Nghiên cứu & Đối thủ, Ảnh & Video, Local SEO, Kiểm duyệt nội dung, Cài đặt (kèm quản trị). */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;

  // ------------------------------------------------------------------ NGHIÊN CỨU & ĐỐI THỦ
  const TYPES = ['Trực tiếp', 'Thứ cấp', 'Gián tiếp'];

  async function renderResearch(el) {
    const [c, legacy] = await Promise.all([App.get('/api/competitors'), App.get('/api/legacy/research')]);
    const comps = c.competitors;
    el.innerHTML = `
      <div class="space-y-5">
        <div class="card">
          <h1 class="text-lg font-bold">Nghiên cứu thị trường & đối thủ</h1>
          <p class="text-sm text-slate-400 mt-1">Các tác vụ nghiên cứu dùng tìm kiếm Google và ghi nguồn cho từng ý. Đối thủ chỉ được lưu khi bạn nhập hoặc có nguồn chứng minh.</p>
          <div class="grid sm:grid-cols-3 gap-3 mt-4">
            <a href="#/studio/market_research" class="card-tight hover:border-sky-500/60"><div class="font-semibold text-sm"><i class="fa-solid fa-earth-asia text-sky-400"></i> Nghiên cứu thị trường</div><div class="text-xs text-slate-400 mt-1">Quy mô, xu hướng, SWOT, kế hoạch 4 tuần — có nguồn.</div></a>
            <a href="#/studio/competitor_discovery" class="card-tight hover:border-sky-500/60"><div class="font-semibold text-sm"><i class="fa-solid fa-users-viewfinder text-sky-400"></i> Tìm đối thủ</div><div class="text-xs text-slate-400 mt-1">Đối thủ trực tiếp, thứ cấp, gián tiếp tại khu vực của bạn.</div></a>
            <a href="#/studio/competitor_dossier" class="card-tight hover:border-sky-500/60"><div class="font-semibold text-sm"><i class="fa-solid fa-file-shield text-sky-400"></i> Hồ sơ đối thủ</div><div class="text-xs text-slate-400 mt-1">Battlecard: định vị, giá, khách phàn nàn, nơi mình thắng.</div></a>
          </div>
        </div>

        <div class="card">
          <div class="flex flex-wrap items-center gap-2 mb-3">
            <h2 class="font-bold flex-1">Danh sách đối thủ (${comps.length})</h2>
            <button type="button" class="btn-primary btn-sm" data-act="add"><i class="fa-solid fa-plus"></i> Thêm tay</button>
            ${comps.length ? '<button type="button" class="btn-ghost btn-sm" data-act="clear"><i class="fa-regular fa-trash-can"></i> Xóa tất cả</button>' : ''}
          </div>
          ${comps.length ? `<div class="grid md:grid-cols-2 gap-3">${comps.map(compCard).join('')}</div>`
            : '<p class="text-sm text-slate-400">Chưa có đối thủ. Thêm tay hoặc chạy tác vụ “Tìm đối thủ”.</p>'}
        </div>

        ${legacy.items.length ? `<details class="card">
          <summary class="font-bold cursor-pointer"><i class="fa-solid fa-box-archive text-amber-400"></i> Nghiên cứu từ phiên bản cũ (${legacy.items.length})</summary>
          <div class="mt-3 rounded-xl border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-200">${esc(legacy.warning)}</div>
          <ul class="mt-3 divide-y divide-slate-800">${legacy.items.map((r) => `<li class="py-2 flex items-center gap-3">
            <div class="flex-1 min-w-0"><div class="text-sm truncate">${esc(r.title || r.category)}</div><div class="text-[11px] text-slate-500">${esc(r.category || '')} · ${esc(App.dt(r.created_at))}</div></div>
            ${r.legacy ? '<span class="chip chip-warn">Chưa kiểm chứng</span>' : ''}
            <button type="button" class="btn-ghost btn-sm" data-act="legacy" data-id="${r.id}">Xem</button></li>`).join('')}</ul>
        </details>` : ''}
      </div>`;

    App.on(el, {
      add: () => openComp(),
      clear: async () => {
        if (!(await App.confirm('Xóa toàn bộ danh sách đối thủ (kể cả battlecard)?', { danger: true, okLabel: 'Xóa tất cả' }))) return;
        await App.del('/api/competitors');
        App.render();
      },
      del: async (btn) => {
        if (!(await App.confirm('Xóa đối thủ này?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del('/api/competitors/' + btn.dataset.id);
        App.render();
      },
      card: (btn) => {
        const x = comps.find((k) => String(k.id) === btn.dataset.id);
        App.modal({ title: 'Battlecard: ' + x.name, wide: true,
          body: `<div class="mb-3">${ui.provenance(x.provenance)}</div><article class="md">${App.md(x.battlecard_content)}</article>` });
      },
      dossier: (btn) => {
        const x = comps.find((k) => String(k.id) === btn.dataset.id);
        App.state.prefill = {
          task: 'competitor_dossier',
          inputs: {
            competitor_name: x.name,
            website: x.website || '',
            social: x.social || '',
            phone: x.phone || '',
            notes: x.notes || '',
          }
        };
        App.go('studio', 'competitor_dossier');
      },
      legacy: (btn) => {
        const r = legacy.items.find((k) => String(k.id) === btn.dataset.id);
        App.modal({ title: r.title || r.category, wide: true,
          body: `<div class="rounded-xl border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-200 mb-4"><i class="fa-solid fa-triangle-exclamation"></i> ${esc(legacy.warning)}</div><article class="md">${App.md(r.content)}</article>` });
      },
    });
  }

  function compCard(x) {
    const ev = x.evidence || [];
    return `<div class="card-tight">
      <div class="flex items-start gap-2">
        <div class="flex-1 min-w-0"><div class="font-semibold">${esc(x.name)}</div>
          <div class="flex flex-wrap gap-1.5 mt-1"><span class="chip chip-mute">${esc(x.competitor_type || 'Trực tiếp')}</span>${x.is_manual ? '<span class="chip chip-mute">Nhập tay</span>' : '<span class="chip chip-info">Từ tìm kiếm</span>'}${x.battlecard_content ? '<span class="chip chip-ok">Có battlecard</span>' : ''}</div></div>
        <button type="button" class="text-slate-500 hover:text-rose-400" data-act="del" data-id="${x.id}" aria-label="Xóa"><i class="fa-regular fa-trash-can"></i></button>
      </div>
      ${x.website ? `<a class="text-xs text-sky-400 break-all block mt-2" href="${esc(/^https?:\/\//.test(x.website) ? x.website : 'https://' + x.website)}" target="_blank" rel="noopener noreferrer"><i class="fa-solid fa-globe"></i> ${esc(x.website)}</a>` : ''}
      ${x.social ? `<a class="text-xs text-sky-400 break-all block mt-1" href="${esc(/^https?:\/\//.test(x.social) ? x.social : 'https://' + x.social)}" target="_blank" rel="noopener noreferrer"><i class="fa-brands fa-facebook"></i> ${esc(x.social)}</a>` : ''}
      ${x.phone ? `<div class="text-xs text-slate-300 mt-1"><i class="fa-solid fa-phone"></i> ${esc(x.phone)}</div>` : ''}
      ${x.core_products ? `<div class="text-xs text-slate-300 mt-1">Bán: ${esc(x.core_products)}</div>` : ''}
      ${x.price_segment ? `<div class="text-xs text-slate-400">Giá: ${esc(x.price_segment)}</div>` : ''}
      ${x.notes ? `<div class="text-xs text-slate-400 mt-1">${esc(x.notes)}</div>` : ''}
      ${ev.length ? `<div class="text-[11px] text-slate-500 mt-2">Nguồn: ${ev.map((s, i) => ui.safeLink(s.url, `[${i + 1}]`, 'text-sky-400 underline')).join(' ')}</div>` : ''}
      <div class="flex flex-wrap gap-2 mt-3">
        ${x.battlecard_content ? `<button type="button" class="btn-soft btn-sm" data-act="card" data-id="${x.id}"><i class="fa-solid fa-file-lines"></i> Xem battlecard</button>` : ''}
        <button type="button" class="btn-ghost btn-sm" data-act="dossier" data-id="${x.id}"><i class="fa-solid fa-wand-magic-sparkles"></i> ${x.battlecard_content ? 'Cập nhật' : 'Lập'} hồ sơ</button>
      </div>
    </div>`;
  }

  function openComp() {
    const body = document.createElement('form');
    body.className = 'space-y-3';
    body.innerHTML = `
      <div><label class="lbl" for="cp-name">Tên đối thủ <span class="text-rose-400">*</span></label><input id="cp-name" name="name" class="inp"></div>
      <div class="grid sm:grid-cols-2 gap-3">
        <div><label class="lbl" for="cp-type">Loại</label><select id="cp-type" name="competitor_type" class="sel">${TYPES.map((t) => `<option>${t}</option>`).join('')}</select></div>
        <div><label class="lbl" for="cp-web">Website/fanpage</label><input id="cp-web" name="website" class="inp" placeholder="https://..."></div>
        <div><label class="lbl" for="cp-social">Mạng xã hội (fanpage, TikTok...)</label><input id="cp-social" name="social" class="inp" placeholder="facebook.com/... hoặc tiktok.com/@..."></div>
        <div><label class="lbl" for="cp-phone">SĐT</label><input id="cp-phone" name="phone" class="inp" placeholder="0905..."></div>
        <div><label class="lbl" for="cp-price">Phân khúc giá</label><input id="cp-price" name="price_segment" class="inp" placeholder="25–45k/ly"></div>
      </div>
      <div><label class="lbl" for="cp-prod">Sản phẩm chính</label><input id="cp-prod" name="core_products" class="inp"></div>
      <div><label class="lbl" for="cp-notes">Ghi chú (điều bạn quan sát được)</label><textarea id="cp-notes" name="notes" class="txt" rows="3"></textarea></div>`;
    App.modal({ title: 'Thêm đối thủ', body, actions: [{ label: 'Hủy' }, { label: '<i class="fa-solid fa-plus"></i> Thêm', cls: 'btn-primary', onClick: async () => {
      const d = {};
      App.$$('[name]', body).forEach((x) => { d[x.name] = x.value.trim(); });
      if (!d.name) { App.toast('Nhập tên đối thủ.', 'warn'); return true; }
      await App.post('/api/competitors', d);
      App.toast('Đã thêm đối thủ.');
      App.render();
      return false;
    } }] });
  }

  // ------------------------------------------------------------------ ẢNH & VIDEO
  const blobUrls = [];
  async function renderMedia(el) {
    const data = await App.get('/api/media');
    const prompt = App.state.mediaPrompt || '';
    App.state.mediaPrompt = '';
    blobUrls.splice(0).forEach((u) => URL.revokeObjectURL(u));
    el.innerHTML = `
      <div class="grid xl:grid-cols-3 gap-5">
        <form class="card space-y-3 h-fit" data-form novalidate>
          <h1 class="text-lg font-bold">Tạo ảnh & video</h1>
          <div class="flex gap-2" role="radiogroup">
            <label class="tab active cursor-pointer" data-kind-label="image"><input type="radio" name="kind" value="image" class="sr-only" checked> <i class="fa-solid fa-image"></i> Ảnh</label>
            <label class="tab cursor-pointer" data-kind-label="video"><input type="radio" name="kind" value="video" class="sr-only"> <i class="fa-solid fa-film"></i> Video</label>
          </div>
          <div><label class="lbl" for="md-prompt">Mô tả hình ảnh</label><textarea id="md-prompt" class="txt" rows="6" data-prompt placeholder="vd: Ly cà phê muối trên bàn gỗ, ánh nắng sáng sớm, phong cách ảnh sản phẩm tối giản">${esc(prompt)}</textarea>
            <p class="help">Mô tả hình ảnh nguyên bản. Không dùng người nổi tiếng, nhân vật hay logo có bản quyền. Ảnh AI dùng cho quảng cáo cần ghi chú phù hợp chính sách nền tảng.</p></div>
          <div><label class="lbl" for="md-ratio">Tỉ lệ</label><select id="md-ratio" class="sel" data-ratio></select></div>
          <button type="submit" class="btn-primary w-full justify-center" data-go><i class="fa-solid fa-wand-magic-sparkles"></i> Tạo</button>
          <p class="text-[11px] text-slate-500" data-note></p>
        </form>
        <div class="xl:col-span-2">
          ${data.jobs.length ? `<div class="grid sm:grid-cols-2 gap-4" data-gallery>${data.jobs.map(jobCard).join('')}</div>`
            : ui.empty('fa-photo-film', 'Chưa có ảnh/video', 'Tạo ảnh cho bài đăng từ prompt trong Gói nội dung hoặc mô tả của bạn.')}
        </div>
      </div>`;

    const form = el.querySelector('[data-form]');
    const ratioSel = form.querySelector('[data-ratio]');
    const note = form.querySelector('[data-note]');
    const setKind = (kind) => {
      App.$$('[data-kind-label]', form).forEach((l) => l.classList.toggle('active', l.dataset.kindLabel === kind));
      const ratios = kind === 'video' ? data.video_ratios : data.image_ratios;
      ratioSel.innerHTML = ratios.map((r) => `<option>${esc(r)}</option>`).join('');
      note.textContent = kind === 'video'
        ? 'Video dùng Veo: cần API key có bật thanh toán, mất vài phút. Bấm “Kiểm tra” trên thẻ video để cập nhật.'
        : 'Ảnh dùng model ảnh của Gemini; một số model cần API key có bật thanh toán.';
    };
    App.$$('input[name=kind]', form).forEach((r) => r.addEventListener('change', () => setKind(r.value)));
    setKind('image');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const kind = form.querySelector('input[name=kind]:checked').value;
      const btn = form.querySelector('[data-go]');
      const text = form.querySelector('[data-prompt]').value.trim();
      if (text.length < 10) { App.toast('Mô tả dài hơn một chút (ít nhất 10 ký tự).', 'warn'); return; }
      App.busy(btn, true, kind === 'video' ? 'Đang gửi yêu cầu…' : 'Đang tạo ảnh…');
      try {
        const r = await App.post('/api/media/' + kind, { prompt: text, aspect_ratio: ratioSel.value });
        if (r.job.status === 'failed') App.toast('Không tạo được: ' + (r.job.error || 'lỗi không rõ'), 'bad');
        else App.toast(kind === 'video' ? 'Đã gửi yêu cầu video. Kiểm tra lại sau 1–3 phút.' : 'Đã tạo ảnh.');
        App.render();
      } catch (err) {
        App.toast(err.message, 'bad');
        App.busy(btn, false);
      }
    });

    App.$$('[data-media]', el).forEach(async (box) => {
      try {
        const res = await App.api('GET', `/api/media/${box.dataset.media}/file`, undefined, { raw: true });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        blobUrls.push(url);
        const isVideo = (blob.type || '').startsWith('video');
        box.innerHTML = isVideo ? `<video src="${url}" controls class="w-full rounded-lg bg-black"></video>` : `<img src="${url}" alt="Ảnh đã tạo" class="w-full rounded-lg">`;
        const dl = box.parentElement.querySelector('[data-dl]');
        if (dl) { dl.href = url; dl.download = `marketing-os-${box.dataset.media}.${isVideo ? 'mp4' : (blob.type.split('/')[1] || 'png')}`; dl.classList.remove('hidden'); }
      } catch (err) {
        box.innerHTML = `<div class="text-xs text-rose-300 p-3">${esc(err.message)}</div>`;
      }
    });

    App.on(el, {
      refresh: async (btn) => {
        App.busy(btn, true, 'Đang kiểm tra…');
        try {
          const r = await App.post(`/api/media/${btn.dataset.id}/refresh`);
          if (r.job.status === 'running') { App.toast(r.job.warning || 'Video vẫn đang tạo. Thử lại sau ít phút.', 'info'); App.busy(btn, false); } else App.render();
        } catch (err) {
          App.busy(btn, false);
          throw err;
        }
      },
      del: async (btn) => {
        if (!(await App.confirm('Xóa file này?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del('/api/media/' + btn.dataset.id);
        App.render();
      },
      reuse: (btn) => {
        const job = data.jobs.find((j) => String(j.id) === btn.dataset.id);
        form.querySelector('[data-prompt]').value = job.prompt;
        form.scrollIntoView({ behavior: 'smooth' });
      },
    });
  }

  function jobCard(j) {
    const status = { done: '<span class="chip chip-ok">Xong</span>', running: '<span class="chip chip-info"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tạo</span>', failed: '<span class="chip chip-bad">Lỗi</span>' }[j.status] || '';
    return `<div class="card-tight space-y-2">
      ${j.status === 'done' ? `<div data-media="${j.id}" class="min-h-[120px] flex items-center justify-center"><div class="skeleton w-full h-40"></div></div>` : ''}
      ${j.status === 'failed' ? `<div class="text-xs text-rose-300">${esc(j.error || 'Không tạo được.')}</div>` : ''}
      <div class="flex items-center gap-2 flex-wrap">${status}<span class="chip chip-mute">${j.kind === 'video' ? 'Video' : 'Ảnh'} ${esc(j.aspect_ratio)}</span>${j.model ? `<span class="chip chip-mute">${esc(j.model)}</span>` : ''}</div>
      <p class="text-xs text-slate-400 line-clamp-3">${esc(j.prompt)}</p>
      <div class="flex flex-wrap gap-2">
        ${j.status === 'running' && j.kind === 'video' ? `<button type="button" class="btn-soft btn-sm" data-act="refresh" data-id="${j.id}"><i class="fa-solid fa-rotate"></i> Kiểm tra</button>` : ''}
        <a class="btn-ghost btn-sm hidden" data-dl><i class="fa-solid fa-download"></i> Tải</a>
        <button type="button" class="btn-ghost btn-sm" data-act="reuse" data-id="${j.id}"><i class="fa-solid fa-pen"></i> Dùng lại prompt</button>
        <button type="button" class="btn-ghost btn-sm ml-auto" data-act="del" data-id="${j.id}" aria-label="Xóa"><i class="fa-regular fa-trash-can"></i></button>
      </div>
    </div>`;
  }

  // ------------------------------------------------------------------ LOCAL SEO
  async function renderLocal(el) {
    const t = await App.get('/api/local-seo');
    const n = t.nap;
    const napText = [n.name, n.address, n.phone, n.website, n.hours].filter(Boolean).join('\n');
    el.innerHTML = `
      <div class="space-y-5">
        <div class="card">
          <h1 class="text-lg font-bold">Local SEO & tối ưu cho AI search</h1>
          <p class="text-sm text-slate-400 mt-1">Mọi thông tin lấy từ Hồ sơ bối cảnh. Hệ thống không tự điền địa chỉ, giờ mở cửa hay câu trả lời FAQ.</p>
          <div class="flex flex-wrap gap-2 mt-3">
            <a href="#/studio/review_reply" class="btn-soft btn-sm"><i class="fa-solid fa-star"></i> Trả lời đánh giá</a>
            <a href="#/studio/answer_first" class="btn-soft btn-sm"><i class="fa-solid fa-comment-dots"></i> Câu trả lời cho AI search</a>
            <a href="#/studio/keyword_plan" class="btn-soft btn-sm"><i class="fa-solid fa-key"></i> Kế hoạch từ khóa</a>
            <a href="#/context" class="btn-ghost btn-sm"><i class="fa-solid fa-id-card"></i> Sửa hồ sơ</a>
          </div>
        </div>
        <div class="grid lg:grid-cols-2 gap-5">
          <div class="card">
            <div class="flex items-center justify-between mb-3"><h2 class="font-bold">NAP chuẩn (dùng giống hệt mọi nơi)</h2>${napText ? '<button type="button" class="btn-ghost btn-sm" data-act="copy-nap"><i class="fa-regular fa-copy"></i></button>' : ''}</div>
            <dl class="text-sm space-y-2">
              ${[['Tên', n.name], ['Địa chỉ', n.address], ['Điện thoại', n.phone], ['Website', n.website], ['Giờ mở cửa', n.hours]].map(([k, v]) => `<div class="flex gap-3"><dt class="w-24 shrink-0 text-slate-400">${k}</dt><dd class="${v ? '' : 'text-amber-300'}">${v ? esc(v) : 'Chưa có'}</dd></div>`).join('')}
            </dl>
          </div>
          <div class="card">
            <h2 class="font-bold mb-3">Checklist</h2>
            <ul class="space-y-2 text-sm">${t.checklist.map((c) => `<li class="flex gap-2">
              <span class="shrink-0 mt-0.5">${c.done === true ? '<i class="fa-solid fa-circle-check text-emerald-400"></i>' : c.done === false ? '<i class="fa-solid fa-circle-xmark text-rose-400"></i>' : '<i class="fa-regular fa-square text-slate-500"></i>'}</span>
              <span>${esc(c.item)}<span class="block text-xs text-slate-500">${esc(c.how)}</span></span></li>`).join('')}</ul>
          </div>
        </div>
        <div class="card">
          <div class="flex items-center justify-between mb-2"><h2 class="font-bold">Dữ liệu có cấu trúc (JSON-LD)</h2><button type="button" class="btn-soft btn-sm" data-act="copy-schema"><i class="fa-regular fa-copy"></i> Sao chép</button></div>
          <p class="text-xs text-slate-400 mb-3">Dán vào thẻ &lt;head&gt; của website để Google và các công cụ AI hiểu doanh nghiệp của bạn.</p>
          ${t.schema.warnings.length ? `<ul class="text-xs text-amber-300 space-y-1 mb-3">${t.schema.warnings.map((w) => `<li><i class="fa-solid fa-triangle-exclamation"></i> ${esc(w)}</li>`).join('')}</ul>` : ''}
          <pre class="text-xs bg-slate-950 border border-slate-800 rounded-xl p-3 overflow-x-auto"><code>${esc(t.schema.html)}</code></pre>
        </div>
      </div>`;
    App.on(el, {
      'copy-nap': () => App.copy(napText),
      'copy-schema': () => App.copy(t.schema.html),
    });
  }

  // ------------------------------------------------------------------ KIỂM DUYỆT
  const KINDS = [['post', 'Bài đăng mạng xã hội'], ['ad', 'Quảng cáo'], ['landing', 'Landing page'], ['email', 'Email'], ['sms', 'SMS'],
    ['video_script', 'Kịch bản video'], ['kol_brief', 'Bài KOL/KOC'], ['pr', 'Thông cáo báo chí'], ['review_reply', 'Trả lời đánh giá'], ['offer_copy', 'Ưu đãi']];
  const RULES = [
    ['G01', 'Số liệu, thống kê phải có nguồn hoặc nằm trong Bằng chứng của hồ sơ'],
    ['G02', 'Không khẳng định tuyệt đối/so sánh nhất (“số 1”, “tốt nhất”) khi không có chứng nhận'],
    ['G03', 'Không tạo khan hiếm giả (“chỉ còn”, “hôm nay cuối”) khi không có bằng chứng'],
    ['G04', 'Không dùng từ cấm trong hồ sơ; không nói xấu, nêu tên đối thủ trong nội dung công khai'],
    ['G05', 'Ưu đãi phải nêu rõ điều kiện; giảm giá phải có thời hạn'],
    ['G06', 'Nội dung tài trợ/KOL phải ghi rõ “Quảng cáo”/“Được tài trợ”'],
    ['G07', 'Chỉ gửi tiếp thị cho khách đã đồng ý (Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP)'],
    ['G10', 'Lời chứng thực/đánh giá phải có thật và được phép dùng'],
    ['G11', 'Nhãn tin cậy: [Unverified], [Inference], [Speculation] cho ý chưa kiểm chứng'],
  ];

  function renderCompliance(el) {
    el.innerHTML = `
      <div class="grid lg:grid-cols-5 gap-5">
        <form class="lg:col-span-3 card space-y-3" data-form novalidate>
          <h1 class="text-lg font-bold">Kiểm duyệt nội dung trước khi đăng</h1>
          <p class="text-sm text-slate-400">Dán bài viết, quảng cáo, kịch bản hoặc tin nhắn. Hệ thống kiểm theo cổng tuân thủ của skill marketing và Hồ sơ bối cảnh (từ cấm, bằng chứng, đối thủ).</p>
          <div class="grid sm:grid-cols-2 gap-3">
            <div><label class="lbl" for="cm-kind">Loại nội dung</label><select id="cm-kind" class="sel" data-kind>${KINDS.map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join('')}</select></div>
            <div><label class="lbl" for="cm-sc">Bằng chứng giới hạn có thật (nếu có)</label><input id="cm-sc" class="inp" data-scarcity placeholder="vd: Chỉ 50 suất theo kế hoạch sự kiện"></div>
          </div>
          <div><label class="lbl" for="cm-text">Nội dung</label><textarea id="cm-text" class="txt" rows="12" data-text maxlength="20000"></textarea></div>
          <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" class="accent-sky-500" data-sponsored> Đây là nội dung tài trợ / hợp tác KOL</label>
          <button type="submit" class="btn-primary w-full justify-center"><i class="fa-solid fa-shield-halved"></i> Kiểm tra</button>
          <div data-out></div>
        </form>
        <div class="lg:col-span-2 card h-fit">
          <h2 class="font-bold mb-3">Các cổng kiểm tra</h2>
          <ul class="space-y-2 text-sm">${RULES.map(([c, t]) => `<li class="flex gap-2"><span class="chip chip-mute shrink-0">${c}</span><span class="text-slate-300">${esc(t)}</span></li>`).join('')}</ul>
          <p class="help mt-3">Kiểm tra tự động giúp bắt lỗi phổ biến, không thay thế ý kiến pháp lý cho chiến dịch lớn hoặc ngành có điều kiện (thực phẩm chức năng, mỹ phẩm, y tế, tài chính).</p>
        </div>
      </div>`;
    const form = el.querySelector('[data-form]');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = form.querySelector('[data-text]').value;
      if (!text.trim()) { App.toast('Dán nội dung cần kiểm.', 'warn'); return; }
      const btn = form.querySelector('[type=submit]');
      App.busy(btn, true, 'Đang kiểm…');
      try {
        const r = await App.post('/api/compliance/check', { text, kind: form.querySelector('[data-kind]').value,
          scarcity_evidence: form.querySelector('[data-scarcity]').value, is_sponsored: form.querySelector('[data-sponsored]').checked });
        form.querySelector('[data-out]').innerHTML = ui.guardrails(r);
      } catch (err) {
        App.toast(err.message, 'bad');
      } finally {
        App.busy(btn, false);
      }
    });
  }

  // ------------------------------------------------------------------ CÀI ĐẶT
  async function renderSettings(el) {
    const user = App.state.user;
    const [ai, hook, ingest] = await Promise.all([App.get('/api/settings/ai'), App.get('/api/settings/webhook'), App.get('/api/settings/ingest')]);
    const st = App.state.status || {};
    el.innerHTML = `
      <div class="space-y-5 max-w-4xl">
        <section class="card space-y-3">
          <h2 class="font-bold"><i class="fa-solid fa-robot text-sky-400"></i> Gemini API</h2>
          <p class="text-sm text-slate-400">Lấy key miễn phí tại <a class="text-sky-400 underline" href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">aistudio.google.com/apikey</a>. Key được lưu trên máy chủ của bạn, không hiển thị lại và không nằm trong file sao lưu.</p>
          <div class="text-sm">${ai.has_key ? `<span class="chip chip-ok"><i class="fa-solid fa-key"></i> Đã có key ${esc(ai.key_hint)}</span>` : (st.ai && st.ai.server_key_available ? '<span class="chip chip-info">Đang dùng key chung của máy chủ</span>' : '<span class="chip chip-warn">Chưa có key</span>')}</div>
          <div class="grid sm:grid-cols-2 gap-3">
            <div><label class="lbl" for="s-key">API key mới</label><input id="s-key" type="password" class="inp" autocomplete="off" data-key placeholder="${ai.has_key ? 'Để trống nếu giữ key cũ' : 'AIza…'}"></div>
            <div><label class="lbl" for="s-model">Model ưu tiên</label><input id="s-model" class="inp" list="s-models" data-model value="${esc(ai.model)}" placeholder="Để trống: tự chọn model tốt nhất"><datalist id="s-models"></datalist>
              <p class="help">Hệ thống tự đổi sang model khác khi model này hết hạn mức hoặc ngừng hỗ trợ.</p></div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="btn-primary btn-sm" data-act="save-ai"><i class="fa-solid fa-floppy-disk"></i> Lưu</button>
            <button type="button" class="btn-ghost btn-sm" data-act="check-ai"><i class="fa-solid fa-plug-circle-check"></i> Kiểm tra kết nối</button>
            ${ai.has_key ? '<button type="button" class="btn-danger btn-sm" data-act="clear-ai"><i class="fa-regular fa-trash-can"></i> Xóa key</button>' : ''}
          </div>
          <div data-ai-out></div>
        </section>

        <section class="card space-y-3">
          <h2 class="font-bold"><i class="fa-solid fa-paper-plane text-sky-400"></i> Webhook xuất bản nội dung</h2>
          <p class="text-sm text-slate-400">Nối với Zapier, Make, n8n… để đăng bài đã duyệt lên Facebook/Zalo/website. Chỉ nhận địa chỉ https công khai; bài chỉ chuyển “Đã đăng” khi webhook trả mã 2xx.</p>
          <div class="flex flex-col sm:flex-row gap-2"><input class="inp" data-hook value="${esc(hook.content_webhook_url)}" placeholder="https://hooks.zapier.com/…" aria-label="Địa chỉ webhook">
          <button type="button" class="btn-primary btn-sm justify-center" data-act="save-hook">Lưu</button></div>
        </section>

        <section class="card space-y-2">
          <h2 class="font-bold"><i class="fa-solid fa-inbox text-sky-400"></i> Nhận lead từ website</h2>
          <p class="text-sm text-slate-400">Địa chỉ riêng của workspace: <code class="text-xs break-all">${esc(location.origin + ingest.path)}</code></p>
          <a href="#/leads" class="text-sm text-sky-400 underline">Lấy mã form mẫu trong CRM → “Nhận lead từ form”</a>
        </section>

        <section class="card space-y-3">
          <h2 class="font-bold"><i class="fa-solid fa-user-lock text-sky-400"></i> Tài khoản</h2>
          <p class="text-sm">${esc(user.name)} · ${esc(user.email)} ${user.is_admin ? '<span class="chip chip-info ml-1">Quản trị</span>' : ''}</p>
          ${user.auth_provider === 'google' ? '<p class="text-sm text-slate-400">Tài khoản đăng nhập bằng Google.</p>' : `
          <form class="grid sm:grid-cols-3 gap-3 items-end" data-pw novalidate>
            <div><label class="lbl" for="s-old">Mật khẩu hiện tại</label><input id="s-old" type="password" class="inp" autocomplete="current-password" name="old_password"></div>
            <div><label class="lbl" for="s-new">Mật khẩu mới</label><input id="s-new" type="password" class="inp" autocomplete="new-password" name="new_password"></div>
            <button type="submit" class="btn-ghost justify-center">Đổi mật khẩu</button>
          </form><p class="help">Ít nhất 8 ký tự, có chữ và số. Đổi xong, mọi thiết bị phải đăng nhập lại.</p>`}
        </section>

        <section class="card space-y-3">
          <h2 class="font-bold"><i class="fa-solid fa-database text-sky-400"></i> Dữ liệu</h2>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="btn-ghost btn-sm" data-act="export"><i class="fa-solid fa-download"></i> Tải bản sao lưu (JSON)</button>
            <button type="button" class="btn-danger btn-sm" data-act="reset"><i class="fa-solid fa-broom"></i> Làm mới workspace</button>
            <button type="button" class="btn-danger btn-sm" data-act="delete-account"><i class="fa-solid fa-user-xmark"></i> Xóa tài khoản</button>
          </div>
          <p class="help">Làm mới xóa nội dung, lịch, khách hàng, số liệu, kết quả AI nhưng giữ tài khoản và key. Xóa tài khoản xóa vĩnh viễn mọi dữ liệu (quyền xóa dữ liệu cá nhân).</p>
        </section>
        ${user.is_admin ? '<section class="card space-y-3" data-admin><div class="skeleton h-24"></div></section>' : ''}
        <p class="text-[11px] text-slate-600">Marketing OS ${esc(st.version || '')}</p>
      </div>`;

    const aiOut = el.querySelector('[data-ai-out]');
    App.on(el, {
      'save-ai': async (btn) => {
        const key = el.querySelector('[data-key]').value.trim();
        App.busy(btn, true, 'Đang lưu…');
        try {
          await App.post('/api/settings/ai', { api_key: key || null, model: el.querySelector('[data-model]').value.trim() });
          el.querySelector('[data-key]').value = '';
          await App.refreshStatus();
          App.toast('Đã lưu cài đặt AI.');
          if (key) await checkAi(aiOut, el);
          else App.render();
        } finally {
          App.busy(btn, false);
        }
      },
      'check-ai': async (btn) => {
        App.busy(btn, true, 'Đang kiểm tra…');
        try { await checkAi(aiOut, el); } finally { App.busy(btn, false); }
      },
      'clear-ai': async () => {
        if (!(await App.confirm('Xóa Gemini API key khỏi máy chủ?', { danger: true, okLabel: 'Xóa key' }))) return;
        await App.post('/api/settings/ai', { clear_key: true });
        await App.refreshStatus();
        App.render();
      },
      'save-hook': async () => {
        const r = await App.post('/api/settings/webhook', { content_webhook_url: el.querySelector('[data-hook]').value.trim() });
        App.toast(r.content_webhook_url ? 'Đã lưu webhook.' : 'Đã tắt webhook.');
      },
      export: () => App.downloadApi('/api/workspace/export', 'marketing-os-sao-luu.json'),
      reset: () => typedConfirm('Làm mới workspace', 'Gõ XOA để xóa toàn bộ dữ liệu làm việc (giữ tài khoản). Nên tải bản sao lưu trước.', 'XOA', async (v) => {
        const r = await App.post('/api/workspace/reset', { confirm: v });
        const n = Object.values(r.deleted || {}).reduce((a, b) => a + b, 0);
        App.state.context = null;
        await App.loadContext(true);
        App.toast(`Đã làm mới workspace (${n} bản ghi).`);
        App.go('home');
      }),
      'delete-account': () => typedConfirm('Xóa tài khoản', `Gõ đúng email ${user.email} để xóa vĩnh viễn tài khoản và mọi dữ liệu.`, user.email, async (v) => {
        await App.del('/api/account', { confirm: v });
        App.setToken('');
        App.state = { user: null, status: null, context: null, tasks: null };
        App.showAuth('Tài khoản đã được xóa.');
      }),
    });

    const pw = el.querySelector('[data-pw]');
    if (pw) {
      pw.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = pw.querySelector('[type=submit]');
        App.busy(btn, true);
        try {
          const r = await App.post('/api/auth/password', { old_password: pw.old_password.value, new_password: pw.new_password.value });
          App.setToken('');
          App.state = { user: null, status: null, context: null, tasks: null };
          App.showAuth(r.message + ' Đăng nhập bằng mật khẩu mới.');
        } catch (err) {
          App.toast(err.message, 'bad');
        } finally {
          App.busy(btn, false);
        }
      });
    }
    if (user.is_admin) renderAdmin(el.querySelector('[data-admin]'));
  }

  async function checkAi(out, el) {
    const r = await App.post('/api/settings/ai/check');
    if (!r.ok) {
      out.innerHTML = `<div class="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200"><i class="fa-solid fa-circle-xmark"></i> ${esc(r.error)}</div>`;
      return;
    }
    el.querySelector('#s-models').innerHTML = (r.text_models || []).map((m) => `<option value="${esc(m)}">`).join('');
    const g = r.generate || {};
    const genHtml = r.generate ? (g.ok
      ? `<div class="text-emerald-300"><i class="fa-solid fa-circle-check"></i> Thử tạo nội dung: thành công với <code>${esc(g.model)}</code>.</div>`
      : `<div class="text-rose-300"><i class="fa-solid fa-circle-xmark"></i> Thử tạo nội dung: lỗi${g.model ? ' (' + esc(g.model) + ')' : ''} — ${esc(g.error)}</div>`) : '';
    out.innerHTML = `<div class="rounded-xl border ${r.generate && !g.ok ? 'border-rose-500/40 bg-rose-500/5' : 'border-emerald-500/30 bg-emerald-500/5'} p-3 text-sm space-y-1">
      <div class="text-emerald-300 font-semibold"><i class="fa-solid fa-circle-check"></i> Key hợp lệ, đọc được danh sách model${r.key_source === 'server' ? ' (key máy chủ)' : ''}.</div>
      ${genHtml}
      <div class="text-xs text-slate-300">Model văn bản: ${(r.text_models || []).slice(0, 6).map((m) => `<code>${esc(m)}</code>`).join(', ') || '—'}</div>
      <div class="text-xs text-slate-300">Model ảnh: ${(r.image_models || []).map((m) => `<code>${esc(m)}</code>`).join(', ') || 'không thấy'} · Model video: ${(r.video_models || []).map((m) => `<code>${esc(m)}</code>`).join(', ') || 'không thấy'}</div></div>`;
  }

  function typedConfirm(title, message, expected, onOk) {
    const body = document.createElement('div');
    body.innerHTML = `<p class="text-sm text-slate-300 mb-3">${esc(message)}</p><input class="inp" data-typed autocomplete="off" aria-label="Xác nhận">`;
    App.modal({ title, body, actions: [{ label: 'Hủy' }, { label: 'Xác nhận', cls: 'btn-danger', onClick: async () => {
      const v = body.querySelector('[data-typed]').value.trim();
      if (v !== expected) { App.toast('Chưa gõ đúng nội dung xác nhận.', 'warn'); return true; }
      await onOk(v);
      return false;
    } }] });
  }

  async function renderAdmin(box) {
    try {
      const [u, sh] = await Promise.all([App.get('/api/admin/users'), App.get('/api/admin/sheets')]);
      box.innerHTML = `
        <h2 class="font-bold"><i class="fa-solid fa-user-shield text-sky-400"></i> Quản trị</h2>
        <div class="flex items-center gap-2"><span class="text-sm text-slate-400 flex-1">${u.total} tài khoản</span><button type="button" class="btn-ghost btn-sm" data-act="users-csv"><i class="fa-solid fa-file-csv"></i> Tải CSV</button></div>
        <div class="scroll-x max-h-80"><table class="tbl"><thead><tr><th>Email</th><th>Thương hiệu</th><th>Đăng nhập</th><th class="num">Số lần</th><th>Gần nhất</th></tr></thead><tbody>
          ${u.users.map((x) => `<tr><td>${esc(x.email)}${x.is_admin ? ' <span class="chip chip-info">QT</span>' : ''}</td><td>${esc(x.brand_name || '')}</td><td>${esc(x.auth_provider || '')}</td><td class="num">${App.num(x.login_count)}</td><td class="text-xs whitespace-nowrap">${esc(App.dt(x.last_login))}</td></tr>`).join('')}
        </tbody></table></div>
        <div class="border-t border-slate-800 pt-3 space-y-2">
          <h3 class="font-semibold text-sm">Đồng bộ danh sách đăng nhập sang Google Sheet</h3>
          <div class="flex flex-col sm:flex-row gap-2"><input class="inp" data-sheet value="${esc(sh.webhook_url)}" placeholder="https://script.google.com/macros/s/…/exec" aria-label="URL Google Apps Script">
            <button type="button" class="btn-primary btn-sm justify-center" data-act="save-sheet">Lưu</button>
            ${sh.connected ? '<button type="button" class="btn-ghost btn-sm justify-center" data-act="sync-sheet">Đồng bộ ngay</button>' : ''}</div>
          <details><summary class="text-xs text-sky-400 cursor-pointer">Mã Apps Script mẫu</summary><textarea class="txt font-mono text-xs mt-2" rows="10" readonly aria-label="Mã Apps Script">${esc(sh.apps_script_template)}</textarea></details>
        </div>`;
      App.on(box, {
        'users-csv': () => App.downloadApi('/api/admin/users.csv', 'nguoi-dung.csv'),
        'save-sheet': async () => { await App.post('/api/admin/sheets', { webhook_url: box.querySelector('[data-sheet]').value.trim() }); App.toast('Đã lưu.'); renderAdmin(box); },
        'sync-sheet': async () => { const r = await App.post('/api/admin/sheets/sync'); App.toast(`Đang gửi ${r.queued} tài khoản sang Google Sheet.`); },
      });
    } catch (e) {
      box.innerHTML = `<p class="text-sm text-rose-300">${esc(e.message)}</p>`;
    }
  }

  App.views.research = { render: renderResearch };
  App.views.media = { render: renderMedia };
  App.views.local = { render: renderLocal };
  App.views.compliance = { render: renderCompliance };
  App.views.settings = { render: renderSettings };
})();
