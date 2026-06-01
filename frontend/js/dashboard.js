const token = localStorage.getItem("token");
const userName = localStorage.getItem("userName");

if (!token) {
  window.location.href = "/frontend/login.html";
}

document.getElementById("welcome").innerText = `Hello, ${userName || "User"}!`;

function logout() {
  localStorage.clear();
  window.location.href = "/frontend/login.html";
}
