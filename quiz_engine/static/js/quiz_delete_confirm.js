(function () {
  const modal = document.getElementById("qe-quiz-delete-modal");
  const cancelButton = document.getElementById("qe-quiz-delete-cancel");
  const confirmButton = document.getElementById("qe-quiz-delete-confirm");
  const messageEl = document.getElementById("qe-quiz-delete-message");
  const forms = document.querySelectorAll('form[data-qe-confirm-delete="quiz"]');

  if (!modal || !cancelButton || !confirmButton || !messageEl || !forms.length) {
    return;
  }

  const t = (key, fallback, vars = {}) => {
    const datasetValueKey =
      key === "quiz_delete_confirm.with_title"
        ? "msgWithTitle"
        : key === "quiz_delete_confirm.without_title"
          ? "msgWithoutTitle"
          : null;
    if (datasetValueKey && typeof modal.dataset[datasetValueKey] === "string") {
      return String(modal.dataset[datasetValueKey]).replace(
        /\{(\w+)\}/g,
        (match, token) =>
          Object.prototype.hasOwnProperty.call(vars, token)
            ? String(vars[token])
            : match
      );
    }
    if (!window.qeI18n || typeof window.qeI18n.t !== "function") {
      return String(fallback || key).replace(/\{(\w+)\}/g, (match, token) =>
        Object.prototype.hasOwnProperty.call(vars, token)
          ? String(vars[token])
          : match
      );
    }
    const translated = window.qeI18n.t(key, vars);
    if (translated !== key) {
      return translated;
    }
    return String(fallback || key).replace(/\{(\w+)\}/g, (match, token) =>
      Object.prototype.hasOwnProperty.call(vars, token)
        ? String(vars[token])
        : match
    );
  };

  const dialogShow = (dialog) => {
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
      return;
    }
    dialog.setAttribute("open", "open");
  };

  const dialogClose = (dialog) => {
    if (typeof dialog.close === "function") {
      dialog.close();
      return;
    }
    dialog.removeAttribute("open");
  };

  const readText = (value) => String(value || "").trim();

  let pendingForm = null;

  forms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.qeConfirmedDelete === "true") {
        form.dataset.qeConfirmedDelete = "false";
        return;
      }
      event.preventDefault();
      pendingForm = form;
      const quizTitle = readText(form.dataset.quizTitle);
      messageEl.textContent = quizTitle
        ? t(
            "quiz_delete_confirm.with_title",
            'Delete "{title}" permanently? This action cannot be undone.',
            { title: quizTitle }
          )
        : t(
            "quiz_delete_confirm.without_title",
            "Delete this quiz permanently? This action cannot be undone."
          );
      dialogShow(modal);
    });
  });

  cancelButton.addEventListener("click", () => {
    pendingForm = null;
    dialogClose(modal);
  });

  confirmButton.addEventListener("click", () => {
    if (!pendingForm) {
      dialogClose(modal);
      return;
    }
    const form = pendingForm;
    pendingForm = null;
    dialogClose(modal);
    form.dataset.qeConfirmedDelete = "true";
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
      return;
    }
    form.submit();
  });
})();
