document.getElementById("registerForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const message = document.getElementById("message");

    message.style.color = "red";

    if (!name || !email || !password || !confirmPassword) {
        message.innerText = "All fields are required";
        return;
    }

    if (password.length < 6) {
        message.innerText = "Password must be at least 6 characters";
        return;
    }

    if (password !== confirmPassword) {
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
        if (data.status === "success") {
            message.style.color = "green";
            message.innerText = "Registration successful! Redirecting...";
            setTimeout(() => {
                window.location.href = "/frontend/login.html";
            }, 1500);
        } else {
            message.innerText = data.message;
        }
    })
    .catch(() => {
        message.innerText = "Server error";
    });
});