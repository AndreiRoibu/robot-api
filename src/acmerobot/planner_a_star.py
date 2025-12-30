#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# This file contains an example path planning algorithm. It uses the A* search
# algorithm to compute the shortest path between two points on a grid map,
# and a greedy coverage algorithm to cover all reachable cells.


from collections import deque
from heapq import heappop, heappush

# ------------------------------------------------------------------------------
# 1. Define constants and type aliases
# ------------------------------------------------------------------------------
# We define the possible movement directions and their corresponding
# coordinate changes. These are immutable internal constants.
DIRECTION = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
REVERSE_DIRECTION = {(0, -1): "north", (0, 1): "south", (1, 0): "east", (-1, 0): "west"}
DIRECTION_ORDER = ["north", "south", "east", "west"]
# Coord = tuple[int,int]

# ------------------------------------------------------------------------------
# 2. Implement helper functions
# ------------------------------------------------------------------------------


def step_direction(a: tuple[int, int], b: tuple[int, int]) -> str | None:
    """Determine the direction of movement from point a to point b.

    Args:
        a (tuple[int,int]): Stacmeng coordinate (x, y).
        b (tuple[int,int]): Ending coordinate (x, y).

    Returns:
        str | None: Direction of movement ("north", "south", "east", "west"),
        or None if the movement is not in a valid direction.

    """

    dx = b[0] - a[0]
    dy = b[1] - a[1]

    return REVERSE_DIRECTION.get((dx, dy), None)


def path_to_actions(path: list[tuple[int, int]]) -> list[dict]:
    """Convert a list of coordinates into a list of movement actions.

    By walking along the path, we determine the direction and number of steps
    taken in each direction, and aggregate them into a list of actions.

    Args:
        path (list[tuple[int,int]]): List of coordinates representing the path.

    Returns:
        list[dict]: List of movement actions, each represented as a dictionary
        with "direction" and "steps" keys.
    """

    # Check for empty or single-point paths
    if not path or len(path) < 2:
        return []

    # Initialize the actions list
    actions = []

    # Find the direction and step count for each segment of the path
    current_direction = step_direction(path[0], path[1])
    count = 1

    # Iterate through the path to aggregate steps in the same direction
    for i in range(1, len(path) - 1):
        direction = step_direction(path[i], path[i + 1])
        if direction == current_direction:
            count += 1
        else:
            actions.append({"direction": current_direction, "steps": count})
            current_direction, count = direction, 1
    # Append the last action
    actions.append({"direction": current_direction, "steps": count})

    return actions


def reachable_set(
    rows: int, columns: int, obstacles: set[tuple[int, int]], start: tuple[int, int]
) -> set[tuple[int, int]]:
    """Compute the set of all reachable cells from the start position.

    This function performs a breadth-first search (BFS) to explore all cells
    that can be reached from the stacmeng position, avoiding obstacles. It
    returns a set of coordinates representing the reachable cells.

    Args:
        rows (int): Number of rows in the grid map.
        columns (int): Number of columns in the grid map.
        obstacles (set[tuple[int,int]]): Set of coordinates representing obstacles.
        start (tuple[int,int]): Stacmeng coordinate (x, y).

    Returns:
        set[tuple[int,int]]: Set of coordinates representing reachable cells.

    """
    # Create a set of obstacle coordinates for quick, O(1), lookup
    blocked = set(obstacles)

    # If the start position is invalid or blocked, return an empty set
    if not (0 <= start[0] < columns and 0 <= start[1] < rows) or (start in blocked):
        return set()

    # Perform BFS to find all reachable cells
    closed_set = {start}
    queue = deque([start])
    while queue:
        # Dequeue the next position to explore
        x, y = queue.popleft()
        # Explore all 4-connected neighbors
        for x_next, y_next in neighbors4(rows, columns, x, y):
            # If the neighbor is already visited or blocked, skip it
            if (x_next, y_next) in closed_set or (x_next, y_next) in blocked:
                continue
            # Mark the neighbor as visited and enqueue it for further exploration
            closed_set.add((x_next, y_next))
            queue.append((x_next, y_next))

    return closed_set


