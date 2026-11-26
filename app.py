# AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI) were used as
# development assistants during the creation of this project.
"""FocusBoard - a task manager organised in focus blocks (CS50x Final Project).

Routes (all HTML forms work without JavaScript; JS only makes them faster):
    GET  /                          board + summary + filters
    GET  /tasks/board               board fragment (used by live filters)
    GET  /tasks/new, POST           create a task
    GET  /tasks/<id>                task detail, focus timer and history
    GET  /tasks/<id>/edit, POST     edit a task
    POST /tasks/<id>/quick          quick change of status and/or priority (HTML or JSON)
    POST /tasks/<id>/delete         delete a task (and its focus logs)
    POST /tasks/<id>/focus          log a focus session
    POST /focus/<id>/delete         delete one focus session
    GET  /projects, POST            list / create projects
    POST /projects/<id>/delete      delete a project (its tasks become "no project")
"""

import os
import sqlite3

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from werkzeug.exceptions import HTTPException

import db
from helpers import (PRIORITIES, SEARCH_MAX, STATUSES, due_info, escape_like,
                     format_minutes, last_n_days, parse_int, safe_next,
                     validate_focus_form, validate_project_form,
                     validate_task_form, wants_json, weekday_short)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    DATABASE=os.environ.get("FOCUSBOARD_DB", os.path.join(app.root_path, "focusboard.db")),
)
db.init_app(app)

app.jinja_env.filters["minutes"] = format_minutes
app.jinja_env.globals["due_info"] = due_info


@app.context_processor
def inject_constants():
    """Make the label dictionaries available in every template."""
    return {"STATUSES": STATUSES, "PRIORITIES": PRIORITIES}


# --------------------------------------------------------------------------- #
# Data helpers (queries reused by several routes)
# --------------------------------------------------------------------------- #

TASK_SELECT = """
    SELECT t.*,
           p.name  AS project_name,
           p.color AS project_color,
           COALESCE((SELECT SUM(f.minutes) FROM focus_logs f WHERE f.task_id = t.id), 0)
               AS focus_minutes
      FROM tasks t
      LEFT JOIN projects p ON p.id = t.project_id
"""


def fetch_projects():
    return db.query("SELECT id, name, color FROM projects ORDER BY name COLLATE NOCASE")


def get_task_or_404(task_id):
    task = db.query(TASK_SELECT + " WHERE t.id = ?", (task_id,), one=True)
    if task is None:
        abort(404, "Esa tarea no existe o fue eliminada.")
    return task


def read_filters(args):
    """Turn the query string into a clean filter dict (invalid values are ignored)."""
    status = args.get("status", "")
    priority = parse_int(args.get("priority"))
    project = args.get("project", "")
    if project not in ("", "none") and parse_int(project) is None:
        project = ""
    return {
        "q": args.get("q", "").strip()[:SEARCH_MAX],
        "status": status if status in STATUSES else "",
        "priority": priority if priority in PRIORITIES else None,
        "project": project,
    }


def fetch_tasks(filters):
    """Return tasks matching the filters, most urgent first."""
    clauses, params = [], []

    if filters["q"]:
        like = f"%{escape_like(filters['q'])}%"
        clauses.append(
            "(t.title LIKE ? ESCAPE '\\' OR t.description LIKE ? ESCAPE '\\'"
            " OR p.name LIKE ? ESCAPE '\\')"
        )
        params += [like, like, like]
    if filters["status"]:
        clauses.append("t.status = ?")
        params.append(filters["status"])
    if filters["priority"]:
        clauses.append("t.priority = ?")
        params.append(filters["priority"])
    if filters["project"] == "none":
        clauses.append("t.project_id IS NULL")
    elif filters["project"]:
        clauses.append("t.project_id = ?")
        params.append(int(filters["project"]))

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    order = """
        ORDER BY t.priority DESC,
                 t.due_date IS NULL, t.due_date,
                 t.created_at DESC
    """
    return db.query(TASK_SELECT + where + order, params)


def group_by_status(tasks):
    board = {status: [] for status in STATUSES}
    for task in tasks:
        board[task["status"]].append(task)
    return board


def fetch_summary():
    """Global numbers for the summary panel (not affected by filters)."""
    row = db.query(
        """
        SELECT COUNT(*) AS total,
               COALESCE(SUM(status = 'pending'), 0)     AS pending,
               COALESCE(SUM(status = 'in_progress'), 0) AS in_progress,
               COALESCE(SUM(status = 'done'), 0)        AS done,
               COALESCE(SUM(status != 'done' AND due_date IS NOT NULL
                            AND due_date < date('now', 'localtime')), 0) AS overdue
          FROM tasks
        """,
        one=True,
    )
    focus = db.query(
        """
        SELECT COALESCE(SUM(minutes), 0) AS total,
               COALESCE(SUM(CASE WHEN date(logged_at) = date('now', 'localtime')
                                 THEN minutes END), 0) AS today
          FROM focus_logs
        """,
        one=True,
    )
    summary = dict(row)
    summary["percent"] = round(summary["done"] * 100 / summary["total"]) if summary["total"] else 0
    summary["focus_total"] = format_minutes(focus["total"])
    summary["focus_today"] = format_minutes(focus["today"])
    return summary


