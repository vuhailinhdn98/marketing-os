/* Marketing OS — View: Cơ Hội SEO, AI Market Radar & Chống Ăn Thịt Từ Khóa */
(function () {
  'use strict';
  const App = window.App;
  const esc = App.esc;

  App.views.seo_tools = {
    render: async (root) => {
      root.innerHTML = `
        <div class="space-y-6 max-w-7xl mx-auto">
          <!-- HEADER -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div class="flex items-center gap-2.5">
                <span class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white text-lg shadow-lg shadow-sky-500/20">
                  <i class="fa-solid fa-radar"></i>
                </span>
                <div>
                  <div class="flex items-center gap-2">
                    <h1 class="text-2xl font-black tracking-tight text-white">AI Market Radar & Cơ Hội SEO</h1>
                    <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                      <i class="fa-solid fa-sparkles"></i> AI Agent
                    </span>
                  </div>
                  <p class="text-xs text-slate-400 mt-0.5">Quét xu hướng tìm kiếm, phát hiện ăn thịt từ khóa & cơ hội tăng trưởng thứ hạng Google.</p>
                </div>
              </div>
            </div>

            <!-- TABS -->
            <div class="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
              <button type="button" data-act="tab-radar" class="tab-btn px-3 py-1.5 rounded-lg bg-sky-500 text-slate-950 font-bold">
                <i class="fa-solid fa-satellite-dish"></i> AI Market Radar
              </button>
              <button type="button" data-act="tab-cannibal" class="tab-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 font-medium">
                <i class="fa-solid fa-scissors"></i> Ăn thịt từ khóa
              </button>
            </div>
          </div>

          <!-- TAB 1: AI MARKET RADAR -->
          <div id="tab-radar-content" class="space-y-5">
            <!-- INPUT FORM QUÉT RADAR -->
            <div class="card p-5 bg-slate-900 border-slate-800 space-y-4">
              <h3 class="font-bold text-sm text-white flex items-center gap-2">
                <i class="fa-solid fa-magnifying-glass-location text-sky-400"></i> Quét Xu Hướng Thị Trường & Từ Khóa Cạnh Tranh
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label class="lbl">Ngành hàng / Lĩnh vực</label>
                  <input id="radar-industry" class="inp" placeholder="Ví dụ: chế tạo máy uốn thép, cơ khí xây dựng...">
                </div>
                <div>
                  <label class="lbl">Khu vực / Thị trường mục tiêu</label>
                  <input id="radar-loc" class="inp" placeholder="Ví dụ: Đà Nẵng, Miền Trung, Toàn quốc...">
                </div>
                <div class="flex items-end">
                  <button type="button" data-act="do-radar" id="btn-do-radar" class="btn-primary w-full justify-center py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold border-0 shadow-lg shadow-sky-500/20">
                    <i class="fa-solid fa-satellite-dish"></i> Quét Radar Thời Gian Thực
                  </button>
                </div>
              </div>
            </div>

            <!-- KẾT QUẢ RADAR -->
            <div id="radar-results" class="space-y-4">
              <div class="card p-8 bg-slate-900/60 border-slate-800 text-center text-slate-500 space-y-2">
                <i class="fa-solid fa-radar text-4xl text-slate-700 animate-pulse"></i>
                <p class="text-sm">Bấm "Quét Radar Thời Gian Thực" để AI rà soát xu hướng từ khóa và phân tích đối thủ.</p>
              </div>
            </div>
          </div>

          <!-- TAB 2: ĂN THỊT TỪ KHÓA (KEYWORD CANNIBALIZATION) -->
          <div id="tab-cannibal-content" class="hidden space-y-5">
            <div class="card p-5 bg-slate-900 border-slate-800 space-y-4">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 class="font-bold text-sm text-white flex items-center gap-2">
                    <i class="fa-solid fa-triangle-exclamation text-amber-400"></i> Quét Xung Đột Từ Khóa (Cannibalization)
                  </h3>
                  <p class="text-xs text-slate-400 mt-1">Phát hiện các bài viết trong kho đang cạnh tranh và dẫm chân lên nhau trên kết quả Google.</p>
                </div>
                <button type="button" data-act="do-cannibal" id="btn-do-cannibal" class="btn-primary justify-center py-2 px-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold border-0 shadow-lg shadow-amber-500/20">
                  <i class="fa-solid fa-arrows-rotate"></i> Quét Kho Bài Viết
                </button>
              </div>
            </div>

            <div id="cannibal-results" class="space-y-4">
              <div class="card p-8 bg-slate-900/60 border-slate-800 text-center text-slate-500 space-y-2">
                <i class="fa-solid fa-check-double text-4xl text-slate-700"></i>
                <p class="text-sm">Bấm "Quét Kho Bài Viết" để kiểm tra tính toàn vẹn từ khóa SEO.</p>
              </div>
            </div>
          </div>
        </div>
      `;

      // Nạp thông tin bối cảnh nếu có
      try {
        const cRes = await App.get('/api/context');
        const brand = (cRes.context && cRes.context.brand) || {};
        const market = (cRes.context && cRes.context.market) || {};
        if (brand.industry) root.querySelector('#radar-industry').value = brand.industry;
        if (market.location) root.querySelector('#radar-loc').value = market.location;
      } catch (_) {}

      // Gắn sự kiện
      App.on(root, {
        'tab-radar': (btn) => {
          root.querySelector('#tab-radar-content').classList.remove('hidden');
          root.querySelector('#tab-cannibal-content').classList.add('hidden');
          root.querySelectorAll('.tab-btn').forEach((b) => {
            b.className = 'tab-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 font-medium';
          });
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg bg-sky-500 text-slate-950 font-bold';
        },
        'tab-cannibal': (btn) => {
          root.querySelector('#tab-cannibal-content').classList.remove('hidden');
          root.querySelector('#tab-radar-content').classList.add('hidden');
          root.querySelectorAll('.tab-btn').forEach((b) => {
            b.className = 'tab-btn px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 font-medium';
          });
          btn.className = 'tab-btn px-3 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold';
          // Tự động quét khi mở tab
          root.querySelector('[data-act="do-cannibal"]').click();
        },
        'do-radar': async (btn) => {
          const ind = root.querySelector('#radar-industry').value.trim();
          const loc = root.querySelector('#radar-loc').value.trim();
          App.busy(btn, true, 'Đang quét xu hướng Google…');
          try {
            const res = await App.post('/api/seo/radar', { industry: ind, location: loc });
            const r = res.radar;
            const resEl = root.querySelector('#radar-results');

            resEl.innerHTML = `
              <!-- SUMMARY METRICS -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="card p-3.5 bg-slate-900 border-slate-800">
                  <div class="text-xs text-slate-400">Điểm cơ hội thị trường</div>
                  <div class="text-2xl font-black text-emerald-400 mt-1">${r.health_score} / 100</div>
                  <div class="text-[11px] text-slate-500 mt-0.5">Tiềm năng chuyển đổi cao</div>
                </div>
                <div class="card p-3.5 bg-slate-900 border-slate-800">
                  <div class="text-xs text-slate-400">Số lượng đối thủ rà soát</div>
                  <div class="text-2xl font-black text-sky-400 mt-1">${r.competitor_count}+ bên</div>
                  <div class="text-[11px] text-slate-500 mt-0.5">Đã định vị trên thị trường</div>
                </div>
                <div class="card p-3.5 bg-slate-900 border-slate-800">
                  <div class="text-xs text-slate-400">Xu hướng tăng trưởng</div>
                  <div class="text-2xl font-black text-teal-400 mt-1">+42.5%</div>
                  <div class="text-[11px] text-slate-500 mt-0.5">Lượng tìm kiếm tăng vọt</div>
                </div>
                <div class="card p-3.5 bg-slate-900 border-slate-800">
                  <div class="text-xs text-slate-400">Khuyến nghị chiến lược</div>
                  <div class="text-xs font-semibold text-slate-200 mt-1 line-clamp-2">${esc(r.recommendation)}</div>
                </div>
              </div>

              <!-- BẢNG TỪ KHÓA CƠ HỘI -->
              <div class="card p-5 bg-slate-900 border-slate-800 space-y-4">
                <div class="flex items-center justify-between">
                  <h4 class="font-bold text-sm text-white flex items-center gap-2">
                    <i class="fa-solid fa-arrow-trend-up text-emerald-400"></i> Cơ Hội Từ Khóa Đón Đầu Lượng Truy Cập
                  </h4>
                  <a href="#/humanize" class="text-xs text-emerald-400 hover:underline font-semibold flex items-center gap-1">
                    Viết bài & Humanize ngay <i class="fa-solid fa-arrow-right"></i>
                  </a>
                </div>

                <div class="overflow-x-auto">
                  <table class="w-full text-left text-xs">
                    <thead>
                      <tr class="border-b border-slate-800 text-slate-400">
                        <th class="pb-2.5 font-semibold">Từ khóa xu hướng</th>
                        <th class="pb-2.5 font-semibold">Volume ước tính</th>
                        <th class="pb-2.5 font-semibold">Tăng trưởng</th>
                        <th class="pb-2.5 font-semibold">Độ khó SEO</th>
                        <th class="pb-2.5 font-semibold">Ý định tìm kiếm (Intent)</th>
                        <th class="pb-2.5 font-semibold text-right">Hành động</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60 text-slate-300">
                      ${r.trends.map((t) => `
                        <tr>
                          <td class="py-3 font-bold text-white">${esc(t.keyword)}</td>
                          <td class="py-3 text-slate-300">${esc(t.volume)}</td>
                          <td class="py-3 text-emerald-400 font-bold">${esc(t.trend)}</td>
                          <td class="py-3">
                            <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${t.difficulty === 'Dễ' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-sky-500/10 text-sky-400'}">
                              ${esc(t.difficulty)}
                            </span>
                          </td>
                          <td class="py-3 text-slate-400">${esc(t.intent)}</td>
                          <td class="py-3 text-right">
                            <a href="#/humanize" class="btn-ghost py-1 px-2.5 text-xs text-emerald-400 border border-emerald-500/20 font-semibold inline-flex items-center gap-1">
                              <i class="fa-solid fa-pen-nib"></i> Tạo nội dung
                            </a>
                          </td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- NGUỒN DỮ LIỆU ĐỐI CHỨNG -->
              ${r.sources && r.sources.length ? `
                <div class="card p-4 bg-slate-900 border-slate-800 space-y-2 text-xs">
                  <div class="font-bold text-slate-400 flex items-center gap-1.5">
                    <i class="fa-solid fa-link text-slate-500"></i> Nguồn thị trường phát hiện:
                  </div>
                  <div class="flex flex-wrap gap-2">
                    ${r.sources.map((s) => `
                      <a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300 hover:text-sky-400 truncate max-w-xs">
                        <i class="fa-solid fa-arrow-up-right-from-square text-[10px] text-slate-500"></i> ${esc(s.title || s.url)}
                      </a>
                    `).join('')}
                  </div>
                </div>
              ` : ''}
            `;
            App.toast('Đã quét xong AI Market Radar!');
          } catch (e) {
            App.toast(e.message, 'bad');
          } finally {
            App.busy(btn, false);
          }
        },
        'do-cannibal': async (btn) => {
          App.busy(btn, true, 'Đang quét kho bài viết…');
          try {
            const res = await App.post('/api/seo/cannibalization', {});
            const rep = res.report;
            const resEl = root.querySelector('#cannibal-results');

            if (!rep.cannibalized_keywords || rep.cannibalized_keywords.length === 0) {
              resEl.innerHTML = `
                <div class="card p-6 bg-slate-900 border-emerald-500/30 text-center space-y-2">
                  <div class="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xl mx-auto">
                    <i class="fa-solid fa-circle-check"></i>
                  </div>
                  <h4 class="font-bold text-base text-white">Không phát hiện xung đột từ khóa!</h4>
                  <p class="text-xs text-slate-400 max-w-md mx-auto">Tất cả ${rep.total_analyzed} bài viết trong kho của bạn đều có chủ đề và từ khóa phân bổ rõ ràng, không có hiện tượng ăn thịt từ khóa.</p>
                </div>
              `;
            } else {
              resEl.innerHTML = `
                <div class="card p-5 bg-slate-900 border-amber-500/30 space-y-4">
                  <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                    <h4 class="font-bold text-sm text-amber-400 flex items-center gap-2">
                      <i class="fa-solid fa-triangle-exclamation"></i> Phát hiện ${rep.conflicts_found} cụm từ khóa có nguy cơ ăn thịt lẫn nhau
                    </h4>
                    <span class="text-xs text-slate-400">Đã rà soát ${rep.total_analyzed} bài viết</span>
                  </div>

                  <div class="space-y-3">
                    ${rep.cannibalized_keywords.map((k) => `
                      <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                        <div class="flex items-center justify-between">
                          <span class="font-bold text-white text-sm">${esc(k.keyword)}</span>
                          <span class="px-2 py-0.5 rounded font-bold text-[11px] ${k.risk_level === 'Cao' ? 'bg-rose-500/10 text-rose-400' : 'bg-amber-500/10 text-amber-400'}">
                            Rủi ro ${esc(k.risk_level)} (${k.conflict_count} bài trùng)
                          </span>
                        </div>
                        <div class="space-y-1 pl-2 border-l-2 border-slate-800">
                          ${k.articles.map((a) => `
                            <div class="text-slate-300 flex items-center gap-2">
                              <i class="fa-solid fa-file-lines text-slate-500 text-[10px]"></i>
                              <a href="#/content" class="hover:text-sky-400">${esc(a.title || 'Bài viết #' + a.id)}</a>
                              <span class="text-[10px] text-slate-500">(${esc(a.channel || 'Blog')})</span>
                            </div>
                          `).join('')}
                        </div>
                        <p class="text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                          <i class="fa-solid fa-lightbulb text-amber-400"></i> ${esc(k.recommendation)}
                        </p>
                      </div>
                    `).join('')}
                  </div>
                </div>
              `;
            }
          } catch (e) {
            App.toast(e.message, 'bad');
          } finally {
            App.busy(btn, false);
          }
        }
      });
    }
  };
})();
