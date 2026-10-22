/* Khởi động ứng dụng: kiểm tra phiên, gắn sự kiện chung, điều hướng theo hash. */
(function () {
  'use strict';
  const App = window.App;

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-global]');
    if (!el) return;
    const act = el.dataset.global;
    if (act === 'logout') App.logout();
    if (act === 'drawer') document.getElementById('drawer').classList.remove('hidden');
    if (act === 'drawer-close') document.getElementById('drawer').classList.add('hidden');
  });
  document.getElementById('drawer-nav').addEventListener('click', (e) => {
    if (e.target.closest('a')) document.getElementById('drawer').classList.add('hidden');
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.getElementById('drawer').classList.add('hidden');
  });

  window.addEventListener('hashchange', () => App.render());
  window.addEventListener('unhandledrejection', (e) => {
    const err = e.reason;
    if (err && err.status === 401) { e.preventDefault(); return; }
    if (err && err.message) App.toast(err.message, 'bad');
  });

  (async () => {
    await App.initAuth();
    if (!App.token()) { App.showAuth(); return; }
    try {
      const me = await App.api('GET', '/api/auth/me', undefined, { allow401: true });
      App.state.user = me.user;
      await App.boot();
    } catch (e) {
      // Chỉ bỏ phiên khi máy chủ xác nhận phiên hết hạn; mất mạng tạm thời thì giữ lại để thử lại.
      if (e.status === 401) App.setToken('');
      App.showAuth(e.status === 401 ? 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' : e.message);
    }
  })();
})();
