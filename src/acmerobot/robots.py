#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using
# contact-us_fakeaddress_@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file, I define the Environment class, which represents a 2D grid world
# where robots can navigate. I also define the Robot classes for the base and
# premium models.

# ------------------------------------------------------------------------------
# 1. Define the Environment class
# ------------------------------------------------------------------------------


class Environment:
    """Represents a 2D grid world environment where robots can navigate.

    The class provides the following functionalities:
    - Creates an environment from text or JSON data.
    - Checks if a tile is walkable.
    - Tracks clean tiles.
    - Marks tiles as clean.

    Attributes:
        rows (int): Number of rows in the grid.
        columns (int): Number of columns in the grid.
        obstacles (set[tuple[int, int]]): Set of coordinates representing
            obstacles.
        clean_tiles (set[tuple[int, int]]): Set of coordinates representing
            clean tiles.

    Methods:
        from_txt(cls, text_map: str) -> "Environment":
            Creates an Environment instance from a text file.
        from_json(cls, json_data: dict) -> "Environment":
            Creates an Environment instance from a JSON-like dictionary.
        is_walkable(self, x: int, y: int) -> bool:
            Checks if a tile at the given coordinates is walkable.
        is_clean(self, x: int, y: int) -> bool:
            Checks if a tile at the given coordinates is clean.
        mark_clean(self, x: int, y: int) -> None:
            Marks a tile at the given coordinates as clean.

    """

    def __init__(
        self,
        rows: int,
        columns: int,
        obstacles: list[tuple[int, int]] | None = None,
    ) -> None:
        """Initializes the Environment with given dimensions and obstacles."""
        self.rows = rows
        self.columns = columns
        self.obstacles = set(obstacles) if obstacles else set()
        self.clean_tiles = set()

    @classmethod
    def from_txt(cls, text_map: str) -> "Environment":
        """Creates an Environment instance from a text file.

        The text file should contain a grid representation where:
        - 'x' represents an obstacle.
        - 'o' represents a walkable tile.

        Args:
            text_map (str): String containing the actual text map. We do not pass
                a file path to keep the method flexible. The client code can
                read the file and send the raw data in the body of an HTTP
                POST request. The server can then package the raw data and send
                it to this method.

        Returns:
            Environment: An instance of the Environment class.

        Raises:
            ValueError: If the text map is empty.
            ValueError: If the text map is not rectangular.

        Notes:
            We declare this as a class method because it returns an instance of
            the class, not a specific object. This allows us to create
            Environment instances directly from text files without needing an
            existing instance.
        """

        # Read the file and parse the grid
        lines = [line.strip() for line in text_map.splitlines() if line.strip()]

        # If the lines are empty, raise an error
        if not lines:
            error_message = "The provided text map is empty."
            raise ValueError(error_message)

        # Determine the dimensions of the grid
        rows = len(lines)
        columns = len(lines[0])

        # Identify obstacles in the grid
        obstacles = []
        for y, line in enumerate(lines):
            if len(line) != columns:
                error_message = "Inconsistent row lengths in the text map."
                raise ValueError(error_message)
            for x, elem in enumerate(line):
                if elem.lower() == "x":
                    obstacles.append((x, y))

        return cls(rows=rows, columns=columns, obstacles=obstacles)

    @classmethod
    def from_json(cls, json_data: dict) -> "Environment":
        """Creates an Environment instance from a JSON-like dictionary.

        The dictionary should contain the following keys:
        - 'rows': Number of rows in the grid.
        - 'columns': Number of columns in the grid.
        - 'tiles': List of coordinates representing all tiles. Each tile is a
            dictionary with 'x', 'y', and 'walkable' keys, where 'walkable' is a
            boolean indicating if the tile is walkable.

        Args:
            json_data (dict): Dictionary containing the environment data. We
                do not pass a file path to keep the method flexible. The client
                code can read the file and send the raw data in the body of an
                HTTP POST request. The server can then package the raw data and
                send it to this method.

        Returns:
            Environment: An instance of the Environment class.

        Raises:
            KeyError: If required keys are missing in the dictionary.

        """

        # Extract required data from the JSON dictionary
        rows = json_data.get("rows")
        columns = json_data.get("columns", json_data.get("cols"))
        tiles = json_data.get("tiles")

        # Validate the presence of required keys
        if rows is None or columns is None or tiles is None:
            error_message = (
                "Missing required keys in the JSON data. "
                "Expected 'rows', 'columns', and 'tiles'. "
                f"Got keys: {list(json_data.keys())}"
            )
            raise KeyError(error_message)

        # Extract the obstacles based on walkability
        obstacles = [(tile["x"], tile["y"]) for tile in tiles if not tile.get("walkable", False)]

        return cls(rows=rows, columns=columns, obstacles=obstacles)

    def is_walkable(self, x: int, y: int) -> bool:
        """Checks if a tile at the given coordinates is walkable.

        Args:
            x (int): X-coordinate of the tile.
            y (int): Y-coordinate of the tile.

        Returns:
            bool: True if the tile is walkable, False otherwise.
        """

        # Check boundary conditions
        if x < 0 or x >= self.columns or y < 0 or y >= self.rows:
            return False

        # Else, check if the tile is an obstacle
        return (x, y) not in self.obstacles

    def is_clean(self, x: int, y: int) -> bool:
        """Checks if a tile at the given coordinates is clean.

        This is relevant for the premium robot model, which must avoid cleaned
        tiles from being cleaned again.

        Args:
            x (int): X-coordinate of the tile.
            y (int): Y-coordinate of the tile.

        Returns:
            bool: True if the tile is clean, False otherwise.
        """

        return (x, y) in self.clean_tiles

    def mark_clean(self, x: int, y: int) -> None:
        """Marks a tile at the given coordinates as clean.

        Args:
            x (int): X-coordinate of the tile.
            y (int): Y-coordinate of the tile.

        Returns:
            None
        """

        if self.is_walkable(x, y):
            self.clean_tiles.add((x, y))


