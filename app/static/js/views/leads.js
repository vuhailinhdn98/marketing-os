/* CRM theo phễu 6 tầng + tầng Mất, ghi nhận đồng ý tiếp thị (Luật 91/2025/QH15), chẩn đoán nút thắt. */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;

  const TONE = { new: 'chip-mute', consulting: 'chip-info', won: 'chip-ok', repeat: 'chip-ok', referral: 'chip-ok', loyal: 'chip-ok', lost: 'chip-bad' };
  const SOURCES = ['Facebook', 'Zalo', 'TikTok', 'Google', 'Website/Landing page', 'Khách giới thiệu', 'Tại cửa hàng', 'Sự kiện', 'Khác'];

  async function render(el) {
    const [list, stats] = await Promise.all([App.get('/api/leads'), App.get('/api/leads/stats')]);
    let leads = list.leads;
    let query = '';
    const stages = stats.stages;
    const f = stats.funnel || {};

    el.innerHTML = `
      <div class="space-y-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          ${ui.kpi('Tổng khách', App.num(stats.total))}
          ${ui.kpi('Đồng ý nhận tiếp thị', App.num(stats.consented), stats.total ? App.pct(stats.consented / stats.total * 100) + ' tổng khách' : '')}
          ${ui.kpi('Đã mua (tầng 3+)', App.num(stats.reached.won), stats.reached.new ? 'Tỉ lệ chốt ' + App.pct(stats.reached.won / stats.reached.new * 100) : '')}
          ${ui.kpi('Giá trị đơn đã chốt', App.money(stats.won_value))}
        </div>

        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center gap-3 mb-3">
            <h2 class="font-bold flex-1">Phễu khách hàng & nút thắt</h2>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="btn-primary btn-sm" data-act="new"><i class="fa-solid fa-user-plus"></i> Thêm khách</button>
              <button type="button" class="btn-ghost btn-sm" data-act="embed"><i class="fa-solid fa-code"></i> Nhận lead từ form</button>
              <button type="button" class="btn-ghost btn-sm" data-act="export-ok"><i class="fa-solid fa-file-csv"></i> CSV đã đồng ý</button>
              <button type="button" class="btn-ghost btn-sm" data-act="export-all"><i class="fa-solid fa-file-csv"></i> CSV tất cả</button>
            </div>
          </div>
          ${f.steps && f.steps.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>Bước chuyển</th><th class="num">Số khách</th><th class="num">Tỉ lệ</th><th></th></tr></thead><tbody>
            ${f.steps.map((s) => {
              const isB = f.bottleneck && f.bottleneck.from === s.from && f.bottleneck.to === s.to;
              return `<tr class="${isB ? 'text-amber-200' : ''}"><td>${esc(s.from)} → ${esc(s.to)}</td><td class="num">${s.from_count} → ${s.to_count}</td>
                <td class="num">${s.rate_pct === null ? '—' : App.pct(s.rate_pct)}</td><td>${isB ? '<span class="chip chip-warn">Nút thắt</span>' : (!s.enough_data ? '<span class="text-[11px] text-slate-500">ít dữ liệu</span>' : '')}</td></tr>`;
            }).join('')}</tbody></table></div>` : ''}
          <p class="help mt-2">${f.bottleneck ? `Nút thắt hiện tại: <b>${esc(f.bottleneck.from)} → ${esc(f.bottleneck.to)}</b>. Theo Theory of Constraints, dồn sức sửa đúng bước này trước; dùng tác vụ <a class="text-sky-400 underline" href="#/studio/weekly_loop">Vòng lặp tuần</a> để chọn thử nghiệm.` : esc(f.note || '')}</p>
        </div>

        <div class="flex items-center gap-2">
          <input class="inp md:w-80" data-search placeholder="Tìm tên, SĐT, email, sản phẩm…" aria-label="Tìm khách">
          <span class="text-xs text-slate-500" data-count></span>
        </div>
        <div data-board></div>
      </div>`;

    const board = el.querySelector('[data-board]');
    const draw = () => {
      const lst = leads.filter((l) => !query || `${l.full_name} ${l.phone} ${l.email} ${l.product_interest} ${l.notes}`.toLowerCase().includes(query));
      el.querySelector('[data-count]').textContent = `${lst.length}/${leads.length} khách`;
      if (!leads.length) {
        board.innerHTML = ui.empty('fa-users', 'Chưa có khách hàng', 'Thêm tay, hoặc nhúng form vào landing page để khách tự đăng ký (có ô đồng ý nhận tiếp thị).',
          '<button type="button" class="btn-primary btn-sm" data-act="new">Thêm khách</button><button type="button" class="btn-ghost btn-sm" data-act="embed">Nhận lead từ form</button>');
        return;
      }
      board.innerHTML = `<div class="kanban">${stages.map((s) => {
        const col = lst.filter((l) => l.status === s.key);
        return `<div class="kcol"><div class="flex items-center justify-between mb-2 px-1"><span class="text-sm font-bold">${esc(s.label)}</span><span class="chip ${TONE[s.key]}">${col.length}</span></div>
          <div class="space-y-2">${col.map(cardHtml).join('') || '<p class="text-xs text-slate-600 px-1">Trống</p>'}</div></div>`;
      }).join('')}</div>`;
    };
    const cardHtml = (l) => `<div class="kcard" role="button" tabindex="0" data-act="open" data-id="${l.id}">
      <div class="flex items-start gap-2"><div class="font-semibold text-sm flex-1 truncate">${esc(l.full_name)}</div>
      ${l.consent_marketing ? '<span class="chip chip-ok" title="Đã đồng ý nhận tiếp thị"><i class="fa-solid fa-check"></i></span>' : '<span class="chip chip-mute" title="Chưa đồng ý nhận tiếp thị"><i class="fa-solid fa-ban"></i></span>'}</div>
      <div class="text-xs text-slate-400 truncate">${esc(l.phone || l.email || '')}</div>
      ${l.product_interest ? `<div class="text-xs text-slate-300 truncate mt-1">${esc(l.product_interest)}</div>` : ''}
      <div class="flex items-center justify-between mt-1.5 text-[11px] text-slate-500"><span class="truncate">${esc(l.source || '')}</span>${l.deal_value ? `<span class="text-emerald-300">${App.money(l.deal_value)}</span>` : ''}</div>
      ${l.status === 'lost' && l.lost_reason ? `<div class="text-[11px] text-rose-300 mt-1 truncate">Lý do: ${esc(l.lost_reason)}</div>` : ''}
    </div>`;
    draw();

    const reload = async () => { App.render(); };
    el.querySelector('[data-search]').addEventListener('input', (e) => { query = e.target.value.trim().toLowerCase(); draw(); });
    board.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches('.kcard')) e.target.click(); });
    App.on(el, {
      new: () => openLead(null, stages, reload),
      open: (card) => openLead(leads.find((l) => String(l.id) === card.dataset.id), stages, reload),
      embed: () => openEmbed(),
      'export-ok': () => App.downloadApi('/api/leads/export.csv?consented_only=true', 'khach-dong-y-tiep-thi.csv'),
      'export-all': () => App.downloadApi('/api/leads/export.csv', 'khach-hang.csv'),
    });
  }

  function leadForm(l, stages) {
    const v = l || {};
    const src = v.source && !SOURCES.includes(v.source) ? [v.source, ...SOURCES] : SOURCES;
    return `
      <div class="grid sm:grid-cols-2 gap-3">
        <div><label class="lbl" for="ld-name">Họ tên <span class="text-rose-400">*</span></label><input id="ld-name" class="inp" data-f="full_name" value="${esc(v.full_name || '')}" autocomplete="off"></div>
        <div><label class="lbl" for="ld-phone">Số điện thoại</label><input id="ld-phone" class="inp" data-f="phone" inputmode="tel" value="${esc(v.phone || '')}"></div>
        <div><label class="lbl" for="ld-email">Email</label><input id="ld-email" type="email" class="inp" data-f="email" value="${esc(v.email || '')}"></div>
        <div><label class="lbl" for="ld-source">Nguồn</label><select id="ld-source" class="sel" data-f="source"><option value="">—</option>${src.map((s) => `<option ${s === v.source ? 'selected' : ''}>${esc(s)}</option>`).join('')}</select></div>
        <div><label class="lbl" for="ld-product">Quan tâm sản phẩm</label><input id="ld-product" class="inp" data-f="product_interest" value="${esc(v.product_interest || '')}"></div>
        <div><label class="lbl" for="ld-value">Giá trị đơn (VND)</label><input id="ld-value" type="number" min="0" step="1000" class="inp" data-f="deal_value" value="${esc(v.deal_value || '')}"></div>
        <div><label class="lbl" for="ld-ref">Người giới thiệu</label><input id="ld-ref" class="inp" data-f="referred_by" value="${esc(v.referred_by || '')}"></div>
        <div><label class="lbl" for="ld-utm">Chiến dịch (UTM campaign)</label><input id="ld-utm" class="inp" data-f="utm_campaign" value="${esc(v.utm_campaign || '')}"></div>
      </div>
      <div class="mt-3"><label class="lbl" for="ld-notes">Ghi chú</label><textarea id="ld-notes" class="txt" rows="3" data-f="notes">${esc(v.notes || '')}</textarea></div>
      ${l ? `<div class="mt-3 grid sm:grid-cols-2 gap-3">
        <div><label class="lbl" for="ld-status">Tầng phễu</label><select id="ld-status" class="sel" data-status>${stages.map((s) => `<option value="${s.key}" ${s.key === v.status ? 'selected' : ''}>${esc(s.label)}</option>`).join('')}</select></div>
        <div data-lost-row class="${v.status === 'lost' ? '' : 'hidden'}"><label class="lbl" for="ld-lost">Lý do mất</label><input id="ld-lost" class="inp" data-lost value="${esc(v.lost_reason || '')}" placeholder="vd: Chê giá, chọn đối thủ, chưa cần"></div>
      </div>` : ''}
      <div class="mt-4 rounded-xl border border-slate-700 p-3">
        <div class="text-sm font-semibold mb-1"><i class="fa-solid fa-user-shield text-sky-400"></i> Đồng ý nhận tiếp thị</div>
        ${v.consent_marketing ? `<p class="text-sm text-emerald-300">Khách đã đồng ý lúc ${esc(App.dt(v.consent_at))} qua ${esc(v.consent_source || '')}.</p>
            <p class="text-xs text-slate-400 mt-1">Nội dung đồng ý: “${esc(v.consent_text || '')}”</p>
            <button type="button" class="btn-danger btn-sm mt-2" data-act="withdraw">Khách rút lại đồng ý</button>`
          : `<label class="flex items-start gap-2 text-sm"><input type="checkbox" class="accent-sky-500 mt-1" data-consent> <span>Khách đã đồng ý rõ ràng nhận thông tin tiếp thị (không đánh dấu thay khách).</span></label>
            <input class="inp mt-2 hidden" data-consent-text placeholder="Khách đồng ý điều gì, qua kênh nào? vd: Nhắn Zalo 12/11: “Ok gửi ưu đãi cho chị”">
            <p class="help">Chỉ khách đã đồng ý mới được đưa vào danh sách gửi tiếp thị (xuất CSV “đã đồng ý”, chuỗi chăm sóc).</p>`}
      </div>`;
  }

  function openLead(lead, stages, onChange) {
    const body = document.createElement('div');
    body.innerHTML = leadForm(lead, stages);
    const consent = body.querySelector('[data-consent]');
    if (consent) consent.addEventListener('change', () => body.querySelector('[data-consent-text]').classList.toggle('hidden', !consent.checked));
    const statusSel = body.querySelector('[data-status]');
    if (statusSel) statusSel.addEventListener('change', () => body.querySelector('[data-lost-row]').classList.toggle('hidden', statusSel.value !== 'lost'));

    const collect = () => {
      const out = {};
      App.$$('[data-f]', body).forEach((x) => { out[x.dataset.f] = x.value.trim(); });
      out.deal_value = out.deal_value === '' ? 0 : Number(out.deal_value);
      if (consent && consent.checked) {
        out.consent_marketing = true;
        out.consent_text = body.querySelector('[data-consent-text]').value.trim();
        out.consent_source = 'Nhập tay';
      }
      return out;
    };

    const actions = [];
    if (lead) {
      actions.push({ label: '<i class="fa-regular fa-trash-can"></i> Xóa', cls: 'btn-danger', onClick: async ({ close }) => {
        if (!(await App.confirm(`Xóa khách “${lead.full_name}”? Dữ liệu cá nhân sẽ bị xóa hẳn.`, { danger: true, okLabel: 'Xóa' }))) return true;
        await App.del('/api/leads/' + lead.id);
        App.toast('Đã xóa khách.');
        close();
        onChange();
        return true;
      } });
    }
    actions.push({ label: lead ? '<i class="fa-solid fa-floppy-disk"></i> Lưu' : '<i class="fa-solid fa-user-plus"></i> Thêm khách', cls: 'btn-primary', onClick: async () => {
      const data = collect();
      if (!data.full_name) { App.toast('Nhập họ tên.', 'warn'); return true; }
      if (!data.phone && !data.email) { App.toast('Cần số điện thoại hoặc email.', 'warn'); return true; }
      if (data.consent_marketing && !data.consent_text) { App.toast('Ghi lại nội dung khách đã đồng ý để kiểm chứng được.', 'warn'); return true; }
      if (lead) {
        await App.patch('/api/leads/' + lead.id, data);
        const to = statusSel.value;
        if (to !== lead.status) await App.patch(`/api/leads/${lead.id}/status`, { status: to, lost_reason: body.querySelector('[data-lost]').value });
        App.toast('Đã lưu.');
      } else {
        await App.post('/api/leads', data);
        App.toast('Đã thêm khách.');
      }
      onChange();
      return false;
    } });

    const m = App.modal({ title: lead ? lead.full_name : 'Thêm khách hàng', body, actions });
    App.on(body, {
      withdraw: async () => {
        if (!(await App.confirm('Ghi nhận khách rút lại đồng ý? Khách sẽ bị loại khỏi danh sách gửi tiếp thị.', { okLabel: 'Ghi nhận' }))) return;
        await App.patch('/api/leads/' + lead.id, { consent_marketing: false });
        App.toast('Đã ghi nhận rút đồng ý.');
        m.close();
        onChange();
      },
    });
  }

  async function openEmbed() {
    const info = await App.get('/api/settings/ingest');
    const url = location.origin + info.path;
    const html = `<form id="mos-lead-form">
  <input name="full_name" placeholder="Họ tên" required>
  <input name="phone" placeholder="Số điện thoại" required>
  <input name="product_interest" placeholder="Bạn quan tâm sản phẩm nào?">
  <label><input type="checkbox" name="consent_marketing" value="true">
    Tôi đồng ý nhận thông tin ưu đãi qua điện thoại/Zalo. Có thể từ chối bất cứ lúc nào.</label>
  <button type="submit">Gửi</button>
