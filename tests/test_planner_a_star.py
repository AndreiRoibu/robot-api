#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, we define the tests for the A* based path planning functions.

import itertools

import pytest

import src.acmerobot.planner_a_star as planner_module
from src.acmerobot.planner_a_star import (
    DIRECTION,
    DIRECTION_ORDER,
    a_star,
    greedy_a_star_coverage,
    manhattan_distance,
    neighbors4,
    path_to_actions,
    reachable_set,
    step_direction,
)

# ------------------------------------------------------------------------------
# 1. step_direction
# ------------------------------------------------------------------------------


def test_step_direction_all_cardinal_directions():
    """Test that step_direction correctly identifies all four cardinal directions."""
    origin = (2, 2)
    assert step_direction(origin, (2, 1)) == "north"
    assert step_direction(origin, (2, 3)) == "south"
    assert step_direction(origin, (3, 2)) == "east"
    assert step_direction(origin, (1, 2)) == "west"


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ((1, 1), (1, 1)),  # same point
        ((0, 0), (1, 1)),  # diagonal
        ((2, 2), (0, 3)),  # arbitrary non-cardinal
    ],
)
def test_step_direction_invalid_moves(start, end):
    """Test that step_direction returns None for invalid moves."""
    assert step_direction(start, end) is None


# ------------------------------------------------------------------------------
# 2. path_to_actions
# ------------------------------------------------------------------------------


def test_path_to_actions_empty_or_trivial_paths():
    """Test that path_to_actions returns an empty list for empty or single-point
    paths."""
    assert path_to_actions([]) == []
    assert path_to_actions([(0, 0)]) == []


def test_path_to_actions_merges_consecutive_steps():
    """Test that path_to_actions correctly merges consecutive steps in the same
    direction."""
    path = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    actions = path_to_actions(path)
    assert actions == [
        {"direction": "east", "steps": 2},
        {"direction": "south", "steps": 2},
    ]


def test_path_to_actions_handles_multiple_turns():
    """Test that path_to_actions correctly handles paths with multiple turns."""
    path = [
        (1, 1),
        (1, 2),
        (1, 3),
        (0, 3),
        (0, 2),
        (0, 1),
        (1, 1),
    ]
    actions = path_to_actions(path)
    assert actions == [
        {"direction": "south", "steps": 2},
        {"direction": "west", "steps": 1},
        {"direction": "north", "steps": 2},
        {"direction": "east", "steps": 1},
    ]


# ------------------------------------------------------------------------------
# 3. reachable_set
# ------------------------------------------------------------------------------


def test_reachable_set_basic_grid_without_obstacles():
    """Test that reachable_set returns all cells in an empty grid."""
    rows, columns = 3, 3
    reachable = reachable_set(rows, columns, obstacles=set(), start=(0, 0))
    expected = {(x, y) for x in range(columns) for y in range(rows)}
    assert reachable == expected


def test_reachable_set_with_obstacles_blocks_regions():
    """Test that reachable_set correctly identifies reachable cells when
    obstacles block certain areas."""
    rows, columns = 4, 4
    obstacles = {(1, 0), (1, 1), (1, 2), (1, 3)}  # solid vertical wall
    reachable = reachable_set(rows, columns, obstacles, start=(0, 0))
    expected = {(0, 0), (0, 1), (0, 2), (0, 3)}
    assert reachable == expected


@pytest.mark.parametrize(
    "start",
    [
        (-1, 0),  # x out of bounds
        (0, -1),  # y out of bounds
        (3, 0),  # x out of bounds high
        (0, 3),  # y out of bounds high
        (1, 1),  # obstacle cell
    ],
)
def test_reachable_set_invalid_or_blocked_start(start):
    """Test that reachable_set returns an empty set when stacmeng out of bounds
    or on an obstacle."""
    rows, columns = 3, 3
    obstacles = {(1, 1)}
    assert reachable_set(rows, columns, obstacles, start) == set()


# ------------------------------------------------------------------------------
# 4. neighbors4
# ------------------------------------------------------------------------------


def test_neighbors4_respects_bounds_and_order():
    """Test that neighbors4 returns the correct neighboring cells."""
    rows, columns = 3, 3
    neighbors = list(neighbors4(rows, columns, 1, 1))
    assert neighbors == [(1, 0), (1, 2), (2, 1), (0, 1)]

    corner_neighbors = list(neighbors4(rows, columns, 0, 0))
    assert corner_neighbors == [(0, 1), (1, 0)]


