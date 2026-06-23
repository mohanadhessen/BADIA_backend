import uuid

import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from database.base import Base
from database.session import engine
from models import * 




@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session):
    user = User(company_name="Test Co", email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_request(db_session, sample_user):
    request = Request(
        user_id=sample_user.id,
        request_id=str(uuid.uuid4()),
        service_type="feasibility_study",
        status="pending",
    )
    db_session.add(request)
    db_session.commit()
    return request


@pytest.fixture
def make_user_file():
    def _make_user_file(request_id, suffix="1", size=1024):
        return UserFile(
            request_id=request_id,
            file_id=str(uuid.uuid4()),
            file_key=f"uploads/file{suffix}.pdf",
            filename=f"file{suffix}.pdf",
            content_type="application/pdf",
            size=size,
        )
    return _make_user_file