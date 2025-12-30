#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for the any API endpoints defined in main.py
# that do not fit into other specific test files.


def test_root_endpoint_reports_status(client):
    """Test that the root endpoint reports the API status correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AcmeCleaning-RoboMapper API is running"}