# ------------------------------------------------------------------------------
# 2. Define the base Robot class
# ------------------------------------------------------------------------------


class BaseRobot:
    """Base Robot class representing a simple robot model.

    This robot is the entry-level model that can navigate the environment but does
    not have advanced features like sensors to detect pre-cleaned tiles.

    Attributes:
        environment (Environment): The environment in which the robot operates.
        cleaned_tiles_this_session (list[tuple[int, int]]): List of coordinates
            representing tiles cleaned during the current session.
        direction_map (dict[str, tuple[int, int]]): Mapping of directions to
            coordinate deltas.

    Methods:
        execute_cleaning(
            self,
            x_start: int,
            y_start: int,
            actions: list[tuple[str, int]],
        ) -> tuple[list[tuple[int, int]], str]:
            Executes a series of cleaning actions stacmeng from the given
            coordinates.

    """

    def __init__(
        self,
        environment: Environment,
    ) -> None:
        """Initializes the BaseRobot with the given environment."""
        self.environment = environment
        self.cleaned_tiles_this_session: list[tuple[int, int]] = []

        # Direction deltas
        self.direction_map = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }

    def reset_session(self) -> None:
        """Clear tracked tiles for a fresh cleaning session.

        This method resets the list of cleaned tiles for the current session. This
        is useful when stacmeng a new cleaning session to ensure that the robot
        does not retain any state from previous sessions, thus preventing
        any leakage of information between sessions.

        Returns:
            None

        """
        self.cleaned_tiles_this_session.clear()

    def execute_cleaning(
        self,
        x_start: int,
        y_start: int,
        actions: list[tuple[str, int]],
    ) -> tuple[list[tuple[int, int]], str]:
        """Executes a series of cleaning actions stacmeng from the given
        coordinates.

        Args:
            x_start (int): Stacmeng X-coordinate.
            y_start (int): Stacmeng Y-coordinate.
            actions (list[tuple[str, int]]): List of actions to perform. Each
                action is a tuple containing the direction ('north', 'south',
                'east', 'west') and the number of steps to move in that
                direction.

        Returns:
            tuple: A tuple containing:
                - List of coordinates representing cleaned tiles during this
                  session.
                - Final state as a string ('completed' or 'error').

        """

        # Instantiate stacmeng position
        x, y = x_start, y_start
        final_state = "completed"  # Assume success unless an error occurs

        # Clean the stacmeng tile
        if (x, y) not in self.cleaned_tiles_this_session:
            self.cleaned_tiles_this_session.append((x, y))
        self.environment.mark_clean(x, y)

        # Execute each action in the list
        for direction, steps in actions:
            delta = self.direction_map.get(direction.lower())

            # If the direction is invalid, set error state and break
            if delta is None:
                final_state = "error"
                break

            dx, dy = delta

            # Move step by step in the specified direction
            for _ in range(steps):
                next_x, next_y = x + dx, y + dy

                # Check if the next position is walkable
                if not self.environment.is_walkable(next_x, next_y):
                    final_state = "error"
                    break

                # Update position
                x, y = next_x, next_y

                # Clean the current tile
                if (x, y) not in self.cleaned_tiles_this_session:
                    self.cleaned_tiles_this_session.append((x, y))
                self.environment.mark_clean(x, y)

            # Break outer loop if an error occurred
            if final_state == "error":
                break

        return self.cleaned_tiles_this_session, final_state


