document.getElementById("registerForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirmPassword").value;
    const message = document.getElementById("message");

    if (password !== confirm) {
        message.innerText = "Passwords do not match";
        return;
    }

    fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    })
    .then(res => res.json())
    .then(data => {
        message.innerText = data.message;
        if (data.status === "success") {
            window.location.href = "/frontend/login.html";
        }
    })
    .catch(() => {
        message.innerText = "Server error";
    });
});