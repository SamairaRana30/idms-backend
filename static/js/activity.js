let topChart, bottomChart;

async function loadActivity() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/activity?group_id=${groupId}`);

    destroyChart(topChart);
    topChart = barChart(
        document.getElementById('topUsersChart'),
        data.top_10_active_users.map(u => u.sender_name),
        data.top_10_active_users.map(u => u.message_count),
        'Messages'
    );

    destroyChart(bottomChart);
    bottomChart = barChart(
        document.getElementById('bottomUsersChart'),
        data.bottom_10_active_users.map(u => u.sender_name),
        data.bottom_10_active_users.map(u => u.message_count),
        'Messages'
    );
}

onGroupChange(loadActivity);
