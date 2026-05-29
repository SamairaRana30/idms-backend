document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.style.color = "red";

    if (!email || !password) {
        message.innerText = "Email and password are required";
        return;
    }

    fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Save token & user info
            localStorage.setItem("token", data.data.token);
            localStorage.setItem("userName", data.data.name);
            localStorage.setItem("role", data.data.role);

            message.style.color = "green";
            message.innerText = "Login successful! Redirecting...";

            setTimeout(() => {
                window.location.href = "/frontend/dashboard.html";
            }, 1000);
        } else {
            message.innerText = data.message;
        }
    })
    .catch(() => {
        message.innerText = "Server error. Try again.";
    });
});