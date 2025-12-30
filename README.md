# AcmeRobot

# 1. Overview

AcmeRobot is a controllable “virtual robot” environment for AcmeCleaning household
cleaning robots. To operate it, the user uploads a floor map, picks a robot
model, and drives or plans its cleaning routine through a REST API. The service
tracks each session, reports on cleaning, and can auto-plan routes or
full-room coverage with built-in algorithms. Everything runs locally or in
Docker, and the repository includes tests, documentation, and a demo script,
allowing end-to-end simulation without real hardware.

This file contains the necessary instructions for setting up and running the project. It
also contains detailed implementation information, code structure, and used
dependencies, and other relevant details.

> **_Table of Contents_**:
1. [Overview](#1-overview)
2. [Quick Start Guide](#2-quick-start-guide)
    1. [Local](#21-local)
    2. [Docker](#22-docker)
    3. [Endpoints](#23-endpoints)
    4. [Demo](#24-demo)
    5. [Tests](#25-tests)
    6. [Project Structure](#26-project-structure)
    7. [Conventions](#27-conventions)
3. [Project Description](#3-project-description)
    1. [Core Capabilities](#31-core-capabilities)
    2. [Planning and Autonomy](#32-planning-and-autonomy)
    3. [Developer Experience](#33-developer-experience)
    4. [Technology Choices and Details](#34-technology-choices-and-details)
4. [Project Extension and Future Work](#4-project-extension-and-future-work)
    1. [A* Planning Algorithm](#41-a-planning-algorithm)
    2. [(Deep) Reinforcement Learning](#42-deep-reinforcement-learning)
    3. [Extensions](#43-extensions)

# 2. Quick Start Guide

## 2.1. Local

To start locally, first ensure you have `just` and `uv` installed. If you
don't, run the following OS-specific commands:

MacOS:

```bash
brew install just uv
```

Linux (Debian/Ubuntu):

```bash
sudo apt-get update
sudo apt-get install -y just
curl -LsSf https://astral.sh/uv/install.sh | sh
# then restart your shell so uv is on PATH
```

Windows:
```powershell
# uv (official installer)
irm https://astral.sh/uv/install.ps1 | iex

# just — pick one package manager you support in your project:
# winget (preferred if available)
winget install casey.just -e  # if this ID doesn't resolve on some systems, use one of the following lines
# scoop
scoop install just
# chocolatey
choco install just

```

Then, install the dependencies and activate the virtual environment by running:

```bash
just install
source .venv/bin/activate
```

Finally, run the application using Uvicorn:

```bash
uvicorn src.acmerobot.main:app --host 127.0.0.1 --port 8000
```

## 2.2. Docker

First, ensure you have installed Docker. You can check this by running:

```bash
docker --version
```

If you do not have Docker installed, please follow the instructions on the [Docker website](https://docs.docker.com/get-docker/) to install it for your operating system.

Then, build and run the Docker container:

```bash
docker compose up --build
```

Or, manually:

```bash
docker build -t acmecleaning-api .
docker run -d -p 8000:8000 acmecleaning-api
# Visit http://localhost:8000/docs
```

## 2.3. Endpoints

| Endpoint        | Description                      |
|-----------------|----------------------------------|
| `POST /set-map` | Upload `.txt` or `.json` map    |
| `POST /clean`   | Execute actions with `base` or `premium` model |
| `GET /history`  | CSV of sessions             |
| `POST /plan`    | Generate a path plan between two points using A* |
| `POST /plan-coverage` | Generate a coverage path plan using A* bridges and a Greedy Approach |

## 2.4. Demo

After a server is running (locally or via Docker), you can run the demo script.
Here are several example commands:

```bash
# Basic cleaning with base and premium models:
python src/acmerobot/demo/demo.py --host http://localhost:8000 --start 0,1 --map src/acmerobot/demo/map.txt --model premium

# Route planning from start to goal:
python src/acmerobot/demo/demo.py --host http://localhost:8000 --start 0,1 --map src/acmerobot/demo/map.txt --model premium --plan route --goal 4,4

# Coverage planning to clean all reachable tiles:
python src/acmerobot/demo/demo.py --host http://localhost:8000 --start 0,1 --map src/acmerobot/demo/map.txt --model premium --plan coverage
```

To repeat the cleaning without resetting the map, demonstrating the difference
between `base` and `premium` models, add the `--repeat-clean` flag:
```bash
python src/acmerobot/demo/demo.py --host http://localhost:8000 --start 0,1 --map src/acmerobot/demo/map.txt --model base --plan coverage --repeat-clean &&
python src/acmerobot/demo/demo.py --host http://localhost:8000 --start 0,1 --map src/acmerobot/demo/map.txt --model premium --plan coverage --repeat-clean
```

When inspecting the output, note how the `premium` model skips all previously
cleaned tiles during the second run, while the `base` model re-cleans them.

For a complete list of options, run:

```bash
python src/acmerobot/demo/demo.py --help
```

## 2.5. Tests

To run the tests, make sure you have the virtual environment activated and run:

```bash
python -m pytest
```

To check coverage, run:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

## 2.6. Project Structure

The project structure can be seen below, with files having the following
roles:

| Folder/File         | Description                                      |
|---------------------|--------------------------------------------------|
| `src/acmerobot/main.py` | FastAPI application entrypoint                   |
| `src/acmerobot/robots.py` | Robot models and environment handling            |
| `src/acmerobot/planner_a_star.py` | A* pathfinding and coverage planning algorithms  |
| `src/acmerobot/sessionDB.py` | Database models and session persistence logic    |
| `src/acmerobot/demo/` | Demo script and related files                    |
| `tests/` | Test suite for various components                |

```plaintext
.
├── Dockerfile
├── LICENSE
├── README.md
├── __init__.py
├── cleaning_sessions.db
├── compose.debug.yaml
├── compose.yaml
├── justfile
├── pyproject.toml
├── src
│   ├── __init__.py
│   └── acmerobot
│       ├── __init__.py
│       ├── demo
│       │   ├── __init__.py
│       │   ├── demo.py
│       │   ├── map.json
│       │   └── map.txt
│       ├── main.py
│       ├── planner_a_star.py
│       ├── robots.py
│       └── sessionDB.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_clean.py
│   ├── test_history.py
│   ├── test_main_endpoints.py
│   ├── test_mapping.py
│   ├── test_plan.py
│   ├── test_planner_a_star.py
│   ├── test_robots.py
│   └── test_session_db.py
└── uv.lock
```

## 2.7. Conventions

| Convention        | Value / Format / Description                               |
|-------------------|------------------------------------------------------------|
| Coordinate System  | `(x, y)` with `(0, 0)` at top-left, `x` increasing rightwards, `y` increasing downwards |
| Map Formats      | TXT grid (2D array of chars) and JSON |
| TXT Map Symbols  | `o` = cleanable / open tile, `x` = obstacle |
| JSON Map Schema | `{"rows": int, "cols": int, "tiles": [{"x": int, "y": int, "walkable": bool}, ...]}` |
| Actions          | `[{"direction" : "north/south/east/west", "steps": int}, ...]` |
| Robot Models    | `base` (no pre-cleaning awareness), `premium` (skips already-cleaned tiles) |
| Collision Semantics (`/clean` endpoint) | Stops early and returns `"final_state":"error"`. Else returns `"final_state":"complete"` and the updated map. |


# 3. Project Description

This project contains a product-ready implementation of a RESTful API for a virtual
service for simulating and controlling AcmeCleaning robots. The project provides
a small but complete robotics stack that emphasises clarity, maintainability, and
extensibility.

## 3.1. Core Capabilities

- REST API built with FastAPI (`app` in `main.py`) that exposes several core
endpoints: `POST /set-map`, `POST /clean`, and `GET /history`, plus two
optional proof-of-concept planning endpoints (`POST /plan`, `POST /plan-coverage`).
- Map ingestion for both TXT “grid” and JSON “tile list” formats
(`robots.Environment`), with validation and consistent obstacle handling.
Once uploaded, the map resides in memory and is shared across requests.
- Two robot models (`robots.BaseRobot`, `robots.PremiumRobot`) that execute
action sequences tile-by-tile. The premium variant accounts for pre-cleaned
tiles by avoiding duplicate work.
- Cleaning session persistence via SQLAlchemy (`sessionDB.py`). Each session
records the start time, outcome, number of actions, number of cleaned tiles, and
duration. Users can export history as a CSV through `/history`.

## 3.2. Planning and Autonomy

- `planner_a_star.py` implements an A* pathfinder plus a greedy coverage wrapper.
These algorithms back the new `/plan` and `/plan-coverage` endpoints and can
also be consumed directly from the demo or other services. _For additional details,
see Section 4. below._
- `tests/test_plan.py` proves that the generated plans are executable by both
robot variants, transforming the assignment into a self-contained
planning-and-execution loop.

## 3.3. Developer Experience

- End-to-end demo script (`demo/demo.py`) that can upload maps, choose between
manual, route, or coverage planning modes, and execute runs against a live API.
- Comprehensive pytest suite (unit tests for planners, endpoints, robots, and
database) with isolated, in-memory fixtures.
- Reusable Docker image and Compose configuration that mirrors the production
runtime (Gunicorn + Uvicorn workers, Python 3.12 slim base).
- Dependency management via `uv`/`pyproject.toml`, plus a `justfile` for
one-line setup, testing, and formatting.

## 3.4. Technology Choices and Details

I selected the following technologies to implement this project:

| Technology      | Rationale                                                  |
|-----------------|------------------------------------------------------------|
| FastAPI         | Modern, async-first web framework with automatic validation via Pydantic and interactive docs out of the box—perfect for quickly iterating with interviewers or product partners. |
| SQLAlchemy      | Widely adopted ORM/DB (Object-Relational Mapping / Database) toolkit that keeps the storage layer swappable. I used SQLite in development and demonstration, but future implementations can easily
| Uvicorn + Gunicorn | Uvicorn provides an ASGI server optimised for FastAPI; Gunicorn manages worker processes for production deployments. |
| pytest          | Concise, expressive testing framework with fixture support and great ecosystem plugins—ideal for keeping behaviour verifiable during rapid iteration. |
| uv + just       | Reproducible dependency management and task automation without imposing a heavyweight build system. |
| Docker          | Encapsulates the exact runtime (Python version, dependencies, entrypoint) so the service behaves identically on laptops, CI, or cloud VMs.

Collectively, these allowed me to construct a maintainable service that users can demonstrate to
stakeholders, explain during workshops, or deploy as the foundation for
future robotic automation experiments.

# 4. A* Planning Algorithm

In the base version of the solution, I did not implement any path planning
algorithm. The user provides the sequence of actions for the robot
to execute. This approach leaves room for future improvements and the implementation of different path planning algorithms.

As a proof of concept, to demonstrate how a user could integrate path planning into
the existing architecture (_and out of personal curiosity_), I implemented the
A* (A-star) algorithm with Manhattan heuristic for pathfinding in grid-based
maps with obstacles. I then expanded this with a greedy "nearest unvisited tile"
bridge strategy to cover all reachable tiles in the map.

The A* (A-star) algorithm is a popular pathfinding and graph traversal algorithm, commonly used for robotics for navigation tasks. The algorithm finds the
shortest path from a start node to a goal node by evaluating the cost of each
possible path and selecting the most promising one.

The Manhattan heuristic is a simple and efficient heuristic function used in the
A* algorithm. It calculates the estimated cost from the current node to the goal
node by summing the absolute differences of their x and y coordinates. This
heuristic is particularly suitable for grid-based maps where movement is restricted
to horizontal and vertical directions.

The bridge strategy uses the Manhattan distance to find the nearest unvisited
tile from the robot's current position. Once the robot identifies the nearest tile, it can plan a path to that tile using the A* algorithm, effectively "bridging"
the gap between its current location and the target tile. The robot repeats this process until all reachable tiles are covered.

While not optimal, this approach demonstrates how we can integrate path planning
into the existing architecture in a predictable, explainable, and deterministic
manner, while handling obstacles and navigating various map layouts.

For instance, given a map like this:

```
xxxxxoooooxxxxx
ooooooooooooooo
ooooooooooooooo
ooooooooooooooo
oooooxxxxxooooo
```

The planned coverage path would look like this:

```
        x →
        0 1  2  3  4  5  6  7  8  9  10 11 12 13 14
y = 0: ██ ██ ██ ██ ██ 06 07 08 09 10 ██ ██ ██ ██ ██
y = 1: 00 01 02 03 04 05 14 13 12 11 34 35 36 37 38
y = 2: 21 20 19 18 17 16 15 30 31 32 33 42 41 40 39
y = 3: 22 23 24 25 26 27 28 29 46 45 44 43 50 51 52
y = 4: 59 58 57 56 55 ██ ██ ██ ██ ██ 47 48 49 54 53
```

Where the numbers indicate the order in which the robot visits each tile. As
seen, the robot successfully navigates around obstacles and covers all reachable
tiles, yet the path is not optimal and contains some backtracking.

# 5. Future Work

## 5.1. (Deep) Reinforcement Learning

Another promising direction for future work is to implement a (deep)
reinforcement learning [(D)RL] agent. The agent could tackle two key tasks:
1. **Path Planning**: The agent learns to navigate from a start position to a
goal position while avoiding obstacles. The agent receives positive rewards for
reaching the goal and negative rewards for collisions or inefficient paths.
2. **Coverage Planning**: The agent learns to cover the entire area of the map
efficiently. The agent receives positive rewards for cleaning new tiles and
negative rewards for revisiting already cleaned tiles or getting stuck.

The benefits of using (D)RL for these tasks include:
- **Adaptability**: The agent can learn to adapt to different or changing maps
layouts, recalculating its coverage strategy on the fly when encountering an
obstacle, thus improving its performance in dynamic environments.
- **Efficiency**: The agent can learn to optimise its actions over time,
such as balancing trade-offs between energy usage, water consumption, and cleaning
coverage and penalties for collisions and revising the same tile multiple times.
- **Generalisation**: The agent can potentially generalise its knowledge to new,
unseen environments, making it more robust.

> During my Master's studies, I have implemented several classical and deep RL
> algorithms as detailed on my [personal website](https://andreiroibu.com/projects/meng-reinforcement-learning/)
> which also contains links to my GitHub and ArXiv. The following are notes on
> how I would approach the implementation of an RL agent for the AcmeRobot project.

- **State Representation**: `(x, y)` position of the robot + local tile observations,
such as a fixed-radius patch indicating obstacles and dirty/clean tiles. We can also use a tabular
representation for small maps.
- **Actions**: North, South, East, West movements.
- **Transition Dynamics**: Deterministic inside the grid, with collision handling:
either end the episode with a penalty, or apply a negative reward and stay in place.
- **Reward Structure**: Can depend on what we want to prioritise:
    - Navigation: +ve for reaching the goal (cleaning endpoint), -ve for collisions, small
step negative cost to encourage efficiency.
 - Cleaning: +ve for cleaning a dirty (new) tile, zero or small -ve for already-clean tiles,
small negative cost per step to encourage efficiency, -ve for collisions.
- **Episode Termination**: Similarly, it depends on priority:
    - Navigation: episode ends when the robot reaches the goal, collides, or after a max step count.
    - Cleaning: episode ends when all reachable tiles are clean or after a max step count.
- **Exploration Strategy**: ε-greedy or softmax action selection to balance exploration and exploitation.
- **Algorithm Choice**: Depends on task complexity:
    - Tabular: Q-learning or SARSA work well for small maps with discrete states and actions.
    - Larger Maps: DQN or DSN can be used for function approximation, with a small fully-connected
 network (or even a small transformer like TinyBERT) to process local observations. We can further explore experience
 replay, semi-gradients, and dual networks to stabilise training.

## 5.2. Extensions

We can extend the project further in several ways, including but not limited to:
- **GitHub integration for CI/CD**: While I used git locally to track changes, we should link the
project to a GitHub/GitLab repository for better collaboration,
version control, and CI/CD integration.
- **Packaging**: While the project can be run locally or via Docker, we can also package it
for easier installation and distribution. If the codebase
must be hidden or is proprietary, packages such as `nuitka` can be used to
compile the code into binary format before distribution.
- **Diagonal movement**: The current implementation only allows movement in four
directions (north, south, east, west). Adding support for diagonal movement can
improve the robot's navigation capabilities.
- **Adding more robot models**: We can introduce additional robot models with
different capabilities, such as varying battery life, cleaning efficiency,
or obstacle handling. Doing this is straightforward due to the existing
object-oriented design and the separation between robot models, environment,
and API layers.
- **Session-aware map storage**: Currently, the environment map is stored in
memory and shared across all requests. We can enhance this by implementing
session-aware storage. This would allow multiple users to have their own
independent environments and robots, and also enable horizontal scaling of the API
across multiple workers or instances.
- **Changing Database**: While I used SQLite for simplicity, we can switch to a more robust
database system (e.g., PostgreSQL, MySQL) easily due to the use of ORM (Object-Relational Mapping)
for better scalability and performance.
