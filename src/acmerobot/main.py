#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# This is the main entry point for the AcmeCleaning-RoboMapper application. It
# contains all the necessary code and packages them into a REST API. It also
# defined the relevant endpoints for controlling the robots remotely.

# ------------------------------------------------------------------------------
# 1. Import necessary packages
# ------------------------------------------------------------------------------
import csv
import io
import json
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from src.acmerobot.planner_a_star import a_star, greedy_a_star_coverage, path_to_actions
from src.acmerobot.robots import BaseRobot, Environment, PremiumRobot
from src.acmerobot.sessionDB import CleaningSession, SessionLocal

# ------------------------------------------------------------------------------
# 2. Initialize the FastAPI app
# ------------------------------------------------------------------------------

app = FastAPI(
    title="AcmeCleaning-RoboMapper API",
    description="REST API for remotely controlling AcmeCleaning's robots.",
    version="0.0.1",
)
# Initialize environment holder on application state
app.state.environment = None  # Environment | None

# ------------------------------------------------------------------------------
# 3. Define helper functions
# ------------------------------------------------------------------------------
# These helper functions are used throughout the API endpoints to manage the
# application state, such as storing and retrieving the current environment map.
# We also define a helper to get a database session for endpoints that need to
# access the database.


def set_environment(environment: Environment | None) -> None:
    """Store the current environment on the FastAPI app state.

    This function sets the current environment map in the application state,
    allowing it to be accessed by various API endpoints. This is useful for
    maintaining a shared state across different requests. The alternative would
    be to use global variables, which is not recommended in web applications due
    to potential concurrency issues (this is what I did initially, but then
    changed to this approach).

    Args:
        environment (Environment | None): The environment map to set. If None,
            it clears the current environment.

    Returns:
        None

    """
    app.state.environment = environment


def get_environment() -> Environment:
    """Retrieve the current environment or raise if it has not been set.

    This function retrieves the current environment map from the application
    state. If no environment has been set yet, it raises an HTTPException to
    inform the user that they need to upload a map before proceeding.

    Returns:
        Environment: The current environment map.

    """
    environment: Environment | None = getattr(app.state, "environment", None)
    if environment is None:
        error_message = (
            "No environment map has been set yet."
            " Please upload a map via the /set_map endpoint before stacmeng a cleaning session."
        )
        raise HTTPException(status_code=400, detail=error_message)
    return environment


