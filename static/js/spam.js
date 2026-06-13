let spamChart;

async function loadSpam() {
    const groupId = getSelectedGroupId();
    if (!groupId) return;

    const data = await apiFetch(`/api/v1/analytics/spam?group_id=${groupId}`);

    destroyChart(spamChart);
    spamChart = barChart(
        document.getElementById('spamUsersChart'),
        data.suspected_users.map(u => u.sender_name),
        data.suspected_users.map(u => u.spam_message_count),
        'Spam Messages'
    );

    const list = document.getElementById('spamList');
    list.innerHTML = data.spam_messages.slice(0, 20).map(m =>
        `<div class="spam-item"><strong>${m.sender_name}</strong> (score: ${m.spam_score})
        <br><small>${m.message_text.substring(0, 100)}...</small></div>`
    ).join('') || '<p class="text-muted">No spam detected</p>';
}

onGroupChange(loadSpam);
