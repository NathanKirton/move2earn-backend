// AI frontend logic: fetches insights and updates the collapsible AI box.
// Expects `window.M2E_CHILD_ID` to be set before this script is loaded.

function createAiBoxIfMissing() {
  var container = document.querySelector('.dashboard-main');
  if (!container) return;
    if (document.getElementById('ai-box')) return document.getElementById('ai-box');
    const box = document.createElement('div');
    box.id = 'ai-box';
    box.className = 'ai-box';
    box.innerHTML = `
        <div class="ai-header">Your AI Training Partner <span class="ai-arrow">▾</span></div>
        <div class="ai-content">
            <div class="ai-loading">Loading AI insights...</div>
        </div>
    `;
    document.body.insertBefore(box, document.body.firstChild);
    // Ensure visible
    box.style.opacity = 1;
    // Toggle open/close with animation-friendly class
    const header = box.querySelector('.ai-header');
    header.style.cursor = 'pointer';
    header.addEventListener('click', function () {
        box.classList.toggle('open');
        const arrow = box.querySelector('.ai-arrow');
        if (box.classList.contains('open')) arrow.style.transform = 'rotate(180deg)';
        else arrow.style.transform = 'rotate(0deg)';
    });
    return box;
}

function setAiContent(insights) {
  var box = document.getElementById('ai-box');
    const content = box.querySelector('.ai-content');
    content.innerHTML = '';

    if (!insights) {
        content.innerHTML = '<div class="ai-empty">No insights available.</div>';
        return;
    }

    // Header / quick summary
    const summary = document.createElement('div');
    summary.className = 'ai-summary';
    const title = document.createElement('div');
    title.className = 'ai-title';
    title.innerText = 'Insights';
    summary.appendChild(title);

    if (insights.message) {
        const msg = document.createElement('div');
        msg.className = 'ai-message';
        msg.innerText = insights.message;
        summary.appendChild(msg);
    }
    content.appendChild(summary);

    // Stats
    const stats = document.createElement('div');
    stats.className = 'ai-stats';
    const ul = document.createElement('ul');
    ul.style.margin = '6px 0 0 12px';
    const addStat = (k, v) => { const li = document.createElement('li'); li.innerText = `${k}: ${v}`; ul.appendChild(li); }
    addStat('Activities (7d)', insights.total_activities || 0);
    if (insights.avg_distance !== undefined) addStat('Avg distance (km)', (insights.avg_distance || 0).toFixed(2));
    if (insights.avg_pace !== undefined) addStat('Avg pace (min/km)', (insights.avg_pace || 0).toFixed(2));
    if (insights.avg_heartrate !== undefined) addStat('Avg HR', Math.round(insights.avg_heartrate || 0));
    if (insights.streak_length !== undefined) addStat('Streak', insights.streak_length);
    if (insights.pace_trend) addStat('Pace trend', insights.pace_trend);
    stats.appendChild(ul);
    content.appendChild(stats);

    // Tips / actionable next steps
    if (insights.tips && insights.tips.length) {
        const tips = document.createElement('div');
        tips.className = 'ai-tips';
        const h = document.createElement('div');
        h.className = 'ai-subhead';
        h.innerText = 'Recommendations';
        tips.appendChild(h);
        const tlist = document.createElement('ol');
        insights.tips.forEach(t => {
            const li = document.createElement('li');
            li.innerText = t;
            tlist.appendChild(li);
        });
        tips.appendChild(tlist);
        content.appendChild(tips);
    }

    // Model diagnostics + actions
    const actions = document.createElement('div');
    actions.className = 'ai-actions';
    actions.style.marginTop = '8px';
    if (insights._model_status !== undefined) {
        const diag = document.createElement('div');
        diag.className = 'ai-debug';
        diag.innerText = `Model loaded: ${insights._model_status} (source: ${insights._model_source})`;
        actions.appendChild(diag);
    }
    // Retry / refresh
    const retry = document.createElement('button');
    retry.className = 'ai-btn';
    retry.innerText = 'Refresh';
    retry.addEventListener('click', fetchInsights);
    actions.appendChild(retry);

    // If user not logged in, show login hint (server will return 401)
    const login = document.createElement('a');
    login.href = '/login';
    login.innerText = 'Log in';
    login.style.marginLeft = '8px';
    actions.appendChild(login);

    content.appendChild(actions);
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
