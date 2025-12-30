#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for the CleaningSession class.

import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.acmerobot import main, sessionDB
from src.acmerobot.sessionDB import CleaningSession


@pytest.fixture
def session_factory():
    """Provide a fresh in-memory database session factory for each test."""
    db_engine = create_engine("sqlite:///:memory:")
    sessionDB.Base.metadata.create_all(bind=db_engine)
    Session = sessionmaker(bind=db_engine)
    try:
        yield Session
    finally:
        sessionDB.Base.metadata.drop_all(bind=db_engine)
        db_engine.dispose()


def test_cleaning_session_table_metadata():
    """Test that the CleaningSession table has the correct metadata."""
    table = CleaningSession.__table__

    expected_columns = {
        "session_id",
        "start_time",
        "model",
        "final_state",
        "number_of_actions",
        "number_of_cleaned_tiles",
        "duration",
    }
    assert set(table.columns.keys()) == expected_columns
    assert table.c.session_id.primary_key

    required_columns = {
        "model",
        "final_state",
        "number_of_actions",
        "number_of_cleaned_tiles",
        "duration",
    }
    for column_name in required_columns:
        assert not table.c[column_name].nullable


def test_cleaning_session_persists_records(session_factory):
    """Test that a CleaningSession record can be created, saved, read and
    matches the input data."""

    Session = session_factory
    session = Session()

    try:
        expected_start_time = datetime.datetime(2025, 1, 1, 12, 0, 0)
        cleaning_session = CleaningSession(
            start_time=expected_start_time,
            model="R2-D2",
            final_state="completed",
            number_of_actions=42,
            number_of_cleaned_tiles=21,
            duration=127.5,
        )

        session.add(cleaning_session)
        session.commit()
        session.refresh(cleaning_session)

        stored = session.query(CleaningSession).one()
        assert stored.session_id == cleaning_session.session_id
        assert stored.model == "R2-D2"
        assert stored.final_state == "completed"
        assert stored.number_of_actions == 42
        assert stored.number_of_cleaned_tiles == 21
        assert pytest.approx(stored.duration) == 127.5
        assert stored.start_time == expected_start_time

    finally:
        session.close()


def test_cleaning_session_rejects_missing_required_fields(session_factory):
    """Test that creating a CleaningSession with missing required fields
    raises an IntegrityError."""
    Session = session_factory
    session = Session()
    try:
        invalid_session = CleaningSession(
            final_state="error",
            number_of_actions=3,
            number_of_cleaned_tiles=1,
            duration=14.0,
        )
        session.add(invalid_session)

        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_get_database_context_manager_closes_session(monkeypatch):
    """The dependency generator should close the session once consumed. This
    means that after the first next() call, the session is yielded, and on the
    second next() call, the session is closed and StopIteration is raised. We
    use monkeypatching to track whether close() was called.
    """
    captured = {"closed": False}

    original_session_local = main.SessionLocal

    def fake_session_local():
        session = original_session_local()

        def tracking_close():
            captured["closed"] = True
            session.__class__.close(session)

        session.close = tracking_close
        return session

    monkeypatch.setattr(main, "SessionLocal", fake_session_local)

    generator = main.get_database()
    session = next(generator)
    assert session is not None
    with pytest.raises(StopIteration):
        next(generator)
    assert captured["closed"] is True