def fetch_week():
    """Focus minutes per day for the last 7 days (for the mini bar chart)."""
    days = last_n_days(7)
    rows = db.query(
        """
        SELECT date(logged_at) AS day, SUM(minutes) AS minutes
          FROM focus_logs
         WHERE date(logged_at) >= ?
         GROUP BY day
        """,
        (days[0],),
    )
    totals = {r["day"]: r["minutes"] for r in rows}
    peak = max(totals.values(), default=0) or 1
    return [
        {
            "day": day,
            "label": weekday_short(day),
            "minutes": totals.get(day, 0),
            "height": round(totals.get(day, 0) * 100 / peak),
        }
        for day in days
    ]


def form_values_from_task(task):
    return {
        "title": task["title"],
        "description": task["description"],
        "project_id": task["project_id"] or "",
        "priority": task["priority"],
        "status": task["status"],
        "due_date": task["due_date"] or "",
        "estimate_minutes": task["estimate_minutes"] or "",
    }


# --------------------------------------------------------------------------- #
# Board
# --------------------------------------------------------------------------- #

@app.route("/")
def index():
    filters = read_filters(request.args)
    tasks = fetch_tasks(filters)
    return render_template(
        "index.html",
        board=group_by_status(tasks),
        count=len(tasks),
        filters=filters,
        projects=fetch_projects(),
        summary=fetch_summary(),
        week=fetch_week(),
    )


@app.route("/tasks/board")
def board_fragment():
    """Only the board HTML; fetched by app.js while the user types or filters."""
    filters = read_filters(request.args)
    tasks = fetch_tasks(filters)
    return render_template("_board.html", board=group_by_status(tasks),
                           count=len(tasks), filters=filters)


# --------------------------------------------------------------------------- #
# Tasks CRUD
# --------------------------------------------------------------------------- #

@app.route("/tasks/new", methods=["GET", "POST"])
def task_new():
    projects = fetch_projects()

    if request.method == "POST":
        data, errors = validate_task_form(request.form, {p["id"] for p in projects})
        if errors:
            flash("Revisa los campos marcados.", "error")
            return render_template("task_form.html", task=None, values=request.form,
                                   errors=errors, projects=projects), 400

        task_id = db.execute(
            """
            INSERT INTO tasks (project_id, title, description, priority, status,
                               due_date, estimate_minutes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?,
                    CASE WHEN ? = 'done' THEN datetime('now', 'localtime') END)
            """,
            (data["project_id"], data["title"], data["description"], data["priority"],
             data["status"], data["due_date"], data["estimate_minutes"], data["status"]),
        )
        flash(f"Tarea «{data['title']}» creada.", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    # Allow "?project=<id>" to pre-select a project.
    defaults = {"priority": 2, "status": "pending",
                "project_id": parse_int(request.args.get("project"), "")}
    return render_template("task_form.html", task=None, values=defaults,
                           errors={}, projects=projects)


@app.route("/tasks/<int:task_id>")
def task_detail(task_id):
    task = get_task_or_404(task_id)
    logs = db.query(
        "SELECT * FROM focus_logs WHERE task_id = ? ORDER BY logged_at DESC, id DESC",
        (task_id,),
    )
    progress = None
    if task["estimate_minutes"]:
        progress = min(100, round(task["focus_minutes"] * 100 / task["estimate_minutes"]))
    return render_template("task.html", task=task, logs=logs, progress=progress)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def task_edit(task_id):
    task = get_task_or_404(task_id)
    projects = fetch_projects()

    if request.method == "POST":
        data, errors = validate_task_form(request.form, {p["id"] for p in projects})
        if errors:
            flash("Revisa los campos marcados.", "error")
            return render_template("task_form.html", task=task, values=request.form,
                                   errors=errors, projects=projects), 400

        db.execute(
            """
            UPDATE tasks
               SET project_id = ?, title = ?, description = ?, priority = ?, status = ?,
                   due_date = ?, estimate_minutes = ?,
                   completed_at = CASE WHEN ? = 'done'
                                       THEN COALESCE(completed_at, datetime('now', 'localtime'))
                                  END,
                   updated_at = datetime('now', 'localtime')
             WHERE id = ?
            """,
            (data["project_id"], data["title"], data["description"], data["priority"],
             data["status"], data["due_date"], data["estimate_minutes"], data["status"],
             task_id),
        )
        flash("Cambios guardados.", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    return render_template("task_form.html", task=task, values=form_values_from_task(task),
                           errors={}, projects=projects)


@app.post("/tasks/<int:task_id>/quick")
def task_quick_update(task_id):
    """Change status and/or priority without opening the edit form."""
    task = get_task_or_404(task_id)
    payload = request.get_json(silent=True) or request.form

    status = payload.get("status", task["status"])
    priority = parse_int(payload.get("priority"), task["priority"])
    if status not in STATUSES:
        abort(400, "Estado no válido.")
    if priority not in PRIORITIES:
        abort(400, "Prioridad no válida.")

    db.execute(
        """
        UPDATE tasks
           SET status = ?, priority = ?,
               completed_at = CASE WHEN ? = 'done'
                                   THEN COALESCE(completed_at, datetime('now', 'localtime'))
                              END,
               updated_at = datetime('now', 'localtime')
         WHERE id = ?
        """,
        (status, priority, status, task_id),
    )

    message = f"«{task['title']}»: {STATUSES[status]} · prioridad {PRIORITIES[priority]}."
    if wants_json():
        return jsonify(ok=True, status=status, priority=priority,
                       message=message, summary=fetch_summary())

    flash(message, "success")
    return redirect(safe_next(payload.get("next"), url_for("index")))


@app.post("/tasks/<int:task_id>/delete")
def task_delete(task_id):
    task = get_task_or_404(task_id)
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))   # focus_logs cascade
    flash(f"Tarea «{task['title']}» eliminada.", "success")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Focus sessions
