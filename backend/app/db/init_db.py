from app.db.database import engine
from app.models.database_models import Base


def init_db():
    """
    Creates all database tables defined in Base.metadata
    if they do not already exist.

    This operation is safe and non-destructive:
    it will not drop, alter, or delete existing tables or data.
    """
    print("Creating/verifying database tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Database schema synchronization complete.")


if __name__ == "__main__":
    init_db()
