document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const resultDiv = document.getElementById('uploadResult');

    try {
        const response = await fetch('/api/v1/upload', {
            method: 'POST',
            credentials: 'same-origin',
            headers: getAuthHeaders(),
            body: formData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Upload failed');
        resultDiv.innerHTML = `<div class="alert alert-success d-flex align-items-center gap-2">
            <i class="bi bi-check-circle-fill"></i>
            Imported <strong>${data.message_count}</strong> messages into group "<strong>${data.group_name}</strong>" (ID: ${data.group_id})
        </div>`;
        form.reset();
    } catch (err) {
        resultDiv.innerHTML = `<div class="alert alert-danger d-flex align-items-center gap-2">
            <i class="bi bi-exclamation-triangle-fill"></i> ${err.message}
        </div>`;
    }
});
