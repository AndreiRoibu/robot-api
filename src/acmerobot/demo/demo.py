#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# This file contains a demo script showcasing the usage of the cleaning robot.

import argparse
import os

import requests


def wrap_set_map(host: str, map_path: str) -> dict:
    """Helper function to upload a map file to the API.

    Args:
        host (str): Base URL of the API.
        map_path (str): Path to the map file to upload.

    Returns:
        dict: JSON response from the API.

    """

    with open(map_path, "rb") as file:
        files = {
            "file": (os.path.basename(map_path), file.read(), "application/octet-stream"),
        }

    response = requests.post(f"{host}/set-map", files=files, timeout=10)
    response.raise_for_status()  # Raise error for bad responses
    return response.json()


def wrap_clean(host: str, cleaning_plan: dict) -> dict:
    """Helper function to send a cleaning plan to the API.

    Args:
        host (str): Base URL of the API.
        cleaning_plan (dict): Cleaning plan to send.

    Returns:
        dict: JSON response from the API.

    """

    response = requests.post(f"{host}/clean", json=cleaning_plan, timeout=30)
    response.raise_for_status()  # Raise error for bad responses
    return response.json()


def wrap_history(host: str) -> str:
    """Helper function to retrieve cleaning history from the API.

    Args:
        host (str): Base URL of the API.

    Returns:
        str: CSV string containing the cleaning history.

    """

    response = requests.get(f"{host}/history", timeout=10)
    response.raise_for_status()  # Raise error for bad responses
    return response.text


def wrap_plan_route(host: str, plan_request: dict) -> dict:
    """Helper function to request an A* route plan."""
    response = requests.post(f"{host}/plan", json=plan_request, timeout=10)
    response.raise_for_status()
    return response.json()


def wrap_plan_coverage(host: str, coverage_request: dict) -> dict:
    """Helper function to request a coverage plan."""
    response = requests.post(f"{host}/plan-coverage", json=coverage_request, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_coordinate(value: str) -> tuple[int, int]:
    """Parse a coordinate provided as 'x,y'."""
    try:
        x_str, y_str = value.split(",", maxsplit=1)
        return int(x_str), int(y_str)
    except (ValueError, AttributeError):
        error_message = "Invalid coordinate format. Coordinates must be provided as 'x,y'."
        raise argparse.ArgumentTypeError(error_message) from None


def run_demo():
    """Main function to demonstrate the cleaning robot functionality."""
    print(
        "This is a demo script for the cleaning robot application. The path"
        " for the robot to follow is hard-coded for demonstration purposes."
    )

    # --------------------------------------------------------------------------
    # 1. Parse command-line arguments
    # --------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Demo for AcmeCleaning Robot Application")
    parser.add_argument("--host", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--map", required=True, help="Path to .txt or .json map file")
    parser.add_argument("--start", required=True, type=parse_coordinate, help="Start position as x,y")
    parser.add_argument("--model", default="premium", choices=["base", "premium"], help="Robot model to use")
    parser.add_argument(
        "--plan",
        default="manual",
        choices=["manual", "route", "coverage"],
        help="Planning strategy: manual (default), route, or coverage.",
    )
    parser.add_argument(
        "--goal",
        type=parse_coordinate,
        help="Goal position as x,y (required when --plan route).",
    )
    parser.add_argument(
        "--precleaned",
        type=parse_coordinate,
        nargs="*",
        default=None,
        help="List of pre-cleaned coordinates as x,y (used when --plan coverage).",
    )
    parser.add_argument(
        "--repeat-clean",
        action="store_true",
        help="Execute the generated cleaning plan twice without re-uploading the map.",
    )

    args = parser.parse_args()
    start = args.start
    plan_mode = args.plan

    if plan_mode == "route" and args.goal is None:
        parser.error("--goal must be provided when using '--plan route'.")

    print("===================================================================")
    print(" --> Demo Configuration: <--")
    print("===================================================================")
    print(f"Using API at: {args.host}")
    print(f"Using map file: {args.map}")
    print(f"Stacmeng position: {start}")
    print(f"Robot model: {args.model}")
    print(f"Planning mode: {plan_mode}")
    if args.goal:
        print(f"Route goal: {args.goal}")
    if args.precleaned:
        print(f"Pre-cleaned tiles: {args.precleaned}")

    # --------------------------------------------------------------------------
    # 2. Load the map file and set it in the API
    # --------------------------------------------------------------------------

    print("-------------------------------------------------------------------")
    print(" --> Uploading map to the API...")
    print("-------------------------------------------------------------------")
    print(wrap_set_map(args.host, args.map))

    # --------------------------------------------------------------------------
    # 3. Planning
    # --------------------------------------------------------------------------

    print("-------------------------------------------------------------------")
    print(" --> Planning cleaning path...")
    print("-------------------------------------------------------------------")

    if plan_mode == "manual":
        print("---")
        print(" -> Using built-in demo cleaning plan.")
        print("---")
        plan_result = {
            "path": [],
            "actions": [
                {"direction": "east", "steps": 3},
                {"direction": "south", "steps": 2},
                {"direction": "west", "steps": 3},
                {"direction": "north", "steps": 2},
            ],
        }
    elif plan_mode == "route":
        plan_request = {
            "start_position": {"x": start[0], "y": start[1]},
            "goal": {"x": args.goal[0], "y": args.goal[1]},
        }
        plan_result = wrap_plan_route(args.host, plan_request)
        print("---")
        print(" -> A* route planned:")
        print("---")
        print(plan_result)
    else:  # coverage
        precleaned = args.precleaned or []
        coverage_request = {
            "start_position": {"x": start[0], "y": start[1]},
            "precleaned": [{"x": x, "y": y} for x, y in precleaned],
        }
        plan_result = wrap_plan_coverage(args.host, coverage_request)
        print("---")
        print(" -> Coverage plan generated:")
        print("---")
        print(plan_result)

    cleaning_plan = {
        "start_position": {"x": start[0], "y": start[1]},
        "actions": plan_result["actions"],
        "model": args.model,
    }
    print("---")
    print(" -> Cleaning plan to execute:")
    print("---")
    print(cleaning_plan)

    # --------------------------------------------------------------------------
    # 4. Execute cleaning
    # --------------------------------------------------------------------------

    print("-------------------------------------------------------------------")
    print(" --> Executing cleaning...")
    print("-------------------------------------------------------------------")
    first_run = wrap_clean(args.host, cleaning_plan)
    print(first_run)

    if args.repeat_clean:
        print("---")
        print(" -> Re-executing cleaning (map not reset)...")
        print("---")
        second_run = wrap_clean(args.host, cleaning_plan)
        print(second_run)

    # --------------------------------------------------------------------------
    # 5. Access cleaning history
    # --------------------------------------------------------------------------

    print("-------------------------------------------------------------------")
    print(" --> Retrieving cleaning history...")
    print("-------------------------------------------------------------------")
    print(wrap_history(args.host))


if __name__ == "__main__":
    run_demo()
