import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import Config

from blueprints.auth          import auth_bp
from blueprints.users         import users_bp
from blueprints.migration     import migration_bp
from blueprints.documents     import documents_bp
from blueprints.voting        import voting_bp
from blueprints.meetings      import meetings_bp
from blueprints.notifications import notifications_bp
from blueprints.finances      import finances_bp
from blueprints.analytics     import analytics_bp
from blueprints.audit         import audit_bp

FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')


def create_app():
    if not Config.JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    app = Flask(__name__)
    app.config['JWT_SECRET'] = Config.JWT_SECRET

    CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}})

    for bp in [auth_bp, users_bp, migration_bp, documents_bp,
               voting_bp, meetings_bp, notifications_bp,
               finances_bp, analytics_bp, audit_bp]:
        app.register_blueprint(bp)

    return app


app = create_app()


@app.route('/frontend/')
@app.route('/frontend/<path:filename>')
def frontend(filename='index.html'):
    return send_from_directory(FRONTEND, filename)


@app.route('/')
def home():
    return send_from_directory(FRONTEND, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=Config.ENV == 'development', port=port)