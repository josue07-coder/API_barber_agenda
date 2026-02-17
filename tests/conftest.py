
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database.base import Base
from sqlalchemy.pool import StaticPool
from app.database.session import get_db

from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.core.dependecies import get_current_user



SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db, override_current_user):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def barber_token(db):
    barber = User(
        name="Barber Test",
        email="barber@test.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )
    db.add(barber)
    db.commit()

    token = create_access_token(
        {"sub": str(barber.id), "role": barber.role}
    )
    return token


@pytest.fixture
def admin_token(db):
    admin = User(
        name="Admin Test",
        email="admin@test.com",
        password=get_password_hash("test1234"),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()

    token = create_access_token(
        {"sub": str(admin.id), "role": admin.role}
    )
    return token

@pytest.fixture
def override_current_user():
    def _override():
        return User(
            id=1,
            name="Admin",
            email="admin@test.com",
            role="admin",
            is_active=True
        )

    return _override