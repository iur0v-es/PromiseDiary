"use strict";

const $ = (id) => document.getElementById(id);

let listRequestId = 0;

function showMessage(text, isError = false) {
    $("message").textContent = text;
    $("message").className = isError ? "error" : "";
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    const data = await response.json();

    if (!response.ok) {
        const detail = data.detail;
        const text = Array.isArray(detail)
            ? detail.map((error) => error.msg).join("; ")
            : detail;

        throw new Error(text || "Не удалось выполнить запрос");
    }

    return data;
}

function localDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

function formatDate(value) {
    return new Date(`${value}T12:00:00`).toLocaleDateString("ru-RU");
}

function getDateRange() {
    const period = $("period").value;

    if (period === "all") {
        return null;
    }

    const value = $("period-date").value || localDate(new Date());
    const selected = new Date(`${value}T12:00:00`);

    let start = new Date(selected);
    let end = new Date(selected);

    if (period === "week") {
        const offset = (selected.getDay() + 6) % 7;

        start.setDate(selected.getDate() - offset);
        end = new Date(start);
        end.setDate(start.getDate() + 6);
    }

    if (period === "month") {
        start = new Date(
            selected.getFullYear(),
            selected.getMonth(),
            1,
            12,
        );

        end = new Date(
            selected.getFullYear(),
            selected.getMonth() + 1,
            0,
            12,
        );
    }

    return [localDate(start), localDate(end)];
}

function renderTasks(tasks) {
    const container = $("task-list");
    container.replaceChildren();

    if (tasks.length === 0) {
        container.textContent = "По выбранным условиям дел нет.";
        return;
    }

    for (const task of tasks) {
        const card = document.createElement("article");
        card.className = "task-card";
        card.dataset.taskId = task.id;

        const title = document.createElement("h3");
        title.textContent = task.title;

        const description = document.createElement("p");
        description.className = "task-description";
        description.textContent = task.description;

        const meta = document.createElement("p");
        meta.className = "task-meta";

        const status = task.status === "open" ? "Открыто" : "Закрыто";

        meta.textContent =
            `№${task.id} · ${status} · ` +
            `Обещано: ${formatDate(task.promised_on)} · ` +
            `Срок: ${formatDate(task.due_on)}`;

        const openButton = document.createElement("button");
        openButton.type = "button";
        openButton.textContent = "Открыть";
        openButton.addEventListener("click", () => openTask(task.id));

        card.append(title, description, meta, openButton);
        container.append(card);
    }
}

async function loadTasks() {
    const requestId = ++listRequestId;
    const params = new URLSearchParams();
    const query = $("search").value.trim();
    const status = $("status-filter").value;
    const range = getDateRange();

    if (query) params.set("q", query);
    if (status) params.set("status", status);

    if (range) {
        params.set("date_from", range[0]);
        params.set("date_to", range[1]);
    }

    $("period-caption").textContent = range
        ? `${formatDate(range[0])} — ${formatDate(range[1])}`
        : "Все сроки";

    try {
        const result = await api(`/tasks?${params}`);

        if (requestId !== listRequestId) return;

        renderTasks(result.tasks);
        $("warnings").replaceChildren();

        for (const warning of result.warnings) {
            const paragraph = document.createElement("p");
            paragraph.className = "warning";
            paragraph.textContent = warning;
            $("warnings").append(paragraph);
        }

        showMessage("");
    } catch (error) {
        if (requestId !== listRequestId) return;

        showMessage(
            `Не удалось обновить список: ${error.message}. ` +
            "Проверьте, что сервер работает, и повторите запрос.",
            true,
        );
    }
}

$("filters").addEventListener("submit", (event) => {
    event.preventDefault();
    loadTasks();
});

$("period").addEventListener("change", () => {
    $("period-date").disabled = $("period").value === "all";
    loadTasks();
});

$("period-date").addEventListener("change", loadTasks);
$("status-filter").addEventListener("change", loadTasks);

$("period-date").value = localDate(new Date());

loadTasks();

let currentTaskId = null;
let currentTask = null;
let editorBusy = false;
let draftStorageFailed = false;

const draftMemory = new Map();

function draftKey(type, id) {
    return `pd:${type}:${id ?? "new"}`;
}

function storageWarning() {
    draftStorageFailed = true;
    $("draft-warning").className = "warning";
    $("draft-warning").textContent =
        "Не удалось сохранить черновик в браузере. " +
        "Текст остаётся в этом окне. " +
        "Не закрывайте страницу до сохранения на сервере.";
}

function readDraft(key) {
    if (draftMemory.has(key)) {
        return draftMemory.get(key);
    }

    try {
        const raw = localStorage.getItem(key);
        return raw === null ? null : JSON.parse(raw);
    } catch {
        storageWarning();
        return null;
    }
}

