import pytest

from app.core.database import Base, engine


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
