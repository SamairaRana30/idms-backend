const token = localStorage.getItem("token");const token = localStorage!token) {
    window.location.href = "/frontend/login.html";
}

const viewDiv = document.getElementById("viewProfile");
const editDiv = document.getElementById("editProfile");

const fullName = document.getElementById("fullName");
const role = document.getElementById("role");
const email = document.getElementById("email");
const phone = document.getElementById("phone");
const address = document.getElementById("address");
const joinDate = document.getElementById("joinDate");

function loadProfile() {
    fetch("/api/v1/profile", {
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
        const u = data.data;
        fullName.innerText = u.full_name;
        role.innerText = u.role;
        email.innerText = u.email;
        phone.innerText = u.phone || "-";
        address.innerText = u.address || "-";
        joinDate.innerText = u.join_date;

        // Pre-fill edit form
        editName.value = u.full_name;
        editEmail.value = u.email;
        editPhone.value = u.phone || "";
        editAddress.value = u.address || "";
    });
}

function enableEdit() {
    viewDiv.style.display = "none";
    editDiv.style.display = "block";
}

function cancelEdit() {
    editDiv.style.display = "none";
    viewDiv.style.display = "block";
}

function saveProfile() {
    const name = editName.value.trim();
    const emailVal = editEmail.value.trim();

    if (!name || !emailVal) {
        message.innerText = "Name and email are required";
        return;
    }

    fetch("/api/v1/profile", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            name: name,
            email: emailVal,
            phone: editPhone.value,
            address: editAddress.value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            message.className = "text-success";
            message.innerText = data.message;
            cancelEdit();
            loadProfile(); // refresh immediately
        } else {
            message.innerText = data.message;
        }
    });
}

loadProfile();