function writeDraft(key, value) {
    if (value === null) {
        draftMemory.delete(key);
    } else {
        draftMemory.set(key, value);
    }

    try {
        if (value === null) {
            localStorage.removeItem(key);
        } else {
            localStorage.setItem(key, JSON.stringify(value));
        }

        return true;
    } catch {
        storageWarning();
        return false;
    }
}

function renderDrafts() {
    const keys = new Set(draftMemory.keys());

    try {
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);

            if (key && key.startsWith("pd:")) {
                keys.add(key);
            }
        }
    } catch {
        storageWarning();
    }

    const ids = new Set();

    for (const key of keys) {
        ids.add(key.split(":")[2]);
    }

    const select = $("draft-select");
    select.replaceChildren(new Option("Выберите черновик", ""));

    for (const id of ids) {
        const taskDraft = readDraft(`pd:task:${id}`);
        const commentDraft = readDraft(`pd:comment:${id}`);

        if (!taskDraft && !commentDraft) continue;

        const title = taskDraft?.title ||
            (id === "new" ? "Новое дело" : `Дело №${id}`);

        select.append(new Option(title, id));
    }
}

function getFormData() {
    return {
        title: $("task-title").value,
        description: $("task-description").value,
        promised_on: $("task-promised").value,
        due_on: $("task-due").value,
    };
}

function saveTaskDraft() {
    if ($("editor").hidden) return;

    const data = getFormData();

    const unchanged = currentTask &&
        Object.keys(data).every(
            (field) => data[field] === currentTask[field],
        );

    writeDraft(
        draftKey("task", currentTaskId),
        unchanged ? null : data,
    );

    $("draft-status").textContent = unchanged
        ? "Все изменения сохранены"
        : draftStorageFailed
            ? "Черновик остаётся в текущем окне"
            : "Черновик сохранён в браузере";

    renderDrafts();
}

function saveCommentDraft() {
    if (currentTaskId === null) return;

    const text = $("comment-text").value;

    writeDraft(
        draftKey("comment", currentTaskId),
        text ? { text } : null,
    );

    renderDrafts();
}

function updateStatusButton() {
    $("toggle-status").hidden = currentTaskId === null;

    $("reset-task").hidden = currentTaskId === null;

    $("toggle-status").textContent =
        currentTask?.status === "closed"
            ? "Открыть снова"
            : "Закрыть дело";
}

function fillEditor(task) {
    currentTask = task;
    currentTaskId = task?.id ?? null;

    const today = localDate(new Date());

    const data = readDraft(draftKey("task", currentTaskId)) ||
        task || {
            title: "",
            description: "",
            promised_on: today,
            due_on: today,
        };

    $("task-title").value = data.title;
    $("task-description").value = data.description;
    $("task-promised").value = data.promised_on;
    $("task-due").value = data.due_on;

    $("editor").hidden = false;
    $("editor-title").textContent = task
        ? `Дело №${task.id}`
        : "Создание нового дела";

    $("save-task").textContent = task
        ? "Сохранить изменения"
        : "Создать дело";

    $("comment-section").hidden = !task;
    $("comments").replaceChildren();
    $("comment-warning").textContent = "";

    const commentDraft = task
        ? readDraft(draftKey("comment", task.id))
        : null;

    $("comment-text").value = commentDraft?.text || "";

    $("task-metadata").textContent = task
        ? `Создано: ${new Date(task.created_at).toLocaleString("ru-RU")}`
        : "Сначала сохраните дело, затем добавляйте комментарии.";

    $("draft-status").textContent =
        readDraft(draftKey("task", currentTaskId))
            ? "Восстановлен черновик"
            : "";

    updateStatusButton();
}

function setEditorBusy(value) {
    editorBusy = value;

    const ids = [
        "task-title",
        "task-description",
        "task-promised",
        "task-due",
        "save-task",
        "toggle-status",
        "hide-editor",
        "comment-text",
        "save-comment",
        "new-task",
        "draft-select",
        "reset-task",
    ];

    for (const id of ids) {
        $(id).disabled = value;
    }
}

async function openTask(id) {
    if (editorBusy) return;

    saveTaskDraft();
    saveCommentDraft();
    setEditorBusy(true);

    try {
        const task = await api(`/tasks/${id}`);
        fillEditor(task);
        await loadComments();

        $("editor").scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        setEditorBusy(false);
    }
}

function openNewTask() {
    if (editorBusy) return;

    saveTaskDraft();
    saveCommentDraft();
    fillEditor(null);

    $("editor").scrollIntoView({
        behavior: "smooth",
        block: "start",
    });

    $("task-title").focus({ preventScroll: true });
}

