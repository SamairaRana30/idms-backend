const token = localStorage.getItem("token");
let members = [];
let deleteId = null;

if (!token) location.href = "/frontend/login.html";

function loadMembers() {
  fetch("/api/v1/admin/members", {
    headers: { "Authorization": token }
  })
  .then(res => res.json())
  .then(data => {
    members = data.data || [];
    drawTable();
  });
}

function drawTable() {
  const tbody = document.getElementById("membersBody");
  tbody.innerHTML = "";

  members.forEach(m => {
    tbody.innerHTML += `
      <tr>
        <td>${m.name}</td>
        <td>${m.email}</td>
        <td>${m.role}</td>
        <td>${m.status}</td>
        <td>${m.join_date}</td>
        <td>
          <button class="btn btn-danger btn-sm"
            onclick="confirmDelete(${m.id})">Delete</button>
        </td>
      </tr>
    `;
  });
}

function confirmDelete(id) {
  deleteId = id;
  new bootstrap.Modal(document.getElementById("deleteModal")).show();
}

function deleteConfirmed() {
  fetch(`/api/v1/admin/members/${deleteId}`, {
    method: "DELETE",
    headers: { "Authorization": token }
  })
  .then(() => {
    loadMembers();
    bootstrap.Modal.getInstance(
      document.getElementById("deleteModal")
    ).hide();
  });
}

loadMembers();