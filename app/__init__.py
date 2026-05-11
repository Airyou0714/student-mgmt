from pathlib import Path

from flask import Flask

from app.extensions import db, login_manager
from app.models import User


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.Config")

    instance_dir = Path(app.root_path).parent / "instance"
    instance_dir.mkdir(exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        from app.db_migrate import run_sqlite_migrations

        run_sqlite_migrations()
        _ensure_default_admin(app)

    return app


def _ensure_default_admin(app) -> None:
    username = app.config["DEFAULT_ADMIN_USERNAME"]
    password = app.config["DEFAULT_ADMIN_PASSWORD"]
    if User.query.filter_by(username=username).first() is None:
        u = User(username=username)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
