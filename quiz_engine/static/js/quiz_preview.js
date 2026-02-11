(function () {
  const bootstrapEl = document.getElementById("qe-preview-bootstrap");
  const stageEl = document.getElementById("qe-preview-stage");
  const positionEl = document.getElementById("qe-preview-position");
  const previousButton = document.getElementById("qe-preview-prev");
  const nextButton = document.getElementById("qe-preview-next");

  if (!bootstrapEl || !stageEl || !positionEl || !previousButton || !nextButton) {
    return;
  }

  let bootstrap = {};
  try {
    bootstrap = JSON.parse(bootstrapEl.textContent || "{}");
  } catch (error) {
    bootstrap = {};
  }

  const readText = (value, fallback = "") => {
    const text = String(value || "").trim();
    return text || fallback;
  };

  const draftStorageKey = (quizId) => `qe-editor-draft-v1:${quizId}`;

  const parseDraftSnapshot = (quizId) => {
    if (!quizId || !window.sessionStorage) {
      return null;
    }
    const raw = window.sessionStorage.getItem(draftStorageKey(quizId));
    if (!raw) {
      return null;
    }
    try {
      const snapshot = JSON.parse(raw);
      if (
        !snapshot ||
        typeof snapshot !== "object" ||
        !snapshot.dirty ||
        !snapshot.draft ||
        typeof snapshot.draft !== "object"
      ) {
        return null;
      }
      return snapshot;
    } catch (error) {
      return null;
    }
  };

  const normalizeDraftQuestions = (questions) => {
    if (!Array.isArray(questions)) {
      return [];
    }
    return questions
      .filter((question) => question && typeof question === "object")
      .map((question, index) => ({
        question_id: readText(question.question_id, `question-${index + 1}`),
        type: readText(question.type, "slide"),
        title: readText(question.title, `Question ${index + 1}`),
        spec:
          question.spec && typeof question.spec === "object" && !Array.isArray(question.spec)
            ? question.spec
            : {},
      }));
  };

  const slidePreviewFromSpec = (title, spec) => {
    const content =
      spec && typeof spec.content === "object" && spec.content ? spec.content : {};
    const media =
      content.media && typeof content.media === "object" && content.media
        ? content.media
        : null;
    const payload = {
      title: readText(content.title, title),
      body: readText(content.body),
    };
    if (media && readText(media.type, "none") === "image" && readText(media.src)) {
      payload.media = { type: "image", src: readText(media.src) };
    }
    return {
      kind: "plugin_frame",
      payload,
      is_placeholder: false,
    };
  };

  const buildStagesFromDraft = (draft) => {
    const questions = normalizeDraftQuestions(draft.questions);
    return questions.map((question, stageIndex) => {
      const viewModel =
        question.type === "slide"
          ? slidePreviewFromSpec(question.title, question.spec)
          : {
              kind: "placeholder",
              payload: {
                title: question.title,
                body: `Preview unavailable for '${question.type}'.`,
              },
              is_placeholder: true,
            };

      return {
        stage_id: question.question_id,
        stage_index: stageIndex,
        plugin_id: question.type,
        title: question.title,
        view_model: viewModel,
      };
    });
  };

  const quizId = Number(bootstrap.quiz_id || 0);
  const persistedStages =
    bootstrap.preview && Array.isArray(bootstrap.preview.stages) ? bootstrap.preview.stages : [];
  const snapshot = parseDraftSnapshot(quizId);
  const stages =
    snapshot && snapshot.draft ? buildStagesFromDraft(snapshot.draft) : persistedStages;

  const state = {
    index: 0,
    stages,
  };

  const renderNoStage = () => {
    stageEl.replaceChildren();
    const empty = document.createElement("p");
    empty.className = "qe-hint";
    empty.textContent = "No stages to preview.";
    stageEl.appendChild(empty);
  };

  const renderStage = () => {
    stageEl.replaceChildren();
    if (!state.stages.length) {
      renderNoStage();
      positionEl.textContent = "0 / 0";
      previousButton.disabled = true;
      nextButton.disabled = true;
      return;
    }

    const stage = state.stages[state.index];
    const viewModel =
      stage.view_model && typeof stage.view_model === "object" ? stage.view_model : {};
    const payload =
      viewModel.payload && typeof viewModel.payload === "object" ? viewModel.payload : {};

    const frame = document.createElement("article");
    frame.className = "qe-card qe-card--compact qe-preview-frame";

    const meta = document.createElement("p");
    meta.className = "qe-meta";
    meta.textContent = `Stage ${state.index + 1} • ${stage.plugin_id || "unknown"}`;
    frame.appendChild(meta);

    const title = document.createElement("h2");
    title.className = "qe-title";
    title.textContent = readText(payload.title || stage.title, `Stage ${state.index + 1}`);
    frame.appendChild(title);

    const body = document.createElement("p");
    body.className = "qe-hint";
    body.textContent = readText(payload.body);
    frame.appendChild(body);

    const media =
      payload.media && typeof payload.media === "object" && payload.media ? payload.media : null;
    if (media && readText(media.type) === "image" && readText(media.src)) {
      const image = document.createElement("img");
      image.className = "qe-preview-image";
      image.src = readText(media.src);
      image.alt = readText(payload.title || stage.title, "Stage image");
      image.loading = "lazy";
      frame.appendChild(image);
    }

    if (viewModel.is_placeholder) {
      const note = document.createElement("p");
      note.className = "qe-muted-text";
      note.textContent = "Static placeholder only.";
      frame.appendChild(note);
    }

    stageEl.appendChild(frame);
    positionEl.textContent = `${state.index + 1} / ${state.stages.length}`;
    previousButton.disabled = state.index === 0;
    nextButton.disabled = state.index >= state.stages.length - 1;
  };

  previousButton.addEventListener("click", () => {
    if (state.index <= 0) {
      return;
    }
    state.index -= 1;
    renderStage();
  });

  nextButton.addEventListener("click", () => {
    if (state.index >= state.stages.length - 1) {
      return;
    }
    state.index += 1;
    renderStage();
  });

  renderStage();
})();