# ------------------------------------------------------------------------------
# 5. manhattan_distance
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("point_a", "point_b", "expected"),
    [
        ((0, 0), (2, 3), 5),
        ((2, 3), (0, 0), 5),
        ((5, 5), (5, 5), 0),
        ((-1, -2), (3, 4), 10),
    ],
)
def test_manhattan_distance(point_a, point_b, expected):
    """Test that manhattan_distance computes the correct distance between two
    points."""
    assert manhattan_distance(x=point_a[0], y=point_a[1], x_goal=point_b[0], y_goal=point_b[1]) == expected


# ------------------------------------------------------------------------------
# 6. a_star
# ------------------------------------------------------------------------------


def test_a_star_finds_shortest_path_without_obstacles():
    """Test that a_star finds the shortest path in an empty grid."""
    rows, columns = 3, 3
    path = a_star(rows, columns, obstacles=set(), start=(0, 0), goal=(2, 2))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)
    # Minimal Manhattan path should have length 5 in nodes
    assert len(path) == 5
    # Ensure each step is cardinal move (ie. no diagonals)
    for start, end in itertools.pairwise(path):
        direction = step_direction(start, end)
        assert direction in DIRECTION_ORDER


def test_a_star_respects_obstacles_and_detours():
    """Test that a_star finds a valid path around obstacles."""
    rows, columns = 3, 3
    obstacles = {(1, 0), (1, 1)}
    path = a_star(rows, columns, obstacles, start=(0, 0), goal=(2, 0))
    assert path == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0)]


def test_a_star_returns_none_when_goal_unreachable():
    """Test that a_star returns None when the goal is unreachable."""
    rows, columns = 3, 3
    obstacles = {(1, 0), (1, 1), (1, 2)}  # Solid wall
    assert a_star(rows, columns, obstacles, start=(0, 0), goal=(2, 1)) is None


# ------------------------------------------------------------------------------
# 7. greedy_a_star_coverage
# ------------------------------------------------------------------------------


def test_greedy_a_star_coverage_covers_all_reachable_cells():
    """Test that greedy_a_star_coverage visits all reachable cells."""
    rows, columns = 3, 3
    obstacles = {(1, 1)}
    start = (0, 0)
    path_cells, actions = greedy_a_star_coverage(rows, columns, obstacles, start)

    reachable = reachable_set(rows, columns, obstacles, start)
    assert set(path_cells) == reachable  # path may revisit cells but must cover all
    assert path_cells[0] == start
    # Actions should recreate the path when applied
    reconstructed = [path_cells[0]]
    for action in actions:
        dx, dy = DIRECTION[action["direction"]]
        for _ in range(action["steps"]):
            last_x, last_y = reconstructed[-1]
            reconstructed.append((last_x + dx, last_y + dy))
    assert reconstructed == path_cells


def test_greedy_a_star_coverage_respects_precleaned_cells():
    """Test that greedy_a_star_coverage skips precleaned cells."""
    rows, columns = 2, 2
    start = (0, 0)
    precleaned = {(0, 0), (0, 1), (1, 0), (1, 1)}
    path_cells, actions = greedy_a_star_coverage(rows, columns, obstacles=set(), start=start, precleaned=precleaned)
    assert path_cells == [(0, 0)]
    assert actions == []


def test_greedy_a_star_coverage_handles_unreachable_start():
    """Test that greedy_a_star_coverage returns empty path when start is
    unreachable."""
    rows, columns = 3, 3
    obstacles = {(0, 0)}
    path_cells, actions = greedy_a_star_coverage(rows, columns, obstacles=obstacles, start=(0, 0))
    assert path_cells == []
    assert actions == []


def test_greedy_coverage_skips_targets_without_paths(monkeypatch):
    """Ensure the coverage planner gracefully handles unreachable intermediate
    targets. This is done by mocking the a_star function to return None on the
    first call, and a valid path on the second call. The coverage planner should
    skip the unreachable target and continue planning towards reachable ones.
    """
    call_counter = {"value": 0}

    def fake_a_star(rows, columns, obstacles, start, goal):
        call_counter["value"] += 1
        if call_counter["value"] == 1:
            return None
        mid = (start[0] + 1, start[1]) if start[0] + 1 < columns else start
        return [start, mid, goal]

    monkeypatch.setattr(planner_module, "a_star", fake_a_star)

    path_cells, actions = planner_module.greedy_a_star_coverage(
        rows=1,
        columns=3,
        obstacles=set(),
        start=(0, 0),
    )

    assert path_cells[0] == (0, 0)
    assert actions, "Should eventually plan towards a reachable tile"
    assert call_counter["value"] >= 2
