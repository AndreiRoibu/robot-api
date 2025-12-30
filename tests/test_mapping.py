#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define the tests for the Mapping functions of the Environment
# class.

from io import BytesIO

import pytest

from src.acmerobot.robots import Environment
from tests.conftest import upload_json_map, upload_text_map


def test_environment_from_txt(client):
    """Tests the from_txt method of the Environment class."""
    # Text map: 4x9 with an obstacle at (3,1)
    text_map = "ooooooooo\noooxooooo\nooooooooo\nooooooooo\n"

    response = upload_text_map(client, text_map)
    assert response.status_code == 200  # OK
    data = response.json()
    assert data["message"] == "Map of shape 4x9 has been set successfully."


def test_environment_from_json(client):
    """Tests the from_json method of the Environment class."""
    json_map = {
        "rows": 4,
        "cols": 9,
        "tiles": [{"x": x, "y": y, "walkable": not (x == 3 and y == 1)} for y in range(4) for x in range(9)],
    }

    response = upload_json_map(client, json_map)
    assert response.status_code == 200  # OK
    data = response.json()
    assert data["message"] == "Map of shape 4x9 has been set successfully."


def test_is_walkable_identifies_obstacles():
    """Ensure an obstacle tile is reported as non-walkable."""
    env = Environment.from_txt("ox\noo\n")
    assert not env.is_walkable(1, 0)
    assert env.is_walkable(0, 0)


def test_is_walkable_rejects_out_of_bounds():
    """Out-of-range coordinates must not be walkable."""
    env = Environment(rows=2, columns=2)
    assert not env.is_walkable(-1, 0)
    assert not env.is_walkable(0, -1)
    assert not env.is_walkable(2, 1)
    assert not env.is_walkable(1, 2)


def test_mark_clean_records_clean_tiles():
    """Marking a walkable tile should record it as clean."""
    env = Environment(rows=2, columns=2)
    env.mark_clean(1, 1)
    assert env.is_clean(1, 1)


def test_mark_clean_ignores_obstacles():
    """Attempting to mark an obstacle clean should have no effect."""
    env = Environment.from_txt("ox\noo\n")
    env.mark_clean(1, 0)  # obstacle
    assert not env.is_clean(1, 0)


def test_environment_from_txt_empty_raises_value_error():
    """Creating an environment from an empty text map should raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        Environment.from_txt("\n\n")


def test_environment_from_txt_inconsistent_rows_raises_value_error():
    """Creating an environment from a text map with inconsistent row lengths
    should raise ValueError."""
    with pytest.raises(ValueError, match="Inconsistent row lengths"):
        Environment.from_txt("ooo\nox\n")


def test_environment_from_json_missing_keys_raises_key_error():
    """Creating an environment from JSON missing required keys should raise
    KeyError."""
    with pytest.raises(KeyError):
        Environment.from_json({"rows": 2, "tiles": []})


def test_set_map_rejects_empty_file(client):
    """Test that uploading an empty file to /set-map returns a 400 error."""
    response = client.post(
        "/set-map",
        files={"file": ("map.txt", BytesIO(b""), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty."


@pytest.mark.parametrize(
    ("filename", "content_type", "payload"),
    [
        ("invalid.json", "application/json", b'{"rows": 2}'),
        ("invalid.txt", "text/plain", b"oo\nx"),  # inconsistent row length
    ],
)
def test_set_map_reports_parse_errors(client, filename, content_type, payload):
    """Test that uploading invalid map files returns a 400 error with parsing
    details."""
    response = client.post(
        "/set-map",
        files={"file": (filename, BytesIO(payload), content_type)},
    )
    assert response.status_code == 400
    assert "Error parsing file" in response.json()["detail"]
