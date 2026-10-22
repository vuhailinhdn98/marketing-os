/* Growth Console: tổng quan MER/ROAS/CAC, nhập số liệu & CSV, ngân sách, UTM, thử nghiệm, máy tính marketing. */
(function () {
  'use strict';
  const App = window.App;
  const { esc, ui } = App;

  const TABS = [
    { id: 'overview', label: 'Tổng quan', icon: 'fa-gauge' },
    { id: 'data', label: 'Nhập số liệu', icon: 'fa-table' },
    { id: 'budget', label: 'Ngân sách', icon: 'fa-coins' },
    { id: 'utm', label: 'Link UTM', icon: 'fa-link' },
    { id: 'experiments', label: 'Thử nghiệm', icon: 'fa-flask' },
    { id: 'calc', label: 'Máy tính', icon: 'fa-calculator' },
  ];
  const PROGRAMS = ['Quảng cáo trả phí', 'Content', 'Sự kiện', 'PR', 'Branding & Creative', 'Product Marketing', 'Khác'];
  const EXP_LABEL = { planned: 'Kế hoạch', running: 'Đang chạy', done: 'Hoàn tất', stopped: 'Đã dừng' };
  const EXP_TONE = { planned: 'chip-mute', running: 'chip-info', done: 'chip-ok', stopped: 'chip-bad' };
  const KIND_LABEL = { ads: 'Quảng cáo', sales: 'Bán hàng', web: 'Website (GA4)', social: 'Mạng xã hội', email: 'Email', seo: 'SEO (Search Console)', spend: 'Chi phí', leads: 'Lead' };

  const field = (name, label, type = 'number', extra = '') => `<div><label class="lbl" for="g-${name}">${esc(label)}</label>
    <input id="g-${name}" name="${name}" type="${type}" ${type === 'number' ? 'min="0" step="any" inputmode="decimal"' : ''} class="inp" ${extra}></div>`;
  const formData = (form) => {
    const out = {};
    App.$$('[name]', form).forEach((x) => {
      if (x.type === 'checkbox') out[x.name] = x.checked;
      else out[x.name] = x.value.trim();
    });
    return out;
  };

  function tabbar(active, params) {
    return `<div class="tabbar mb-4" role="tablist">${TABS.map((t) => `<a href="#/growth/${t.id}" role="tab" class="tab ${t.id === active ? 'active' : ''}" aria-selected="${t.id === active}"><i class="fa-solid ${t.icon} mr-1"></i>${esc(t.label)}</a>`).join('')}</div>`;
  }

  // ------------------------------------------------------------------ Tổng quan
  async function overview(box, params) {
    const days = [7, 30, 90].includes(Number(params.days)) ? Number(params.days) : 30;
    const [s, imp] = await Promise.all([App.get('/api/growth/summary?days=' + days), App.get('/api/growth/imported?days=' + Math.max(days, 30))]);
    const u = s.unit_economics;
    const roasTone = u.ads_profitable === undefined ? '' : (u.ads_profitable ? 'text-emerald-300' : 'text-rose-300');
    const contribTone = u.contribution_after_marketing === null ? '' : (u.contribution_after_marketing >= 0 ? 'text-emerald-300' : 'text-rose-300');
    box.innerHTML = `
      <div class="space-y-5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-sm text-slate-400">Khoảng thời gian:</span>
          ${[7, 30, 90].map((d) => `<a href="#/growth/overview?days=${d}" class="tab ${d === days ? 'active' : ''}">${d} ngày</a>`).join('')}
          <span class="text-xs text-slate-500 ml-auto">${esc(App.dateVi(s.period.start))} – ${esc(App.dateVi(s.period.end))} · ${s.entries} dòng số liệu</span>
        </div>
        ${!s.entries ? ui.empty('fa-chart-pie', 'Chưa có số liệu trong khoảng này', 'Nhập chi phí, doanh thu, số đơn, khách mới theo ngày hoặc tuần (tab Nhập số liệu), hoặc nhập CSV xuất từ nền tảng.', '<a href="#/growth/data" class="btn-primary btn-sm">Nhập số liệu</a>') : `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          ${ui.kpi('Doanh thu', App.money(u.revenue), `${App.num(u.orders)} đơn · AOV ${App.money(u.aov)}`)}
          ${ui.kpi('Tổng chi marketing', App.money(u.total_marketing_cost), `Quảng cáo ${App.money(u.ad_spend)}`)}
          ${ui.kpi('MER (doanh thu ÷ tổng chi)', u.mer === null ? '—' : App.num(u.mer, 2) + '×', 'Chỉ số sức khỏe tổng')}
          ${ui.kpi('ROAS quảng cáo', u.roas === null ? '—' : App.num(u.roas, 2) + '×', u.breakeven_roas ? `Hòa vốn khi ≥ ${App.num(u.breakeven_roas, 2)}×` : 'Cần biên lãi gộp', roasTone)}
          ${ui.kpi('Lãi gộp sau marketing', App.money(u.contribution_after_marketing), u.gross_margin_pct ? `Biên lãi gộp ${App.pct(u.gross_margin_pct)}` : 'Cần biên lãi gộp trong hồ sơ', contribTone)}
          ${ui.kpi('CAC (chi phí/khách mới)', App.money(u.cac), u.new_customers ? `${App.num(u.new_customers)} khách mới` : 'Cần nhập số khách mới')}
          ${ui.kpi('Chi phí mỗi đơn', App.money(u.cost_per_order), 'Không phải CAC')}
          ${ui.kpi('Chi phí mỗi lead', App.money(u.cpl), `${App.num(u.leads)} lead`)}
        </div>
        ${u.notes && u.notes.length ? `<div class="rounded-xl border border-slate-700 bg-slate-900/60 p-3 text-xs text-slate-300 space-y-1">${u.notes.map((n) => `<div><i class="fa-solid fa-circle-info text-sky-400"></i> ${esc(n)}</div>`).join('')}</div>` : ''}
        <div class="card"><h3 class="font-bold mb-3">Doanh thu và chi quảng cáo theo ngày</h3><div class="h-64"><canvas data-chart aria-label="Biểu đồ doanh thu và chi quảng cáo"></canvas></div></div>
        <div class="card"><h3 class="font-bold mb-3">Theo kênh</h3><div class="scroll-x"><table class="tbl"><thead><tr><th>Kênh</th><th class="num">Chi QC</th><th class="num">Chi khác</th><th class="num">Doanh thu</th><th class="num">Đơn</th><th class="num">Lead</th><th class="num">MER</th></tr></thead><tbody>
          ${s.channels.map((c) => `<tr><td>${esc(c.channel)}</td><td class="num">${App.money(c.ad_spend)}</td><td class="num">${App.money(c.other_marketing_cost)}</td><td class="num">${App.money(c.revenue)}</td><td class="num">${App.num(c.orders_count)}</td><td class="num">${App.num(c.leads_count)}</td><td class="num">${c.mer === null ? '—' : App.num(c.mer, 2) + '×'}</td></tr>`).join('')}
        </tbody></table></div></div>`}
        ${importedHtml(imp)}
      </div>`;
    const canvas = box.querySelector('[data-chart]');
    if (canvas && s.series.length) {
      ui.chart(canvas, {
        type: 'line',
        data: { labels: s.series.map((p) => App.dateVi(p.date).slice(0, 5)),
          datasets: [
            { label: 'Doanh thu', data: s.series.map((p) => p.revenue), borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,.15)', fill: true, tension: 0.25, pointRadius: 2 },
            { label: 'Chi quảng cáo', data: s.series.map((p) => p.ad_spend), borderColor: '#fb7185', backgroundColor: 'transparent', tension: 0.25, pointRadius: 2 },
          ] },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
          plugins: { tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${App.money(c.parsed.y)}` } } },
          scales: { y: { ticks: { callback: (v) => App.compact(v) } } } },
      });
    }
    const salesCanvas = box.querySelector('[data-sales-chart]');
    if (salesCanvas && imp.sales) {
      const f = imp.sales.forecast_30d;
      const labels = imp.sales.series.map((p) => p.date).concat(f ? f.points.map((p) => p.date) : []);
      ui.chart(salesCanvas, {
        type: 'line',
        data: { labels: labels.map((d) => App.dateVi(d).slice(0, 5)),
          datasets: [
            { label: 'Doanh thu thực tế', data: imp.sales.series.map((p) => p.revenue), borderColor: '#34d399', pointRadius: 0, tension: 0.2 },
            ...(f ? [{ label: 'Dự báo tuyến tính (tham khảo)', data: imp.sales.series.map(() => null).concat(f.points.map((p) => p.value)), borderColor: '#fbbf24', borderDash: [6, 4], pointRadius: 0 }] : []),
          ] },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
          scales: { y: { ticks: { callback: (v) => App.compact(v) } } } },
      });
    }
  }

  function importedHtml(r) {
    const parts = [];
    if (r.ads) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Quảng cáo (từ CSV)</h3><div class="scroll-x"><table class="tbl"><thead><tr><th>Nền tảng · chiến dịch</th><th class="num">Chi</th><th class="num">CTR</th><th class="num">CPC</th><th class="num">CPA</th><th class="num">ROAS</th></tr></thead><tbody>
        ${r.ads.slice(0, 20).map((a) => `<tr><td>${esc(a.campaign)}</td><td class="num">${App.money(a.spend)}</td><td class="num">${App.pct(a.ctr_pct)}</td><td class="num">${App.money(a.cpc)}</td><td class="num">${App.money(a.cpa)}</td><td class="num">${a.roas === null ? '—' : App.num(a.roas, 2) + '×'}</td></tr>`).join('')}
        </tbody></table></div>
        ${r.ads_spend_anomalies && r.ads_spend_anomalies.length ? `<p class="text-xs text-amber-300 mt-2"><i class="fa-solid fa-triangle-exclamation"></i> Chi tiêu bất thường (lệch ≥30% so với TB 7 ngày): ${r.ads_spend_anomalies.slice(-5).map((x) => `${esc(App.dateVi(x.date))} (${x.change_pct > 0 ? '+' : ''}${App.num(x.change_pct, 1)}%)`).join(', ')}</p>` : ''}</div>`);
    }
    if (r.sales) {
      const s = r.sales;
      const f = s.forecast_30d;
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Bán hàng (từ CSV)</h3>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          ${ui.kpi('Doanh thu', App.money(s.revenue))}${ui.kpi('Đơn', App.num(s.orders))}${ui.kpi('Khách', App.num(s.customers), `${App.num(s.new_customers)} khách mới`)}
          ${ui.kpi('AOV', App.money(s.aov))}${ui.kpi('Đơn/khách', App.num(s.orders_per_customer, 2))}
        </div>
        <div class="h-56"><canvas data-sales-chart aria-label="Biểu đồ doanh thu bán hàng"></canvas></div>
        ${f ? `<p class="text-xs text-amber-200 mt-2">${esc(f.label)} Tổng 30 ngày tới ≈ ${App.money(f.total_next)} · R² = ${App.num(f.r2, 2)}.</p>` : '<p class="help mt-2">Cần ít nhất 14 ngày dữ liệu để vẽ dự báo.</p>'}
        ${s.anomalies.length ? `<p class="text-xs text-amber-300 mt-1"><i class="fa-solid fa-triangle-exclamation"></i> Ngày bất thường: ${s.anomalies.slice(-6).map((x) => `${esc(App.dateVi(x.date))} (${x.change_pct > 0 ? '+' : ''}${App.num(x.change_pct, 1)}%)`).join(', ')}</p>` : ''}
        <div class="mt-3 text-xs text-slate-400">Theo kênh: ${s.by_channel.map((c) => `${esc(c.channel)} ${App.money(c.revenue)}`).join(' · ')}</div></div>`);
    }
    if (r.web) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Website (từ CSV)</h3><div class="scroll-x"><table class="tbl"><thead><tr><th>Nguồn / kênh</th><th class="num">Phiên</th><th class="num">Người dùng</th><th class="num">Chuyển đổi</th><th class="num">CVR</th><th class="num">Doanh thu</th></tr></thead><tbody>
        ${r.web.slice(0, 15).map((w) => `<tr><td>${esc(w.source_medium)}</td><td class="num">${App.num(w.sessions)}</td><td class="num">${App.num(w.users)}</td><td class="num">${App.num(w.conversions)}</td><td class="num">${App.pct(w.cvr_pct)}</td><td class="num">${App.money(w.revenue)}</td></tr>`).join('')}
        </tbody></table></div></div>`);
    }
    if (r.social) {
      const row = (p) => `<tr><td>${esc(App.dateVi(p.date))}</td><td>${esc(p.platform)}</td><td>${esc(p.post_type)}</td><td class="num">${App.num(p.reach)}</td><td class="num">${App.pct(p.engagement_rate_pct)}</td></tr>`;
      parts.push(`<div class="card"><h3 class="font-bold mb-1">Mạng xã hội (từ CSV)</h3><p class="text-xs text-slate-400 mb-3">${r.social.posts} bài. Học từ bài tốt nhất, xem lại bài kém nhất.</p>
        <div class="grid md:grid-cols-2 gap-4"><div><div class="text-xs font-semibold text-emerald-300 mb-1">Top 3 tương tác</div><div class="scroll-x"><table class="tbl"><tbody>${r.social.top3.map(row).join('')}</tbody></table></div></div>
        <div><div class="text-xs font-semibold text-rose-300 mb-1">Thấp nhất</div><div class="scroll-x"><table class="tbl"><tbody>${r.social.bottom3.map(row).join('') || '<tr><td class="text-slate-500">—</td></tr>'}</tbody></table></div></div></div></div>`);
    }
    if (r.email) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Email (từ CSV)</h3><div class="scroll-x"><table class="tbl"><thead><tr><th>Chiến dịch</th><th class="num">Mở</th><th class="num">CTOR</th><th class="num">Hủy đăng ký</th><th class="num">Doanh thu</th></tr></thead><tbody>
        ${r.email.map((e) => `<tr><td>${esc(e.campaign)}</td><td class="num">${App.pct(e.open_rate_pct)}</td><td class="num">${App.pct(e.ctor_pct)}</td><td class="num">${App.pct(e.unsub_rate_pct)}</td><td class="num">${App.money(e.revenue)}</td></tr>`).join('')}
        </tbody></table></div></div>`);
    }
    if (r.seo) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Từ khóa SEO (từ CSV)</h3><div class="scroll-x"><table class="tbl"><thead><tr><th>Truy vấn</th><th class="num">Hiển thị</th><th class="num">Click</th><th class="num">Vị trí TB</th></tr></thead><tbody>
        ${r.seo.slice(0, 15).map((q) => `<tr><td>${esc(q.query)}</td><td class="num">${App.num(q.impressions)}</td><td class="num">${App.num(q.clicks)}</td><td class="num">${App.num(q.avg_position, 1)}</td></tr>`).join('')}
        </tbody></table></div></div>`);
    }
    if (r.spend) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Chi phí theo hạng mục (từ CSV)</h3><ul class="text-sm space-y-1">${r.spend.map((x) => `<li class="flex justify-between"><span>${esc(x.category)}</span><span class="num">${App.money(x.amount)}</span></li>`).join('')}</ul></div>`);
    }
    if (r.leads) {
      parts.push(`<div class="card"><h3 class="font-bold mb-3">Lead theo giai đoạn (từ CSV)</h3><ul class="text-sm space-y-1">${r.leads.map((x) => `<li class="flex justify-between"><span>${esc(x.stage)}</span><span class="num">${App.num(x.count)}</span></li>`).join('')}</ul></div>`);
    }
    if (!parts.length) return '';
    return `<div class="space-y-5"><h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider pt-2">Dữ liệu nhập từ nền tảng</h2>${parts.join('')}</div>`;
  }

  // ------------------------------------------------------------------ Nhập số liệu
  async function dataTab(box) {
    const [m, im] = await Promise.all([App.get('/api/metrics?days=90'), App.get('/api/imports')]);
    const channels = ((App.state.context && App.state.context.context.channels_active) || []);
    box.innerHTML = `
      <div class="grid xl:grid-cols-5 gap-5">
        <div class="xl:col-span-2 space-y-5">
          <form class="card space-y-3" data-metric-form novalidate>
            <h3 class="font-bold">Nhập số liệu (ngày hoặc cả tuần)</h3>
            <p class="text-xs text-slate-400">Nhập theo một kênh mỗi dòng nếu có thể. Tách doanh thu do quảng cáo để tính ROAS; nhập số khách mới để tính CAC đúng.</p>
            <div class="grid grid-cols-2 gap-3">
              ${field('date', 'Ngày', 'date', `value="${App.today()}" required`)}
              <div><label class="lbl" for="g-channel">Kênh</label><input id="g-channel" name="channel" class="inp" list="g-channels" placeholder="Facebook, TikTok…"><datalist id="g-channels">${channels.map((c) => `<option value="${esc(c)}">`).join('')}</datalist></div>
              ${field('ad_spend', 'Chi quảng cáo (VND)')}
              ${field('other_marketing_cost', 'Chi marketing khác (VND)')}
              ${field('revenue', 'Tổng doanh thu (VND)')}
              ${field('ad_attributed_revenue', 'Doanh thu từ quảng cáo', 'number', 'placeholder="Để trống nếu không biết"')}
              ${field('orders_count', 'Số đơn')}
              ${field('new_customers', 'Khách mới', 'number', 'placeholder="Để trống nếu không biết"')}
              ${field('leads_count', 'Số lead')}
              ${field('messages_count', 'Tin nhắn')}
              ${field('impressions', 'Lượt hiển thị')}
              ${field('clicks', 'Lượt click')}
            </div>
            <div><label class="lbl" for="g-campaign">Chiến dịch</label><input id="g-campaign" name="campaign" class="inp"></div>
            <div><label class="lbl" for="g-notes">Ghi chú</label><input id="g-notes" name="notes" class="inp"></div>
            <button type="submit" class="btn-primary w-full justify-center"><i class="fa-solid fa-plus"></i> Lưu số liệu</button>
          </form>

          <form class="card space-y-3" data-import-form novalidate>
            <h3 class="font-bold">Nhập file CSV từ nền tảng</h3>
            <p class="text-xs text-slate-400">Xuất CSV từ Meta/Google Ads, GA4, Search Console, sàn TMĐT… Đặt tên file bắt đầu bằng <code>ads_</code>, <code>sales_</code>, <code>web_</code>… hoặc chọn loại. Hỗ trợ số kiểu 1.234.567 và 1,234,567.</p>
            <div><label class="lbl" for="g-kind">Loại dữ liệu</label><select id="g-kind" class="sel" name="kind"><option value="">Tự nhận diện theo tên file</option>${im.kinds.map((k) => `<option value="${esc(k.kind)}">${esc(KIND_LABEL[k.kind] || k.kind)} — ${esc(k.description)}</option>`).join('')}</select>
              <p class="help" data-cols></p></div>
            <div><label class="lbl" for="g-file">File CSV (tối đa 5 MB)</label><input id="g-file" type="file" accept=".csv,text/csv" class="block w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"></div>
            <label class="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" name="replace_period" class="accent-sky-500" checked> Thay dữ liệu cũ cùng loại trong cùng khoảng ngày (tránh nhân đôi)</label>
            <button type="submit" class="btn-soft w-full justify-center"><i class="fa-solid fa-file-import"></i> Nhập file</button>
            <div data-import-result></div>
          </form>
        </div>

        <div class="xl:col-span-3 space-y-5">
          <div class="card">
            <h3 class="font-bold mb-3">Số liệu đã nhập (90 ngày)</h3>
            ${m.items.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>Ngày</th><th>Kênh</th><th class="num">Chi QC</th><th class="num">Doanh thu</th><th class="num">DT từ QC</th><th class="num">Đơn</th><th class="num">Khách mới</th><th class="num">Lead</th><th></th></tr></thead><tbody>
              ${m.items.map((r) => `<tr><td class="whitespace-nowrap">${esc(App.dateVi(r.date))}</td><td>${esc(r.channel || '—')}${r.campaign ? `<div class="text-[11px] text-slate-500">${esc(r.campaign)}</div>` : ''}</td>
              <td class="num">${App.money(r.ad_spend)}</td><td class="num">${App.money(r.revenue)}</td><td class="num">${r.ad_attributed_revenue === null ? '—' : App.money(r.ad_attributed_revenue)}</td>
              <td class="num">${App.num(r.orders_count)}</td><td class="num">${r.new_customers === null ? '—' : App.num(r.new_customers)}</td><td class="num">${App.num(r.leads_count)}</td>
              <td><button type="button" class="text-slate-500 hover:text-rose-400" data-act="del-metric" data-id="${r.id}" aria-label="Xóa dòng"><i class="fa-regular fa-trash-can"></i></button></td></tr>`).join('')}
            </tbody></table></div>` : '<p class="text-sm text-slate-400">Chưa có dữ liệu.</p>'}
          </div>
          <div class="card">
            <h3 class="font-bold mb-3">Lịch sử nhập file</h3>
            ${im.imports.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>File</th><th>Loại</th><th class="num">Dòng</th><th class="num">Bỏ qua</th><th>Lúc</th></tr></thead><tbody>
              ${im.imports.map((x) => `<tr><td class="break-all">${esc(x.filename)}</td><td>${esc(KIND_LABEL[x.kind] || x.kind)}</td><td class="num">${App.num(x.row_count)}</td><td class="num">${App.num((x.errors || []).length)}</td><td class="whitespace-nowrap text-xs">${esc(App.dt(x.created_at))}</td></tr>`).join('')}
            </tbody></table></div>` : '<p class="text-sm text-slate-400">Chưa nhập file nào.</p>'}
          </div>
        </div>
      </div>`;

    const kindSel = box.querySelector('[name="kind"]');
    const showCols = () => {
      const k = im.kinds.find((x) => x.kind === kindSel.value);
      box.querySelector('[data-cols]').textContent = k ? 'Cột bắt buộc: ' + k.required_columns.join(', ') : '';
    };
    kindSel.addEventListener('change', showCols);

    box.querySelector('[data-metric-form]').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      const d = formData(e.target);
      ['ad_attributed_revenue', 'new_customers'].forEach((k) => { if (d[k] === '') d[k] = null; });
      App.busy(btn, true, 'Đang lưu…');
      try {
        await App.post('/api/metrics', d);
        App.toast('Đã lưu số liệu.');
        App.render();
      } catch (err) {
        App.toast(err.message, 'bad');
      } finally {
        App.busy(btn, false);
      }
    });

    box.querySelector('[data-import-form]').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const btn = form.querySelector('[type=submit]');
      const file = form.querySelector('#g-file').files[0];
      const out = form.querySelector('[data-import-result]');
      if (!file) { App.toast('Chọn file CSV.', 'warn'); return; }
      if (file.size > 5 * 1024 * 1024) { App.toast('File lớn hơn 5 MB. Hãy tách theo tháng.', 'warn'); return; }
      App.busy(btn, true, 'Đang nhập…');
      try {
        const content = await file.text();
        const r = await App.post('/api/imports', { filename: file.name, kind: kindSel.value, content, replace_period: form.querySelector('[name=replace_period]').checked });
        out.innerHTML = `<div class="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm">
          <div class="text-emerald-300 font-semibold"><i class="fa-solid fa-check"></i> Đã nhập ${App.num(r.rows)} dòng ${esc(KIND_LABEL[r.kind] || r.kind)} (${esc(App.dateVi(r.date_range[0]))} – ${esc(App.dateVi(r.date_range[1]))}).</div>
          ${r.skipped ? `<div class="text-amber-300 text-xs mt-1">Bỏ qua ${r.skipped} dòng lỗi:</div><ul class="text-xs text-slate-400 list-disc ml-5">${r.errors.slice(0, 8).map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
          <a href="#/growth/overview" class="text-sky-400 text-xs underline">Xem báo cáo</a></div>`;
        App.toast('Đã nhập file.');
      } catch (err) {
        out.innerHTML = `<div class="rounded-xl border border-rose-500/40 bg-rose-500/5 p-3 text-sm text-rose-200">${esc(err.message)}</div>`;
      } finally {
        App.busy(btn, false);
      }
    });

    App.on(box, {
      'del-metric': async (btn) => {
        if (!(await App.confirm('Xóa dòng số liệu này?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del('/api/metrics/' + btn.dataset.id);
        btn.closest('tr').remove();
        App.toast('Đã xóa.');
      },
    });
  }

  // ------------------------------------------------------------------ Ngân sách
  async function budgetTab(box, params) {
    const month = /^\d{4}-\d{2}$/.test(params.month || '') ? params.month : App.month();
    const b = await App.get('/api/budget?month=' + month);
    const pace = b.pacing;
    box.innerHTML = `
      <div class="space-y-5">
        <div class="flex flex-wrap items-center gap-2">
          <label class="text-sm text-slate-400" for="b-month">Tháng</label>
          <input id="b-month" type="month" class="inp w-44" value="${esc(month)}" data-month>
          <a href="#/studio/budget_plan" class="btn-soft btn-sm ml-auto"><i class="fa-solid fa-wand-magic-sparkles"></i> Lập ngân sách bằng AI</a>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          ${ui.kpi('Dự kiến', App.money(b.projected_total))}
          ${ui.kpi('Thực chi', App.money(b.actual_total))}
          ${ui.kpi('Chênh lệch', App.money(b.variance), b.variance > 0 ? 'Vượt kế hoạch' : 'Trong kế hoạch', b.variance > 0 ? 'text-rose-300' : 'text-emerald-300')}
          ${ui.kpi('Nhịp chi', pace && pace.pacing_pct !== null ? App.pct(pace.pacing_pct) : '—', pace ? esc(pace.status || '') + (pace.projected_month_end ? ` · cuối tháng ≈ ${App.money(pace.projected_month_end)}` : '') : 'Chỉ tính cho tháng hiện tại')}
        </div>
        <div class="grid xl:grid-cols-3 gap-5">
          <div class="xl:col-span-2 card">
            <h3 class="font-bold mb-3">Hạng mục</h3>
            ${b.lines.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>Chương trình</th><th>Hạng mục</th><th class="num">Dự kiến</th><th class="num">Thực chi</th><th class="num">Chênh</th><th></th></tr></thead><tbody>
              ${b.lines.map((l) => `<tr><td class="text-xs">${esc(l.program)}</td><td>${esc(l.item)}<div class="text-[11px] text-slate-500">${App.money(l.unit_price)} × ${App.num(l.quantity, 2)} ${esc(l.unit || '')}${l.notes ? ' · ' + esc(l.notes) : ''}</div></td>
                <td class="num">${App.money(l.projected_total)}</td>
                <td class="num"><input type="number" min="0" step="1000" class="inp w-32 text-right py-1" value="${esc(l.actual_total || 0)}" data-actual="${l.id}" aria-label="Thực chi"></td>
                <td class="num ${l.variance > 0 ? 'text-rose-300' : ''}">${App.money(l.variance)}</td>
                <td class="whitespace-nowrap"><button type="button" class="text-sky-400 mr-2" data-act="save-actual" data-id="${l.id}" aria-label="Lưu thực chi"><i class="fa-solid fa-floppy-disk"></i></button><button type="button" class="text-slate-500 hover:text-rose-400" data-act="del-line" data-id="${l.id}" aria-label="Xóa"><i class="fa-regular fa-trash-can"></i></button></td></tr>`).join('')}
            </tbody></table></div>
            <div class="mt-4 scroll-x"><table class="tbl"><thead><tr><th>Theo chương trình</th><th class="num">Dự kiến</th><th class="num">Thực chi</th><th class="num">Chênh</th></tr></thead><tbody>
              ${b.programs.filter((p) => p.projected || p.actual).map((p) => `<tr><td>${esc(p.program)}</td><td class="num">${App.money(p.projected)}</td><td class="num">${App.money(p.actual)}</td><td class="num ${p.variance > 0 ? 'text-rose-300' : ''}">${App.money(p.variance)}</td></tr>`).join('')}
            </tbody></table></div>` : '<p class="text-sm text-slate-400">Chưa có hạng mục cho tháng này.</p>'}
          </div>
          <form class="card space-y-3 h-fit" data-line-form novalidate>
            <h3 class="font-bold">Thêm hạng mục</h3>
            <div><label class="lbl" for="b-program">Chương trình</label><select id="b-program" name="program" class="sel">${PROGRAMS.map((p) => `<option>${esc(p)}</option>`).join('')}</select></div>
            <div><label class="lbl" for="b-item">Hạng mục</label><input id="b-item" name="item" class="inp" placeholder="vd: Quảng cáo tin nhắn Facebook"></div>
            <div class="grid grid-cols-2 gap-3">
              ${field('unit_price', 'Đơn giá (VND)')}
              ${field('quantity', 'Số lượng')}
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div><label class="lbl" for="b-unit">Đơn vị</label><input id="b-unit" name="unit" class="inp" placeholder="ngày, bài, buổi"></div>
              ${field('actual_total', 'Đã chi (VND)')}
            </div>
            <div><label class="lbl" for="b-notes">Ghi chú / KPI</label><input id="b-notes" name="notes" class="inp"></div>
            <button type="submit" class="btn-primary w-full justify-center"><i class="fa-solid fa-plus"></i> Thêm</button>
          </form>
        </div>
      </div>`;

    box.querySelector('[data-month]').addEventListener('change', (e) => { if (e.target.value) location.hash = '#/growth/budget?month=' + e.target.value; });
    box.querySelector('[data-line-form]').addEventListener('submit', async (e) => {
      e.preventDefault();
      const d = formData(e.target);
      if (!d.item) { App.toast('Nhập hạng mục.', 'warn'); return; }
      const btn = e.target.querySelector('[type=submit]');
      App.busy(btn, true);
      try {
        await App.post('/api/budget/lines', { ...d, month });
        App.toast('Đã thêm.');
        App.render();
      } catch (err) {
        App.toast(err.message, 'bad');
      } finally {
        App.busy(btn, false);
      }
    });
    App.on(box, {
      'save-actual': async (btn) => {
        const v = box.querySelector(`[data-actual="${btn.dataset.id}"]`).value;
        await App.patch('/api/budget/lines/' + btn.dataset.id, { actual_total: v === '' ? 0 : Number(v) });
        App.toast('Đã lưu thực chi.');
        App.render();
      },
      'del-line': async (btn) => {
        if (!(await App.confirm('Xóa hạng mục này?', { danger: true, okLabel: 'Xóa' }))) return;
        await App.del('/api/budget/lines/' + btn.dataset.id);
        App.render();
      },
    });
  }

  // ------------------------------------------------------------------ UTM
  async function utmTab(box) {
    const r = await App.get('/api/utm');
    const site = (App.state.context && App.state.context.context.brand && App.state.context.context.brand.website) || '';
    box.innerHTML = `
      <div class="grid xl:grid-cols-3 gap-5">
        <form class="card space-y-3 h-fit" data-utm-form novalidate>
          <h3 class="font-bold">Tạo link có UTM</h3>
          <p class="text-xs text-slate-400">Mỗi bài/quảng cáo một link riêng để biết khách đến từ đâu. Giá trị được chuẩn hóa: chữ thường, không dấu, gạch nối.</p>
          <div><label class="lbl" for="u-base">Link gốc</label><input id="u-base" name="base_url" class="inp" value="${esc(site)}" placeholder="https://…"></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl" for="u-src">Nguồn (source)</label><input id="u-src" name="utm_source" class="inp" list="u-srcs" placeholder="facebook"><datalist id="u-srcs"><option value="facebook"><option value="zalo"><option value="tiktok"><option value="google"><option value="email"></datalist></div>
            <div><label class="lbl" for="u-med">Kênh (medium)</label><input id="u-med" name="utm_medium" class="inp" list="u-meds" placeholder="social"><datalist id="u-meds"><option value="social"><option value="cpc"><option value="email"><option value="sms"><option value="referral"><option value="qr"></datalist></div>
          </div>
          <div><label class="lbl" for="u-camp">Chiến dịch (campaign)</label><input id="u-camp" name="utm_campaign" class="inp" placeholder="ra-mat-t11"></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl" for="u-content">Nội dung (content)</label><input id="u-content" name="utm_content" class="inp" placeholder="video-a"></div>
            <div><label class="lbl" for="u-term">Từ khóa (term)</label><input id="u-term" name="utm_term" class="inp"></div>
          </div>
          <div><label class="lbl" for="u-label">Ghi chú</label><input id="u-label" name="label" class="inp" placeholder="Bài ghim fanpage tuần 1"></div>
          <button type="submit" class="btn-primary w-full justify-center"><i class="fa-solid fa-link"></i> Tạo link</button>
        </form>
        <div class="xl:col-span-2 card">
          <h3 class="font-bold mb-3">Link đã tạo</h3>
          ${r.links.length ? `<ul class="divide-y divide-slate-800">${r.links.map((l) => `<li class="py-2.5 flex gap-3 items-start">
            <div class="flex-1 min-w-0"><div class="text-sm">${esc(l.label || l.utm_campaign)}</div><div class="text-xs text-sky-300 break-all font-mono">${esc(l.full_url)}</div>
            <div class="text-[11px] text-slate-500">${esc(l.utm_source)} / ${esc(l.utm_medium)} · ${esc(App.dt(l.created_at))}</div></div>
            <button type="button" class="btn-ghost btn-sm" data-act="copy" data-url="${esc(l.full_url)}" aria-label="Sao chép"><i class="fa-regular fa-copy"></i></button>
            <button type="button" class="btn-ghost btn-sm" data-act="del" data-id="${l.id}" aria-label="Xóa"><i class="fa-regular fa-trash-can"></i></button></li>`).join('')}</ul>`
            : '<p class="text-sm text-slate-400">Chưa có link nào.</p>'}
        </div>
      </div>`;
    box.querySelector('[data-utm-form]').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      App.busy(btn, true);
      try {
        const res = await App.post('/api/utm', formData(e.target));
        App.copy(res.full_url);
        App.render();
      } catch (err) {
        App.toast(err.message, 'bad');
      } finally {
        App.busy(btn, false);
      }
    });
    App.on(box, {
      copy: (btn) => App.copy(btn.dataset.url),
      del: async (btn) => {
        if (!(await App.confirm('Xóa link này khỏi danh sách? Link đã đăng vẫn hoạt động.', { okLabel: 'Xóa' }))) return;
        await App.del('/api/utm/' + btn.dataset.id);
        App.render();
      },
    });
  }

  // ------------------------------------------------------------------ Thử nghiệm
  async function expTab(box) {
    const r = await App.get('/api/experiments');
    box.innerHTML = `
      <div class="space-y-5">
        <div class="flex flex-wrap gap-2 items-center">
          <p class="text-sm text-slate-400 flex-1">Mỗi tuần chỉ một thử nghiệm ở đúng nút thắt phễu: giả thuyết → thay đổi → chỉ số chính → chỉ số bảo vệ → điều kiện dừng.</p>
          <button type="button" class="btn-primary btn-sm" data-act="new"><i class="fa-solid fa-plus"></i> Thử nghiệm mới</button>
          <a href="#/studio/weekly_loop" class="btn-soft btn-sm"><i class="fa-solid fa-rotate"></i> Gợi ý từ Vòng lặp tuần</a>
        </div>
        ${r.experiments.length ? `<div class="grid md:grid-cols-2 xl:grid-cols-3 gap-3">${r.experiments.map((x) => `<div class="card-tight cursor-pointer hover:border-sky-500/60" data-act="edit" data-id="${x.id}" role="button" tabindex="0">
          <div class="flex items-center gap-2 mb-1"><span class="chip ${EXP_TONE[x.status] || 'chip-mute'}">${esc(EXP_LABEL[x.status] || x.status)}</span>${x.funnel_stage ? `<span class="chip chip-mute">${esc(x.funnel_stage)}</span>` : ''}</div>
          <div class="font-semibold text-sm">${esc(x.title)}</div>
          ${x.hypothesis ? `<div class="text-xs text-slate-400 mt-1 line-clamp-3">${esc(x.hypothesis)}</div>` : ''}
          ${x.primary_metric ? `<div class="text-[11px] text-slate-500 mt-1">Chỉ số chính: ${esc(x.primary_metric)}</div>` : ''}
          ${x.result ? `<div class="text-xs text-emerald-300 mt-1">Kết quả: ${esc(x.result)}</div>` : ''}</div>`).join('')}</div>`
          : ui.empty('fa-flask', 'Chưa có thử nghiệm', 'Tạo tay hoặc lấy từ tác vụ Vòng lặp tuần.')}
      </div>`;
    App.on(box, {
      new: () => openExp(null),
      edit: (el) => openExp(r.experiments.find((x) => String(x.id) === el.dataset.id)),
    });
  }

  function openExp(x) {
    const v = x || { status: 'planned' };
    const f = (name, label, type = 'text') => `<div><label class="lbl" for="x-${name}">${esc(label)}</label>${type === 'textarea'
      ? `<textarea id="x-${name}" name="${name}" class="txt" rows="2">${esc(v[name] || '')}</textarea>`
      : `<input id="x-${name}" name="${name}" type="${type}" class="inp" value="${esc(v[name] || '')}">`}</div>`;
    const body = document.createElement('form');
    body.className = 'space-y-3';
    body.innerHTML = `
      ${f('title', 'Tên thử nghiệm')}
      <div class="grid sm:grid-cols-2 gap-3">
        <div><label class="lbl" for="x-status">Trạng thái</label><select id="x-status" name="status" class="sel">${Object.keys(EXP_LABEL).map((k) => `<option value="${k}" ${k === v.status ? 'selected' : ''}>${EXP_LABEL[k]}</option>`).join('')}</select></div>
        ${f('funnel_stage', 'Bước phễu')}
      </div>
      ${f('hypothesis', 'Giả thuyết (Nếu… thì… vì…)', 'textarea')}
      ${f('change_desc', 'Thay đổi cụ thể', 'textarea')}
      <div class="grid sm:grid-cols-2 gap-3">${f('primary_metric', 'Chỉ số chính')}${f('guardrail_metric', 'Chỉ số bảo vệ')}</div>
      ${f('stop_condition', 'Điều kiện dừng')}
      <div class="grid sm:grid-cols-2 gap-3">${f('start_date', 'Bắt đầu', 'date')}${f('end_date', 'Kết thúc', 'date')}</div>
      ${f('result', 'Kết quả (số liệu)', 'textarea')}
      ${f('learning', 'Bài học', 'textarea')}`;
    const actions = [];
    if (x) {
      actions.push({ label: '<i class="fa-regular fa-trash-can"></i> Xóa', cls: 'btn-danger', onClick: async ({ close }) => {
        if (!(await App.confirm('Xóa thử nghiệm này?', { danger: true, okLabel: 'Xóa' }))) return true;
        await App.del('/api/experiments/' + x.id);
        close();
        App.render();
        return true;
      } });
    }
    actions.push({ label: '<i class="fa-solid fa-floppy-disk"></i> Lưu', cls: 'btn-primary', onClick: async () => {
      const d = formData(body);
      if (!d.title) { App.toast('Nhập tên thử nghiệm.', 'warn'); return true; }
      if (x) await App.patch('/api/experiments/' + x.id, d); else await App.post('/api/experiments', d);
      App.toast('Đã lưu.');
      App.render();
      return false;
    } });
    App.modal({ title: x ? 'Thử nghiệm' : 'Thử nghiệm mới', body, actions });
  }

  // ------------------------------------------------------------------ Máy tính
  function calcTab(box) {
    const ue = (App.state.context && App.state.context.context.unit_economics) || {};
    const card = (id, title, desc, inner) => `<form class="card space-y-3" data-calc="${id}" novalidate><div><h3 class="font-bold">${esc(title)}</h3><p class="text-xs text-slate-400 mt-1">${esc(desc)}</p></div>${inner}
      <button type="submit" class="btn-soft w-full justify-center"><i class="fa-solid fa-equals"></i> Tính</button><div data-out class="text-sm"></div></form>`;
    box.innerHTML = `<div class="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
      ${card('budget-reverse', 'Ngân sách ngược từ mục tiêu', 'Doanh thu mục tiêu ÷ giá trị mỗi khách = số khách mới cần; × CAC = ngân sách (+ dự phòng thử nghiệm).',
        `<div class="grid grid-cols-2 gap-3">${field('target_revenue', 'Doanh thu mục tiêu')}${field('aov', 'Giá trị đơn TB', 'number', `value="${esc(ue.avg_order_value_vnd || '')}"`)}${field('purchases_per_customer', 'Số lần mua/khách', 'number', 'value="1"')}${field('cac', 'CAC (VND)')}${field('test_reserve_pct', 'Dự phòng thử nghiệm %', 'number', 'value="15"')}</div>`)}
      ${card('paid-funnel', 'KPI suy từ phễu quảng cáo', 'Ngân sách ÷ CPM/CPC → hiển thị, click → chuyển đổi. Hoặc ngân sách ÷ chi phí mỗi kết quả.',
        `<div class="grid grid-cols-2 gap-3">${field('budget', 'Ngân sách (VND)')}${field('cost_per_result', 'Chi phí/kết quả')}${field('cpm', 'CPM')}${field('cpc', 'CPC')}${field('ctr_pct', 'CTR %')}${field('cvr_pct', 'Tỉ lệ chuyển đổi %')}</div>`)}
      ${card('ltv', 'LTV, LTV/CAC, thời gian hoàn vốn', 'LTV tính trên lãi gộp (không phải doanh thu). Lấy giá trị đơn và biên lãi từ hồ sơ nếu bỏ trống.',
        `<div class="grid grid-cols-2 gap-3">${field('purchases_per_customer', 'Số lần mua/khách (đời khách)')}${field('cac', 'CAC (VND)')}${field('purchases_per_month', 'Số lần mua/tháng')}${field('aov', 'Giá trị đơn TB')}${field('gross_margin_pct', 'Biên lãi gộp %')}</div>`)}
      ${card('ab-test', 'Kiểm định A/B', 'Kiểm định z hai tỉ lệ, độ tin cậy 95%. Không dừng thử nghiệm sớm chỉ vì thấy chênh.',
        `<div class="grid grid-cols-2 gap-3">${field('visitors_a', 'Lượt xem A')}${field('conv_a', 'Chuyển đổi A')}${field('visitors_b', 'Lượt xem B')}${field('conv_b', 'Chuyển đổi B')}</div>`)}
      ${card('sample-size', 'Cỡ mẫu cần cho A/B', 'Mỗi nhánh cần bao nhiêu lượt để phát hiện mức tăng mong muốn (α 5%, power 80%).',
        `<div class="grid grid-cols-2 gap-3">${field('baseline_pct', 'Tỉ lệ hiện tại %')}${field('lift_pct', 'Mức tăng muốn phát hiện %')}</div>`)}
    </div>`;

    const show = (id, r) => {
      const rows = [];
      if (id === 'budget-reverse') {
        rows.push(['Giá trị mỗi khách', App.money(r.value_per_customer)], ['Số khách mới cần', App.num(r.customers_needed)]);
        if (r.total_budget !== undefined) rows.push(['Ngân sách cơ bản', App.money(r.base_budget)], ['Dự phòng thử nghiệm', App.money(r.test_reserve)], ['Tổng ngân sách', App.money(r.total_budget)]);
      } else if (id === 'paid-funnel') {
        if (r.results !== undefined) rows.push(['Số kết quả dự kiến', App.num(r.results)]);
        if (r.impressions !== undefined) rows.push(['Lượt hiển thị', App.num(r.impressions)]);
        if (r.clicks !== undefined) rows.push(['Lượt click', App.num(r.clicks)]);
        if (r.conversions !== undefined) rows.push(['Chuyển đổi', App.num(r.conversions)]);
        if (rows.length === 0) rows.push(['Kết quả', 'Nhập chi phí mỗi kết quả, hoặc CPM + CTR, hoặc CPC']);
      } else if (id === 'ltv') {
        rows.push(['LTV (lãi gộp)', App.money(r.ltv_gross_profit)], ['Dùng giá trị đơn', App.money(r.aov)], ['Dùng biên lãi', App.pct(r.gross_margin_pct)]);
        if (r.ltv_cac !== undefined) rows.push(['LTV/CAC', r.ltv_cac === null ? '—' : App.num(r.ltv_cac, 2) + (r.ltv_cac >= 3 ? ' (tốt, ≥3)' : ' (dưới 3: cần xem lại)')]);
        if (r.payback_months !== undefined) rows.push(['Hoàn vốn CAC', r.payback_months === null ? '—' : App.num(r.payback_months, 1) + ' tháng']);
      } else if (id === 'ab-test') {
        rows.push(['Tỉ lệ A', App.pct(r.rate_a)], ['Tỉ lệ B', App.pct(r.rate_b)], ['Chênh lệch', r.lift_pct === null ? '—' : App.pct(r.lift_pct)], ['p-value', String(r.p_value).replace('.', ',')], ['Kết luận', r.verdict]);
      } else if (id === 'sample-size') {
        rows.push(['Mỗi nhánh', App.num(r.per_variant) + ' lượt'], ['Tổng', App.num(r.total) + ' lượt']);
      }
      return `<dl class="divide-y divide-slate-800 rounded-xl border border-slate-800">${rows.map(([k, val]) => `<div class="flex justify-between gap-3 px-3 py-2"><dt class="text-slate-400">${esc(k)}</dt><dd class="font-semibold text-right">${esc(val)}</dd></div>`).join('')}</dl>${r.note ? `<p class="help mt-2">${esc(r.note)}</p>` : ''}`;
    };

    App.$$('[data-calc]', box).forEach((form) => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = form.dataset.calc;
        const d = formData(form);
        Object.keys(d).forEach((k) => { if (d[k] === '') delete d[k]; });
        const out = form.querySelector('[data-out]');
        try {
          const r = await App.post('/api/calc/' + id, d);
          out.innerHTML = show(id, r);
        } catch (err) {
          out.innerHTML = `<p class="text-rose-300">${esc(err.message)}</p>`;
        }
      });
    });
  }

  App.views.growth = {
    render: async (el, args, params) => {
      const tab = TABS.some((t) => t.id === args[0]) ? args[0] : 'overview';
      await App.loadContext();
      el.innerHTML = tabbar(tab) + '<div data-tab></div>';
      const box = el.querySelector('[data-tab]');
      if (tab === 'overview') await overview(box, params);
      else if (tab === 'data') await dataTab(box);
      else if (tab === 'budget') await budgetTab(box, params);
      else if (tab === 'utm') await utmTab(box);
      else if (tab === 'experiments') await expTab(box);
      else calcTab(box);
    },
  };
})();