def neighbors4(rows: int, columns: int, x: int, y: int):
    """Generate the 4-connected neighbors of a cell within grid bounds.

    Args:
        rows (int): Number of rows in the grid map.
        columns (int): Number of columns in the grid map.
        x (int): x-coordinate of the cell.
        y (int): y-coordinate of the cell.

    Yields:
        tuple[int,int]: Coordinates of a neighboring cell (nx, ny).

    Notes:
    - We yield rather than return a list to save memory when iterating over
      neighbors in large grids. Yielding allows for lazy evaluation, generating
      neighbors one at a time as needed, rather than storing them all in memory
      at once.
    """

    for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
        x_new, y_new = x + dx, y + dy
        if 0 <= x_new < columns and 0 <= y_new < rows:
            yield (x_new, y_new)


# ------------------------------------------------------------------------------
# 3. Implement the vanilla A* pathfinding algorithm
# ------------------------------------------------------------------------------


def manhattan_distance(x: int, y: int, x_goal: int, y_goal: int) -> int:
    """Calculate the Manhattan distance between two points.

    The Manhattan distance is a heuristic suitable for grid-based maps where
    movement is restricted to horizontal and vertical directions. It calculates
    the distance between two points by summing the absolute differences of their
    x and y coordinates:

        h(x, y) = |x1 - x2| + |y1 - y2| where (x1, y1) and (x2, y2) are the
        coordinates of the two points.

    Args:
        x (int): x-coordinate of the first point.
        y (int): y-coordinate of the first point.
        x_goal (int): x-coordinate of the second point (goal).
        y_goal (int): y-coordinate of the second point (goal).
    """
    return abs(x - x_goal) + abs(y - y_goal)


def a_star(
    rows: int, columns: int, obstacles: set[tuple[int, int]], start: tuple[int, int], goal: tuple[int, int]
) -> list[tuple[int, int]] | None:
    """Compute the shortest path from start to goal using A* algorithm.

    The A* algorithm is a popular pathfinding and graph traversal algorithm
    that finds the shortest path between nodes in a weighted graph. It uses a
    heuristic to estimate the cost from the current node to the goal, allowing
    it to prioritize nodes that are more likely to lead to the goal.

    The heuristic used to guide the search is a priority queue of sports to
    explore, ordered by the estimated total cost:

        f = g + h where:
        - f is the total estimated cost, with A* prioritizing nodes with the
            lowest f value first. This ensures the algorithm does not waste time
            and finds the shortest path quickly.
        - g is the cost from the start node to the current node. It is the
            historical cost incurred to reach the current node from the start.
        - h is the estimated cost from the current node to the goal node. It is
            calculated using the Manhattan distance.

    Args:
        rows (int): Number of rows in the grid map.
        columns (int): Number of columns in the grid map.
        obstacles (set[tuple[int,int]]): Set of coordinates representing obstacles.
        start (tuple[int,int]): Stacmeng coordinate (x, y).
        goal (tuple[int,int]): Goal coordinate (x, y).

    Returns:
        list[tuple[int,int]] | None: List of coordinates representing the path
        from start to goal, or None if no path exists.

    """
    # Create a set of obstacle coordinates for quick, O(1), lookup
    blocked = set(obstacles)

    # Unpack start and goal coordinates
    x_start, y_start = start
    x_goal, y_goal = goal

    # Define the open set priority queue
    open_set = []
    heappush(
        open_set,
        (
            manhattan_distance(x_start, y_start, x_goal, y_goal),  # f = h
            0,  # g
            (x_start, y_start),  # (here) next position
            None,  # parent
        ),
    )

    # Define the closed set to track visited nodes
    closed_set = {}

    # While there are nodes to explored, we continue the search
    while open_set:
        # Pop the node with the lowest f value
        _, g, (x, y), parent = heappop(open_set)
        # If we have already visited this node with a lower g cost, skip it
        if (x, y) in closed_set and g >= closed_set[(x, y)][0]:
            continue
        # Mark the node as visited and store its g cost and parent: I have
        # visited this node with cost g coming from parent
        closed_set[(x, y)] = (g, parent)
        # If we reached the goal, reconstruct the path
        if (x, y) == (x_goal, y_goal):
            path = []
            current = (x, y)
            while current is not None:
                path.append(current)
                current = closed_set[current][1]
            path.reverse()
            return path
        # If not at the goal, explore neighbors and add them to the open set
        for d in DIRECTION_ORDER:
            dx, dy = DIRECTION[d]
            x_next, y_next = x + dx, y + dy
            # Check if the neighbor is within bounds and not an obstacle
            if x_next < 0 or y_next < 0 or x_next >= columns or y_next >= rows:
                continue
            if (x_next, y_next) in blocked:
                continue
            g_next = g + 1
            # Add a valid neighbor to the open set
            heappush(
                open_set,
                (
                    g_next + manhattan_distance(x_next, y_next, x_goal, y_goal),  # f = g + h
                    g_next,  # g
                    (x_next, y_next),  # next position
                    (x, y),  # parent
                ),
            )

    # If we exhaust the open set without finding the goal, return None
    return None


