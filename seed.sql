-- AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI)
-- were used as development assistants during the creation of this project.
--
-- Optional demo data for FocusBoard. Dates are relative to "today" so the
-- board always looks realistic (some tasks due soon, one overdue, etc.).

INSERT INTO projects (name, color) VALUES
    ('CS50',     '#7f9cc2'),
    ('Personal', '#8fb39a'),
    ('Trabajo',  '#c2a477');

INSERT INTO tasks (project_id, title, description, priority, status, due_date, estimate_minutes, completed_at) VALUES
    (1, 'Grabar video del Final Project', 'Máximo 3 minutos. Seguir el guion y mostrar todas las funciones.', 3, 'pending', date('now', 'localtime', '+3 day'), 60, NULL),
    (1, 'Escribir README.md', 'Explicar cada archivo y las decisiones de diseño.', 3, 'in_progress', date('now', 'localtime', '+2 day'), 90, NULL),
    (1, 'Terminar Problem Set 9 (Finance)', 'Revisar check50 y style50 antes de enviar.', 2, 'done', date('now', 'localtime', '-2 day'), 240, datetime('now', 'localtime', '-1 day')),
    (2, 'Hacer ejercicio 30 minutos', '', 1, 'pending', date('now', 'localtime'), 30, NULL),
    (2, 'Leer capítulo 4 de "Clean Code"', 'Tomar notas de las ideas principales.', 1, 'pending', NULL, 45, NULL),
    (3, 'Preparar informe mensual', 'Consolidar métricas y enviar al equipo.', 3, 'pending', date('now', 'localtime', '-1 day'), 120, NULL),
    (NULL, 'Organizar escritorio y archivos', 'Tarea sin proyecto asignado.', 2, 'pending', NULL, NULL, NULL);

INSERT INTO focus_logs (task_id, minutes, note, logged_at) VALUES
    (2, 25, 'Estructura y secciones del README', datetime('now', 'localtime', '-1 day')),
    (2, 30, 'Descripción de archivos', datetime('now', 'localtime', '-3 hours')),
    (3, 50, 'Ruta /buy y /sell', datetime('now', 'localtime', '-4 day')),
    (3, 45, 'Historial y estilos', datetime('now', 'localtime', '-3 day')),
    (3, 60, 'Depuración final', datetime('now', 'localtime', '-2 day')),
    (6, 20, 'Recolección de datos', datetime('now', 'localtime', '-5 day'));
