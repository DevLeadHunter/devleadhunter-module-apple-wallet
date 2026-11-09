"""The schema steps of the wallet migrations, written once for MySQL in production and SQLite in the tests."""

from __future__ import annotations

from sqlalchemy import Table, inspect, text
from sqlalchemy.engine import Engine

from core.database import Base


class WalletSchemaChanges:
    """
    Creates the module's missing tables, columns and indexes, and leaves alone what already exists.

    ``init_db()`` runs before the migrations and creates every missing table from the models, so on an up-to-date
    database each step finds its work done: every step can run any number of times.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine: Engine = engine

    def create_missing_tables(self, *models: type[Base]) -> list[str]:
        """
        Create the table of each model that has none yet, in the given order (a referenced table first).

        Args:
            models: The module's ORM classes.

        Returns:
            The names of the tables created.
        """
        created: list[str] = []
        for model in models:
            table: Table = Base.metadata.tables[model.__tablename__]
            if inspect(self._engine).has_table(table.name):
                continue
            table.create(self._engine)
            created.append(table.name)
        return created

    def add_missing_column(self, table_name: str, column_name: str, column_type: str) -> bool:
        """
        Add a nullable column to a table that lacks it.

        Args:
            table_name: The table to alter.
            column_name: The column to add.
            column_type: Its SQL type, in a spelling MySQL and SQLite both accept (``VARCHAR(255)``).

        Returns:
            True when the column was added, False when the table already has it or does not exist yet (the models
            then create it whole).
        """
        inspector = inspect(self._engine)
        if not inspector.has_table(table_name):
            return False
        if column_name in {column["name"] for column in inspector.get_columns(table_name)}:
            return False
        with self._engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} NULL"))
        return True

    def add_missing_unique_index(self, table_name: str, index_name: str, column_name: str) -> bool:
        """
        Add a unique index on one column of a table that lacks it (NULLs stay allowed, several times).

        Args:
            table_name: The indexed table.
            index_name: The index name the models give it (``ix_<table>_<column>``).
            column_name: The indexed column.

        Returns:
            True when the index was created, False when it exists already or the table does not.
        """
        inspector = inspect(self._engine)
        if not inspector.has_table(table_name):
            return False
        if index_name in {index["name"] for index in inspector.get_indexes(table_name)}:
            return False
        with self._engine.begin() as connection:
            connection.execute(text(f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({column_name})"))
        return True
