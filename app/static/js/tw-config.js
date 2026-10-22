/* Cấu hình Tailwind Play CDN (tách khỏi HTML để chạy được với Content-Security-Policy) */
window.tailwind = window.tailwind || {};
tailwind.config = {
  darkMode: 'class',
  theme: { extend: { fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'] } } }
};
