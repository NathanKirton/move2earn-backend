// AI frontend logic: fetches insights and updates the collapsible AI box.
// Expects `window.M2E_CHILD_ID` to be set before this script is loaded.

function createAiBoxIfMissing() {
  var container = document.querySelector('.dashboard-main');
  if (!container) return;
  if (document.getElementById('ai-box')) return;

  var box = document.createElement('div');
  box.id = 'ai-box';
  box.className = 'ai-collapsible';
  box.innerHTML = "<div class=\"ai-header\">Your AI Training Partner <span class='ai-toggle'>▼</span></div><div class=\"ai-content\"><div class=\"ai-loading\">Loading AI insights...</div></div>";
  container.insertBefore(box, container.firstChild);
  // Make sure the loading text is visible even if CSS sets opacity elsewhere
  try {
    var contentEl = box.querySelector('.ai-content');
    if (contentEl) {
      contentEl.style.opacity = '1';
      contentEl.style.transition = 'none';
      // allow subsequent JS to control height
      contentEl.style.maxHeight = contentEl.scrollHeight + 'px';
    }
  } catch (err) {
    console.debug('ai create visibility guard failed', err);
  }
}

function setAiContent(insights) {
  var box = document.getElementById('ai-box');
  if (!box) return;
  var content = box.querySelector('.ai-content');
  if (!content) return;

  var html = '';
  if (insights) {
    // Show core insights
    html += '<div class="ai-row"><strong>Message:</strong> ' + (insights.message || '') + '</div>';
    html += '<div class="ai-row"><strong>Predicted Minutes:</strong> ' + (insights.predicted_minutes || 0) + '</div>';
    html += '<div class="ai-row"><strong>Challenge:</strong> ' + (insights.challenge_recommendation || '') + '</div>';
    html += '<div class="ai-row"><strong>Workout:</strong> ' + (insights.recommended_workout || '') + '</div>';
    if (insights.streak_risk) {
      html += '<div class="ai-row ai-warning">⚠ Streak at risk — try a short activity to keep it.</div>';
    }

    // Show model diagnostics when available
    if (insights._model_status || insights._model_source) {
      html += '<hr/>';
      html += '<div class="ai-row"><strong>Model Source:</strong> ' + (insights._model_source || 'unknown') + '</div>';
      try {
        html += '<div class="ai-row"><strong>Model Status:</strong> ' + JSON.stringify(insights._model_status) + '</div>';
      } catch (e) {
        html += '<div class="ai-row"><strong>Model Status:</strong> (unavailable)</div>';
      }
    }
    html += '<div class="ai-row"><button id="ai-refresh-btn" class="btn">Refresh</button> <button id="ai-login-btn" class="btn">Login</button></div>';
  } else {
    html = '<div class="ai-row">AI unavailable right now. If you are logged in, check server logs for errors.</div>';
    html += '<div class="ai-row"><button id="ai-refresh-btn" class="btn">Retry</button> <button id="ai-login-btn" class="btn">Login</button></div>';
  }

  content.innerHTML = html;
  // ensure visible regardless of external CSS
  try {
    content.style.opacity = '1';
    content.style.transition = 'none';
    content.style.maxHeight = content.scrollHeight + 'px';
  } catch (e) {}

  // Hook up buttons
  try {
    var refBtn = document.getElementById('ai-refresh-btn');
    if (refBtn) refBtn.addEventListener('click', function() { refreshAI(); });
    var loginBtn = document.getElementById('ai-login-btn');
    if (loginBtn) loginBtn.addEventListener('click', function() { window.location = '/login'; });
  } catch (e) {}
}

// Expose a debug helper to surface fetch errors directly into the AI box
window.debugAIError = function(err) {
  var box = document.getElementById('ai-box');
  if (!box) return;
  var content = box.querySelector('.ai-content');
  if (!content) return;
  content.innerHTML = '<div class="ai-row ai-warning">AI error: ' + String(err) + '</div>';
}

function toggleAiBox(e) {
  var box = document.getElementById('ai-box');
  if (!box) return;
  var content = box.querySelector('.ai-content');
  if (!content) return;
  box.classList.toggle('open');
  if (box.classList.contains('open')) {
    content.style.maxHeight = content.scrollHeight + 'px';
  } else {
    content.style.maxHeight = '0px';
  }
}

async function fetchInsights(childId) {
  if (!childId) return null;
  try {
    var resp = await fetch('/ai/insights/' + encodeURIComponent(childId), { credentials: 'same-origin' });
    if (!resp.ok) {
      var txt = '';
      try {
        var j = await resp.json(); txt = JSON.stringify(j);
      } catch (e) {
        try { txt = await resp.text(); } catch (e2) { txt = resp.statusText; }
      }
      window.debugAIError('Fetch error ' + resp.status + ': ' + txt);
      return null;
    }
    var json = await resp.json();
    return json;
  } catch (e) {
    console.error('Failed to fetch AI insights', e);
    window.debugAIError(e.message || String(e));
    return null;
  }
}

async function refreshAI() {
  var childId = window.M2E_CHILD_ID || sessionStorage.getItem('m2e_child_id');
  if (!childId) return;
  var box = document.getElementById('ai-box');
  var content = box ? box.querySelector('.ai-content') : null;
  if (content) {
    content.innerHTML = '<div class="ai-loading">Loading AI insights...</div>';
    try { content.style.maxHeight = content.scrollHeight + 'px'; } catch (e) {}
  }

  console.debug('AI: fetching insights for', childId);
  var insights = await fetchInsights(childId);
  if (!insights) {
    // Show actionable fallback
    var debugUrl = '/ai/insights/' + encodeURIComponent(childId) + '?debug=1';
    var msg = '<div class="ai-row ai-warning">Unable to load AI insights. Possible causes: not logged in, server error, or models missing.</div>' +
              '<div class="ai-row">Try: <a href="' + debugUrl + '" target="_blank">Open debug response</a> or <button id="ai-refresh-fallback" class="btn">Retry</button></div>';
    if (content) content.innerHTML = msg;
    // hook retry
    setTimeout(function() {
      var b = document.getElementById('ai-refresh-fallback'); if (b) b.addEventListener('click', function(){ refreshAI(); });
    }, 100);
    return;
  }

  setAiContent(insights);
}

// Public refresh helper
window.refreshAI = refreshAI;

document.addEventListener('DOMContentLoaded', function() {
  // Insert the AI box near the top of the dashboard
  createAiBoxIfMissing();

  // Hook up toggle
  var header = document.querySelector('#ai-box .ai-header');
  if (header) header.addEventListener('click', toggleAiBox);

  // Initial fetch
  var childId = window.M2E_CHILD_ID || sessionStorage.getItem('m2e_child_id');
  if (childId) sessionStorage.setItem('m2e_child_id', childId);
  refreshAI();

  // Open the AI box by default so loading text is visible
  var box = document.getElementById('ai-box');
  if (box) {
    box.classList.add('open');
    var content = box.querySelector('.ai-content');
    if (content) content.style.maxHeight = content.scrollHeight + 'px';
  }

  // Listen for app-wide custom events to refresh AI insights
  ['activity:submitted', 'strava:sync', 'timer:stopped'].forEach(function(evt) {
    document.addEventListener(evt, function() {
      // small debounce
      setTimeout(refreshAI, 500);
    });
  });

  // Also refresh when the app emits a custom `ai:refresh` event
  document.addEventListener('ai:refresh', function() { refreshAI(); });
});
