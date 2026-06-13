let dailyChart, mediaChart;

async function loadDashboard() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    try {
        const [activity, sentiment, peak, daily, media] = await Promise.all([
            apiFetch(`/api/v1/analytics/activity?group_id=${groupId}`),
            apiFetch(`/api/v1/analytics/sentiment?group_id=${groupId}`),
            apiFetch(`/api/v1/analytics/peak-hours?group_id=${groupId}`),
            apiFetch(`/api/v1/analytics/frequency/daily?group_id=${groupId}`),
            apiFetch(`/api/v1/analytics/media-comparison?group_id=${groupId}`)
        ]);

        document.getElementById('kpi-total').textContent = activity.total_messages;
        document.getElementById('kpi-top-user').textContent =
            activity.top_10_active_users[0]?.sender_name || '-';
        document.getElementById('kpi-positive').textContent = sentiment.positive_count;
        document.getElementById('kpi-peak').textContent = `${peak.busiest_hour}:00`;

        destroyChart(dailyChart);
        dailyChart = lineChart(
            document.getElementById('dailyChart'),
            daily.labels,
            daily.values
        );

        destroyChart(mediaChart);
        mediaChart = pieChart(
            document.getElementById('mediaChart'),
            media.breakdown.map(b => b.type),
            media.breakdown.map(b => b.count)
        );
    } catch (e) {
        console.error(e);
    }
}

onGroupChange(loadDashboard);
