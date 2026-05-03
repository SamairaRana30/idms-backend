const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/frontend/login.html";
}

document.getElementById("welcome").innerText = "Hello 👋";

function logout() {
    localStorage.clear();
    window.location.href = "/frontend/login.html";
}