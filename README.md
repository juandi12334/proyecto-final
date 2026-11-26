# FocusBoard

#### Video Demo: https://youtu.be/x2QojzbHHQE

#### Description:

FocusBoard is a web application for managing tasks and tracking the real time spent focused on each one. It was built with Python, Flask, SQLite, Jinja, CSS, and vanilla JavaScript as my final project for CS50x. The interface is written in Spanish because that is my native language and the language of the people I built it for, while the code, comments, and this document are in English.

Most to-do apps answer one question: *what do I still have to do?* While studying for CS50, I noticed that I also wanted to answer a second question: *where did my time actually go?* I could mark a problem set as done without knowing whether it took two hours or ten, and I had no simple way to see whether I was making progress during the week. FocusBoard addresses both needs in one place. Tasks are organized in a three-column board (Pending, In progress, and Done), can be grouped by project, and can be assigned a priority (High, Medium, or Low), a due date, and an optional time estimate. Each task also has a focus timer that records work sessions in the database.

The home page summarizes completed tasks, overdue tasks, focus minutes for the current day and overall, and a bar chart showing focus time over the last seven days. This makes it possible to review not only what remains to be done, but also how time is being spent.

### Main features

- **Task management (CRUD):** create, view, edit, and delete tasks, with server-side validation and inline error messages.
- **Projects:** create projects with custom colors. Deleting a project does not delete its tasks; those tasks simply become unassigned.
- **Three-column board:** tasks are sorted by priority and then by due date, with visual cues for overdue tasks and tasks due soon.
- **Live search and filters:** searching or changing the status, priority, or project filter refreshes the board without reloading the page. The URL is updated so a filtered view can be bookmarked or shared.
- **Quick changes:** each task card includes controls for changing status and priority. Changes are saved in the background and summary values are updated immediately.
- **Focus timer:** each task page includes a start, pause, and reset timer. Its state is saved in the browser, so it continues accurately after a page reload. Selecting “Finish and save” stores the session duration in the database. Focus sessions can also be added manually.
- **Progress summary:** completion percentage, task counts by status, overdue tasks, focus time today and in total, a seven-day chart, and a task-level progress bar comparing focused time with the estimate.
- **Error handling:** friendly pages for HTTP 400, 404, 405, and 500 errors, plus JSON error responses for background requests.
- **Responsive design:** a low-saturation dark interface designed to work on phones without horizontal scrolling.

### Files

- **`app.py`** is the Flask application. It configures the app, registers Jinja filters, and defines the routes for the board (`/`), the board fragment used by live filters (`/tasks/board`), task creation, viewing, editing and deletion, quick status and priority updates (`/tasks/<id>/quick`), focus-session logging and deletion, and project management. It also contains helper functions for SQL queries used by filters, summaries, and the seven-day chart. Its error handler renders `error.html` or returns JSON, depending on the request.
- **`db.py`** contains the database layer. It opens one SQLite connection per request (stored in Flask's `g`), enables foreign keys, provides `query` and `execute` helpers that use parameterized SQL, and closes the connection at the end of the request. It defines the `flask --app app init-db [--seed]` command and creates the database from `schema.sql` the first time the app runs.
- **`helpers.py`** contains constants, status and priority labels, input validators for task, focus-session, and project forms, and display helpers such as `format_minutes` and `due_info`.
- **`schema.sql`** defines the related `projects`, `tasks`, and `focus_logs` tables. Foreign keys preserve relationships, `CHECK` constraints protect valid statuses, priorities, and focus-session lengths, and indexes support common filters and summaries.
- **`seed.sql`** contains optional demonstration data. Its dates are relative to the current day, so the sample data includes tasks due today, overdue, due soon, and recent focus sessions.
- **`requirements.txt`** lists Flask, the project's Python dependency. **`.gitignore`** excludes virtual environments, caches, secrets, editor files, and local database files.
- **`templates/layout.html`** is the base template containing navigation, flash messages, the footer, and the toast notification used by JavaScript. **`templates/_icons.html`** is an inline SVG sprite, and **`templates/_macros.html`** contains reusable Jinja macros for icons, priority badges, project labels, and form errors.
- **`templates/index.html`** displays the summary, filter bar, and includes **`templates/_board.html`**, which renders the three-column board. The same board partial is returned by `/tasks/board`, allowing the live filters to reuse the server-rendered markup.
- **`templates/task.html`** displays task details, the focus timer, the manual focus-session form, and session history. **`templates/task_form.html`** is shared by task creation and editing. **`templates/projects.html`** manages projects, and **`templates/error.html`** displays friendly error messages.
- **`static/styles.css`** contains the visual design, using CSS custom properties, CSS Grid, Flexbox, and media queries for smaller screens.
- **`static/app.js`** contains the vanilla JavaScript for live filtering with `fetch` (including cancellation of older requests with `AbortController`), quick status and priority updates, summary updates, the focus timer with `localStorage`, delete confirmations, and dismissible messages.

### Design decisions

**Progressive enhancement.** Each action is implemented as a normal HTML form that works without JavaScript. JavaScript improves the experience by intercepting filter changes, quick updates, and timer actions. This keeps the server as the source of truth and makes the application easier to test and debug.

**Rendering HTML fragments instead of building cards in JavaScript.** For live search, I considered returning JSON and creating the task cards in JavaScript. That would duplicate the card markup in two languages. Instead, `/tasks/board` renders the same `_board.html` partial, and JavaScript replaces the board container. Filtering takes place in SQL, with `LIKE` wildcards escaped, so the results remain consistent with the database.

**A separate `focus_logs` table.** Storing each focus session separately, rather than keeping only a total number of minutes on a task, makes it possible to show session history, add notes, delete an incorrect entry, and calculate daily and weekly totals with SQL aggregation.

**Validation in two layers.** Python validates form input and displays helpful messages. SQLite `CHECK` constraints and foreign keys provide an additional layer of data integrity.

**Automatic status changes.** Logging focus time on a pending task moves it to In progress, because working on a task means it has started. Marking a task as Done stores `completed_at`, and reopening it clears that date.

**No user accounts.** FocusBoard is designed as a personal, local tool. I chose to focus on time tracking and the interface rather than adding a login system. A future multi-user version could add a `users` table and a `user_id` column.

### How to run

1. Install Python 3.
2. Create and activate a virtual environment:

   **Windows (PowerShell):**

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **macOS/Linux:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   flask --app app run
   ```

5. Open http://127.0.0.1:5000 in a browser.

The application creates an empty database automatically on its first run. To reset the database and load the optional demonstration data, run `flask --app app init-db --seed`. **This command deletes the existing database contents before recreating the tables and loading the sample data**, so it should only be used when a reset is intended.

### AI citation

In accordance with CS50's academic honesty policy, I used **Claude (by Anthropic)** and **ChatGPT (by OpenAI)** as development assistants while working on this project. They supported parts of the development process, including planning, code structure, debugging, and documentation. The final project was reviewed and assembled for this submission, and the use of these tools is also acknowledged in comments at the top of the relevant project files.
