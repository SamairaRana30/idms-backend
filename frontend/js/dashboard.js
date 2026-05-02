const token = localStorage.getItem("token");
const name = localStorage.getItem("name");

if (!token) {
  window.location.href = "/frontend/login.html";
}

document.getElementById("welcome").innerText = `Hello, ${name}! 💖`;

function logout() {
  localStorage.clear();
  window.location.href = "/frontend/login.html";
}
