from app.extensions import db
from app.models import TimeStampBase


class User(db.Model, TimeStampBase):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
