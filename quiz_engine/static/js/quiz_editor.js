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
  const previewButton = document.getElementById("qe-editor-preview");
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
    !previewButton ||
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

  const isPlainObject = (value) =>
    Boolean(value) && typeof value === "object" && !Array.isArray(value);

  const cloneJsonObject = (value, fallback = {}) => {
    if (!isPlainObject(value)) {
      return { ...fallback };
    }
    try {
      return JSON.parse(JSON.stringify(value));
    } catch (error) {
      return { ...fallback };
    }
  };

  const buildQuestionId = () => {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return `question-${Date.now()}-${Math.floor(Math.random() * 1000000)}`;
  };

  const typeOptions = typeOptionsInput
    .filter((option) => option && typeof option === "object")
    .map((option) => ({
      type: readText(option.type),
      label: readText(option.label || option.type),
      description: readText(option.description) || null,
      pluginType: readText(option.plugin_type) || null,
      stageConfigSchema: isPlainObject(option.stage_config_schema)
        ? cloneJsonObject(option.stage_config_schema)
        : null,
      defaultStageConfig: isPlainObject(option.default_stage_config)
        ? cloneJsonObject(option.default_stage_config)
        : {},
      editorHints: isPlainObject(option.editor_hints)
        ? cloneJsonObject(option.editor_hints)
        : null,
    }))
    .filter((option) => option.type);
  if (!typeOptions.some((option) => option.type === "slide")) {
    typeOptions.unshift({
      type: "slide",
      label: "Slide",
      description: null,
      pluginType: "info",
      stageConfigSchema: null,
      defaultStageConfig: {},
      editorHints: null,
    });
  }

  const questionTypeOptionsByType = new Map(
    typeOptions.map((option) => [option.type, option])
  );
  const defaultQuestionType = typeOptions.length ? typeOptions[0].type : "question";

  const getQuestionTypeOption = (questionType) =>
    questionTypeOptionsByType.get(questionType) || null;

  const getDefaultTitlePrefix = (questionType) => {
    const option = getQuestionTypeOption(questionType);
    if (
      option &&
      option.editorHints &&
      typeof option.editorHints.default_title_prefix === "string"
    ) {
      return readText(option.editorHints.default_title_prefix, option.label);
    }
    if (option && option.label) {
      return option.label;
    }
    return "Question";
  };

  const defaultQuestionSpec = (questionType) => {
    const option = getQuestionTypeOption(questionType);
    if (option && isPlainObject(option.defaultStageConfig)) {
      return cloneJsonObject(option.defaultStageConfig);
    }
    return {};
  };

  const normalizeQuestionSpec = (value, questionType) => {
    if (isPlainObject(value)) {
      return cloneJsonObject(value);
    }
    return defaultQuestionSpec(questionType);
  };

  const formatSchemaFieldLabel = (rawKey) => {
    const source = readText(rawKey, "field");
    const normalized = source
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!normalized) {
      return "Field";
    }
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
  };

  const readSchemaType = (schemaNode) => {
    if (!isPlainObject(schemaNode)) {
      return null;
    }
    if (Array.isArray(schemaNode.enum) && schemaNode.enum.length > 0) {
      return "enum";
    }
    if (typeof schemaNode.type === "string") {
      return readText(schemaNode.type).toLowerCase();
    }
    if (Array.isArray(schemaNode.type)) {
      const compatible = schemaNode.type.find(
        (candidate) =>
          typeof candidate === "string" && candidate.trim().toLowerCase() !== "null"
      );
      if (typeof compatible === "string") {
        return compatible.trim().toLowerCase();
      }
    }
    if (isPlainObject(schemaNode.properties)) {
      return "object";
    }
    return null;
  };

  const readSchemaFormatHint = (schemaNode) => {
    if (!isPlainObject(schemaNode)) {
      return "";
    }
    const raw =
      schemaNode["x-ui-widget"] ||
      schemaNode["ui:widget"] ||
      schemaNode.widget ||
      schemaNode.format;
    return readText(raw).toLowerCase();
  };

  const readSchemaProperties = (schemaNode) => {
    if (!isPlainObject(schemaNode) || !isPlainObject(schemaNode.properties)) {
      return null;
    }
    return schemaNode.properties;
  };

  const readSpecValueAtPath = (spec, path) => {
    if (!isPlainObject(spec)) {
      return undefined;
    }
    let cursor = spec;
    for (const segment of path) {
      if (!isPlainObject(cursor) || !(segment in cursor)) {
        return undefined;
      }
      cursor = cursor[segment];
    }
    return cursor;
  };

  const writeSpecValueAtPath = (spec, path, value) => {
    const nextSpec = cloneJsonObject(spec, {});
    if (!Array.isArray(path) || path.length === 0) {
      return nextSpec;
    }
    let cursor = nextSpec;
    for (let index = 0; index < path.length - 1; index += 1) {
      const segment = path[index];
      const nextValue = cursor[segment];
      cursor[segment] = isPlainObject(nextValue) ? cloneJsonObject(nextValue) : {};
      cursor = cursor[segment];
    }
    cursor[path[path.length - 1]] = value;
    return nextSpec;
  };

  const readSchemaDefaultValue = (schemaNode) => {
    if (!isPlainObject(schemaNode) || !("default" in schemaNode)) {
      return undefined;
    }
    try {
      return JSON.parse(JSON.stringify(schemaNode.default));
    } catch (error) {
      return undefined;
    }
  };

  const isRenderableSchemaRoot = (schemaNode) => {
    const schemaType = readSchemaType(schemaNode);
    return schemaType === "object" && Boolean(readSchemaProperties(schemaNode));
  };

  const createSchemaAutoForm = ({
    question,
    schema,
    applySpecUpdate,
    setErrorMessage,
  }) => {
    if (!isRenderableSchemaRoot(schema)) {
      return null;
    }

    const maxSchemaDepth = 6;
    const unsupportedPaths = [];

    const hiddenRootKeys = new Set(["schema_version", "type", "plugin"]);
    const container = document.createElement("section");
    container.className = "qe-schema-form";

    const renderObjectProperties = ({ schemaNode, path, target, depth }) => {
      if (depth > maxSchemaDepth) {
        unsupportedPaths.push(path.join(".") || "(root)");
        return;
      }
      const properties = readSchemaProperties(schemaNode);
      if (!properties) {
        return;
      }
      const requiredSet = new Set(
        Array.isArray(schemaNode.required)
          ? schemaNode.required.filter(
              (item) => typeof item === "string" && item.trim()
            )
          : []
      );

      Object.entries(properties).forEach(([key, rawChildSchema]) => {
        if (path.length === 0 && hiddenRootKeys.has(key)) {
          return;
        }
        const childSchema = isPlainObject(rawChildSchema) ? rawChildSchema : null;
        const childPath = [...path, key];
        const childPathText = childPath.join(".");
        if (!childSchema) {
          unsupportedPaths.push(childPathText);
          return;
        }

        const childType = readSchemaType(childSchema);
        const childLabel = readText(
          childSchema.title,
          formatSchemaFieldLabel(key)
        );
        const childDescription = readText(childSchema.description);
        const isRequired = requiredSet.has(key);

        if (childType === "object") {
          const group = document.createElement("section");
          group.className = "qe-schema-group";

          const groupTitle = document.createElement("h4");
          groupTitle.className = "qe-schema-group__title";
          groupTitle.textContent = isRequired ? `${childLabel} *` : childLabel;
          group.appendChild(groupTitle);

          if (childDescription) {
            const description = document.createElement("p");
            description.className = "qe-muted-text";
            description.textContent = childDescription;
            group.appendChild(description);
          }

          renderObjectProperties({
            schemaNode: childSchema,
            path: childPath,
            target: group,
            depth: depth + 1,
          });
          target.appendChild(group);
          return;
        }

        const currentValue = readSpecValueAtPath(question.spec, childPath);
        const schemaDefault = readSchemaDefaultValue(childSchema);
        const fallbackValue =
          currentValue !== undefined ? currentValue : schemaDefault;
        const field = document.createElement("label");
        field.className = "qe-question__field";
        field.textContent = isRequired ? `${childLabel} *` : childLabel;

        if (childType === "enum") {
          const enumValues = Array.isArray(childSchema.enum)
            ? childSchema.enum.filter((candidate) =>
                ["string", "number", "boolean"].includes(typeof candidate)
              )
            : [];
          if (!enumValues.length) {
            unsupportedPaths.push(childPathText);
            return;
          }

          const select = document.createElement("select");
          enumValues.forEach((optionValue, optionIndex) => {
            const optionEl = document.createElement("option");
            optionEl.value = String(optionIndex);
            optionEl.textContent = String(optionValue);
            select.appendChild(optionEl);
          });

          const selectedIndex = enumValues.findIndex(
            (candidate) => candidate === fallbackValue
          );
          if (selectedIndex >= 0) {
            select.value = String(selectedIndex);
          } else {
            select.value = "0";
          }

          select.addEventListener("change", () => {
            const parsedIndex = Number(select.value);
            if (
              !Number.isInteger(parsedIndex) ||
              parsedIndex < 0 ||
              parsedIndex >= enumValues.length
            ) {
              setErrorMessage("Invalid enum value selected.");
              return;
            }
            const nextSpec = writeSpecValueAtPath(
              question.spec,
              childPath,
              enumValues[parsedIndex]
            );
            applySpecUpdate(nextSpec);
          });
          field.appendChild(select);
        } else if (childType === "string") {
          const formatHint = readSchemaFormatHint(childSchema);
          const useTextarea =
            formatHint === "textarea" ||
            formatHint === "multiline" ||
            formatHint === "markdown" ||
            formatHint === "md";
          const input = useTextarea
            ? document.createElement("textarea")
            : document.createElement("input");
          if (!useTextarea) {
            input.type =
              formatHint === "email"
                ? "email"
                : formatHint === "uri" || formatHint === "url"
                  ? "url"
                  : "text";
          } else {
            input.rows = 4;
          }
          input.value = typeof fallbackValue === "string" ? fallbackValue : "";
          input.addEventListener("input", () => {
            const nextSpec = writeSpecValueAtPath(
              question.spec,
              childPath,
              String(input.value || "")
            );
            applySpecUpdate(nextSpec);
          });
          field.appendChild(input);
        } else if (childType === "integer" || childType === "number") {
          const input = document.createElement("input");
          input.type = "number";
          input.step = childType === "integer" ? "1" : "any";
          if (typeof childSchema.minimum === "number") {
            input.min = String(childSchema.minimum);
          }
          if (typeof childSchema.maximum === "number") {
            input.max = String(childSchema.maximum);
          }
          input.value =
            typeof fallbackValue === "number" && Number.isFinite(fallbackValue)
              ? String(fallbackValue)
              : "";

          const resetFromSpec = () => {
            const current = readSpecValueAtPath(question.spec, childPath);
            input.value =
              typeof current === "number" && Number.isFinite(current)
                ? String(current)
                : "";
          };

          input.addEventListener("change", () => {
            const raw = String(input.value || "").trim();
            if (!raw) {
              setErrorMessage("Numeric field cannot be empty.");
              resetFromSpec();
              return;
            }
            const parsed = Number(raw);
            if (!Number.isFinite(parsed)) {
              setErrorMessage("Numeric field must contain a finite number.");
              resetFromSpec();
              return;
            }
            if (childType === "integer" && !Number.isInteger(parsed)) {
              setErrorMessage("Integer field must contain an integer.");
              resetFromSpec();
              return;
            }
            const nextSpec = writeSpecValueAtPath(
              question.spec,
              childPath,
              childType === "integer" ? Math.trunc(parsed) : parsed
            );
            applySpecUpdate(nextSpec);
          });
          field.appendChild(input);
        } else if (childType === "boolean") {
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.checked =
            typeof fallbackValue === "boolean" ? fallbackValue : false;
          checkbox.addEventListener("change", () => {
            const nextSpec = writeSpecValueAtPath(
              question.spec,
              childPath,
              Boolean(checkbox.checked)
            );
            applySpecUpdate(nextSpec);
          });
          field.appendChild(checkbox);
        } else {
          unsupportedPaths.push(childPathText);
          return;
        }

        if (childDescription) {
          const description = document.createElement("p");
          description.className = "qe-muted-text";
          description.textContent = childDescription;
          field.appendChild(description);
        }

        target.appendChild(field);
      });
    };

    renderObjectProperties({ schemaNode: schema, path: [], target: container, depth: 0 });

    if (unsupportedPaths.length > 0) {
      const preview = unsupportedPaths.slice(0, 4).join(", ");
      const suffix = unsupportedPaths.length > 4 ? ", ..." : "";
      const note = document.createElement("p");
      note.className = "qe-muted-text";
      note.textContent =
        `Some schema fields are not auto-rendered (${preview}${suffix}). ` +
        "Use Advanced JSON for full control.";
      container.appendChild(note);
    }

    return container;
  };

  const normalizeQuestion = (rawQuestion, index) => {
    const source = isPlainObject(rawQuestion) ? rawQuestion : {};
    const questionType = readText(
      source.type || source.plugin_id,
      defaultQuestionType
    );
    const questionId = readText(
      source.question_id || source.stage_id,
      `question-${index + 1}`
    );

    let rawSpec = null;
    if (isPlainObject(source.spec)) {
      rawSpec = source.spec;
    } else if (isPlainObject(source.plugin_spec)) {
      rawSpec = source.plugin_spec;
    } else {
      const text = readText(source.text);
      const choices = Array.isArray(source.choices)
        ? source.choices
            .map((choice) => readText(choice))
            .filter((choiceText) => choiceText)
        : [];
      if (text || choices.length) {
        rawSpec = { text, choices };
      }
    }
    const spec = normalizeQuestionSpec(rawSpec, questionType);

    const fallbackTitle = `${getDefaultTitlePrefix(questionType)} ${index + 1}`;
    const title = readText(source.title || source.text, fallbackTitle);

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
    dragUiCollapsed: false,
    allowEditorNavigation: false,
  };

  const getQuestionIndexById = (questionId) =>
    state.draft.questions.findIndex((question) => question.question_id === questionId);

  const buildDraftStorageKey = () => `qe-editor-draft-v1:${state.quizId}`;

  const buildDraftPayload = () => ({
    schema_version: readText(state.draft.schema_version, "v1"),
    title: readText(state.draft.title, "Untitled quiz"),
    description: readText(state.draft.description) || null,
    questions: state.draft.questions.map((question) => ({
      question_id: question.question_id,
      type: question.type,
      title: readText(question.title, "Untitled question"),
      spec: normalizeQuestionSpec(question.spec, question.type),
    })),
  });

  const syncDraftSnapshot = () => {
    if (!window.sessionStorage || state.quizId <= 0) {
      return;
    }
    const storageKey = buildDraftStorageKey();
    if (!state.dirty) {
      window.sessionStorage.removeItem(storageKey);
      return;
    }
    const snapshot = {
      version: 1,
      quiz_id: state.quizId,
      dirty: true,
      active_question_id: state.activeQuestionId,
      draft: buildDraftPayload(),
    };
    window.sessionStorage.setItem(storageKey, JSON.stringify(snapshot));
  };

  const loadDraftSnapshot = () => {
    if (!window.sessionStorage || state.quizId <= 0) {
      return null;
    }
    const raw = window.sessionStorage.getItem(buildDraftStorageKey());
    if (!raw) {
      return null;
    }
    try {
      const parsed = JSON.parse(raw);
      if (
        !parsed ||
        typeof parsed !== "object" ||
        Number(parsed.quiz_id || 0) !== state.quizId ||
        !parsed.dirty ||
        !parsed.draft ||
        typeof parsed.draft !== "object"
      ) {
        return null;
      }
      return parsed;
    } catch (error) {
      return null;
    }
  };

  const snapshot = loadDraftSnapshot();
  if (snapshot) {
    state.draft = {
      schema_version: readText(snapshot.draft.schema_version, "v1"),
      title: readText(snapshot.draft.title, "Untitled quiz"),
      description: readText(snapshot.draft.description),
      questions: normalizeQuestions(snapshot.draft.questions),
    };
    state.activeQuestionId = readText(snapshot.active_question_id) || null;
    state.dirty = true;
  }

  if (
    !state.activeQuestionId ||
    getQuestionIndexById(state.activeQuestionId) < 0
  ) {
    state.activeQuestionId = state.draft.questions.length
      ? state.draft.questions[0].question_id
      : null;
  }

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
    syncDraftSnapshot();
    renderToolbar();
  };

  const beginDragUi = (sourceEl) => {
    if (state.dragUiCollapsed) {
      return;
    }
    state.dragUiCollapsed = true;
    state.preDragActiveQuestionId = state.activeQuestionId;

    const beforeTop =
      sourceEl && typeof sourceEl.getBoundingClientRect === "function"
        ? sourceEl.getBoundingClientRect().top
        : null;
    listEl.classList.add("is-dragging");
    if (typeof beforeTop === "number") {
      const afterTop = sourceEl.getBoundingClientRect().top;
      const delta = afterTop - beforeTop;
      if (Math.abs(delta) > 1) {
        window.scrollBy(0, delta);
      }
    }
  };

  const finishDragUi = () => {
    if (!state.dragUiCollapsed && !state.draggingQuestionId) {
      return;
    }
    state.dragUiCollapsed = false;
    listEl.classList.remove("is-dragging");
    listEl.querySelectorAll(".qe-question.is-drop-target").forEach((card) => {
      card.classList.remove("is-drop-target");
    });
    state.draggingQuestionId = null;
    state.preDragActiveQuestionId = null;
  };

  const renderToolbar = () => {
    const statusText = state.saving
      ? "Saving..."
      : state.dirty
        ? "Unsaved"
        : "Saved";
    statusEl.textContent = statusText;
    previewButton.disabled = state.saving || state.draft.questions.length === 0;
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
    handle.addEventListener("pointerdown", () => {
      beginDragUi(handle);
    });
    handle.addEventListener("pointerup", () => {
      if (!state.draggingQuestionId) {
        finishDragUi();
      }
    });
    handle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
    });
    handle.addEventListener("dragstart", (event) => {
      beginDragUi(handle);
      state.draggingQuestionId = question.question_id;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", question.question_id);
      }
    });
    handle.addEventListener("dragend", () => {
      finishDragUi();
    });

    const titleButton = document.createElement("button");
    titleButton.type = "button";
    titleButton.className = "qe-question__title";
    titleButton.textContent = `${index + 1}. ${question.title}`;
    titleButton.addEventListener("click", () => {
      if (state.activeQuestionId === question.question_id) {
        state.activeQuestionId = null;
      } else {
        state.activeQuestionId = question.question_id;
      }
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

      const sourceQuestion = state.draft.questions[fromIndex];
      const targetQuestion = state.draft.questions[toIndex];
      state.draft.questions[fromIndex] = targetQuestion;
      state.draft.questions[toIndex] = sourceQuestion;

      finishDragUi();
      setDirty(true);
      renderQuestions({ preserveScroll: true });
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

    const deleteButton = document.createElement("button");
    deleteButton.className = "qe-btn";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete question";
    deleteButton.addEventListener("click", () => {
      state.pendingDeleteQuestionId = question.question_id;
      dialogShow(deleteModal);
    });

    panel.appendChild(titleLabel);
    const questionTypeOption = getQuestionTypeOption(question.type);
    if (questionTypeOption && questionTypeOption.description) {
      const typeDescription = document.createElement("p");
      typeDescription.className = "qe-muted-text";
      typeDescription.textContent = questionTypeOption.description;
      panel.appendChild(typeDescription);
    }

    question.spec = normalizeQuestionSpec(question.spec, question.type);

    const specLabel = document.createElement("label");
    specLabel.className = "qe-question__field";
    specLabel.textContent = "Configuration (JSON)";
    const specField = document.createElement("textarea");
    specField.rows = 8;
    specField.value = JSON.stringify(question.spec, null, 2);
    let shouldRerenderAfterJsonChange = false;
    const applySpecUpdate = (nextSpec, options = {}) => {
      question.spec = normalizeQuestionSpec(nextSpec, question.type);
      specField.value = JSON.stringify(question.spec, null, 2);
      setError("");
      setDirty(true);
      if (options.rerender) {
        renderQuestions({ preserveScroll: true });
      }
    };
    specField.addEventListener("change", () => {
      try {
        const parsed = JSON.parse(specField.value || "{}");
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("spec must be a JSON object");
        }
        applySpecUpdate(parsed, { rerender: shouldRerenderAfterJsonChange });
      } catch (error) {
        setError("Configuration must be a valid JSON object.");
        specField.value = JSON.stringify(question.spec, null, 2);
      }
    });
    specLabel.appendChild(specField);

    const schemaObject =
      questionTypeOption &&
      questionTypeOption.stageConfigSchema &&
      typeof questionTypeOption.stageConfigSchema === "object"
        ? questionTypeOption.stageConfigSchema
        : null;
    if (schemaObject) {
      const schemaForm = createSchemaAutoForm({
        question,
        schema: schemaObject,
        applySpecUpdate,
        setErrorMessage: setError,
      });
      if (schemaForm) {
        panel.appendChild(schemaForm);
        shouldRerenderAfterJsonChange = true;

        const advanced = document.createElement("details");
        advanced.className = "qe-schema-json-details";
        const advancedSummary = document.createElement("summary");
        advancedSummary.textContent = "Advanced JSON";
        advanced.appendChild(advancedSummary);
        advanced.appendChild(specLabel);
        panel.appendChild(advanced);
      } else {
        panel.appendChild(specLabel);
        const schemaFallback = document.createElement("p");
        schemaFallback.className = "qe-muted-text";
        schemaFallback.textContent =
          "This plugin provides a schema. Auto-form is not available for this shape yet.";
        panel.appendChild(schemaFallback);
      }
    } else {
      panel.appendChild(specLabel);
    }

    panel.appendChild(deleteButton);

    card.appendChild(panel);
    return card;
  };

  const renderQuestions = (options = {}) => {
    const preserveScroll = Boolean(options.preserveScroll);
    const previousScrollY = preserveScroll ? window.scrollY : 0;

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

    if (preserveScroll) {
      window.scrollTo(0, previousScrollY);
    }
  };

  const addQuestion = (questionType) => {
    const sourceType = readText(questionType, defaultQuestionType);
    const activeIndex = state.activeQuestionId
      ? getQuestionIndexById(state.activeQuestionId)
      : -1;
    const insertAt = activeIndex < 0 ? 0 : activeIndex + 1;

    const newQuestion = {
      question_id: buildQuestionId(),
      type: sourceType,
      title: `${getDefaultTitlePrefix(sourceType)} ${
        state.draft.questions.length + 1
      }`,
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

    const requestBody = buildDraftPayload();

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

  previewButton.addEventListener("click", () => {
    if (state.quizId <= 0 || state.draft.questions.length === 0) {
      return;
    }
    syncDraftSnapshot();
    state.allowEditorNavigation = true;
    window.location.assign(`/admin/quizzes/${state.quizId}/preview`);
  });

  window.addEventListener("dragend", () => {
    finishDragUi();
  });

  window.addEventListener("beforeunload", (event) => {
    if (state.allowEditorNavigation || !state.dirty) {
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
