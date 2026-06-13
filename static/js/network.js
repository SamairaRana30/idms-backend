let networkChart;

async function loadNetwork() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/network?group_id=${groupId}`);

    document.getElementById('networkStats').innerHTML = `
        <li class="list-group-item">Nodes: ${data.nodes.length}</li>
        <li class="list-group-item">Edges: ${data.edges.length}</li>
        <li class="list-group-item">Density: ${data.density}</li>
        <li class="list-group-item">Communities: ${data.communities.length}</li>
    `;

    destroyChart(networkChart);
    const labels = data.centrality.slice(0, 10).map(c => c.user);
    const scores = data.centrality.slice(0, 10).map(c => c.score);
    networkChart = barChart(
        document.getElementById('networkCanvas'),
        labels,
        scores,
        'Centrality'
    );
}

onGroupChange(loadNetwork);
