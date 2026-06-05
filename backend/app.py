from flask import Flask
from flask_cors import CORS
from voting import voting_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='/frontend')
CORS(app)

app.register_blueprint(voting_bp, url_prefix='/api/v1')

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    print("IDMS API is running!")
    app.run(debug=True, port=5000)