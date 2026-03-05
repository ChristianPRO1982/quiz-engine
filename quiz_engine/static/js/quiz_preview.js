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
  const bootstrapTranslations =
    bootstrap &&
    typeof bootstrap.translations === "object" &&
    !Array.isArray(bootstrap.translations)
      ? bootstrap.translations
      : {};

  const t = (key, fallback, vars = {}) => {
    const interpolate = (text) =>
      String(text || "").replace(/\{(\w+)\}/g, (match, token) =>
        Object.prototype.hasOwnProperty.call(vars, token)
          ? String(vars[token])
          : match
      );
    const fromBootstrap = Object.prototype.hasOwnProperty.call(
      bootstrapTranslations,
      key
    )
      ? bootstrapTranslations[key]
      : null;
    if (typeof fromBootstrap === "string" && fromBootstrap) {
      return interpolate(fromBootstrap);
    }
    if (window.qeI18n && typeof window.qeI18n.t === "function") {
      const translated = window.qeI18n.t(key, vars);
      if (translated !== key) {
        return translated;
      }
    }
    return interpolate(fallback || key);
  };

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
        title: readText(
          question.title,
          t("quiz_preview.question_fallback", "Question {index}", { index: index + 1 })
        ),
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
    const bodyFormat = readText(content.body_format, "text").toLowerCase();
    const payload = {
      title: readText(
        title,
        readText(content.title, t("quiz_preview.stage_fallback", "Stage"))
      ),
      body: readText(content.body),
      body_format: bodyFormat === "markdown" ? "markdown" : "text",
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
                body: t(
                  "quiz_preview.unavailable_type",
                  "Preview unavailable for '{type}'.",
                  { type: question.type }
                ),
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
    empty.textContent = t("quiz_preview.no_stages", "No stages to preview.");
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
    if (window.qeSlideRenderer && typeof window.qeSlideRenderer.renderFrame === "function") {
      window.qeSlideRenderer.renderFrame(stageEl, { ...viewModel, payload }, {
        fallbackTitle: readText(
          payload.title || stage.title,
          t("quiz_preview.stage_number", "Stage {index}", { index: state.index + 1 })
        ),
        metaText: t(
          "quiz_preview.stage_meta",
          "Stage {index} • {plugin}",
          {
            index: state.index + 1,
            plugin: stage.plugin_id || t("common.unknown", "unknown"),
          }
        ),
        showPlaceholderNote: true,
        placeholderNoteText: t(
          "slide_renderer.static_placeholder_only",
          "Static placeholder only."
        ),
      });
    } else {
      const fallback = document.createElement("p");
      fallback.className = "qe-hint";
      fallback.textContent = readText(
        payload.body,
        t("quiz_preview.renderer_unavailable", "Renderer unavailable.")
      );
      stageEl.appendChild(fallback);
    }
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
