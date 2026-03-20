// Apply saved theme immediately (before DOM paint) to prevent flash
(function () {
    var t = localStorage.getItem('m2e-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', t);
})();

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('m2e-theme', theme);
    var cb = document.getElementById('themeToggle');
    if (cb) cb.checked = (theme === 'light');
}

document.addEventListener('DOMContentLoaded', function () {
    var saved = localStorage.getItem('m2e-theme') || 'dark';
    var cb = document.getElementById('themeToggle');
    if (cb) cb.checked = (saved === 'light');
});
