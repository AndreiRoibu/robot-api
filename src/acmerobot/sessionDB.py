#
# ----------------------------------------------------------------------------
# Copyright (C) 2025 AcmeCleaning. All rights reserved.
# Developed by Andrei Roibu for AcmeCleaning
# All rights reserved. Reproduction in whole or part is prohibited without
# the written permission of the copyright owner.
# For additional information, please contact AcmeCleaning using contact-us@acmecleaning.ai
# ----------------------------------------------------------------------------
#
# In this file we define the CleaningSession class, which creates an SQL
# database to store cleaning session data. We will record the following data:
# - id: Unique identifier for each cleaning session.
# - start_time: Timestamp when the cleaning session started.
# - model: The robot model used for the cleaning session.
# - final_state: The final state of the cleaning session (completed / error).
# - number_of_actions: Total number of actions performed during the session.
# - number_of_cleaned_tiles: Total number of unique tiles cleaned during the
#       session.
# - duration: Duration of the cleaning session in seconds.

# ------------------------------------------------------------------------------
# 1. Import necessary modules
# ------------------------------------------------------------------------------


from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ------------------------------------------------------------------------------
# 2. Initialize the database
# ------------------------------------------------------------------------------
# Here we create the engine that connects to the SQLite database. If the
# database file does not exist, it will be created automatically. We also make
# the session factory and the base class for our ORM models. If you are
# unfamiliar, ORM = Object Relational Mapping, a technique that allows us to
# interact with the database using Python classes and objects instead of raw
# SQL queries.

db_engine = create_engine(
    "sqlite:///cleaning_sessions.db",
    connect_args={"check_same_thread": False},  # Needed to access FastAPI's async context
)

SessionLocal = sessionmaker(bind=db_engine)

Base = declarative_base()

# ------------------------------------------------------------------------------
# 3. Define the CleaningSession class
# ------------------------------------------------------------------------------


class CleaningSession(Base):
    """Represents a cleaning session in the database.

    This class is essentially a SQL table mapped to a Python class using
    SQLAlchemy's ORM capabilities. Each instance of this class corresponds to a
    row in the "cleaning_sessions" table.

    Args:
        Base: The base class for SQLAlchemy ORM models.

    Attributes:
        session_id: Unique identifier for each cleaning session.
        start_time: UTC timestamp when the cleaning session started.
        model: The robot model used for the cleaning session.
        final_state: The final state of the cleaning session (completed /
                error).
        number_of_actions: Total number of actions performed during the session.
        number_of_cleaned_tiles: Total number of unique tiles cleaned during the
                session.
        duration: Duration of the cleaning session in seconds.

    Raises:
        IntegrityError: If a nullable field is not provided when creating a new
            instance.

    """

    __tablename__ = "cleaning_sessions"
    # Define the columns of the table. Start with the primary key.
    session_id = Column(Integer, primary_key=True, index=True)

    # Define the necessary columns with their types and constraints. Failing to
    # provide a value for a non-nullable column will raise an error.
    start_time = Column(DateTime, nullable=False)
    model = Column(String, nullable=False)
    final_state = Column(String, nullable=False)
    number_of_actions = Column(Integer, nullable=False)
    number_of_cleaned_tiles = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)


# ------------------------------------------------------------------------------
# 4. Create the database tables
# ------------------------------------------------------------------------------
# Create the table if it does not exist already.

Base.metadata.create_all(bind=db_engine)
