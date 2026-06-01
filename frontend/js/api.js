const API_BASE = "/api/v1";

export async function register(email, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    return res.json();
}

export async function login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    return res.json();
}

export async function getUsers(token) {
    const res = await fetch(`${API_BASE}/users`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    });
    return res.json();
}

export async function getProfile(token) {
    const res = await fetch(`${API_BASE}/auth/profile`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    });
    return res.json();
}
