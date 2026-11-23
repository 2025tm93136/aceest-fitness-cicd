"""ACEest Fitness & Gym - Flask application package.

Each feature lives in its own blueprint module. Modules are registered in the
order they were introduced across the ACEest releases (see CHANGELOG.md).
"""
import importlib
import os
from pathlib import Path

from flask import Flask, jsonify, render_template

from . import db

FEATURE_MODULES = (
    "programs",      # v1.0   - fitness programs (workout + diet plans)
    "clients",       # v1.1   - client profiles and calorie estimation
    "exports",       # v1.1.2 - CSV export
    "progress",      # v2.0.1 - weekly adherence tracking (v2.2.1 adds chart data)
    "workouts",      # v2.2.4 - workout log, body metrics, BMI
    "auth",          # v3.1.2 - login, AI-style program generator, client report
    "membership",    # v3.2.4 - membership status and renewal
)


def read_version():
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("ACEEST_DB", "aceest_fitness.db"),
        APP_VERSION=os.environ.get("APP_VERSION", read_version()),
        DEPLOYMENT=os.environ.get("DEPLOYMENT_TRACK", "local"),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-secret"),
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    features = []
    for name in FEATURE_MODULES:
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except ModuleNotFoundError:
            continue
        app.register_blueprint(module.bp)
        features.append(name)
    app.config["FEATURES"] = features

    with app.app_context():
        db.init_db()

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            version=app.config["APP_VERSION"],
            track=app.config["DEPLOYMENT"],
            features=features,
        )

    @app.get("/health")
    def health():
        return jsonify(status="UP")

    @app.get("/version")
    def version():
        return jsonify(
            version=app.config["APP_VERSION"],
            track=app.config["DEPLOYMENT"],
            features=features,
        )

    @app.after_request
    def add_version_headers(response):
        response.headers["X-App-Version"] = app.config["APP_VERSION"]
        response.headers["X-Deployment-Track"] = app.config["DEPLOYMENT"]
        return response

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify(error="Not found"), 404

    return app
