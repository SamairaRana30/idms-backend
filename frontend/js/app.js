const BASE_URL = "http://127.0.0.1:5000/api";

// LOGIN (dummy for now)
function login() {
    alert("Login working (dummy) ✅");
}

// REGISTER USER
async function registerUser(event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${BASE_URL}/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.status === "success") {
            alert("User registered ✅");
            loadUsers();
        } else {
            alert("Error ❌");
        }

    } catch (error) {
        console.error(error);
    }
}


// LOAD USERS
async function loadUsers() {
    const table = document.getElementById("userTable");

    if (!table) {
        console.error("userTable not found ❌");
        return;
    }

    table.innerHTML = "";

    try {
        const response = await fetch(`${BASE_URL}/users`);
        const data = await response.json();

        data.data.forEach(user => {
            const row = `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                </tr>
            `;
            table.innerHTML += row;
        });

    } catch (error) {
        console.error("Load error:", error);
    }
}

// AUTO LOAD
window.onload = loadUsers;