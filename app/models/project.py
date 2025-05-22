from app.extensions import db
from app.models import TimeStampBase


class Project(db.Model, TimeStampBase):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    tasks = db.relationship(
        "Task",
        backref="project",
        lazy=True,
        cascade="all, delete-orphan",  # delete all task when project is deleted
        passive_deletes=True,
    )
