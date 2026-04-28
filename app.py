from flask import Flask
from routes.user_routes import user_routes

app = Flask(__name__)

# register blueprint
app.register_blueprint(user_routes)

# home route
@app.route("/")
def home():
    return "Hello World"

# run server
if __name__ == "__main__":
    app.run(debug=True)