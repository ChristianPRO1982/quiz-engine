(function () {
  const modal = document.getElementById("qe-quiz-delete-modal");
  const cancelButton = document.getElementById("qe-quiz-delete-cancel");
  const confirmButton = document.getElementById("qe-quiz-delete-confirm");
  const messageEl = document.getElementById("qe-quiz-delete-message");
  const forms = document.querySelectorAll('form[data-qe-confirm-delete="quiz"]');

  if (!modal || !cancelButton || !confirmButton || !messageEl || !forms.length) {
    return;
  }

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
        ? `Delete "${quizTitle}" permanently? This action cannot be undone.`
        : "Delete this quiz permanently? This action cannot be undone.";
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
