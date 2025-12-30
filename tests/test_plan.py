#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for planning FastAPI endpoints.

import pytest

from tests.conftest import upload_text_map


@pytest.mark.parametrize("robot_type", ["base", "premium"])
def test_plan_route_generates_actions_executable_by_robot(client, robot_type):
    """Test that the /plan endpoint generates a valid path and actions
    for a simple map.
    """
    # Set a simple 3x3 map with no obstacles
    text_map = "ooo\nooo\nooo\n"
    upload_text_map(client, text_map)

    # Create a plan from (0,0) to (2,2)
    plan_payload = {
        "start_position": {"x": 0, "y": 0},
        "goal": {"x": 2, "y": 2},
    }
    plan_response = client.post("/plan", json=plan_payload)

    # Verify the plan response
    assert plan_response.status_code == 200
    plan_data = plan_response.json()

    path = plan_data["path"]
    actions = plan_data["actions"]

    # Verify that the path starts and ends at the correct positions
    assert path[0] == {"x": 0, "y": 0}
    assert path[-1] == {"x": 2, "y": 2}
    assert actions, "Expected non-empty action list for a non-trivial path"

    # Now test that the generated actions can be executed by the robot
    clean_payload = {
        "start_position": {"x": 0, "y": 0},
        "model": robot_type,
        "actions": actions,
    }
    clean_response = client.post("/clean", json=clean_payload)
    assert clean_response.status_code == 200
    clean_data = clean_response.json()

    assert clean_data["final_state"] == "completed"
    assert clean_data["cleaned_tiles"][0] == {"x": 0, "y": 0}
    assert clean_data["cleaned_tiles"][-1] == {"x": 2, "y": 2}


@pytest.mark.parametrize("robot_type", ["base", "premium"])
def test_plan_coverage_cleans_all_reachable_tiles(client, robot_type):
    """Test that the /plan-coverage endpoint generates a coverage path
    that allows the robot to clean all reachable tiles.
    """
    # Set a simple 3x3 map with no obstacles
    text_map = "ooo\nooo\nooo\n"
    upload_text_map(client, text_map)

    # Create a coverage plan stacmeng from (0,0)
    coverage_payload = {
        "start_position": {"x": 0, "y": 0},
        "precleaned": [],
    }

    # Verify the coverage plan response
    coverage_response = client.post("/plan-coverage", json=coverage_payload)
    assert coverage_response.status_code == 200
    coverage_data = coverage_response.json()

    path = coverage_data["path"]
    actions = coverage_data["actions"]
    assert path[0] == {"x": 0, "y": 0}
    assert actions, "Coverage plan should produce actions to traverse the grid"

    # Now test that the generated coverage actions can be executed by the robot
    clean_response = client.post(
        "/clean",
        json={
            "start_position": {"x": 0, "y": 0},
            "model": robot_type,
            "actions": actions,
        },
    )
    assert clean_response.status_code == 200
    clean_data = clean_response.json()

    assert clean_data["final_state"] == "completed"
    cleaned_tiles = clean_data["cleaned_tiles"]
    assert len(cleaned_tiles) == 9  # Entire 3x3 grid
    assert cleaned_tiles[0] == {"x": 0, "y": 0}


def test_plan_route_requires_map(client):
    """Planning without uploading a map should fail."""
    response = client.post(
        "/plan",
        json={
            "start_position": {"x": 0, "y": 0},
            "goal": {"x": 1, "y": 1},
        },
    )
    assert response.status_code == 400
    assert "No environment map has been set yet" in response.json()["detail"]


@pytest.mark.parametrize(
    "start, goal",
    [
        ({"x": 0, "y": 0}, {"x": 2, "y": 2}),  # blocked start
        ({"x": 0, "y": 1}, {"x": 0, "y": 0}),  # blocked goal
    ],
)
def test_plan_route_rejects_non_walkable_positions(client, start, goal):
    """Test that planning rejects start or goal positions that are not walkable."""
    text_map = "xoo\nooo\nooo\n"
    upload_text_map(client, text_map)

    response = client.post(
        "/plan",
        json={
            "start_position": start,
            "goal": goal,
        },
    )
    assert response.status_code == 400
    assert "not walkable" in response.json()["detail"]


def test_plan_route_returns_422_when_goal_unreachable(client):
    """Test that planning returns a 422 error when the goal is unreachable."""
    text_map = "oxo\nxxx\nooo\n"
    upload_text_map(client, text_map)

    response = client.post(
        "/plan",
        json={
            "start_position": {"x": 0, "y": 0},
            "goal": {"x": 2, "y": 0},  # unreachable goal because of obstacles
        },
    )
    assert response.status_code == 422
    assert "No path could be found" in response.json()["detail"]


def test_plan_coverage_requires_map(client):
    """Coverage planning without uploading a map should fail."""
    response = client.post(
        "/plan-coverage",
        json={
            "start_position": {"x": 0, "y": 0},
            "precleaned": [],
        },
    )
    assert response.status_code == 400
    assert "No environment map has been set yet" in response.json()["detail"]


def test_plan_coverage_rejects_invalid_start(client):
    """Test that coverage planning rejects start positions that are not
    walkable.
    """
    text_map = "xoo\nooo\nooo\n"
    upload_text_map(client, text_map)

    response = client.post(
        "/plan-coverage",
        json={
            "start_position": {"x": 0, "y": 0},
            "precleaned": [],
        },
    )
    assert response.status_code == 400
    assert "not walkable" in response.json()["detail"]
