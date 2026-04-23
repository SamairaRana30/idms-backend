document.getElementById("registerForm")?.addEventListener("submit", async function(e) {
    e.preventDefault();

    const full_name = document.getElementById("name").value;
    const email = document.getElementById("email").value;

    try {
        const response = await fetch("https://idms-backend-deu6.onrender.com/api/v1/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                full_name: full_name,
                email: email,
                password: "Test@123"   // temporary password
            })
        });

        const data = await response.json();

        document.getElementById("responseMsg").innerText =
            data.message || JSON.stringify(data);

    } catch (error) {
        document.getElementById("responseMsg").innerText =
            "Error connecting to backend";
    }
});