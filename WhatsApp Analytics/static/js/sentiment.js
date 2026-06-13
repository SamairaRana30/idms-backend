let pieChartInst, lineChartInst;

async function loadSentiment() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/sentiment?group_id=${groupId}`);

    destroyChart(pieChartInst);
    pieChartInst = pieChart(
        document.getElementById('sentimentPie'),
        ['Positive', 'Negative', 'Neutral'],
        [data.positive_count, data.negative_count, data.neutral_count]
    );

    destroyChart(lineChartInst);
    lineChartInst = lineChart(
        document.getElementById('sentimentLine'),
        data.timeline.labels,
        data.timeline.values,
        'Messages'
    );
}

onGroupChange(loadSentiment);
