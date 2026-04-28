from flask import Blueprint, request, jsonify
import jwt
import datetime
import json
from functools import wraps

user_routes = Blueprint('user_routes', __name__)

SECRET_KEY = "mysecretkey"

# 📁 Load & Save users
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

users = load_users()

# 🔐 Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            token = auth_header.split(" ")[1] if " " in auth_header else None

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data["email"]
        except:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# 🟢 REGISTER
@user_routes.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    for user in users:
        if user["email"] == email:
            return jsonify({"error": "User already exists"}), 400

    new_user = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": password
    }

    users.append(new_user)
    save_users(users)

    return jsonify({"message": "User registered successfully"}), 201


# 🟢 LOGIN
@user_routes.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    for user in users:
        if user["email"] == email and user["password"] == password:

            token = jwt.encode({
                "email": email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm="HS256")

            return jsonify({
                "success": True,
                "token": token
            })

    return jsonify({"error": "Invalid credentials"}), 401


# 🟢 PROFILE (protected)
@user_routes.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    for user in users:
        if user["email"] == current_user:
            return jsonify({
                "message": "Profile fetched",
                "user": user
            })

    return jsonify({"error": "User not found"}), 404