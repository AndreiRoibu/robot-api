#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define the fixtures and common utilities for testing the
# FastAPI application.


import io
import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.acmerobot import main, sessionDB


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fixture to create a TestClient for the FastAPI app. Any test function
    that requires a client can use this fixture to get one. We also override
    the database dependency to use an in-memory SQLite database for testing.
    This ensures that tests do not interfere with the production database.
    """
    # Create an in-memory SQLite database engine to use for testing
    db_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sessionDB.Base.metadata.create_all(bind=db_engine)
    TestingSessionLocal = sessionmaker(bind=db_engine)

    def override_get_database() -> Iterator[Session]:
        """Override the get_database dependency to use the test database. Each
        test will get a fresh session connected to the in-memory database.
        """
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    # Override the dependency in the FastAPI app to use the test database
    main.app.dependency_overrides[main.get_database] = override_get_database
    main.app.state.environment = None

    try:
        # Create the TestClient for the FastAPI app and yield it for use in tests.
        # While the fixture is active, every clean or history request will use the
        # in-memory database.
        yield TestClient(main.app)
    finally:
        # Clean up: remove the dependency override and dispose of the test database
        # This leaves no persistent database state after tests complete, keeping
        # the test environment isolated.
        main.app.dependency_overrides.pop(main.get_database, None)
        main.app.state.environment = None
        sessionDB.Base.metadata.drop_all(bind=db_engine)
        db_engine.dispose()


def upload_text_map(client: TestClient, text_map: str):
    """Helper function to upload a text map to the /set-map endpoint."""
    files = {
        "file": (
            "map.txt",  # The name of the file
            io.BytesIO(text_map.encode("utf-8")),  # Create a fake file-like object
            "text/plain",  # The content type
        )
    }
    response = client.post("/set-map", files=files)
    return response


def upload_json_map(client: TestClient, json_map: dict):
    """Helper function to upload a JSON map to the /set-map endpoint."""
    json_data = json.dumps(json_map).encode("utf-8")
    files = {
        "file": (
            "map.json",  # The name of the file
            io.BytesIO(json_data),  # Create a fake file-like object
            "application/json",  # The content type
        )
    }
    response = client.post("/set-map", files=files)
    return response