async function loadComments() {
    if (currentTaskId === null) return;

    try {
        const result = await api(
            `/tasks/${currentTaskId}/comments`,
        );

        $("comments").replaceChildren();
        $("comment-warning").textContent =
            result.warnings.join("\n");

        for (const comment of result.comments) {
            const article = document.createElement("article");
            article.className = "comment";

            const time = document.createElement("time");
            time.dateTime = comment.created_at;
            time.textContent =
                new Date(comment.created_at).toLocaleString("ru-RU");

            const text = document.createElement("p");
            text.textContent = comment.text;

            article.append(time, text);
            $("comments").append(article);
        }

        if (result.comments.length === 0) {
            $("comments").textContent = "Комментариев пока нет.";
        }
    } catch (error) {
        $("comment-warning").textContent =
            `Не удалось загрузить комментарии: ${error.message}`;
    }
}

$("task-form").addEventListener("input", saveTaskDraft);

$("comment-text").addEventListener("input", saveCommentDraft);

$("new-task").addEventListener("click", openNewTask);

$("hide-editor").addEventListener("click", () => {
    if (editorBusy) return;

    saveTaskDraft();
    saveCommentDraft();

    $("editor").hidden = true;
    currentTaskId = null;
    currentTask = null;
});

$("draft-select").addEventListener("change", () => {
    const value = $("draft-select").value;

    if (!value) return;

    if (value === "new") {
        openNewTask();
    } else {
        openTask(Number(value));
    }
});

$("task-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (editorBusy) return;

    saveTaskDraft();
    saveCommentDraft();

    const oldId = currentTaskId;
    const commentText = $("comment-text").value;
    const data = getFormData();

    setEditorBusy(true);

    try {
        const url = oldId === null
            ? "/tasks"
            : `/tasks/${oldId}`;

        const task = await api(url, {
            method: oldId === null ? "POST" : "PUT",
            body: JSON.stringify(data),
        });

        writeDraft(draftKey("task", oldId), null);

        fillEditor(task);

        if (oldId !== null) {
            $("comment-text").value = commentText;
        }

        renderDrafts();
        await loadComments();
        await loadTasks();

        showMessage("Дело сохранено");
    } catch (error) {
        showMessage(
            `Сохранение не удалось: ${error.message}. ` +
            "Введённый текст оставлен в черновике.",
            true,
        );
    } finally {
        setEditorBusy(false);
    }
});

$("toggle-status").addEventListener("click", async () => {
    if (editorBusy || currentTaskId === null) return;

    saveTaskDraft();
    setEditorBusy(true);

    try {
        const status = currentTask.status === "open"
            ? "closed"
            : "open";

        currentTask = await api(
            `/tasks/${currentTaskId}/status`,
            {
                method: "PATCH",
                body: JSON.stringify({ status }),
            },
        );

        updateStatusButton();

        saveTaskDraft();
        await loadTasks();

        showMessage(
            status === "closed"
                ? "Дело закрыто"
                : "Дело снова открыто",
        );
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        setEditorBusy(false);
    }
});

$("comment-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (editorBusy || currentTaskId === null) return;

    saveCommentDraft();
    setEditorBusy(true);

    try {
        await api(`/tasks/${currentTaskId}/comments`, {
            method: "POST",
            body: JSON.stringify({
                text: $("comment-text").value,
            }),
        });

        writeDraft(draftKey("comment", currentTaskId), null);
        $("comment-text").value = "";

        renderDrafts();
        await loadComments();
        await loadTasks();

        showMessage("Комментарий добавлен");
    } catch (error) {
        showMessage(
            `Комментарий не добавлен: ${error.message}. ` +
            "Текст оставлен в черновике.",
            true,
        );
    } finally {
        setEditorBusy(false);
    }
});

window.addEventListener("beforeunload", (event) => {
    if (draftStorageFailed && draftMemory.size > 0) {
        event.preventDefault();
        event.returnValue = "";
    }
});

renderDrafts();

$("reset-task").addEventListener("click", async () => {
    if (editorBusy || currentTaskId === null) return;

    const confirmed = confirm(
        "Отменить несохранённые изменения полей дела? " +
        "Будет загружена последняя сохранённая версия. " +
        "Черновик комментария останется.",
    );

    if (!confirmed) return;

    saveTaskDraft();
    saveCommentDraft();
    setEditorBusy(true);

    try {
        const task = await api(`/tasks/${currentTaskId}`);

        const removed = writeDraft(
            draftKey("task", currentTaskId),
            null,
        );

        if (!removed) {
            throw new Error(
                "Не удалось удалить черновик из хранилища браузера",
            );
        }

        fillEditor(task);
        renderDrafts();
        await loadComments();

        showMessage("Восстановлена сохранённая версия дела");
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        setEditorBusy(false);
    }
});