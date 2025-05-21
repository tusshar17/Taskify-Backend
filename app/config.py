from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("MYSQL_URI")
    SQLALCHEMY_TRACK_MODIFICATION = False
