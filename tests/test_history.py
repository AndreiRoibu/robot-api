#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for history FastAPI endpoint.


def test_history_csv(client):
    """Test retrieving cleaning session history in CSV format."""
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})
    request = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 1}], "model": "base"}
    client.post("/clean", json=request)

    response = client.get("/history")
    assert response.status_code == 200
    csv_text = response.text.strip()
    lines = csv_text.splitlines()
    assert lines[0].startswith(
        "session_id,start_time,model,final_state,number_of_actions,number_of_cleaned_tiles,duration"
    )
    assert len(lines) >= 2  # at least one record


def test_history_empty_db(client):
    """Test retrieving cleaning session history from an empty database. It
    should return only the CSV header line.
    """
    response = client.get("/history")
    assert response.status_code == 200
    csv_text = response.text.strip()
    lines = csv_text.splitlines()
    assert len(lines) == 1  # only header line present
    assert lines[0].startswith(
        "session_id,start_time,model,final_state,number_of_actions,number_of_cleaned_tiles,duration"
    )


def test_history_multiple_sessions(client):
    """Test retrieving cleaning session history after multiple sessions."""
    text_map = "ooo\nooo\nooo\n"
    client.post("/set-map", files={"file": ("map.txt", text_map, "text/plain")})

    for _ in range(3):
        request = {"start_position": {"x": 0, "y": 0}, "actions": [{"direction": "east", "steps": 1}], "model": "base"}
        client.post("/clean", json=request)

    response = client.get("/history")
    assert response.status_code == 200
    csv_text = response.text.strip()
    lines = csv_text.splitlines()
    assert len(lines) == 4  # header + 3 records
