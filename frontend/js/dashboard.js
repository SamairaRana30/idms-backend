const token = localStorage.getItem("token");
const userName = localStorage.getItem("userName");
const role = localStorage.getItem("role");

if (!token) {
  window.location.href = "/frontend/login.html";
}

// Populate welcome and sidebar
document.getElementById("welcome").innerText = `Welcome back, ${userName || "User"}!`;
document.getElementById("sidebarEmail").innerText = userName || "";
document.getElementById("sidebarRole").innerText = role || "user";
document.getElementById("avatarInitial").innerText = (userName || "U")[0].toUpperCase();

// Profile card
document.getElementById("profileEmail").innerText = userName || "—";
document.getElementById("profileRole").innerText = role || "—";

// Load users if admin
if (role === "admin") {
  document.getElementById("usersNavItem").style.display = "block";
  document.getElementById("usersCard").style.display = "block";
  document.getElementById("statsGrid").style.display = "grid";

  fetch("/api/v1/users", {
    headers: { "Authorization": `Bearer ${token}` }
  })
  .then(res => res.json())
  .then(data => {
    if (!data.success) return;

    const users = data.users;

    document.getElementById("statTotal").innerText = users.length;
    document.getElementById("statActive").innerText = users.filter(u => u.is_active).length;
    document.getElementById("statAdmins").innerText = users.filter(u => u.role === "admin").length;

    const tbody = document.getElementById("usersTableBody");
    tbody.innerHTML = users.map(u => `
      <tr>
        <td>${u.full_name || '—'}</td>
        <td>${u.email}</td>
        <td><span class="badge badge-${u.role}">${u.role}</span></td>
        <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
      </tr>
    `).join("");
  })
  .catch(() => {
    document.getElementById("usersTableBody").innerHTML =
      '<tr><td colspan="4" style="text-align:center;color:red">Failed to load users</td></tr>';
  });
}

function logout() {
  localStorage.clear();
  window.location.href = "/frontend/login.html";
}
