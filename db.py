# AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI) were used as
# development assistants during the creation of this project.
"""SQLite access layer for FocusBoard.

One connection is opened per request (stored in Flask's `g`) and closed
automatically when the request ends. All queries use `?` placeholders so
user input is never concatenated into SQL.
"""

import os
import sqlite3

import click
from flask import current_app, g


def get_db():
    """Return the SQLite connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row          # rows behave like dicts
        g.db.execute("PRAGMA foreign_keys = ON")  # enforce ON DELETE rules
    return g.db


def close_db(exception=None):
    """Close the connection at the end of the request (if one was opened)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    """Run a SELECT and return a list of rows (or a single row / None if one=True)."""
    cursor = get_db().execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE, commit it, and return the last inserted row id."""
    db = get_db()
    cursor = db.execute(sql, params)
    db.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id


def _run_script(filename):
    with current_app.open_resource(filename) as file:
        get_db().executescript(file.read().decode("utf-8"))


def init_db(seed=False):
    """(Re)create every table from schema.sql and optionally load seed.sql."""
    _run_script("schema.sql")
    if seed:
        _run_script("seed.sql")
    get_db().commit()


@click.command("init-db")
@click.option("--seed", is_flag=True, help="Also load the demo data from seed.sql.")
def init_db_command(seed):
    """Flask CLI: `flask --app app init-db [--seed]` (WARNING: deletes existing data)."""
    init_db(seed=seed)
    click.echo("Database initialized" + (" with demo data." if seed else "."))


def init_app(app):
    """Register teardown + CLI command and create the database file on first run."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db(seed=False)
