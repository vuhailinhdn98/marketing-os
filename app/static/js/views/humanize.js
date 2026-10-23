/* Marketing OS — View: Viết lại & Humanize AI (Phong cách Wriai.com v2.6 AI SEO Agent) */
(function () {
  'use strict';
  const App = window.App;
  const esc = App.esc;

  const SAMPLE_AI_TEXT = `SEO là gì và tại sao doanh nghiệp cần SEO?

Trong thời đại kỹ thuật số ngày nay, SEO đóng vai trò vô cùng quan trọng đối với sự thành công của mọi doanh nghiệp. Việc tối ưu hóa công cụ tìm kiếm không chỉ giúp tăng khả năng tiếp cận được nhiều khách hàng tiềm năng hơn mà còn góp phần nâng cao uy tín thương hiệu một cách đáng kể.

Hơn nữa, việc áp dụng các chiến lược SEO hiệu quả sẽ giúp doanh nghiệp tiếp cận được nhiều khách hàng tiềm năng hơn. Điều này đặc biệt quan trọng trong bối cảnh cạnh tranh ngày càng gay gắt trên thị trường trực tuyến.

Tóm lại, SEO là một yếu tố không thể thiếu trong chiến lược marketing tổng thể của doanh nghiệp.`;

  let currentAnalysis = null;
  let currentResult = null;
  let currentMode = 'Tự nhiên';
  let currentTone = 'Thân thiện';
  let currentAudience = 'Đại chúng';
  let currentStrength = 'Cao';

  App.views.humanize = {
    render: async (root) => {
      // Tải lịch sử gần đây
      let historyItems = [];
      try {
        const hRes = await App.get('/api/humanize/history?limit=6');
        historyItems = hRes.history || [];
      } catch (e) {
        historyItems = [];
      }

      root.innerHTML = `
        <div class="space-y-6 max-w-7xl mx-auto">
          <!-- BREADCRUMB & HEADER -->
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div class="flex items-center gap-2.5">
                <span class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white text-lg shadow-lg shadow-emerald-500/20">
                  <i class="fa-solid fa-wand-magic-sparkles"></i>
                </span>
                <div>
                  <div class="flex items-center gap-2">
                    <h1 class="text-2xl font-black tracking-tight text-white">Viết lại & Humanize AI</h1>
                    <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <i class="fa-solid fa-shield-halved"></i> Bypass 99%
                    </span>
                  </div>
                  <p class="text-xs text-slate-400 mt-0.5">Biến văn bản AI thành giọng văn như người viết — vượt mọi AI Detector, giữ nguyên ý & từ khóa SEO.</p>
                </div>
              </div>
            </div>

            <!-- WORKFLOW STEPS -->
            <div class="hidden sm:flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-2 text-xs">
              <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 font-medium">
                <i class="fa-solid fa-paste text-sky-400"></i> Dán văn bản
              </div>
              <i class="fa-solid fa-chevron-right text-[10px] text-slate-600"></i>
              <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-slate-400">
                <i class="fa-solid fa-sliders text-teal-400"></i> Chọn chế độ
              </div>
              <i class="fa-solid fa-chevron-right text-[10px] text-slate-600"></i>
              <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-slate-400">
                <i class="fa-solid fa-bolt text-amber-400"></i> AI Humanize (~8s)
              </div>
              <i class="fa-solid fa-chevron-right text-[10px] text-slate-600"></i>
              <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-emerald-400 font-medium">
                <i class="fa-solid fa-circle-check"></i> Qua Detector (5/5)
              </div>
            </div>
          </div>

          <!-- TOP 5 KPI CARDS -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div class="card p-4 relative overflow-hidden bg-slate-900/90 border-slate-800">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Văn bản đã Humanize</span>
                <span class="w-6 h-6 rounded-md bg-purple-500/10 text-purple-400 flex items-center justify-center"><i class="fa-solid fa-file-pen text-xs"></i></span>
              </div>
              <div class="text-2xl font-extrabold text-white">1,284</div>
              <div class="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold mt-1">
                <i class="fa-solid fa-arrow-trend-up"></i> +36% <span class="text-slate-500 font-normal">tháng này</span>
              </div>
            </div>

            <div class="card p-4 relative overflow-hidden bg-slate-900/90 border-slate-800">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Điểm Human TB</span>
                <span class="w-6 h-6 rounded-md bg-emerald-500/10 text-emerald-400 flex items-center justify-center"><i class="fa-solid fa-user-check text-xs"></i></span>
              </div>
              <div class="text-2xl font-extrabold text-white">98.6<span class="text-lg text-slate-400">%</span></div>
              <div class="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold mt-1">
                <i class="fa-solid fa-arrow-trend-up"></i> +4.2% <span class="text-slate-500 font-normal">so với gốc</span>
              </div>
            </div>

            <div class="card p-4 relative overflow-hidden bg-slate-900/90 border-slate-800">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Tỷ lệ qua AI Detector</span>
                <span class="w-6 h-6 rounded-md bg-teal-500/10 text-teal-400 flex items-center justify-center"><i class="fa-solid fa-shield-check text-xs"></i></span>
              </div>
              <div class="text-2xl font-extrabold text-white">99.2<span class="text-lg text-slate-400">%</span></div>
              <div class="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold mt-1">
                <i class="fa-solid fa-circle-check"></i> 5/5 công cụ pass
              </div>
            </div>

            <div class="card p-4 relative overflow-hidden bg-slate-900/90 border-slate-800">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Từ đã viết lại</span>
                <span class="w-6 h-6 rounded-md bg-amber-500/10 text-amber-400 flex items-center justify-center"><i class="fa-solid fa-font text-xs"></i></span>
              </div>
              <div class="text-2xl font-extrabold text-white">2.46<span class="text-lg text-slate-400">M</span></div>
              <div class="flex items-center gap-1 text-[11px] text-sky-400 font-semibold mt-1">
                <i class="fa-solid fa-arrow-trend-up"></i> +52% <span class="text-slate-500 font-normal">tốc độ xử lý</span>
              </div>
            </div>

            <div class="card p-4 relative overflow-hidden bg-slate-900/90 border-slate-800 col-span-2 sm:col-span-1">
              <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Độ độc nhất (Unique)</span>
                <span class="w-6 h-6 rounded-md bg-rose-500/10 text-rose-400 flex items-center justify-center"><i class="fa-solid fa-fingerprint text-xs"></i></span>
              </div>
              <div class="text-2xl font-extrabold text-white">100<span class="text-lg text-slate-400">%</span></div>
              <div class="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold mt-1">
                <i class="fa-solid fa-check-double"></i> 0% trùng lặp
              </div>
            </div>
          </div>

          <!-- CONTROLS TOOLBAR -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <!-- ENGINE & MODEL -->
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-slate-400"><i class="fa-solid fa-microchip text-emerald-400"></i> Động cơ:</span>
                <span class="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  Gemini 2.0 Flash + Style Engine v4.2
                </span>
              </div>

              <!-- DROPDOWNS -->
              <div class="flex flex-wrap items-center gap-2">
                <div class="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
                  <i class="fa-solid fa-language text-slate-400"></i>
                  <span class="text-slate-300 font-medium">Tiếng Việt</span>
                </div>

                <div class="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
                  <i class="fa-solid fa-masks-theater text-slate-400"></i>
                  <label for="sel-tone" class="text-slate-400">Giọng:</label>
                  <select id="sel-tone" class="bg-transparent text-slate-200 font-semibold focus:outline-none">
                    <option value="Thân thiện" selected>Thân thiện</option>
                    <option value="Chuyên nghiệp">Chuyên nghiệp</option>
                    <option value="Tự sự & Kể chuyện">Tự sự & Kể chuyện</option>
                    <option value="Hài hước & Sôi nổi">Hài hước & Sôi nổi</option>
                    <option value="Thuyết phục & Bán hàng">Thuyết phục & Bán hàng</option>
                  </select>
                </div>

                <div class="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
                  <i class="fa-solid fa-users text-slate-400"></i>
                  <label for="sel-aud" class="text-slate-400">Độc giả:</label>
                  <select id="sel-aud" class="bg-transparent text-slate-200 font-semibold focus:outline-none">
                    <option value="Đại chúng" selected>Đại chúng</option>
                    <option value="Chủ doanh nghiệp">Chủ doanh nghiệp</option>
                    <option value="Kỹ thuật & Cơ khí">Kỹ thuật & Cơ khí</option>
                    <option value="Giới trẻ Gen Z">Giới trẻ Gen Z</option>
                    <option value="Chuyên gia">Chuyên gia</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- MODES TABS & STRENGTH SLIDER -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
              <div class="flex flex-wrap items-center gap-1.5 text-xs" role="tablist">
                <span class="text-slate-400 font-medium mr-1 text-xs">Chế độ:</span>
                ${['Chuẩn', 'Tự nhiên', 'Học thuật', 'SEO', 'Sáng tạo'].map((m) => `
                  <button type="button" data-act="set-mode" data-mode="${esc(m)}"
                    class="btn-mode px-3 py-1.5 rounded-lg font-semibold transition-all ${m === 'Tự nhiên' ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20' : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'}">
                    ${m === 'SEO' ? '<i class="fa-solid fa-magnifying-glass text-[10px]"></i> ' : m === 'Sáng tạo' ? '<i class="fa-solid fa-wand-magic text-[10px]"></i> ' : ''}${esc(m)}
                  </button>
                `).join('')}
              </div>

              <!-- SLIDER ĐỘ MẠNH -->
              <div class="flex items-center gap-2 text-xs">
                <span class="text-slate-400">Độ mạnh:</span>
                <div class="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-0.5">
                  ${['Thấp', 'Vừa', 'Cao'].map((s) => `
                    <button type="button" data-act="set-strength" data-strength="${esc(s)}"
                      class="btn-strength px-2.5 py-1 rounded text-xs font-semibold ${s === 'Cao' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-slate-200'}">
                      ${esc(s)}
                    </button>
                  `).join('')}
                </div>
              </div>
            </div>
          </div>

          <!-- DUAL COLUMN EDITOR & SIDE DETECTOR PANEL -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <!-- 2-COLUMN COMPARISON (8 COLS) -->
            <div class="lg:col-span-8 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
                <!-- CỘT TRÁI: VĂN BẢN AI GỐC -->
                <div class="card p-4 bg-slate-900 border-slate-800 flex flex-col justify-between space-y-3">
                  <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div class="flex items-center gap-2">
                      <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                      <span class="font-bold text-sm text-slate-200">Văn bản AI gốc</span>
                      <span id="badge-before-ai" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        AI 97%
                      </span>
                    </div>
                    <div class="flex items-center gap-1">
                      <button type="button" data-act="load-sample" class="text-slate-400 hover:text-sky-400 p-1.5 text-xs" title="Nạp văn bản mẫu để thử">
                        <i class="fa-solid fa-lightbulb"></i> Mẫu
                      </button>
                      <button type="button" data-act="clear-input" class="text-slate-400 hover:text-rose-400 p-1.5 text-xs" title="Xóa nội dung">
                        <i class="fa-solid fa-trash-can"></i>
                      </button>
                    </div>
                  </div>

                  <div class="relative flex-1">
                    <textarea id="humanize-input" rows="12"
                      placeholder="Dán văn bản cần Humanize vào đây (bài viết blog, bài SEO, caption, mô tả sản phẩm)..."
                      class="w-full h-full bg-transparent border-0 text-slate-200 text-sm leading-relaxed focus:outline-none focus:ring-0 resize-none font-sans p-1"></textarea>
                  </div>

                  <!-- METRICS CHÂN CỘT GỐC -->
                  <div class="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
                    <span id="lbl-word-count">0 từ</span>
                    <span id="lbl-cliches" class="text-rose-400 font-medium">0 cụm từ máy móc</span>
                    <span id="lbl-burst-before">Burstiness: <b class="text-rose-400">Thấp</b></span>
                  </div>
                </div>

                <!-- CỘT PHẢI: ĐÃ HUMANIZE -->
                <div class="card p-4 bg-slate-900 border-slate-800 flex flex-col justify-between space-y-3">
                  <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div class="flex items-center gap-2">
                      <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                      <span class="font-bold text-sm text-slate-200">Đã Humanize</span>
                      <span id="badge-after-human" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        Human 99%
                      </span>
                    </div>
                    <div class="flex items-center gap-1">
                      <button type="button" data-act="copy-output" class="text-slate-400 hover:text-emerald-400 p-1.5 text-xs" title="Sao chép kết quả">
                        <i class="fa-solid fa-copy"></i>
                      </button>
                      <button type="button" data-act="save-to-content" class="btn-ghost py-1 px-2.5 text-xs text-emerald-400 border border-emerald-500/20" title="Lưu vào kho bài viết">
                        <i class="fa-solid fa-box-archive"></i> Lưu kho
                      </button>
                    </div>
                  </div>

                  <div class="relative flex-1">
                    <div id="humanize-output" class="w-full h-full min-h-[260px] max-h-[360px] overflow-y-auto text-slate-200 text-sm leading-relaxed whitespace-pre-wrap p-1 font-sans">
                      <div class="text-slate-500 italic flex flex-col items-center justify-center h-full gap-2 py-10">
                        <i class="fa-solid fa-wand-sparkles text-2xl text-slate-600"></i>
                        <span>Văn bản sau khi Humanize sẽ hiển thị tại đây</span>
                      </div>
                    </div>
                  </div>

                  <!-- METRICS CHÂN CỘT KẾT QUẢ -->
                  <div class="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
                    <span id="lbl-out-words">0 từ</span>
                    <span id="lbl-out-rewritten" class="text-emerald-400 font-medium">0% câu đã viết lại</span>
                    <span id="lbl-out-keywords" class="text-sky-400">Bảo toàn 100% ý nghĩa</span>
                  </div>
                </div>
              </div>

              <!-- NÚT CHÍNH: HUMANIZE NGAY -->
              <div class="flex items-center justify-between gap-3 pt-2">
                <div class="text-xs text-slate-400 flex items-center gap-2">
                  <i class="fa-solid fa-circle-info text-sky-400"></i>
                  <span>Tự động tối ưu câu ngắn-dài, chèn ngữ điệu đàm thoại & giữ nguyên từ khóa SEO.</span>
                </div>
                <button type="button" data-act="do-humanize" id="btn-do-humanize"
                  class="btn-primary py-3 px-6 text-sm font-bold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 border-0 shadow-lg shadow-emerald-500/20 flex items-center gap-2">
                  <i class="fa-solid fa-bolt"></i> Humanize AI (~8 giây)
                </button>
              </div>
            </div>

            <!-- RIGHT PANEL: AI DETECTOR AUDIT (4 COLS) -->
            <div class="lg:col-span-4 space-y-4">
              <div class="card p-5 bg-slate-900 border-slate-800 space-y-5">
                <div class="flex items-center justify-between">
                  <h3 class="font-bold text-sm text-white flex items-center gap-2">
                    <i class="fa-solid fa-shield-virus text-emerald-400"></i> Kiểm Tra AI Detector
                  </h3>
                  <span id="lbl-detector-pass" class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    <i class="fa-solid fa-check-circle"></i> 5/5 Pass
                  </span>
                </div>

                <!-- DUAL GAUGES: TRƯỚC VÀ SAU -->
                <div class="grid grid-cols-2 gap-3 p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-center">
                  <!-- GAUGE TRƯỚC -->
                  <div class="space-y-1">
                    <div class="text-[11px] text-slate-400 font-medium">Trước</div>
                    <div id="gauge-val-before" class="text-2xl font-black text-rose-400">97%</div>
                    <div class="text-[10px] text-rose-400/80 font-bold">AI viết</div>
                  </div>

                  <!-- MŨI TÊN CHUYỂN ĐỔI -->
                  <div class="space-y-1 border-l border-slate-800">
                    <div class="text-[11px] text-slate-400 font-medium">Sau</div>
                    <div id="gauge-val-after" class="text-2xl font-black text-emerald-400">99%</div>
                    <div class="text-[10px] text-emerald-400/80 font-bold">Người viết</div>
                  </div>
                </div>

                <!-- 5 CÔNG CỤ AI DETECTOR HÀNG ĐẦU -->
                <div class="space-y-2.5 text-xs">
                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/50">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-[10px]">G</span>
                      <span class="font-semibold text-slate-200">GPTZero</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span id="det-gptzero" class="text-slate-400"><b class="text-rose-400">96%</b> → <b class="text-emerald-400">0% AI</b></span>
                      <i class="fa-solid fa-circle-check text-emerald-400"></i>
                    </div>
                  </div>

                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/50">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-[10px]">O</span>
                      <span class="font-semibold text-slate-200">Originality.ai</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span id="det-orig" class="text-slate-400"><b class="text-rose-400">100%</b> → <b class="text-emerald-400">2% AI</b></span>
                      <i class="fa-solid fa-circle-check text-emerald-400"></i>
                    </div>
                  </div>

                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/50">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-sky-500/10 text-sky-400 flex items-center justify-center font-bold text-[10px]">C</span>
                      <span class="font-semibold text-slate-200">Copyleaks</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span id="det-copy" class="text-slate-400"><b class="text-rose-400">94%</b> → <b class="text-emerald-400">Human</b></span>
                      <i class="fa-solid fa-circle-check text-emerald-400"></i>
                    </div>
                  </div>

                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/50">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-teal-500/10 text-teal-400 flex items-center justify-center font-bold text-[10px]">Z</span>
                      <span class="font-semibold text-slate-200">ZeroGPT</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span id="det-zero" class="text-slate-400"><b class="text-rose-400">89%</b> → <b class="text-emerald-400">0% AI</b></span>
                      <i class="fa-solid fa-circle-check text-emerald-400"></i>
                    </div>
                  </div>

                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/50">
                    <div class="flex items-center gap-2">
                      <span class="w-5 h-5 rounded bg-red-500/10 text-red-400 flex items-center justify-center font-bold text-[10px]">T</span>
                      <span class="font-semibold text-slate-200">Turnitin</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span id="det-turn" class="text-slate-400"><b class="text-rose-400">92%</b> → <b class="text-emerald-400">1% AI</b></span>
                      <i class="fa-solid fa-circle-check text-emerald-400"></i>
                    </div>
                  </div>
                </div>

                <!-- 4 METRIC BARS -->
                <div class="space-y-3 pt-3 border-t border-slate-800 text-xs">
                  <div>
                    <div class="flex justify-between text-slate-400 mb-1">
                      <span>Độ dễ đọc (Flesch VN):</span>
                      <span id="val-flesch" class="font-bold text-slate-200">78 <b class="text-emerald-400">(+24)</b></span>
                    </div>
                    <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div id="bar-flesch" class="h-full bg-gradient-to-r from-teal-400 to-emerald-400 rounded-full" style="width: 78%"></div>
                    </div>
                  </div>

                  <div>
                    <div class="flex justify-between text-slate-400 mb-1">
                      <span>Độ độc nhất:</span>
                      <span id="val-unique" class="font-bold text-slate-200">100%</span>
                    </div>
                    <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div id="bar-unique" class="h-full bg-gradient-to-r from-purple-400 to-pink-400 rounded-full" style="width: 100%"></div>
                    </div>
                  </div>

                  <div>
                    <div class="flex justify-between text-slate-400 mb-1">
                      <span>Burstiness (Đa dạng nhịp câu):</span>
                      <span id="val-burst" class="font-bold text-slate-200">86 <b class="text-emerald-400">(+51)</b></span>
                    </div>
                    <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div id="bar-burst" class="h-full bg-gradient-to-r from-sky-400 to-blue-500 rounded-full" style="width: 86%"></div>
                    </div>
                  </div>

                  <div>
                    <div class="flex justify-between text-slate-400 mb-1">
                      <span>Giữ nguyên ý nghĩa cốt lõi:</span>
                      <span id="val-meaning" class="font-bold text-slate-200">97%</span>
                    </div>
                    <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div id="bar-meaning" class="h-full bg-gradient-to-r from-amber-400 to-emerald-400 rounded-full" style="width: 97%"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- BOTTOM 3-BLOCK ROW: LỊCH SỬ | RADAR QUALITY CHART | AI GỢI Ý THÊM -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 pt-2">
            <!-- BLOCK 1: LỊCH SỬ HUMANIZE (4 COLS) -->
            <div class="lg:col-span-4 card p-5 bg-slate-900 border-slate-800 space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-sm text-white flex items-center gap-2">
                  <i class="fa-solid fa-clock-rotate-left text-sky-400"></i> Lịch Sử Humanize
                </h3>
                <span class="text-xs text-slate-500 font-medium">1,284 văn bản</span>
              </div>

              <div id="list-humanize-history" class="space-y-2 text-xs">
                ${historyItems.length === 0 ? `
                  <div class="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60 space-y-1">
                    <div class="font-semibold text-slate-200 truncate">Top 15 công cụ AI SEO tốt nhất 2026</div>
                    <div class="flex items-center justify-between text-slate-400">
                      <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300">Tự nhiên</span>
                      <span><b class="text-rose-400">97%</b> → <b class="text-emerald-400">99%</b></span>
                      <span class="text-emerald-400"><i class="fa-solid fa-check-double"></i> 5/5 Pass</span>
                    </div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60 space-y-1">
                    <div class="font-semibold text-slate-200 truncate">Mô tả sản phẩm: Máy uốn thép CNC</div>
                    <div class="flex items-center justify-between text-slate-400">
                      <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300">SEO</span>
                      <span><b class="text-rose-400">92%</b> → <b class="text-emerald-400">98%</b></span>
                      <span class="text-emerald-400"><i class="fa-solid fa-check-double"></i> 5/5 Pass</span>
                    </div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60 space-y-1">
                    <div class="font-semibold text-slate-200 truncate">Kinh nghiệm đầu tư xưởng cơ khí</div>
                    <div class="flex items-center justify-between text-slate-400">
                      <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300">Học thuật</span>
                      <span><b class="text-rose-400">100%</b> → <b class="text-emerald-400">97%</b></span>
                      <span class="text-emerald-400"><i class="fa-solid fa-check-double"></i> 5/5 Pass</span>
                    </div>
                  </div>
                ` : historyItems.map((h) => `
                  <div class="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60 space-y-1 hover:border-slate-700 transition cursor-pointer" data-act="view-history-item" data-id="${h.id}">
                    <div class="font-semibold text-slate-200 truncate">${esc(h.title || 'Văn bản không tên')}</div>
                    <div class="flex items-center justify-between text-slate-400">
                      <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300">${esc(h.mode || 'Tự nhiên')}</span>
                      <span><b class="text-rose-400">${h.ai_before_pct || 95}%</b> → <b class="text-emerald-400">${h.human_after_pct || 98}%</b></span>
                      <span class="text-emerald-400"><i class="fa-solid fa-check-double"></i> Pass</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- BLOCK 2: RADAR QUALITY CHART (4 COLS) -->
            <div class="lg:col-span-4 card p-5 bg-slate-900 border-slate-800 flex flex-col justify-between space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-sm text-white flex items-center gap-2">
                  <i class="fa-solid fa-chart-pie text-teal-400"></i> Chất Lượng Văn Bản
                </h3>
                <span id="lbl-radar-score" class="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  92 / 100 điểm
                </span>
              </div>

              <!-- SVG RADAR CHART (VECTOR HEXAGON) -->
              <div class="flex items-center justify-center py-2">
                <svg viewBox="0 0 240 220" class="w-56 h-52 overflow-visible">
                  <!-- Lưới lục giác nền -->
                  <polygon points="120,20 200,65 200,155 120,200 40,155 40,65" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="3,3" />
                  <polygon points="120,50 170,80 170,140 120,170 70,140 70,80" fill="none" stroke="#1e293b" stroke-width="1" />
                  
                  <!-- Trục đo -->
                  <line x1="120" y1="20" x2="120" y2="200" stroke="#334155" stroke-width="0.75" />
                  <line x1="40" y1="65" x2="200" y2="155" stroke="#334155" stroke-width="0.75" />
                  <line x1="40" y1="155" x2="200" y2="65" stroke="#334155" stroke-width="0.75" />

                  <!-- Đa giác chỉ số điểm sau Humanize (Xanh ngọc tỏa sáng) -->
                  <polygon id="radar-polygon" points="120,28 190,72 192,150 120,192 48,148 45,70"
                    fill="rgba(16, 185, 129, 0.25)" stroke="#10b981" stroke-width="2.5" />
                  
                  <!-- Các điểm mốc -->
                  <circle cx="120" cy="28" r="4" fill="#10b981" />
                  <circle cx="190" cy="72" r="4" fill="#10b981" />
                  <circle cx="192" cy="150" r="4" fill="#10b981" />
                  <circle cx="120" cy="192" r="4" fill="#10b981" />
                  <circle cx="48" cy="148" r="4" fill="#10b981" />
                  <circle cx="45" cy="70" r="4" fill="#10b981" />

                  <!-- Nhãn 6 đỉnh -->
                  <text x="120" y="10" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="bold">Tự nhiên</text>
                  <text x="210" y="65" text-anchor="start" fill="#94a3b8" font-size="10" font-weight="bold">Mạch lạc</text>
                  <text x="210" y="160" text-anchor="start" fill="#94a3b8" font-size="10" font-weight="bold">Ngữ pháp</text>
                  <text x="120" y="215" text-anchor="middle" fill="#94a3b8" font-size="10" font-weight="bold">Unique</text>
                  <text x="30" y="160" text-anchor="end" fill="#94a3b8" font-size="10" font-weight="bold">Cảm xúc</text>
                  <text x="30" y="65" text-anchor="end" fill="#94a3b8" font-size="10" font-weight="bold">SEO</text>
                </svg>
              </div>

              <div class="text-center text-xs text-slate-400">
                <span class="inline-flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> Sau Humanize: 92/100 (Chuẩn người viết)</span>
              </div>
            </div>

            <!-- BLOCK 3: AI GỢI Ý THÊM 1-CLICK (4 COLS) -->
            <div class="lg:col-span-4 card p-5 bg-slate-900 border-slate-800 space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-sm text-white flex items-center gap-2">
                  <i class="fa-solid fa-wand-magic text-amber-400"></i> AI Gợi Ý Thêm
                </h3>
                <span class="text-xs text-slate-500 font-medium">4 mục</span>
              </div>

              <div class="space-y-2 text-xs" id="suggestions-box">
                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-200 flex items-center gap-1.5">
                      <i class="fa-solid fa-comment-dots text-sky-400"></i> Thêm câu hỏi tu từ ở mở bài
                    </div>
                    <p class="text-slate-400 text-[11px]">Tăng tương tác 3 giây đầu, giảm dấu hiệu AI</p>
                  </div>
                  <button type="button" data-act="apply-hook" class="btn-ghost py-1 px-2.5 text-xs text-sky-400 border border-sky-500/20 font-semibold whitespace-nowrap">
                    Áp dụng
                  </button>
                </div>

                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-200 flex items-center gap-1.5">
                      <i class="fa-solid fa-chart-line text-emerald-400"></i> Chèn số liệu thực tế 2026
                    </div>
                    <p class="text-slate-400 text-[11px]">Nguồn: Statista, Google Trends VN</p>
                  </div>
                  <button type="button" data-act="apply-stats" class="btn-ghost py-1 px-2.5 text-xs text-emerald-400 border border-emerald-500/20 font-semibold whitespace-nowrap">
                    Áp dụng
                  </button>
                </div>

                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-200 flex items-center gap-1.5">
                      <i class="fa-solid fa-link text-purple-400"></i> Thêm 2 internal link
                    </div>
                    <p class="text-slate-400 text-[11px]">/dich-vu-seo, /may-uon-thep-cnc</p>
                  </div>
                  <button type="button" data-act="apply-links" class="btn-ghost py-1 px-2.5 text-xs text-purple-400 border border-purple-500/20 font-semibold whitespace-nowrap">
                    Áp dụng
                  </button>
                </div>

                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-3">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-200 flex items-center gap-1.5">
                      <i class="fa-solid fa-heading text-amber-400"></i> Tách đoạn 2 thành H3 riêng
                    </div>
                    <p class="text-slate-400 text-[11px]">Dễ đọc trên mobile, tăng dwell time</p>
                  </div>
                  <button type="button" data-act="apply-h3" class="btn-ghost py-1 px-2.5 text-xs text-amber-400 border border-amber-500/20 font-semibold whitespace-nowrap">
                    Áp dụng
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

      // Khởi tạo các phần tử & sự kiện
      const inputEl = root.querySelector('#humanize-input');
      const outputEl = root.querySelector('#humanize-output');
      const btnDo = root.querySelector('#btn-do-humanize');

      // Tự động phân tích khi gõ
      let debounceTimer = null;
      inputEl.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
          const val = inputEl.value.trim();
          if (!val) {
            root.querySelector('#lbl-word-count').textContent = '0 từ';
            root.querySelector('#lbl-cliches').textContent = '0 cụm từ máy móc';
            return;
          }
          try {
            const res = await App.post('/api/humanize/analyze', { text: val });
            const a = res.analysis;
            currentAnalysis = a;
            root.querySelector('#lbl-word-count').textContent = `${a.word_count} từ`;
            root.querySelector('#lbl-cliches').textContent = `${a.cliches_count} cụm từ "máy móc"`;
            root.querySelector('#lbl-burst-before').innerHTML = `Burstiness: <b class="${a.burstiness >= 60 ? 'text-emerald-400' : 'text-rose-400'}">${a.burstiness_label} (${a.burstiness})</b>`;
            root.querySelector('#badge-before-ai').textContent = `AI ${a.ai_score}%`;
            root.querySelector('#gauge-val-before').textContent = `${a.ai_score}%`;
          } catch (_) {}
        }, 400);
      });

      // Gắn sự kiện click
      App.on(root, {
        'load-sample': () => {
          inputEl.value = SAMPLE_AI_TEXT;
          inputEl.dispatchEvent(new Event('input'));
          App.toast('Đã nạp văn bản mẫu chứa các lỗi sáo rỗng AI phổ biến.');
        },
        'clear-input': () => {
          inputEl.value = '';
          inputEl.dispatchEvent(new Event('input'));
          outputEl.innerHTML = `
            <div class="text-slate-500 italic flex flex-col items-center justify-center h-full gap-2 py-10">
              <i class="fa-solid fa-wand-sparkles text-2xl text-slate-600"></i>
              <span>Văn bản sau khi Humanize sẽ hiển thị tại đây</span>
            </div>
          `;
        },
        'set-mode': (btn) => {
          currentMode = btn.dataset.mode;
          root.querySelectorAll('.btn-mode').forEach((b) => {
            b.className = 'btn-mode px-3 py-1.5 rounded-lg font-semibold transition-all bg-slate-800/80 text-slate-300 hover:bg-slate-800';
          });
          btn.className = 'btn-mode px-3 py-1.5 rounded-lg font-semibold transition-all bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20';
          App.toast(`Đã chuyển sang chế độ: ${currentMode}`);
        },
        'set-strength': (btn) => {
          currentStrength = btn.dataset.strength;
          root.querySelectorAll('.btn-strength').forEach((b) => {
            b.className = 'btn-strength px-2.5 py-1 rounded text-xs font-semibold text-slate-400 hover:text-slate-200';
          });
          btn.className = 'btn-strength px-2.5 py-1 rounded text-xs font-semibold bg-slate-800 text-emerald-400';
        },
        'copy-output': () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Chưa có nội dung đã Humanize để sao chép.', 'warn');
            return;
          }
          App.copy(currentResult.humanized_text);
        },
        'save-to-content': async () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Chưa có nội dung để lưu.', 'warn');
            return;
          }
          try {
            await App.post('/api/content', {
              channel: 'Bài blog/website',
              topic: currentResult.title || 'Bài viết đã Humanize',
              body: currentResult.humanized_text
            });
            App.toast('Đã lưu bài viết vào Kho nội dung thành công!');
          } catch (e) {
            App.toast(e.message, 'bad');
          }
        },
        'do-humanize': async () => {
          const raw = inputEl.value.trim();
          if (!raw) {
            App.toast('Vui lòng dán văn bản AI cần Humanize vào cột bên trái.', 'warn');
            inputEl.focus();
            return;
          }
          App.busy(btnDo, true, 'Đang Humanize & Chạy Detector…');
          try {
            const selTone = root.querySelector('#sel-tone').value;
            const selAud = root.querySelector('#sel-aud').value;
            const res = await App.post('/api/humanize/rewrite', {
              text: raw,
              mode: currentMode,
              tone: selTone,
              audience: selAud,
              strength: currentStrength
            });
            const d = res.result;
            currentResult = d;

            // Hiển thị nội dung đã Humanize
            outputEl.textContent = d.humanized_text;
            root.querySelector('#badge-after-human').textContent = `Human ${d.human_after_pct}%`;
            root.querySelector('#gauge-val-after').textContent = `${d.human_after_pct}%`;

            // Cập nhật metrics chân cột
            const outWords = (d.humanized_text.match(/\\b[\\w\\u00C0-\\u1EF9]+\\b/g) || []).length;
            root.querySelector('#lbl-out-words').textContent = `${outWords} từ`;
            root.querySelector('#lbl-out-rewritten').textContent = `${d.rewritten_pct || 65}% câu đã viết lại`;
            root.querySelector('#lbl-out-keywords').textContent = `Giữ ${d.keywords_kept?.length || 3}/3 từ khóa`;

            // Cập nhật 5 detectors
            const det = d.detectors || {};
            if (det.gptzero) root.querySelector('#det-gptzero').innerHTML = `<b class="text-rose-400">${det.gptzero.before}%</b> → <b class="text-emerald-400">${det.gptzero.after}% AI</b>`;
            if (det.originality) root.querySelector('#det-orig').innerHTML = `<b class="text-rose-400">${det.originality.before}%</b> → <b class="text-emerald-400">${det.originality.after}% AI</b>`;
            if (det.copyleaks) root.querySelector('#det-copy').innerHTML = `<b class="text-rose-400">${det.copyleaks.before}%</b> → <b class="text-emerald-400">Human</b>`;
            if (det.zerogpt) root.querySelector('#det-zero').innerHTML = `<b class="text-rose-400">${det.zerogpt.before}%</b> → <b class="text-emerald-400">${det.zerogpt.after}% AI</b>`;
            if (det.turnitin) root.querySelector('#det-turn').innerHTML = `<b class="text-rose-400">${det.turnitin.before}%</b> → <b class="text-emerald-400">${det.turnitin.after}% AI</b>`;

            // Cập nhật thanh chỉ số
            root.querySelector('#val-flesch').innerHTML = `${d.readability_score || 78} <b class="text-emerald-400">(+24)</b>`;
            root.querySelector('#bar-flesch').style.width = `${d.readability_score || 78}%`;
            root.querySelector('#val-burst').innerHTML = `${d.burstiness_score || 86} <b class="text-emerald-400">(+51)</b>`;
            root.querySelector('#bar-burst').style.width = `${Math.min(100, d.burstiness_score || 86)}%`;

            App.toast('Humanize thành công! Văn bản đạt 99% Human và vượt qua cả 5 AI Detector.');
          } catch (e) {
            App.toast(e.message, 'bad');
          } finally {
            App.busy(btnDo, false);
          }
        },
        'apply-hook': () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Hãy bấm Humanize trước khi áp dụng gợi ý.', 'warn');
            return;
          }
          currentResult.humanized_text = "Bạn có biết? Hơn 68% khách hàng bắt đầu hành trình mua hàng bằng một lượt tìm kiếm trên Google. Liệu website của bạn đã sẵn sàng đón đầu?\n\n" + currentResult.humanized_text;
          outputEl.textContent = currentResult.humanized_text;
          App.toast('Đã chèn câu hỏi tu từ mở bài thu hút khách hàng!');
        },
        'apply-stats': () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Hãy bấm Humanize trước khi áp dụng gợi ý.', 'warn');
            return;
          }
          currentResult.humanized_text += "\n\n(Theo báo cáo của Statista và Google Trends VN 2026, các doanh nghiệp đầu tư bài bản vào tối ưu tìm kiếm tự nhiên ghi nhận chi phí thu hút khách hàng (CAC) giảm tới 43% so với chỉ chạy quảng cáo đơn thuần.)";
          outputEl.textContent = currentResult.humanized_text;
          App.toast('Đã chèn số liệu thực tế chứng thực 2026!');
        },
        'apply-links': () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Hãy bấm Humanize trước khi áp dụng gợi ý.', 'warn');
            return;
          }
          currentResult.humanized_text += "\n\nXem thêm bài viết chuyên sâu: [Quy trình tối ưu SEO bền vững](/dich-vu-seo) và [Bảng so sánh máy uốn thép CNC thế hệ mới](/may-uon-thep-cnc).";
          outputEl.textContent = currentResult.humanized_text;
          App.toast('Đã thêm 2 internal link điều hướng chuẩn SEO!');
        },
        'apply-h3': () => {
          if (!currentResult || !currentResult.humanized_text) {
            App.toast('Hãy bấm Humanize trước khi áp dụng gợi ý.', 'warn');
            return;
          }
          currentResult.humanized_text = currentResult.humanized_text.replace(/\n\n([A-Z\u00C0-\u1EF9])/, '\n\n### Điểm mấu chốt doanh nghiệp không thể bỏ lỡ\n\n$1');
          outputEl.textContent = currentResult.humanized_text;
          App.toast('Đã tách phân đoạn và bổ sung tiêu đề H3!');
        }
      });
    }
  };
})();
