#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define tests for the Robot classes.

import pytest

from src.acmerobot.robots import BaseRobot, Environment, PremiumRobot


@pytest.mark.parametrize("robot_class", [BaseRobot, PremiumRobot])
def test_robot_cleans_straight_path(robot_class):
    """Robot should clean every tile along a valid path."""
    environment = Environment(rows=3, columns=3)
    robot = robot_class(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1), ("south", 1)],
    )

    assert state == "completed"
    assert cleaned_tiles == [(0, 0), (1, 0), (1, 1)]
    assert environment.is_clean(1, 1)


@pytest.mark.parametrize("robot_class", [BaseRobot, PremiumRobot])
def test_robot_skips_precleaned_start_tile(robot_class):
    """Robot should report an error when encountering an obstacle."""
    environment = Environment.from_txt("ox\noo\n")
    robot = robot_class(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1)],
    )

    assert state == "error"
    assert cleaned_tiles == [(0, 0)]
    assert environment.is_clean(0, 0)
    assert not environment.is_clean(1, 0)


def test_premium_robot_skips_precleaned_start_tile():
    """Premium robot should not re-clean a tile that is already clean."""
    environment = Environment(rows=2, columns=2)
    environment.mark_clean(0, 0)
    robot = PremiumRobot(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1)],
    )

    assert state == "completed"
    assert len(cleaned_tiles) == 1
    assert cleaned_tiles == [(1, 0)]
    assert environment.is_clean(1, 0)


def test_premium_robot_skips_entirely_precleaned_path():
    """Premium robot should avoid cleaning tiles that are already clean."""
    environment = Environment(rows=2, columns=2)
    environment.mark_clean(0, 0)
    environment.mark_clean(1, 0)
    robot = PremiumRobot(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1)],
    )

    assert state == "completed"
    assert len(cleaned_tiles) == 0
    assert cleaned_tiles == []
    assert environment.is_clean(0, 0)
    assert environment.is_clean(1, 0)


def test_premium_robot_skips_precleaned_path_but_cleans_dirty_tiles():
    """Premium robot should avoid cleaning tiles that are already clean."""
    environment = Environment(rows=2, columns=2)
    environment.mark_clean(0, 0)
    environment.mark_clean(1, 0)
    robot = PremiumRobot(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1), ("south", 1)],
    )

    assert state == "completed"
    assert len(cleaned_tiles) == 1
    assert cleaned_tiles == [(1, 1)]
    assert environment.is_clean(0, 0)
    assert environment.is_clean(1, 0)


@pytest.mark.parametrize("robot_class", [BaseRobot, PremiumRobot])
def test_robot_reports_error_on_unknown_direction(robot_class):
    """Robots must stop when an unknown direction is provided."""
    environment = Environment(rows=2, columns=2)
    robot = robot_class(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("north-east", 1)],
    )

    assert state == "error"
    assert cleaned_tiles == [(0, 0)]
    assert environment.is_clean(0, 0)


def test_base_robot_avoids_duplicate_tiles():
    """Base robot should not duplicate cleaned tiles when revisiting them."""
    environment = Environment(rows=2, columns=2)
    robot = BaseRobot(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1), ("west", 1)],
    )

    assert state == "completed"
    assert cleaned_tiles == [(0, 0), (1, 0)]
    assert environment.is_clean(0, 0)
    assert environment.is_clean(1, 0)


def test_premium_robot_respects_precleaned_tiles_mid_path():
    """Premium robot should skip tiles that are already clean while traversing."""
    environment = Environment(rows=2, columns=2)
    environment.mark_clean(1, 0)
    robot = PremiumRobot(environment)

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1), ("west", 1)],
    )

    assert state == "completed"
    # Only the stacmeng tile should be added; precleaned tile is skipped.
    assert cleaned_tiles == [(0, 0)]


@pytest.mark.parametrize("robot_class", [BaseRobot, PremiumRobot])
def test_robot_retains_existing_clean_list(robot_class):
    """If stacmeng tile already tracked, robots should not re-append it."""
    environment = Environment(rows=1, columns=1)
    robot = robot_class(environment)
    robot.cleaned_tiles_this_session = [(0, 0)]

    cleaned_tiles, state = robot.execute_cleaning(0, 0, [])

    assert state == "completed"
    assert cleaned_tiles == [(0, 0)]


def test_premium_robot_skips_duplicate_dirty_tile_after_move():
    """Premium robot should avoid re-appending tiles already in its session list."""
    environment = Environment(rows=1, columns=2)
    robot = PremiumRobot(environment)
    robot.cleaned_tiles_this_session = [(0, 0), (1, 0)]

    cleaned_tiles, state = robot.execute_cleaning(
        0,
        0,
        [("east", 1)],
    )

    assert state == "completed"
    assert cleaned_tiles == [(0, 0), (1, 0)]


@pytest.mark.parametrize("robot_class", [BaseRobot, PremiumRobot])
def test_reset_session_clears_state(robot_class):
    """Resetting the robot's session should clear its cleaned tiles list."""
    environment = Environment(rows=1, columns=1)
    robot = robot_class(environment)
    robot.cleaned_tiles_this_session = [(0, 0)]
    robot.reset_session()
    assert robot.cleaned_tiles_this_session == []
