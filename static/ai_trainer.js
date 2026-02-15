// ai_trainer.js
// Local ML/AI logic for "Your AI Trainer" (text-only insights)

// Analyze activity data and return a list of insights/tips
function getAITrainerInsights(activities) {
    if (!activities || activities.length === 0) {
        return [
            "No activities found. Try logging your first activity to get personalized tips!",
            "Remember: Consistency is key. Even a short walk counts!"
        ];
    }

    // Example features: frequency, intensity, streaks, inactivity, variety
    const now = new Date();
    const last7 = activities.filter(a => {
        const d = new Date(a.activity_date || a.start_date);
        return (now - d) / (1000 * 60 * 60 * 24) < 7;
    });
    const lastActivity = activities[0];
    const daysSinceLast = lastActivity ? Math.floor((now - new Date(lastActivity.activity_date || lastActivity.start_date)) / (1000 * 60 * 60 * 24)) : null;
    const types = new Set(activities.map(a => a.type));
    const hardCount = activities.filter(a => (a.intensity || '').toLowerCase() === 'hard').length;
    const easyCount = activities.filter(a => (a.intensity || '').toLowerCase() === 'easy').length;
    const total = activities.length;

    const insights = [];

    // Inactivity
    if (daysSinceLast !== null && daysSinceLast > 3) {
        insights.push(`It's been ${daysSinceLast} days since your last activity. Try a short session today!`);
    }

    // Frequency
    if (last7.length < 3) {
        insights.push("Try to be active at least 3 days a week for best results.");
    } else {
        insights.push("Great job staying active this week! Keep it up.");
    }

    // Intensity balance
    if (hardCount > total * 0.5) {
        insights.push("Consider mixing in some easy or moderate sessions for recovery.");
    } else if (easyCount > total * 0.7) {
        insights.push("Add a higher intensity session to boost your fitness.");
    }

    // Variety
    if (types.size === 1) {
        insights.push("Try a new activity type for variety and fun.");
    }

    // Streak
    if (last7.length >= 5) {
        insights.push("You're on a roll! Can you keep your streak going?");
    }

    // General tip
    if (insights.length < 2) {
        insights.push("Remember to log your activities for more personalized tips.");
    }

    return insights;
}

// Render AI Trainer insights in the dashboard
function renderAITrainer(activities) {
    let container = document.getElementById('ai-trainer');
    if (!container) {
        // Insert after greeting-section
        const greeting = document.querySelector('.greeting-section');
        if (greeting) {
            container = document.createElement('div');
            container.id = 'ai-trainer';
            container.style.background = 'rgba(0, 212, 255, 0.08)';
            container.style.border = '1px solid #00d4ff33';
            container.style.borderRadius = '12px';
            container.style.padding = '20px';
            container.style.marginBottom = '20px';
            container.innerHTML = '<h3 style="color:#00d4ff; margin-bottom:10px;">🤖 Your AI Trainer</h3><div id="ai-trainer-insights"></div>';
            greeting.parentNode.insertBefore(container, greeting.nextSibling);
        }
    }
    if (container) {
        const insights = getAITrainerInsights(activities);
        const insightsHtml = insights.map(tip => `<div style="color:#00d4ff; margin-bottom:8px; font-size:15px;">${tip}</div>`).join('');
        document.getElementById('ai-trainer-insights').innerHTML = insightsHtml;
    }
}

// Hook into activity loading
(function() {
    const origLoadActivities = window.loadActivities;
    window.loadActivities = async function() {
        await origLoadActivities.apply(this, arguments);
        // After activities are loaded and rendered, get the data and show AI Trainer
        let allActivities = [];
        try {
            // Try to reuse the same logic as dashboard
            const stravaResp = await fetch('/api/activities');
            const manualResp = await fetch('/api/manual-activities');
            let strava = stravaResp.ok ? await stravaResp.json() : [];
            let manual = manualResp.ok ? (await manualResp.json()).activities || [] : [];
            allActivities = [
                ...strava.map(a => ({...a, activity_date: a.start_date})),
                ...manual.map(a => ({...a, activity_date: a.date}))
            ];
            // Sort by date descending
            allActivities.sort((a, b) => new Date(b.activity_date) - new Date(a.activity_date));
        } catch (e) {}
        renderAITrainer(allActivities);
    };
})();