# --------------------------------------------------------------------------- #

@app.post("/tasks/<int:task_id>/focus")
def focus_add(task_id):
    task = get_task_or_404(task_id)
    data, errors = validate_focus_form(request.form)
    if errors:
        for message in errors.values():
            flash(message, "error")
        return redirect(url_for("task_detail", task_id=task_id))

    db.execute(
        "INSERT INTO focus_logs (task_id, minutes, note) VALUES (?, ?, ?)",
        (task_id, data["minutes"], data["note"]),
    )
    # Working on a pending task means it is now in progress.
    if task["status"] == "pending":
        db.execute(
            "UPDATE tasks SET status = 'in_progress', updated_at = datetime('now', 'localtime')"
            " WHERE id = ?",
            (task_id,),
        )
        flash("La tarea pasó a «En progreso».", "info")

    flash(f"Sesión de enfoque de {format_minutes(data['minutes'])} registrada.", "success")
    return redirect(url_for("task_detail", task_id=task_id))


@app.post("/focus/<int:log_id>/delete")
def focus_delete(log_id):
    log = db.query("SELECT task_id FROM focus_logs WHERE id = ?", (log_id,), one=True)
    if log is None:
        abort(404, "Esa sesión de enfoque no existe.")
    db.execute("DELETE FROM focus_logs WHERE id = ?", (log_id,))
    flash("Sesión eliminada.", "success")
    return redirect(url_for("task_detail", task_id=log["task_id"]))


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #

@app.route("/projects", methods=["GET", "POST"])
def projects():
    errors, values, status_code = {}, {}, 200

    if request.method == "POST":
        data, errors = validate_project_form(request.form)
        values = request.form
        if not errors:
            try:
                db.execute("INSERT INTO projects (name, color) VALUES (?, ?)",
                           (data["name"], data["color"]))
            except sqlite3.IntegrityError:
                errors["name"] = "Ya existe un proyecto con ese nombre."
            else:
                flash(f"Proyecto «{data['name']}» creado.", "success")
                return redirect(url_for("projects"))
        status_code = 400

    rows = db.query(
        """
        SELECT p.id, p.name, p.color,
               COUNT(t.id)                            AS total,
               COALESCE(SUM(t.status = 'done'), 0)    AS done
          FROM projects p
          LEFT JOIN tasks t ON t.project_id = p.id
         GROUP BY p.id
         ORDER BY p.name COLLATE NOCASE
        """
    )
    return render_template("projects.html", projects=rows, errors=errors,
                           values=values), status_code


@app.post("/projects/<int:project_id>/delete")
def project_delete(project_id):
    project = db.query("SELECT name FROM projects WHERE id = ?", (project_id,), one=True)
    if project is None:
        abort(404, "Ese proyecto no existe.")
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))  # tasks -> NULL
    flash(f"Proyecto «{project['name']}» eliminado. Sus tareas quedaron sin proyecto.", "success")
    return redirect(url_for("projects"))


# --------------------------------------------------------------------------- #
# Friendly error pages (HTML for browsers, JSON for fetch requests)
# --------------------------------------------------------------------------- #

FRIENDLY_ERRORS = {
    400: "La solicitud no es válida. Revisa los datos enviados.",
    404: "No encontramos la página que buscas.",
    405: "Ese método no está permitido para esta dirección.",
    500: "Algo salió mal en el servidor. Inténtalo de nuevo.",
}


@app.errorhandler(HTTPException)
def handle_http_error(error):
    # Use our custom message from abort(code, "...") if there is one.
    custom = error.description != type(error).description
    message = error.description if custom else FRIENDLY_ERRORS.get(error.code, error.description)
    if wants_json():
        return jsonify(ok=False, error=message), error.code
    return render_template("error.html", code=error.code, name=error.name,
                           message=message), error.code


if __name__ == "__main__":
    app.run(debug=True)
