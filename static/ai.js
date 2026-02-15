// AI frontend logic: fetches insights and updates the collapsible AI box.
// Expects `window.M2E_CHILD_ID` to be set before this script is loaded.

function createAiBoxIfMissing() {
  var container = document.querySelector('.dashboard-main');
  if (!container) return;
  if (document.getElementById('ai-box')) return;

  var box = document.createElement('div');
  box.id = 'ai-box';
  box.className = 'ai-collapsible';
  box.innerHTML = "<div class=\"ai-header\">Your AI Training Partner <span class='ai-toggle'>▼</span></div><div class=\"ai-content\">Loading AI insights...</div>";
  container.insertBefore(box, container.firstChild);
}

function setAiContent(insights) {
  var box = document.getElementById('ai-box');
  if (!box) return;
  var content = box.querySelector('.ai-content');
  if (!content) return;

  var html = '';
  if (insights) {
    html += '<div class="ai-row"><strong>Message:</strong> ' + (insights.message || '') + '</div>';
    html += '<div class="ai-row"><strong>Predicted Minutes:</strong> ' + (insights.predicted_minutes || 0) + '</div>';
    html += '<div class="ai-row"><strong>Challenge:</strong> ' + (insights.challenge_recommendation || '') + '</div>';
    html += '<div class="ai-row"><strong>Workout:</strong> ' + (insights.recommended_workout || '') + '</div>';
    if (insights.streak_risk) {
      html += '<div class="ai-row ai-warning">⚠ Streak at risk — try a short activity to keep it.</div>';
    }
  } else {
    html = '<div class="ai-row">AI unavailable right now.</div>';
  }

  content.innerHTML = html;
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
    var resp = await fetch('/ai/insights/' + encodeURIComponent(childId));
    if (!resp.ok) return null;
    var json = await resp.json();
    return json;
  } catch (e) {
    console.error('Failed to fetch AI insights', e);
    return null;
  }
}

async function refreshAI() {
  var childId = window.M2E_CHILD_ID || sessionStorage.getItem('m2e_child_id');
  if (!childId) return;
  var insights = await fetchInsights(childId);
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
