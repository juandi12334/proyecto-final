# AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI) were used as
# development assistants during the creation of this project.
"""Constants, input validation and small formatting helpers for FocusBoard.

Keeping validation here (instead of inside the routes) makes app.py shorter
and lets the same rules be reused for HTML forms and JSON requests.
"""

import re
from datetime import date, timedelta

from flask import request

# Internal value -> label shown in the (Spanish) interface.
STATUSES = {
    "pending": "Pendiente",
    "in_progress": "En progreso",
    "done": "Completada",
}

# Ordered from highest to lowest so selects show "Alta" first.
PRIORITIES = {
    3: "Alta",
    2: "Media",
    1: "Baja",
}

TITLE_MAX = 120
DESCRIPTION_MAX = 1000
NOTE_MAX = 200
PROJECT_NAME_MAX = 40
SEARCH_MAX = 100
FOCUS_MIN, FOCUS_MAX = 1, 600          # minutes per focus session
ESTIMATE_MAX = 10000                   # minutes (~166 h)

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_COLOR = "#7f9cc2"


# --------------------------------------------------------------------------- #
# Generic parsing helpers
# --------------------------------------------------------------------------- #

def wants_json():
    """True when the client (our fetch() calls) asked for a JSON response."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return request.is_json or best == "application/json"


def parse_int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_iso_date(value):
    """Return a valid 'YYYY-MM-DD' string, None for empty input, or raise ValueError."""
    value = (value or "").strip()
    if not value:
        return None
    parsed = date.fromisoformat(value)
    if not 2000 <= parsed.year <= 2100:
        raise ValueError("year out of range")
    return parsed.isoformat()


def safe_next(target, fallback):
    """Only allow redirects to local paths (prevents open redirects)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def escape_like(text):
    """Escape LIKE wildcards so a search for '50%' matches the literal text."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# --------------------------------------------------------------------------- #
# Form validators: each returns (clean_data, errors) where errors maps
# field name -> message in Spanish. An empty errors dict means valid input.
# --------------------------------------------------------------------------- #

def validate_task_form(form, valid_project_ids):
    errors = {}

    title = (form.get("title") or "").strip()
    if not title:
        errors["title"] = "El título es obligatorio."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"El título no puede superar {TITLE_MAX} caracteres."

    description = (form.get("description") or "").strip()
    if len(description) > DESCRIPTION_MAX:
        errors["description"] = f"La descripción no puede superar {DESCRIPTION_MAX} caracteres."

    project_raw = (form.get("project_id") or "").strip()
    project_id = None
    if project_raw:
        project_id = parse_int(project_raw)
        if project_id not in valid_project_ids:
            errors["project_id"] = "Selecciona un proyecto válido."

    priority = parse_int(form.get("priority"), 2)
    if priority not in PRIORITIES:
        errors["priority"] = "Selecciona una prioridad válida."

    status = form.get("status") or "pending"
    if status not in STATUSES:
        errors["status"] = "Selecciona un estado válido."

    try:
        due_date = parse_iso_date(form.get("due_date"))
    except ValueError:
        due_date = None
        errors["due_date"] = "La fecha límite no es válida (usa AAAA-MM-DD)."

    estimate_raw = (form.get("estimate_minutes") or "").strip()
    estimate = None
    if estimate_raw:
        estimate = parse_int(estimate_raw)
        if estimate is None or not 1 <= estimate <= ESTIMATE_MAX:
            errors["estimate_minutes"] = f"La estimación debe ser un entero entre 1 y {ESTIMATE_MAX}."

    data = {
        "title": title,
        "description": description,
        "project_id": project_id,
        "priority": priority,
        "status": status,
        "due_date": due_date,
        "estimate_minutes": estimate,
    }
    return data, errors


def validate_focus_form(form):
    errors = {}
    minutes = parse_int(form.get("minutes"))
    if minutes is None or not FOCUS_MIN <= minutes <= FOCUS_MAX:
        errors["minutes"] = f"Los minutos deben ser un entero entre {FOCUS_MIN} y {FOCUS_MAX}."

    note = (form.get("note") or "").strip()
    if len(note) > NOTE_MAX:
        errors["note"] = f"La nota no puede superar {NOTE_MAX} caracteres."

    return {"minutes": minutes, "note": note}, errors


def validate_project_form(form):
    errors = {}
    name = " ".join((form.get("name") or "").split())   # collapse extra spaces
    if not name:
        errors["name"] = "El nombre del proyecto es obligatorio."
    elif len(name) > PROJECT_NAME_MAX:
        errors["name"] = f"El nombre no puede superar {PROJECT_NAME_MAX} caracteres."

    color = (form.get("color") or DEFAULT_COLOR).strip()
    if not COLOR_RE.match(color):
        errors["color"] = "El color debe tener el formato #RRGGBB."

    return {"name": name, "color": color.lower()}, errors


# --------------------------------------------------------------------------- #
# Jinja filters / display helpers
# --------------------------------------------------------------------------- #

def format_minutes(minutes):
    """75 -> '1 h 15 min', 40 -> '40 min', 0 -> '0 min'."""
    minutes = int(minutes or 0)
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} h {rest} min"
    if hours:
        return f"{hours} h"
    return f"{rest} min"


def due_info(due_date, status):
    """Return (label, css_class) describing how close a due date is."""
    if not due_date:
        return None, ""
    try:
        due = date.fromisoformat(due_date)
    except ValueError:
        return due_date, ""

    if status == "done":
        return f"Vencía {due.strftime('%d/%m')}", "due-done"

    days = (due - date.today()).days
    if days < 0:
        return f"Vencida hace {-days} día{'s' if days != -1 else ''}", "due-overdue"
    if days == 0:
        return "Vence hoy", "due-today"
    if days == 1:
        return "Vence mañana", "due-soon"
    if days <= 3:
        return f"Vence en {days} días", "due-soon"
    return f"Vence {due.strftime('%d/%m/%Y')}", ""


def last_n_days(n=7):
    """List of ISO dates for the last n days, oldest first (today included)."""
    today = date.today()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(n - 1, -1, -1)]


WEEKDAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def weekday_short(iso_date):
    return WEEKDAYS_ES[date.fromisoformat(iso_date).weekday()]