# ------------------------------------------------------------------------------
# 4. Implement a greedy coverage path planner using A*
# ------------------------------------------------------------------------------


def greedy_a_star_coverage(
    rows: int,
    columns: int,
    obstacles: set[tuple[int, int]],
    start: tuple[int, int],
    precleaned: set[tuple[int, int]] | None = None,
) -> tuple[list[tuple[int, int]], list[dict]]:
    """Compute a complete coverage path using a greedy A* algorithm.

    This function computes a coverage path that visits all reachable cells on
    the grid map using a greedy, albeit not very smart, "Nearest Neighbor"
    approach combined with the A* pathfinding algorithm. The robot starts from
    the specified stacmeng position and iteratively selects the nearest unvisited
    cell to move to next, ensuring efficient coverage of the area. It first
    identifies all reachable, valid cells, discards those that are already
    precleaned, identifies the closest unvisited cell using Manhattan distance,
    and then uses the A* algorithm to find the shortest path to that cell. This
    process continues until all reachable cells have been visited. The function
    returns both the complete path as a list of coordinates and the corresponding
    list of movement actions. The algorithm terminates when there are no more
    unvisited targets.

    Notes:
    - This implementation does not optimize the overall path length or
      efficiency beyond the greedy nearest neighbor approach. More advanced
      techniques, such as backtracking or path smoothing, could be employed
      for better results.

    Args:
        rows (int): Number of rows in the grid map.
        columns (int): Number of columns in the grid map.
        obstacles (set[tuple[int,int]]): Set of coordinates representing obstacles.
        start (tuple[int,int]): Stacmeng coordinate (x, y).
        precleaned (set[tuple[int,int]] | None): Set of coordinates that have
            already been cleaned. Defaults to None.

    Returns:
        tuple[list[tuple[int,int]], list[dict]]: A tuple containing:
            - List of coordinates representing the coverage path.
            - List of movement actions, each represented as a dictionary with
              "direction" and "steps" keys.

    """

    # Initialize precleaned set if not provided
    if precleaned is None:
        precleaned = set()

    # Identify all reachable cells from the stacmeng position
    reach = reachable_set(rows, columns, obstacles, start)

    # Determine the set of target cells to clean (by excluding precleaned cells)
    targets = reach - set(precleaned)

    # If there are no reachable targets, return empty path and actions.
    # This could happen if the start is blocked or all reachable cells are
    # already precleaned, or if the robot is trapped.
    if not reach:
        return [], []

    # Initialize path, current position and visited targets
    path_cells = [start]
    current = start
    visited_targets = set()

    # While there are unvisited targets, continue planning
    while visited_targets != targets:
        # Mark the current cell as visited if it's a target
        if current in targets and current not in visited_targets:
            visited_targets.add(current)
        # If all targets have been visited, break
        if visited_targets == targets:
            break

        # Identify the nearest unvisited target using Manhattan distance.
        # Of all targets we could visit next, we choose the one with the
        # smallest Manhattan distance from our current position. In case of
        # ties, we choose the one with the smallest y coordinate, and if still
        # tied, the smallest x coordinate
        remaining_targets = targets - visited_targets
        chosen = min(
            remaining_targets,
            key=lambda target: (
                manhattan_distance(x=current[0], y=current[1], x_goal=target[0], y_goal=target[1]),
                target[1],  # tie-breaker-1: smaller y coordinate
                target[0],  # tie-breaker-2: smaller x coordinate
            ),
        )

        # Once we have a target, use A* to find the shortest path to the chosen
        # target
        path = a_star(rows, columns, obstacles, current, chosen)

        # As a safety check, if no path exists to the chosen target, mark it as
        # visited and continue to the next iteration
        if path is None:
            visited_targets.add(chosen)
            continue

        # Append the path to the chosen target to the overall path
        for cell in path[1:]:
            path_cells.append(cell)

        # Update the current position to the chosen target
        current = chosen

    # Convert the complete path into movement actions
    actions = path_to_actions(path_cells)

    return path_cells, actions
