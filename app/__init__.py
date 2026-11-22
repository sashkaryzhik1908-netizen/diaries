from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    csrf.init_app(app)
    db.init_app(app)

    from app import models as models
    import laboratory.models as laboratory_models
    from app.routes.auth import auth_bp
    from app.routes.categories import categories_bp
    from app.routes.therapy import therapy_bp
    from app.routes.diaries import diaries_bp
    from app.routes.diary_entries import diary_entries_bp
    from app.services.diary_service import to_local_time
    from laboratory.routes import laboratory_bp

    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_message = (
        "Для доступа к этой странице необходимо войти в систему."
    )
    login_manager.login_message_category = "warning"
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(therapy_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(diary_entries_bp)
    app.register_blueprint(laboratory_bp)

    @app.context_processor
    def inject_utilities():
        return dict(to_local_time=to_local_time)

    return app
