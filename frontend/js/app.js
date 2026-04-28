const BASE_URL = "http://127.0.0.1:5000/api/users";

// LOAD USERS
async function loadUsers() {
    const table = document.getElementById("userTable");
    table.innerHTML = "";

    const res = await fetch(BASE_URL);
    const data = await res.json();

    data.forEach(user => {
        const row = `
            <tr>
                <td>${user.id}</td>
                <td>
                    <input type="text" id="email-${user.id}" value="${user.email}">
                </td>
                <td>
                    <button onclick="updateUser(${user.id})">Update</button>
                    <button onclick="deleteUser(${user.id})">Delete</button>
                </td>
            </tr>
        `;
        table.innerHTML += row;
    });
}

// REGISTER USER
async function registerUser(event) {
    event.preventDefault();

    const email = document.getElementById("email").value;

    await fetch(BASE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    });

    document.getElementById("email").value = "";
    loadUsers();
}

// DELETE USER
async function deleteUser(id) {
    await fetch(`${BASE_URL}/${id}`, {
        method: "DELETE"
    });

    loadUsers();
}

// UPDATE USER ✅
async function updateUser(id) {
    const newEmail = document.getElementById(`email-${id}`).value;

    await fetch(`${BASE_URL}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: newEmail })
    });

    loadUsers();
}