</form>
<script>
document.getElementById('mos-lead-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  var f = new FormData(this), data = Object.fromEntries(f.entries());
  data.consent_marketing = f.get('consent_marketing') === 'true';
  data.consent_text = data.consent_marketing ? this.querySelector('label').innerText.trim() : '';
  var p = new URLSearchParams(location.search);
  ['utm_source', 'utm_medium', 'utm_campaign'].forEach(function (k) { if (p.get(k)) data[k] = p.get(k); });
  var res = await fetch('${url}', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  this.innerHTML = res.ok ? 'Cảm ơn bạn! Chúng tôi sẽ liên hệ sớm.' : 'Gửi chưa được, vui lòng thử lại.';
});
</script>`;
    const body = document.createElement('div');
    body.innerHTML = `
      <p class="text-sm text-slate-300">Dán đoạn mã này vào landing page/website. Khách gửi form sẽ vào cột “Mới” trong CRM, kèm nguồn UTM và việc có đồng ý tiếp thị hay không.</p>
      <label class="lbl mt-4" for="emb-url">Địa chỉ nhận lead (giữ bí mật)</label>
      <div class="flex gap-2"><input id="emb-url" class="inp font-mono text-xs" readonly value="${esc(url)}"><button type="button" class="btn-ghost btn-sm" data-act="copy-url"><i class="fa-regular fa-copy"></i></button></div>
      <label class="lbl mt-4" for="emb-code">Mã form mẫu</label>
      <textarea id="emb-code" class="txt font-mono text-xs" rows="14" readonly>${esc(html)}</textarea>
      <div class="flex flex-wrap gap-2 mt-2"><button type="button" class="btn-soft btn-sm" data-act="copy-code"><i class="fa-regular fa-copy"></i> Sao chép mã</button>
      <button type="button" class="btn-danger btn-sm" data-act="rotate"><i class="fa-solid fa-rotate"></i> Đổi địa chỉ (vô hiệu địa chỉ cũ)</button></div>
      <p class="help mt-3">Ô đồng ý phải để trống mặc định và khách tự tích. Giới hạn 30 lần gửi/10 phút mỗi IP để chống spam.</p>`;
    const m = App.modal({ title: 'Nhận lead từ form bên ngoài', body, wide: true });
    App.on(body, {
      'copy-url': () => App.copy(url),
      'copy-code': () => App.copy(html),
      rotate: async () => {
        if (!(await App.confirm('Form đang dùng địa chỉ cũ sẽ ngừng nhận lead. Tiếp tục?', { danger: true, okLabel: 'Đổi địa chỉ' }))) return;
        await App.post('/api/settings/ingest/rotate');
        m.close();
        App.toast('Đã đổi địa chỉ. Cập nhật lại mã trên website.');
        openEmbed();
      },
    });
  }

  App.views.leads = { render };
})();