# ------------------------------------------------------------------------------
# 3. Define the premium Robot class
# ------------------------------------------------------------------------------


class PremiumRobot(BaseRobot):
    """Premium Robot class representing an advanced robot model.

    This robot is the premium model that can detect pre-cleaned tiles and avoid
    cleaning them again to save resources.

    Attributes:
        environment (Environment): The environment in which the robot operates.
        cleaned_tiles_this_session (list[tuple[int, int]]): List of coordinates
            representing tiles cleaned during the current session.
        direction_map (dict[str, tuple[int, int]]): Mapping of directions to
            coordinate deltas.

    Methods:
        execute_cleaning(
            self,
            x_start: int,
            y_start: int,
            actions: list[tuple[str, int]],
        ) -> tuple[list[tuple[int, int]], str]:
            Executes a series of cleaning actions stacmeng from the given
            coordinates, avoiding already clean tiles.
    """

    def execute_cleaning(
        self, x_start: int, y_start: int, actions: list[tuple[str, int]]
    ) -> tuple[list[tuple[int, int]], str]:
        """Executes cleaning while avoiding already clean tiles.

        Args:
            x_start (int): Stacmeng X-coordinate.
            y_start (int): Stacmeng Y-coordinate.
            actions (list[tuple[str, int]]): List of actions to perform. Each
                action is a tuple containing the direction ('north', 'south',
                'east', 'west') and the number of steps to move in that
                direction.
        Returns:
            tuple: A tuple containing:
                - List of coordinates representing cleaned tiles during this
                  session.
                - Final state as a string ('completed' or 'error').
        """

        # Instantiate stacmeng position
        x, y = x_start, y_start
        final_state = "completed"  # Assume success unless an error occurs

        # Clean the stacmeng tile IF not already clean
        if not self.environment.is_clean(x, y):
            if (x, y) not in self.cleaned_tiles_this_session:
                self.cleaned_tiles_this_session.append((x, y))
            self.environment.mark_clean(x, y)

        # Execute each action in the list
        for direction, steps in actions:
            delta = self.direction_map.get(direction.lower())

            # If the direction is invalid, set error state and break
            if delta is None:
                final_state = "error"
                break

            dx, dy = delta

            # Move step by step in the specified direction
            for _ in range(steps):
                next_x, next_y = x + dx, y + dy

                # Check if the next position is walkable
                if not self.environment.is_walkable(next_x, next_y):
                    final_state = "error"
                    break

                # Update position
                x, y = next_x, next_y

                # Clean the current tile IF not already clean
                if not self.environment.is_clean(x, y):
                    if (x, y) not in self.cleaned_tiles_this_session:
                        self.cleaned_tiles_this_session.append((x, y))
                    self.environment.mark_clean(x, y)

            # Break outer loop if an error occurred
            if final_state == "error":
                break

        return self.cleaned_tiles_this_session, final_state
