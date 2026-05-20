(function () {
  const STATUS_LABELS = {
    pending: "Ожидает",
    queued: "В очереди",
    running: "Выполняется",
    completed: "Завершена",
    failed: "Ошибка",
  };

  const VERDICT_LABELS = {
    accepted: "Принято",
    wrong_answer: "Неверный ответ",
    time_limit_exceeded: "Превышен лимит времени",
    memory_limit_exceeded: "Превышен лимит памяти",
    runtime_error: "Ошибка выполнения",
    compilation_error: "Ошибка компиляции",
    presentation_error: "Ошибка формата вывода",
    system_error: "Системная ошибка",
  };

  function label(mapping, value) {
    if (value == null || value === "" || value === "-") return "—";
    return mapping[value] || value;
  }

  const form = document.getElementById("submit-form");
  if (!form) return;

  const statusBox = document.getElementById("submit-status");
  const idEl = document.getElementById("submission-id");
  const statusEl = document.getElementById("submission-status");
  const verdictEl = document.getElementById("submission-verdict");
  const messageEl = document.getElementById("submission-message");
  const submitButton = form.querySelector("button[type='submit']");
  const pollIntervalMs = 2500;
  let pollTimer = null;

  function setStatusView(data) {
    idEl.textContent = String(data.id ?? "—");
    statusEl.textContent = label(STATUS_LABELS, data.status);
    verdictEl.textContent = label(VERDICT_LABELS, data.verdict);
    messageEl.textContent = data.message ?? "";
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    submitButton.disabled = false;
  }

  async function pollSubmission(submissionId) {
    const response = await fetch(`/submissions/${submissionId}?poll=1`, {
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error(`Ошибка опроса статуса: ${response.status}`);
    }
    const data = await response.json();
    setStatusView(data);
    if (data.is_final) {
      stopPolling();
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    stopPolling();
    submitButton.disabled = true;
    statusBox.classList.remove("hidden");
    setStatusView({
      id: "—",
      status: STATUS_LABELS.queued,
      verdict: "—",
      message: "Посылка отправлена…",
    });

    const formData = new FormData(form);
    const payload = {
      problem_id: Number(form.dataset.problemId),
      language: String(formData.get("language") || "").trim(),
      source_code: String(formData.get("source_code") || ""),
    };

    try {
      const response = await fetch("/api/submissions", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Ошибка отправки: ${response.status}`);
      }
      const created = await response.json();
      setStatusView({
        id: created.id,
        status: label(STATUS_LABELS, created.status),
        verdict: label(VERDICT_LABELS, created.verdict),
        message: created.message ?? "",
      });

      pollTimer = setInterval(() => {
        pollSubmission(created.id).catch((err) => {
          messageEl.textContent = `Ошибка проверки: ${err.message}`;
          stopPolling();
        });
      }, pollIntervalMs);

      await pollSubmission(created.id);
    } catch (err) {
      messageEl.textContent = `Ошибка отправки: ${err.message}`;
      submitButton.disabled = false;
    }
  });
})();
