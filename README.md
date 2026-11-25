# FocusBoard
#### Video Demo: <URL HERE>
#### Description:

FocusBoard is a web application for managing tasks and tracking the real time you spend focused on each one. It was built with Python, Flask, SQLite, Jinja, CSS and vanilla JavaScript as my final project for CS50x. The interface is written in Spanish because that is my native language and the language of the people I built it for, but the code, comments and this document are in English.

Most to-do apps answer only one question: *what do I still have to do?* While studying for CS50 I noticed that I also wanted to answer a second question: *where did my time actually go?* I would mark a problem set as "done" without knowing whether it took me two hours or ten, and I had no simple way to see whether I was progressing during the week. FocusBoard tries to solve both problems in one place. Tasks are organized in a three-column board (Pending, In progress, Done), they can be grouped by project, given a priority (High, Medium, Low), a due date and an optional time estimate, and every task has a built-in focus timer that records work sessions in the database. The home page then summarizes everything: how many tasks are completed, how many are overdue, how many minutes I focused today and in total, and a small bar chart of the focus minutes of the last seven days.

##### Main features

- **Full CRUD for tasks**: create, read, edit and delete tasks, with server-side validation and inline error messages.
- **Projects (labels)**: create projects with a custom color; deleting a project does not delete its tasks, they simply become "no project".
- **Three-column board** sorted by priority and then by due date, with color cues for overdue tasks and tasks due soon.
- **Real-time search and filters**: typing in the search box or changing the status, priority or project filters refreshes the board instantly without reloading the page, and the URL is updated so the filtered view can be bookmarked or shared.
- **Quick changes**: every card has two selects to change status and priority; the change is saved in the background and the summary numbers are updated immediately.
- **Focus timer**: on each task page there is a start/pause/reset timer. Its state is saved in the browser, so if I reload the page or close the tab by accident the timer keeps counting. When I press "Finish and save" the minutes are stored as a focus session. Sessions can also be added manually.
- **Progress summary**: completion percentage, counts by status, overdue tasks, focus time today and in total, a seven-day chart, and on each task a progress bar comparing focused time against the estimate.
- **Friendly error pages** for 400, 404, 405 and 500 errors (and JSON errors for background requests).
- **Responsive, low-saturation dark design** that works on phones without horizontal scrolling.

##### Files

- **`app.py`** is the Flask application. It configures the app, registers Jinja filters and defines every route: the board (`/`), the board fragment used by the live filters (`/tasks/board`), creating, viewing, editing and deleting tasks, the quick status/priority endpoint (`/tasks/<id>/quick`, which answers with HTML redirects for normal forms or JSON for JavaScript), logging and deleting focus sessions, and managing projects. It also contains helper functions that build the SQL queries for the filters, the summary and the seven-day chart, and a single error handler that renders `error.html` or returns JSON depending on what the client asked for.
- **`db.py`** contains the database layer. It opens one SQLite connection per request (stored in Flask's `g`), enables foreign keys, offers two small helpers (`query` and `execute`) that always use `?` placeholders, and closes the connection when the request ends. It also defines the `flask --app app init-db [--seed]` command and automatically creates the database from `schema.sql` the first time the app runs.
- **`helpers.py`** holds the constants (status and priority labels, length limits), the validators for task, focus and project forms, and display helpers such as `format_minutes` (turns 75 into "1 h 15 min") and `due_info` (turns a date into "Due tomorrow", "Overdue 2 days ago", etc.). Keeping validation here keeps the routes short and lets the same rules be applied to HTML forms and JSON requests.
- **`schema.sql`** defines three related tables: `projects`, `tasks` (with a foreign key to projects using `ON DELETE SET NULL`) and `focus_logs` (with a foreign key to tasks using `ON DELETE CASCADE`). `CHECK` constraints protect the data even if a bug slipped past the Python validation (valid statuses, priorities 1-3, focus sessions between 1 and 600 minutes), and indexes speed up the columns used by filters and summaries.
- **`seed.sql`** is optional demo data. Its dates are relative to the current day, so the demo always contains a task due today, one overdue, one due soon, and recent focus sessions.
- **`requirements.txt`** lists the only dependency, Flask. **`.gitignore`** excludes the virtual environment, caches, secrets and the local database file.
- **`templates/layout.html`** is the base template with the navigation bar, flash messages, footer and the toast used by JavaScript. **`_icons.html`** is an inline SVG sprite, so icons need no external library, and **`_macros.html`** contains reusable macros for icons, priority badges, project chips and field errors.
- **`templates/index.html`** shows the summary, the filter bar and includes **`_board.html`**, the three-column board. `_board.html` is also rendered alone by `/tasks/board`, so the live filters reuse exactly the same template as the server.
- **`templates/task.html`** is the task detail page with the timer, the manual focus form and the session history. **`task_form.html`** is shared by "new task" and "edit task". **`projects.html`** lists and creates projects, and **`error.html`** renders friendly error messages.
- **`static/styles.css`** contains the whole visual design, built with CSS custom properties, CSS Grid and Flexbox and a few media queries for tablets and phones.
- **`static/app.js`** contains the vanilla JavaScript: live filtering with `fetch` (cancelling older requests with `AbortController`), quick status/priority updates, updating the summary, the focus timer with `localStorage`, delete confirmations and closable messages.

##### Design decisions

**Progressive enhancement.** Every action is a normal HTML form that works without JavaScript. JavaScript only makes it faster: it intercepts filter changes, quick updates and the timer. This kept the server as the single source of truth and made debugging much easier, because I could always test a route with a plain form first.

**Rendering HTML fragments instead of building cards in JavaScript.** For the live search I considered returning JSON and creating the cards in JavaScript, but that would duplicate the card markup in two languages. Instead, `/tasks/board` renders the same `_board.html` partial and JavaScript only replaces the container. Filtering happens in SQL (with `LIKE` wildcards escaped), so search results are always consistent with the database.

**A separate `focus_logs` table.** I could have stored a single "minutes spent" number in `tasks`, but storing each session separately allows a history with notes, deleting a wrong entry, and calculating "today" and the seven-day chart with simple `GROUP BY` queries.

**Validation in two layers.** Python validates and shows friendly messages; SQLite `CHECK` and foreign-key constraints guarantee integrity anyway.

**Automatic status change.** Logging focus on a pending task moves it to "In progress", because working on a task means it has started. Marking a task as done stores `completed_at`, and reopening it clears that date.

**No user accounts.** FocusBoard is designed as a personal, local tool, so I chose to spend my time on the focus tracking and the interface instead of a login system. Adding a `users` table and a `user_id` column would be the natural next step.

##### How to run

```
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
flask --app app init-db --seed # optional: reset the database and load demo data
flask --app app run
```

Then open http://127.0.0.1:5000. If `init-db` is not run, an empty database is created automatically on the first start.

##### AI citation

In accordance with CS50's academic honesty policy, I used Claude (by Anthropic) as a development assistant while building this project, to help with the structure of the code, debugging and writing. Every source file contains a comment at the top stating this.
