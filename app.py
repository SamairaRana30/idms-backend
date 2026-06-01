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


def create_app():
    if not Config.JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    app = Flask(__name__)
    app.config['JWT_SECRET'] = Config.JWT_SECRET

    CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}})

    blueprints = [
        auth_bp, users_bp, migration_bp, documents_bp,
        voting_bp, meetings_bp, notifications_bp, finances_bp, analytics_bp
    ]
    for bp in blueprints:
        app.register_blueprint(bp)

    @app.route('/frontend/<path:filename>')
    def frontend(filename):
        return send_from_directory('frontend', filename)

    @app.route('/')
    def home():
        return jsonify({
            'message': 'IDMS API is running!',
            'version': '2.0.0',
            'environment': Config.ENV,
            'docs': '/api/v1/health'
        })

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=Config.ENV == 'development', port=port)
