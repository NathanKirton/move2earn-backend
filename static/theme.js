// Apply persisted theme as early as possible to avoid a flash of wrong theme.
(function () {
    var t = localStorage.getItem('m2e-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', t);
})();

// Toggle and persist theme preference for the current and future pages.
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('m2e-theme', theme);
    var cb = document.getElementById('themeToggle');
    if (cb) cb.checked = (theme === 'light');
}

// Sync checkbox state with stored preference after markup loads.
document.addEventListener('DOMContentLoaded', function () {
    var saved = localStorage.getItem('m2e-theme') || 'dark';
    var cb = document.getElementById('themeToggle');
    if (cb) cb.checked = (saved === 'light');
});
