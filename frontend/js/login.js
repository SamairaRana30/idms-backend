document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message  = document.getElementById("message");

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
    .then(res => {
        if (res.success) {
            const { token, user } = res.data;
            localStorage.setItem("token",     token);
            localStorage.setItem("userName",  user.full_name || user.email);
            localStorage.setItem("userEmail", user.email);
            localStorage.setItem("role",      user.role);
            localStorage.setItem("userId",    user.id);

            message.style.color = "green";
            message.innerText   = "Login successful! Redirecting...";
            setTimeout(() => { window.location.href = "/frontend/dashboard.html"; }, 1000);
        } else {
            message.innerText = res.error || "Login failed";
        }
    })
    .catch(() => { message.innerText = "Server error. Try again."; });
});