def get_database():
    """Helper function to get a database session.

    This helper is needed to create a new database session for each request
    that requires database access. FastAPI will automatically handle the
    creation and closing of the session for us.

    Yields:
        database session: A SQLAlchemy database session.

    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


# ------------------------------------------------------------------------------
# 4. Define the Pydantic models for request and response bodies
# ------------------------------------------------------------------------------
# We use Pydantic models to define the request and response schemas for our API
# endpoints. Pydantic is what FastAPI uses under the hood for data validation
# and serialization. When we define a Pydantic model, we create a class that
# inherits from pydantic.BaseModel and defines the expected fields and their
# types. During request handling, FastAPI will automatically validate the incoming
# data against these models, ensuring that the data conforms to the expected
# structure before passing it to the endpoint function.


class Action(BaseModel):
    """Pydantic model representing a robot action.

    Args:
        direction (str): The direction of the action (north, south, east, west).
        steps (int): The number of steps to move in the specified direction.

    """

    direction: str
    steps: int


class Position(BaseModel):
    """Pydantic model representing a position on the map.

    Args:
        x (int): The x-coordinate of the position.
        y (int): The y-coordinate of the position.

    """

    x: int
    y: int


class CleanRequest(BaseModel):
    """Pydantic model representing a cleaning request.

    Args:
        start_position (Position): The stacmeng position of the robot.
        actions (list[Action]): The list of actions to perform.
        model (str): The robot model to use (default is "base").

    """

    start_position: Position
    actions: list[Action]
    model: str = "base"  # Default robot model is "base". Can also be "premium".


class CleanResponse(BaseModel):
    """Pydantic model representing a cleaning response.

    Args:
        cleaned_tiles (list[Position]): The list of unique tiles cleaned.
        final_state (str): The final state of the cleaning session (completed /
            error).

    """

    cleaned_tiles: list[Position]
    final_state: str


class PlanRequest(BaseModel):
    """Pydantic model representing a path planning request.

    Args:
        start_position (Position): The stacmeng position of the robot.
        goal (Position): The goal position for the robot to reach.

    """

    start_position: Position
    goal: Position


class CoverageRequest(BaseModel):
    """Pydantic model representing a coverage path planning request.

    Args:
        start_position (Position): The stacmeng position of the robot.
        precleaned (list[Position]): The list of pre-cleaned positions.

    """

    start_position: Position
    precleaned: list[Position] = []


# ------------------------------------------------------------------------------
# 5. Define the API endpoints
# ------------------------------------------------------------------------------
# Here, we define the various API endpoints that will allow users to interact
# with the AcmeCleaning-RoboMapper application. Each endpoint corresponds to a
# specific functionality.


@app.get("/")
def root():
    """Root endpoint to check if the API is running.

    This is a simple health check endpoint that can be used to verify that the
    API is up and running, when accessed via a web browser or HTTP client.

    Returns:
        dict: A message indicating that the API is running.
    """

    return {"message": "AcmeCleaning-RoboMapper API is running"}


@app.post("/set-map")
async def set_map(file: UploadFile = File(...)) -> dict:  # noqa: B008
    """Uploads a map file (either .txt or .json) and sets the current environment.

    Args:
        file (UploadFile): The uploaded map file. This is a dependency injected
            by FastAPI when the endpoint is called.

    Returns:
        dict: A confirmation message indicating the map has been set.

    Raises:
        HTTPException: If the file is empty or has an unsupported format.
        HTTPException: If there is an error parsing the file.

    """

    # Read the file content into memory as raw bytes
    file_content = await file.read()
    file_name = file.filename or ""

    # If the file is empty, raise an error
    if not file_content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    # Determine the file type based on the extension and parse accordingly
    # .txt files are parsed as text maps, while .json files are parsed as
    # JSON-like dictionaries.
    try:
        if file_name.lower().endswith(".json") or file.content_type == "application/json":
            json_data = json.loads(file_content.decode("utf-8"))
            environment = Environment.from_json(json_data)
        else:
            text_map = file_content.decode("utf-8")
            environment = Environment.from_txt(text_map)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {e}") from e

    # Store the parsed environment in the application state. This makes it
    # accessible to other endpoints that require the environment map.
    set_environment(environment)

    return {"message": f"Map of shape {environment.rows}x{environment.columns} has been set successfully."}


@app.post("/clean", response_model=CleanResponse)
def clean(
    request: CleanRequest,
    environment: Environment = Depends(get_environment),  # noqa: B008
    database=Depends(get_database),  # noqa: B008
):
    """Starts a new cleaning session.

    Main endpoint exposed by the API to start a new cleaning session. Takes as
    input a stacmeng location and a sequence of actions. Returns a JSON report
    containing a list of tiles cleaned and the final state.

    It also stores in a local database the details of the cleaning session for
    future reference. These include:
    - id: Unique identifier for each cleaning session.
    - start_time: Timestamp when the cleaning session started.
    - model: The robot model used for the cleaning session.
    - final_state: The final state of the cleaning session (completed / error).
    - number_of_actions: Total number of actions performed during the session.
    - number_of_cleaned_tiles: Total number of unique tiles cleaned during the
          session.
    - duration: Duration of the cleaning session in seconds.

    Args:
        request (CleanRequest): The cleaning request containing the stacmeng
            position, list of actions, and robot model.
        database: The database session dependency injected by FastAPI.

    Returns:
        CleanResponse: The response containing the cleaned tiles and final state.

    Raises:
        HTTPException: If no environment map has been set yet.
        HTTPException: If the requested start position is not walkable.
        HTTPException: If the requested robot model is not recognized.
        HTTPException: If we try to specify an invalid robot model.

    """

    # --------------------------------------------------------------------------
    # 1. Validate the request
    # --------------------------------------------------------------------------

    # Check if the requested start position is valid
    x_start = request.start_position.x
    y_start = request.start_position.y
    if not environment.is_walkable(x_start, y_start):
        error_message = (
            f"Start position {x_start},{y_start} is not walkable." " Please choose a different stacmeng position."
        )
        raise HTTPException(status_code=400, detail=error_message)

    # Check if the requested robot model is valid
    robot_model = request.model.lower()
    if robot_model not in ["base", "premium"]:
        error_message = (
            f"Robot model '{robot_model}' is not recognized."
            " Supported models are 'base' and 'premium'."
            " Please choose a valid robot model and try again."
        )
        raise HTTPException(status_code=400, detail=error_message)

    # --------------------------------------------------------------------------
    # 2. Initialize the Robot
    # --------------------------------------------------------------------------

    robot = PremiumRobot(environment=environment) if robot_model == "premium" else BaseRobot(environment=environment)
    robot.reset_session()

    # --------------------------------------------------------------------------
    # 3. Execute Cleaning
    # --------------------------------------------------------------------------

    cleaning_start_time = datetime.now(UTC)
    actions = [(action.direction, action.steps) for action in request.actions]
    cleaned_tiles_this_session, final_state = robot.execute_cleaning(
        x_start=x_start,
        y_start=y_start,
        actions=actions,
    )
    cleaning_end_time = datetime.now(UTC)
    duration = (cleaning_end_time - cleaning_start_time).total_seconds()

    # --------------------------------------------------------------------------
    # 4. Store the session in the database
    # --------------------------------------------------------------------------

    session_record = CleaningSession(
        start_time=cleaning_start_time,
        model=robot_model,
        final_state=final_state,
        number_of_actions=len(request.actions),
        number_of_cleaned_tiles=len(cleaned_tiles_this_session),
        duration=duration,
    )
    database.add(session_record)

    # We try-except here to catch any database errors and rollback if needed
    # to maintain database integrity. The HTTP 500 error indicates a server-side
    # issue that the client cannot resolve. These could be due to various reasons
    # such as database connection issues, constraint violations, etc.
    try:
        database.commit()
    except Exception as exception:
        database.rollback()
        error_message = "Failed to record cleaning session in the database."
        raise HTTPException(status_code=500, detail=error_message) from exception

    # --------------------------------------------------------------------------
    # 5. Prepare and return the response
    # --------------------------------------------------------------------------

    cleaned_tiles_response = [{"x": x, "y": y} for x, y in cleaned_tiles_this_session]

    return {
        "cleaned_tiles": cleaned_tiles_response,
        "final_state": final_state,
    }


@app.get("/history")
def history(database=Depends(get_database)):  # noqa: B008
    """Retrieves the history of all cleaning sessions stored in the database.

    This is a read-only endpoint that allows users to retrieve the full history of
    cleaning sessions recorded in the local database.

    The history is retrived as a large dump of all cleaning sessions recorded
    in the local database. Each record contains:
    - id: Unique identifier for each cleaning session.
    - start_time: Timestamp when the cleaning session started.
    - model: The robot model used for the cleaning session.
    - final_state: The final state of the cleaning session (completed / error).
    - number_of_actions: Total number of actions performed during the session.
    - number_of_cleaned_tiles: Total number of unique tiles cleaned during the
          session.
    - duration: Duration of the cleaning session in seconds.

    Args:
        database: The database session dependency injected by FastAPI.

    Returns:
        PlainTextResponse: The CSV response containing the cleaning session
            history.

    """

    # Select the records, order by session_id and return all rows
    session = database.query(CleaningSession).order_by(CleaningSession.session_id).all()

    # Create a CSV placeholder in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the CSV header
    writer.writerow([
        "session_id",
        "start_time",
        "model",
        "final_state",
        "number_of_actions",
        "number_of_cleaned_tiles",
        "duration",
    ])

    # Write each record as a row in the CSV
    for record in session:
        writer.writerow([
            record.session_id,
            record.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            record.model,
            record.final_state,
            record.number_of_actions,
            record.number_of_cleaned_tiles,
            record.duration,
        ])

    # Reset the pointer of the StringIO object to the beginning
    output.seek(0)

    return PlainTextResponse(
        content=output.read(),
        media_type="text/csv",
    )


@app.post("/plan")
def plan_route(
    request: PlanRequest,
    environment: Environment = Depends(get_environment),  # noqa: B008
):
    """Plans a path from start to goal using A* algorithm.

    This endpoint allows users to request a path plan from a stacmeng position
    to a goal position using the A* pathfinding algorithm. It returns the
    computed path as a list of positions and the corresponding movement actions.

    IMPORTANT: This endpoint plans only a route from point A to point B. For
    coverage planning, use the /plan-coverage endpoint instead.

    Args:
        request (PlanRequest): The path planning request containing the stacmeng
            position and goal position.

    Returns:
        dict: A dictionary containing the planned path and movement actions.

    Raises:
        HTTPException: If no environment map has been set yet.
        HTTPException: If the start or goal position is not walkable.
        HTTPException: If no path could be found between the start and goal.
    """

    # Validate start and goal positions
    x_start, y_start = request.start_position.x, request.start_position.y
    x_goal, y_goal = request.goal.x, request.goal.y

    if not environment.is_walkable(x_start, y_start) or not environment.is_walkable(x_goal, y_goal):
        error_message = (
            f"Start position {x_start},{y_start} or goal position {x_goal},{y_goal} is not walkable."
            " Please choose different positions."
        )
        raise HTTPException(status_code=400, detail=error_message)

    # Plan the path using A* algorithm
    path = a_star(
        rows=environment.rows,
        columns=environment.columns,
        obstacles=environment.obstacles,
        start=(x_start, y_start),
        goal=(x_goal, y_goal),
    )

    # If no path could be found, raise an error
    if not path:
        error_message = (
            f"No path could be found from start position {x_start},{y_start} " f"to goal position {x_goal},{y_goal}."
        )
        raise HTTPException(status_code=422, detail=error_message)

    # Convert the path to movement actions
    actions = path_to_actions(path)

    # Return the planned path and actions
    return {"path": [{"x": x, "y": y} for (x, y) in path], "actions": actions}


@app.post("/plan-coverage")
def plan_coverage(
    request: CoverageRequest,
    environment: Environment = Depends(get_environment),  # noqa: B008
):
    """Plans a coverage path using greedy A* coverage algorithm.

    This endpoint allows users to request a coverage path plan from a stacmeng
    position, optionally specifying pre-cleaned positions. It returns the
    computed coverage path as a list of positions and the corresponding movement
    actions.

    Args:
        request (CoverageRequest): The coverage planning request containing the
            stacmeng position and pre-cleaned positions.

    Returns:
        dict: A dictionary containing the planned coverage path and movement
            actions.

    """

    # Validate start position
    x_start, y_start = request.start_position.x, request.start_position.y
    if not environment.is_walkable(x_start, y_start):
        error_message = (
            f"Start position {x_start},{y_start} is not walkable." " Please choose a different stacmeng position."
        )
        raise HTTPException(status_code=400, detail=error_message)

    # Convert the list of Pydantic 'precleaned' objects from the request into a
    # set of (x,y) tuples that the algorithm expects, and filter out any invalid
    # coordinates for safety.
    precleaned = {
        (position.x, position.y) for position in request.precleaned if environment.is_walkable(position.x, position.y)
    }
    cells, actions = greedy_a_star_coverage(
        rows=environment.rows,
        columns=environment.columns,
        obstacles=environment.obstacles,
        start=(x_start, y_start),
        precleaned=precleaned,
    )

    return {"path": [{"x": x, "y": y} for (x, y) in cells], "actions": actions}
