#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for cleaning FastAPI endpoint.

import pytest

from src.acmerobot import main


@pytest.mark.parametrize("robot_type", ["base", "premium"])
def test_clean_complete_base(client, robot_type):
    """Test a complete cleaning session with no obstacles"""
    # Set an easy 3x3 map with no obstacles
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    request = {
        "start_position": {"x": 0, "y": 0},
        "model": robot_type,
        "actions": [
            {"direction": "east", "steps": 2},
            {"direction": "south", "steps": 2},
        ],
    }
    response = client.post("/clean", json=request)
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["final_state"] == "completed"
    assert len(data["cleaned_tiles"]) == 5
    assert data["cleaned_tiles"][0] == {"x": 0, "y": 0}
    assert data["cleaned_tiles"][-1] == {"x": 2, "y": 2}


@pytest.mark.parametrize("robot_type", ["base", "premium"])
def test_clean_collision_error(client, robot_type):
    """Test a cleaning session that ends in error due to collision with
    an obstacle. The robot should return an error and report a single cleaned
    tile (the stacmeng position).
    """

    text_map = "oxo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    payload = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 2}], "model": robot_type}
    response = client.post("/clean", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["final_state"] == "error"
    assert len(data["cleaned_tiles"]) == 1


def test_start_invalid_400(client):
    """Test that stacmeng on an obstacle returns a 400 Bad Request error."""
    text_map = "xoo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    payload = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 1}], "model": "premium"}
    response = client.post("/clean", json=payload)
    assert response.status_code == 400


def test_call_clean_before_map_400(client):
    """Test that calling /clean before setting a map returns a 400 Bad
    Request error.
    """
    payload = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 1}], "model": "premium"}
    response = client.post("/clean", json=payload)
    assert response.status_code == 400


def test_invalid_robot_model_400(client):
    """Test that providing an invalid robot model returns a 400 Bad Request
    error.
    """
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    payload = {
        "start_position": {"x": 0, "y": 0},
        "actions": [{"direction": "east", "steps": 1}],
        "model": "ultra-premium",  # Invalid model
    }
    response = client.post("/clean", json=payload)
    assert response.status_code == 400


def test_out_of_bounds_start_400(client):
    """Test that stacmeng out of map bounds returns a 400 Bad Request error."""
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    payload = {
        "start_position": {"x": 99, "y": 99},  # Out of bounds
        "actions": [{"direction": "east", "steps": 1}],
        "model": "base",
    }
    response = client.post("/clean", json=payload)
    assert response.status_code == 400


@pytest.mark.parametrize("robot_type", ["base", "premium"])
def test_skip_already_clean_tiles(client, robot_type):
    """Test that premium robot skips already clean tiles, while base robot
    does not.
    """
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    payload = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 2}], "model": robot_type}

    # First cleaning: all tiles should be cleaned
    response_1 = client.post("/clean", json=payload).json()
    assert response_1["final_state"] == "completed"
    assert len(response_1["cleaned_tiles"]) == 3  # (0,0),(1,0),(2,0)

    # Repeat same path: premium should skip (already clean)
    response_2 = client.post("/clean", json=payload).json()
    assert response_2["final_state"] == "completed"
    if robot_type == "premium":
        assert len(response_2["cleaned_tiles"]) == 0
    else:
        assert len(response_2["cleaned_tiles"]) == 3  # (0,0),(1,0),(2,0)


def test_clean_rolls_back_on_commit_failure(client):
    """Ensure database commit failures trigger a rollback and return HTTP 500.
    This tests simulates a database commit failure. If commit() fails (maybe the
    disk is full or the DB is down) we must undo the pending transaction
    (rollback()) so the session isn't left in a half-written state.
    """

    # Set a simple map
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})

    # Define a mock session that fails on commit
    class FailingSession:
        """A mock database session that fails on commit. The methods are no-ops
        except for commit which raises an exception. It also tracks if rollback
        was called.
        """

        def __init__(self) -> None:
            self.rollback_called = False

        def add(self, _obj):
            pass

        def commit(self):
            raise RuntimeError("boom")

        def rollback(self):
            self.rollback_called = True

        def close(self):
            pass

    # Override the get_database dependency to use the failing session
    holder: dict[str, FailingSession] = {}

    def failing_database():
        """Dependency override that yields a FailingSession instance."""
        session = FailingSession()
        holder["session"] = session
        try:
            yield session
        finally:
            session.close()

    # Apply the dependency override
    client.app.dependency_overrides[main.get_database] = failing_database

    # Call the /clean endpoint, which should trigger the commit failure
    payload = {
        "start_position": {"x": 0, "y": 0},
        "actions": [{"direction": "east", "steps": 1}],
        "model": "base",
    }
    response = client.post("/clean", json=payload)
    assert response.status_code == 500
    assert holder["session"].rollback_called is True

    client.app.dependency_overrides.pop(main.get_database, None)
