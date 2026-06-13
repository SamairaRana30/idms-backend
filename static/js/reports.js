let monthlyChart, emotionsChart;

async function loadReports() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const [monthly, emotions, activity, sentiment] = await Promise.all([
        apiFetch(`/api/v1/analytics/frequency/monthly?group_id=${groupId}`),
        apiFetch(`/api/v1/analytics/emotions?group_id=${groupId}`),
        apiFetch(`/api/v1/analytics/activity?group_id=${groupId}`),
        apiFetch(`/api/v1/analytics/sentiment?group_id=${groupId}`)
    ]);

    destroyChart(monthlyChart);
    monthlyChart = lineChart(
        document.getElementById('monthlyChart'),
        monthly.labels,
        monthly.values
    );

    destroyChart(emotionsChart);
    emotionsChart = barChart(
        document.getElementById('emotionsChart'),
        emotions.topics.map(t => t.topic),
        emotions.topics.map(t => t.engagement_score),
        'Engagement'
    );

    document.getElementById('reportSummary').textContent = JSON.stringify({
        total_messages: activity.total_messages,
        sentiment: {
            positive: sentiment.positive_count,
            negative: sentiment.negative_count,
            neutral: sentiment.neutral_count
        },
        emotional_topics: emotions.topics
    }, null, 2);
}

onGroupChange(loadReports);
