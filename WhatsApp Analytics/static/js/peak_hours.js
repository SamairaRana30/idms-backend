let peakChart;

async function loadPeakHours() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/peak-hours?group_id=${groupId}`);

    destroyChart(peakChart);
    peakChart = barChart(
        document.getElementById('peakHoursChart'),
        data.peak_hours.map(h => `${h.hour}:00`),
        data.peak_hours.map(h => h.message_count),
        'Messages'
    );
}

onGroupChange(loadPeakHours);
