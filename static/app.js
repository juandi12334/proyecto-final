// AI citation (CS50x Final Project): Claude (Anthropic) and ChatGPT (OpenAI) were used as
// development assistants during the creation of this project.
//
// FocusBoard front-end (vanilla JavaScript, no libraries).
// Every feature here is a progressive enhancement: the HTML forms already
// work without JavaScript, this file just makes them instant.
//   1. Live filters/search  -> fetches the board fragment from /tasks/board
//   2. Quick status/priority -> POST JSON to /tasks/<id>/quick, updates summary
//   3. Focus timer           -> survives reloads (localStorage), saves minutes
//   4. Small UI helpers      -> confirm dialogs, closable flashes, toast

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  setupFlashes();
  setupConfirmForms();
  setupFilters();
  setupQuickUpdates();
  setupTimer();
});

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function debounce(fn, wait) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), wait);
  };
}

let toastTimer;
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("toast-error", isError);
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 2800);
}

// localStorage can throw (private mode, blocked storage) - never let that break the page.
const storage = {
  get(key) {
    try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ }
  },
  remove(key) {
    try { localStorage.removeItem(key); } catch { /* ignore */ }
  },
};

/* ------------------------------------------------------------------ */
/* Flash messages and confirmations                                    */
/* ------------------------------------------------------------------ */

function setupFlashes() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-dismiss]");
    if (button) button.closest(".flash")?.remove();
  });
}

function setupConfirmForms() {
  // Any <form data-confirm="..."> asks before submitting (used for deletes).
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (form.matches("[data-confirm]") && !window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });
}

/* ------------------------------------------------------------------ */
/* 1. Live filters / search                                            */
/* ------------------------------------------------------------------ */

function setupFilters() {
  const form = document.getElementById("filters");
  const board = document.getElementById("board");
  if (!form || !board) return;

  let controller = null;

  const refresh = async () => {
    const params = new URLSearchParams(new FormData(form));
    // Drop empty values so the URL stays clean (e.g. "/?q=video").
    for (const [key, value] of [...params]) {
      if (!value) params.delete(key);
    }
    const query = params.toString();

    controller?.abort();                       // cancel an older, slower request
    controller = new AbortController();
    try {
      const response = await fetch(`${form.dataset.boardUrl}?${query}`, {
        headers: { Accept: "text/html" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      board.innerHTML = await response.text();
      history.replaceState(null, "", query ? `?${query}` : location.pathname);
    } catch (error) {
      if (error.name !== "AbortError") showToast("No se pudo actualizar el tablero.", true);
    }
  };

  const debouncedRefresh = debounce(refresh, 200);
  form.addEventListener("input", debouncedRefresh);       // typing in the search box
  form.addEventListener("change", debouncedRefresh);      // selects
  form.addEventListener("submit", (event) => { event.preventDefault(); refresh(); });

  form.querySelector("[data-clear-filters]")?.addEventListener("click", (event) => {
    event.preventDefault();
    form.reset();
    form.querySelectorAll("input, select").forEach((field) => { field.value = ""; });
    refresh();
  });

  // Expose so quick updates can re-render the board (cards change column).
  board.refresh = refresh;
}

/* ------------------------------------------------------------------ */
/* 2. Quick status / priority change on the board                      */
/* ------------------------------------------------------------------ */

function updateSummary(summary) {
  if (!summary) return;
  for (const [key, value] of Object.entries(summary)) {
    document.querySelectorAll(`[data-stat="${key}"]`).forEach((el) => {
      el.textContent = value;
      if (key === "overdue") el.classList.toggle("text-danger", value > 0);
    });
  }
  const bar = document.querySelector("[data-progress]");
  if (bar) {
    bar.style.width = `${summary.percent}%`;
    bar.parentElement.setAttribute("aria-valuenow", summary.percent);
  }
}

function setupQuickUpdates() {
  const board = document.getElementById("board");
  if (!board) return;

  // Event delegation: works for cards rendered later by the live filters.
  board.addEventListener("change", async (event) => {
    const form = event.target.closest("form[data-quick]");
    if (!form) return;

    const card = form.closest(".task-card");
    card?.classList.add("is-updating");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          status: form.elements.status.value,
          priority: form.elements.priority.value,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "Error");

      updateSummary(data.summary);
      showToast(data.message);
      if (typeof board.refresh === "function") await board.refresh();
    } catch (error) {
      showToast(error.message || "No se pudo guardar el cambio.", true);
      card?.classList.remove("is-updating");
    }
  });
}

/* ------------------------------------------------------------------ */
/* 3. Focus timer                                                      */
/* ------------------------------------------------------------------ */

function formatClock(totalMs) {
  const totalSeconds = Math.floor(totalMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return hours ? `${hours}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`;
}

function setupTimer() {
  const timer = document.getElementById("timer");
  const focusForm = document.getElementById("focus-form");
  if (!timer || !focusForm) return;

  const key = `focusboard.timer.${timer.dataset.taskId}`;
  const display = timer.querySelector("[data-timer-display]");
  const stateLabel = timer.querySelector("[data-timer-state]");
  const startBtn = timer.querySelector("[data-timer-start]");
  const pauseBtn = timer.querySelector("[data-timer-pause]");
  const resetBtn = timer.querySelector("[data-timer-reset]");
  const finishBtn = timer.querySelector("[data-timer-finish]");
  const baseTitle = document.title;

  // State: accumulated milliseconds + timestamp of the current run (or null).
  let state = storage.get(key) || { accumulated: 0, startedAt: null };
  let tickId = null;

  const elapsed = () => state.accumulated + (state.startedAt ? Date.now() - state.startedAt : 0);
  const save = () => storage.set(key, state);

  function render() {
    const running = Boolean(state.startedAt);
    const clock = formatClock(elapsed());
    display.textContent = clock;
    timer.classList.toggle("is-running", running);
    startBtn.hidden = running;
    pauseBtn.hidden = !running;
    startBtn.lastElementChild.textContent = elapsed() > 0 ? "Reanudar" : "Iniciar";
    stateLabel.textContent = running ? "Enfocado…" : (elapsed() > 0 ? "En pausa" : "Listo para empezar");
    document.title = running ? `⏱ ${clock} · ${baseTitle}` : baseTitle;
  }

  function startTicking() {
    clearInterval(tickId);
    tickId = setInterval(render, 500);
  }

  startBtn.addEventListener("click", () => {
    state.startedAt = Date.now();
    save();
    startTicking();
    render();
  });

  pauseBtn.addEventListener("click", () => {
    state.accumulated = elapsed();
    state.startedAt = null;
    save();
    clearInterval(tickId);
    render();
  });

  resetBtn.addEventListener("click", () => {
    if (elapsed() > 0 && !window.confirm("¿Reiniciar el temporizador sin guardar?")) return;
    state = { accumulated: 0, startedAt: null };
    storage.remove(key);
    clearInterval(tickId);
    render();
  });

  finishBtn.addEventListener("click", () => {
    const ms = elapsed();
    if (ms < 1000) {
      showToast("Inicia el temporizador antes de guardar.", true);
      return;
    }
    // Round to the nearest minute, minimum 1 (the server accepts 1-600).
    const minutes = Math.min(600, Math.max(1, Math.round(ms / 60000)));
    focusForm.elements.minutes.value = minutes;
    if (!focusForm.elements.note.value.trim()) {
      focusForm.elements.note.value = "Sesión con temporizador";
    }
    storage.remove(key);
    clearInterval(tickId);
    focusForm.submit();                         // normal POST -> server validates & saves
  });

  if (state.startedAt) startTicking();          // resume a timer that was running before reload
  render();
}
