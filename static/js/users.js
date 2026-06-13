let influenceChart;

async function loadUsers() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/influential-users?group_id=${groupId}`);
    const top = data.users.slice(0, 15);

    destroyChart(influenceChart);
    influenceChart = barChart(
        document.getElementById('influenceChart'),
        top.map(u => u.sender_name),
        top.map(u => u.influence_score),
        'Influence Score'
    );
}

onGroupChange(loadUsers);
