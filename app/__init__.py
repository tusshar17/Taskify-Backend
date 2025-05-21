from flask import Flask
from .extensions import db, migrate, cors
from .config import Config

import pymysql

pymysql.install_as_MySQLdb()


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)
    migrate(app, db)

    from .models import Project, Task, User

    with app.app_context():
        db.create_all()
    cors.init_app(app)

    # register routes
    from app.routes.project_routes import project_bp
    from app.routes.task_routes import task_bp
    from app.routes.user_routes import user_bp

    app.register_blueprint(project_bp, url_prefix="/api/project")
    app.register_blueprint(task_bp, url_prefix="/api/project/<int:project_id>/task")
    app.register_blueprint(user_bp, url_prefix="/api/user")

    return app
