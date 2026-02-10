(function () {
  const bootstrapEl = document.getElementById("qe-editor-bootstrap");
  if (!bootstrapEl) {
    return;
  }

  let bootstrap = {};
  try {
    bootstrap = JSON.parse(bootstrapEl.textContent || "{}");
  } catch (error) {
    bootstrap = {};
  }

  const quizPayload = bootstrap.quiz || {};
  const typeOptionsInput = Array.isArray(bootstrap.question_types)
    ? bootstrap.question_types
    : [];

  const titleInput = document.getElementById("qe-editor-title");
  const descriptionInput = document.getElementById("qe-editor-description");
  const statusEl = document.getElementById("qe-editor-status");
  const saveButton = document.getElementById("qe-editor-save");
  const addQuestionButton = document.getElementById("qe-editor-add-question");
  const errorEl = document.getElementById("qe-editor-error");
  const listEl = document.getElementById("qe-editor-question-list");
  const serverEmptyStateEl = document.getElementById("qe-editor-empty-server");

  const typeModal = document.getElementById("qe-question-type-modal");
  const typeModalClose = document.getElementById("qe-question-type-close");
  const typeListEl = document.getElementById("qe-question-type-list");

  const deleteModal = document.getElementById("qe-editor-delete-modal");
  const deleteCancelButton = document.getElementById("qe-editor-delete-cancel");
  const deleteConfirmButton = document.getElementById("qe-editor-delete-confirm");

  if (
    !titleInput ||
    !descriptionInput ||
    !statusEl ||
    !saveButton ||
    !addQuestionButton ||
    !listEl ||
    !typeModal ||
    !typeListEl ||
    !deleteModal ||
    !deleteCancelButton ||
    !deleteConfirmButton
  ) {
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

  const readText = (value, fallback = "") => {
    const text = String(value || "").trim();
    return text || fallback;
  };

  const buildQuestionId = () => {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return `question-${Date.now()}-${Math.floor(Math.random() * 1000000)}`;
  };

  const defaultQuestionSpec = (questionType) => {
    if (questionType === "slide") {
      return {
        schema_version: "v0",
        type: "slide",
        content: {
          title: "",
          body: "",
          media: {
            type: "none",
            src: null,
          },
        },
      };
    }
    return {};
  };

  const normalizeQuestion = (rawQuestion, index) => {
    const source =
      rawQuestion && typeof rawQuestion === "object" ? rawQuestion : {};
    const questionType = readText(source.type || source.plugin_id, "slide");
    const questionId = readText(
      source.question_id || source.stage_id,
      `question-${index + 1}`
    );

    let spec = {};
    if (source.spec && typeof source.spec === "object" && !Array.isArray(source.spec)) {
      spec = source.spec;
    } else if (
      source.plugin_spec &&
      typeof source.plugin_spec === "object" &&
      !Array.isArray(source.plugin_spec)
    ) {
      spec = source.plugin_spec;
    } else {
      const text = readText(source.text);
      const choices = Array.isArray(source.choices)
        ? source.choices
            .map((choice) => readText(choice))
            .filter((choiceText) => choiceText)
        : [];
      if (text || choices.length) {
        spec = { text, choices };
      }
    }

    let title = readText(source.title || source.text);
    if (!title && spec && typeof spec === "object") {
      const content = spec.content;
      if (content && typeof content === "object") {
        title = readText(content.title);
      }
    }
    if (!title) {
      title = questionType === "slide" ? `Slide ${index + 1}` : `Question ${index + 1}`;
    }

    return {
      question_id: questionId,
      type: questionType,
      title,
      spec,
    };
  };

  const normalizeQuestions = (rawQuestions) => {
    const list = Array.isArray(rawQuestions) ? rawQuestions : [];
    const seen = new Set();
    return list.map(normalizeQuestion).map((question) => {
      let nextId = question.question_id;
      let suffix = 2;
      while (seen.has(nextId)) {
        nextId = `${question.question_id}-${suffix}`;
        suffix += 1;
      }
      seen.add(nextId);
      return { ...question, question_id: nextId };
    });
  };

  const typeOptions = typeOptionsInput
    .filter((option) => option && typeof option === "object")
    .map((option) => ({
      type: readText(option.type),
      label: readText(option.label || option.type),
      description: readText(option.description) || null,
    }))
    .filter((option) => option.type);
  if (!typeOptions.some((option) => option.type === "slide")) {
    typeOptions.unshift({ type: "slide", label: "Slide", description: null });
  }

  const state = {
    quizId: Number(quizPayload.quiz_id || quizPayload.id || 0),
    draft: {
      schema_version: readText(quizPayload.schema_version, "v1"),
      title: readText(quizPayload.title, "Untitled quiz"),
      description: readText(quizPayload.description),
      questions: normalizeQuestions(quizPayload.questions),
    },
    activeQuestionId: null,
    dirty: false,
    saving: false,
    pendingDeleteQuestionId: null,
    draggingQuestionId: null,
    preDragActiveQuestionId: null,
  };

  if (state.draft.questions.length > 0) {
    state.activeQuestionId = state.draft.questions[0].question_id;
  }

  const getQuestionIndexById = (questionId) =>
    state.draft.questions.findIndex((question) => question.question_id === questionId);

  const setError = (message) => {
    const text = readText(message);
    if (!text) {
      errorEl.hidden = true;
      errorEl.textContent = "";
      return;
    }
    errorEl.hidden = false;
    errorEl.textContent = text;
  };

  const setDirty = (nextValue) => {
    state.dirty = Boolean(nextValue);
    renderToolbar();
  };

  const renderToolbar = () => {
    const statusText = state.saving
      ? "Saving..."
      : state.dirty
        ? "Unsaved"
        : "Saved";
    statusEl.textContent = statusText;
    saveButton.disabled = state.saving || !state.dirty;
  };

  const createQuestionCard = (question, index) => {
    const isActive = question.question_id === state.activeQuestionId;
    const card = document.createElement("article");
    card.className = "qe-question";
    if (isActive) {
      card.classList.add("is-active");
    }
    card.dataset.questionId = question.question_id;

    const header = document.createElement("header");
    header.className = "qe-question__header";

    const handle = document.createElement("button");
    handle.type = "button";
    handle.className = "qe-question__handle";
    handle.draggable = true;
    handle.ariaLabel = "Reorder question";
    handle.textContent = "⋮⋮";
    handle.addEventListener("dragstart", (event) => {
      state.draggingQuestionId = question.question_id;
      state.preDragActiveQuestionId = state.activeQuestionId;
      listEl.classList.add("is-dragging");
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", question.question_id);
      }
    });
    handle.addEventListener("dragend", () => {
      listEl.classList.remove("is-dragging");
      if (!state.activeQuestionId) {
        state.activeQuestionId = state.preDragActiveQuestionId;
      }
      state.preDragActiveQuestionId = null;
      state.draggingQuestionId = null;
      renderQuestions();
    });

    const titleButton = document.createElement("button");
    titleButton.type = "button";
    titleButton.className = "qe-question__title";
    titleButton.textContent = `${index + 1}. ${question.title}`;
    titleButton.addEventListener("click", () => {
      state.activeQuestionId = question.question_id;
      renderQuestions();
    });

    const questionType = document.createElement("span");
    questionType.className = "qe-pill qe-pill--inline";
    questionType.textContent = question.type;

    header.appendChild(handle);
    header.appendChild(titleButton);
    header.appendChild(questionType);
    card.appendChild(header);

    card.addEventListener("dragover", (event) => {
      event.preventDefault();
      if (state.draggingQuestionId && state.draggingQuestionId !== question.question_id) {
        card.classList.add("is-drop-target");
      }
    });

    card.addEventListener("dragleave", () => {
      card.classList.remove("is-drop-target");
    });

    card.addEventListener("drop", (event) => {
      event.preventDefault();
      card.classList.remove("is-drop-target");
      const sourceId =
        state.draggingQuestionId ||
        (event.dataTransfer ? event.dataTransfer.getData("text/plain") : "");
      if (!sourceId || sourceId === question.question_id) {
        return;
      }

      const fromIndex = getQuestionIndexById(sourceId);
      const toIndex = getQuestionIndexById(question.question_id);
      if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) {
        return;
      }

      const moved = state.draft.questions.splice(fromIndex, 1)[0];
      const adjustedTargetIndex = fromIndex < toIndex ? toIndex - 1 : toIndex;
      state.draft.questions.splice(adjustedTargetIndex, 0, moved);

      state.activeQuestionId = moved.question_id;
      state.draggingQuestionId = null;
      state.preDragActiveQuestionId = null;
      listEl.classList.remove("is-dragging");
      setDirty(true);
      renderQuestions();
    });

    if (!isActive) {
      return card;
    }

    const panel = document.createElement("section");
    panel.className = "qe-question__panel";

    const titleLabel = document.createElement("label");
    titleLabel.className = "qe-question__field";
    titleLabel.textContent = "Question title";
    const titleField = document.createElement("input");
    titleField.type = "text";
    titleField.value = question.title;
    titleField.addEventListener("input", () => {
      question.title = readText(titleField.value, "Untitled question");
      titleButton.textContent = `${index + 1}. ${question.title}`;
      setDirty(true);
    });
    titleLabel.appendChild(titleField);

    const specLabel = document.createElement("label");
    specLabel.className = "qe-question__field";
    specLabel.textContent = "Question spec (JSON)";
    const specField = document.createElement("textarea");
    specField.rows = 6;
    specField.value = JSON.stringify(question.spec || {}, null, 2);
    specField.addEventListener("change", () => {
      try {
        const parsed = JSON.parse(specField.value || "{}");
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("spec must be a JSON object");
        }
        question.spec = parsed;
        setError("");
        setDirty(true);
      } catch (error) {
        setError("Spec must be valid JSON object.");
        specField.value = JSON.stringify(question.spec || {}, null, 2);
      }
    });
    specLabel.appendChild(specField);

    const deleteButton = document.createElement("button");
    deleteButton.className = "qe-btn";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete question";
    deleteButton.addEventListener("click", () => {
      state.pendingDeleteQuestionId = question.question_id;
      dialogShow(deleteModal);
    });

    panel.appendChild(titleLabel);
    panel.appendChild(specLabel);
    panel.appendChild(deleteButton);

    card.appendChild(panel);
    return card;
  };

  const renderQuestions = () => {
    listEl.replaceChildren();
    if (serverEmptyStateEl) {
      serverEmptyStateEl.hidden = true;
    }

    if (state.draft.questions.length === 0) {
      const empty = document.createElement("p");
      empty.className = "qe-hint";
      empty.textContent = "No questions in this quiz.";
      listEl.appendChild(empty);
      return;
    }

    state.draft.questions.forEach((question, index) => {
      const card = createQuestionCard(question, index);
      listEl.appendChild(card);
    });
  };

  const addQuestion = (questionType) => {
    const sourceType = readText(questionType, "slide");
    const activeIndex = state.activeQuestionId
      ? getQuestionIndexById(state.activeQuestionId)
      : -1;
    const insertAt = activeIndex < 0 ? 0 : activeIndex + 1;

    const newQuestion = {
      question_id: buildQuestionId(),
      type: sourceType,
      title:
        sourceType === "slide"
          ? `Slide ${state.draft.questions.length + 1}`
          : `Question ${state.draft.questions.length + 1}`,
      spec: defaultQuestionSpec(sourceType),
    };

    state.draft.questions.splice(insertAt, 0, newQuestion);
    state.activeQuestionId = newQuestion.question_id;
    dialogClose(typeModal);
    setDirty(true);
    renderQuestions();
  };

  const deleteQuestion = (questionId) => {
    const index = getQuestionIndexById(questionId);
    if (index < 0) {
      return;
    }
    state.draft.questions.splice(index, 1);

    if (state.activeQuestionId === questionId) {
      if (index < state.draft.questions.length) {
        state.activeQuestionId = state.draft.questions[index].question_id;
      } else if (index - 1 >= 0) {
        state.activeQuestionId = state.draft.questions[index - 1].question_id;
      } else {
        state.activeQuestionId = null;
      }
    }
    setDirty(true);
    renderQuestions();
  };

  const renderTypePicker = () => {
    typeListEl.replaceChildren();
    typeOptions.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "qe-type-picker__item";
      button.dataset.questionType = option.type;

      const label = document.createElement("strong");
      label.textContent = option.label;
      button.appendChild(label);

      if (option.description) {
        const description = document.createElement("span");
        description.className = "qe-muted-text";
        description.textContent = option.description;
        button.appendChild(description);
      }

      button.addEventListener("click", () => {
        addQuestion(option.type);
      });
      typeListEl.appendChild(button);
    });
  };

  const saveDraft = async () => {
    if (state.saving || !state.dirty || state.quizId <= 0) {
      return;
    }

    state.saving = true;
    renderToolbar();
    setError("");

    const requestBody = {
      schema_version: readText(state.draft.schema_version, "v1"),
      title: readText(state.draft.title, "Untitled quiz"),
      description: readText(state.draft.description) || null,
      questions: state.draft.questions.map((question) => ({
        question_id: question.question_id,
        type: question.type,
        title: readText(question.title, "Untitled question"),
        spec:
          question.spec &&
          typeof question.spec === "object" &&
          !Array.isArray(question.spec)
            ? question.spec
            : {},
      })),
    };

    try {
      const response = await fetch(`/api/quizzes/${state.quizId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`save failed: ${response.status}`);
      }

      const saved = await response.json();
      state.draft = {
        schema_version: readText(saved.schema_version, "v1"),
        title: readText(saved.title, "Untitled quiz"),
        description: readText(saved.description),
        questions: normalizeQuestions(saved.questions),
      };

      titleInput.value = state.draft.title;
      descriptionInput.value = state.draft.description;
      if (
        state.activeQuestionId &&
        getQuestionIndexById(state.activeQuestionId) < 0 &&
        state.draft.questions.length
      ) {
        state.activeQuestionId = state.draft.questions[0].question_id;
      }
      setDirty(false);
      renderQuestions();
    } catch (error) {
      setError("Unable to save quiz. Leave this page only after saving.");
      setDirty(true);
    } finally {
      state.saving = false;
      renderToolbar();
    }
  };

  titleInput.addEventListener("input", () => {
    state.draft.title = titleInput.value;
    setDirty(true);
  });

  descriptionInput.addEventListener("input", () => {
    state.draft.description = descriptionInput.value;
    setDirty(true);
  });

  addQuestionButton.addEventListener("click", () => {
    renderTypePicker();
    dialogShow(typeModal);
  });

  typeModalClose.addEventListener("click", () => {
    dialogClose(typeModal);
  });

  deleteCancelButton.addEventListener("click", () => {
    state.pendingDeleteQuestionId = null;
    dialogClose(deleteModal);
  });

  deleteConfirmButton.addEventListener("click", () => {
    if (state.pendingDeleteQuestionId) {
      deleteQuestion(state.pendingDeleteQuestionId);
    }
    state.pendingDeleteQuestionId = null;
    dialogClose(deleteModal);
  });

  saveButton.addEventListener("click", () => {
    void saveDraft();
  });

  window.addEventListener("beforeunload", (event) => {
    if (!state.dirty) {
      return;
    }
    const warning = "Leave without saving?";
    event.preventDefault();
    event.returnValue = warning;
    return warning;
  });

  titleInput.value = state.draft.title;
  descriptionInput.value = state.draft.description;
  renderToolbar();
  renderQuestions();
  renderTypePicker();
})();
