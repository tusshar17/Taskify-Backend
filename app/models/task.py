from app.extensions import db
from app.models import TimeStampBase

import enum


user_task = db.Table(
    "user_tasks",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("task_id", db.Integer, db.ForeignKey("task.id"), primary_key=True),
)


class StatusEnum(enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class Task(db.Model, TimeStampBase):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    status = db.Column(
        db.Enum(StatusEnum), default=StatusEnum.NOT_STARTED, nullable=False
    )
    due_date = db.Column(db.DateTime, nullable=False)

    project_id = db.Column(
        db.Integer, db.ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )

    users = db.relationship(
        "User",
        secondary="user_tasks",
        backref=db.backref("task", lazy="dynamic"),
        cascade="all, delete",
        passive_deletes=True,
    )
