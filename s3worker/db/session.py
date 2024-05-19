from sqlalchemy.orm import sessionmaker
from .engine import engine


def get_db():
    SessionLocal = sessionmaker(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
