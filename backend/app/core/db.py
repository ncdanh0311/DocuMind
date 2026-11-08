from sqlmodel import Session, create_engine
from backend.app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 5})

def get_session():
    with Session(engine) as session:
        yield session
