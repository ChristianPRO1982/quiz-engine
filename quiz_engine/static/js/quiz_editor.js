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

  const bootstrapTranslations =
    bootstrap &&
    typeof bootstrap.translations === "object" &&
    !Array.isArray(bootstrap.translations)
      ? bootstrap.translations
      : {};
  const interpolate = (text, vars = {}) =>
    String(text || "").replace(/\{(\w+)\}/g, (match, key) =>
      Object.prototype.hasOwnProperty.call(vars, key) ? String(vars[key]) : match
    );
  const t = (key, fallback, vars = {}) => {
    const globalT =
      window.qeI18n && typeof window.qeI18n.t === "function" ? window.qeI18n.t : null;
    const fromGlobal = globalT ? globalT(key, vars) : key;
    const fromBootstrap = Object.prototype.hasOwnProperty.call(
      bootstrapTranslations,
      key
    )
      ? bootstrapTranslations[key]
      : null;
    const source =
      typeof fromBootstrap === "string" && fromBootstrap
        ? fromBootstrap
        : fromGlobal !== key
          ? fromGlobal
          : fallback;
    return interpolate(source || key, vars);
  };

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
  const validationModal = document.getElementById("qe-editor-validation-modal");
  const validationCloseButton = document.getElementById(
    "qe-editor-validation-close"
  );
  const validationList = document.getElementById("qe-editor-validation-list");

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
    !deleteConfirmButton ||
    !validationModal ||
    !validationCloseButton ||
    !validationList
  ) {
    return;
  }

  const dialogShow = (dialog) => {
    if (typeof dialog.showModal === "function") {
      if (dialog.open) {
        return;
      }
      dialog.showModal();
      return;
    }
    dialog.setAttribute("open", "open");
  };

  const dialogClose = (dialog) => {
    if (typeof dialog.close === "function") {
      if (!dialog.open) {
        return;
      }
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

  const copyTextToClipboard = async (text) => {
    const payload = String(text || "");
    if (
      navigator.clipboard &&
      typeof navigator.clipboard.writeText === "function"
    ) {
      await navigator.clipboard.writeText(payload);
      return;
    }

    const fallback = document.createElement("textarea");
    fallback.value = payload;
    fallback.setAttribute("readonly", "readonly");
    fallback.style.position = "fixed";
    fallback.style.opacity = "0";
    document.body.appendChild(fallback);
    fallback.focus();
    fallback.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(fallback);
    if (!copied) {
      throw new Error("copy failed");
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
      label: t("quiz_editor.default_slide_label", "Slide"),
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
    return t("quiz_editor.default_title_prefix", "Question");
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
    const source = readText(rawKey, t("quiz_editor.field.fallback", "field"));
    const normalized = source
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!normalized) {
      return t("quiz_editor.field.unknown", "Field");
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

    const hiddenRootKeys = new Set(["schema_version", "type", "plugin"]);
    const inlineRootKeys = new Set(["mode", "points", "time_limit_s"]);
    const inlineRootKeyOrder = ["mode", "points", "time_limit_s", "examination"];
    inlineRootKeys.add("examination");
    const container = document.createElement("section");
    container.className = "qe-schema-form";
    let rootInlineRow = null;
    const pendingInlineFields = new Map();

    const getRootInlineRow = () => {
      if (rootInlineRow) {
        return rootInlineRow;
      }
      rootInlineRow = document.createElement("div");
      rootInlineRow.className = "qe-schema-inline-grid";
      container.appendChild(rootInlineRow);
      return rootInlineRow;
    };

    const readChoiceList = (path) => {
      const current = readSpecValueAtPath(question.spec, path);
      if (!Array.isArray(current)) {
        return [];
      }
      return current
        .filter((choice) => isPlainObject(choice))
        .map((choice) => ({ ...choice }));
    };

    const rootProperties = readSchemaProperties(schema) || {};
    const pointsSchema = isPlainObject(rootProperties.points)
      ? rootProperties.points
      : null;
    const responseMaxPoints = (() => {
      const maximum =
        pointsSchema && typeof pointsSchema.maximum === "number"
          ? pointsSchema.maximum
          : null;
      if (typeof maximum === "number" && Number.isFinite(maximum) && maximum > 0) {
        return Math.trunc(maximum);
      }
      return 100000;
    })();
    const responseMinPoints = -responseMaxPoints;
    const defaultQuestionPoints = (() => {
      const schemaDefault = pointsSchema ? readSchemaDefaultValue(pointsSchema) : null;
      if (typeof schemaDefault === "number" && Number.isFinite(schemaDefault)) {
        return Math.max(responseMinPoints, Math.min(responseMaxPoints, Math.trunc(schemaDefault)));
      }
      return 0;
    })();

    const normalizeChoicesByMode = (rawChoices, nextMode) => {
      const list = Array.isArray(rawChoices)
        ? rawChoices.filter((choice) => isPlainObject(choice)).map((choice) => ({ ...choice }))
        : [];

      if (nextMode === "multianswer") {
        return list.map((choice) => {
          const nextChoice = { ...choice };
          const existingWeight =
            typeof nextChoice.weight === "number" && Number.isFinite(nextChoice.weight)
              ? Math.trunc(nextChoice.weight)
              : null;
          if (existingWeight === null) {
            const isCorrect = nextChoice.is_correct === true;
            nextChoice.weight = isCorrect
              ? defaultQuestionPoints
              : -defaultQuestionPoints;
          } else if (existingWeight === 0) {
            nextChoice.weight = defaultQuestionPoints;
          }
          delete nextChoice.is_correct;
          return nextChoice;
        });
      }

      const normalized = list.map((choice) => {
        const nextChoice = { ...choice };
        if (typeof nextChoice.is_correct !== "boolean") {
          const weight =
            typeof nextChoice.weight === "number" && Number.isFinite(nextChoice.weight)
              ? Math.trunc(nextChoice.weight)
              : 0;
          nextChoice.is_correct = weight > 0;
        }
        delete nextChoice.weight;
        return nextChoice;
      });
      if (!normalized.some((choice) => choice.is_correct)) {
        if (normalized.length > 0) {
          normalized[0].is_correct = true;
        }
      }
      return normalized;
    };

    const buildNewChoiceItem = ({ choices, itemSchema }) => {
      const nextChoice = {};
      const itemProperties = readSchemaProperties(itemSchema);
      if (itemProperties) {
        Object.entries(itemProperties).forEach(([propertyKey, propertySchemaRaw]) => {
          const propertySchema = isPlainObject(propertySchemaRaw)
            ? propertySchemaRaw
            : null;
          if (!propertySchema) {
            return;
          }
          const defaultValue = readSchemaDefaultValue(propertySchema);
          if (defaultValue !== undefined) {
            nextChoice[propertyKey] = defaultValue;
            return;
          }
          const propertyType = readSchemaType(propertySchema);
          if (propertyType === "boolean") {
            nextChoice[propertyKey] = false;
            return;
          }
          if (propertyType === "integer" || propertyType === "number") {
            nextChoice[propertyKey] = 0;
          }
        });
      }

      const nextIndex = choices.length + 1;
      if (!readText(nextChoice.id)) {
        nextChoice.id = `choice_${nextIndex}`;
      }
      if (!("label" in nextChoice)) {
        nextChoice.label = "";
      }

      const mode = readText(readSpecValueAtPath(question.spec, ["mode"]));
      const hasWeightShape =
        mode === "multianswer" ||
        choices.some((choice) => "weight" in choice && !("is_correct" in choice));
      if (hasWeightShape) {
        delete nextChoice.is_correct;
        if (!("weight" in nextChoice)) {
          nextChoice.weight = defaultQuestionPoints;
        }
      } else {
        delete nextChoice.weight;
        if (!("is_correct" in nextChoice)) {
          nextChoice.is_correct = false;
        }
      }

      return nextChoice;
    };

    const syncChoiceInputState = (input) => {
      const normalized = readText(input.value);
      const isBlank = !normalized;
      if (isBlank && input.value) {
        input.value = "";
      }
      input.classList.toggle("qe-choice-input--invalid", isBlank);
      input.placeholder = isBlank
        ? t("quiz_editor.choice.empty_placeholder", "cannot be empty")
        : "";
    };

    const renderObjectProperties = ({ schemaNode, path, target, depth }) => {
      if (depth > maxSchemaDepth) {
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
        if (
          path.length === 0 &&
          key === "points" &&
          readText(readSpecValueAtPath(question.spec, ["mode"])) === "multianswer"
        ) {
          return;
        }
        const childSchema = isPlainObject(rawChildSchema) ? rawChildSchema : null;
        const childPath = [...path, key];
        if (!childSchema) {
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
          if (path.length === 0 && key === "content") {
            renderObjectProperties({
              schemaNode: childSchema,
              path: childPath,
              target,
              depth: depth + 1,
            });
            return;
          }

          const group = document.createElement("section");
          group.className = "qe-schema-group";

          const groupTitle = document.createElement("h4");
          groupTitle.className = "qe-schema-group__title";
          groupTitle.textContent = childLabel;
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
        let field = document.createElement("label");
        field.className = "qe-question__field";
        field.textContent = childLabel;

        if (childType === "enum") {
          const enumValues = Array.isArray(childSchema.enum)
            ? childSchema.enum.filter((candidate) =>
                ["string", "number", "boolean"].includes(typeof candidate)
              )
            : [];
          if (!enumValues.length) {
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
              setErrorMessage(
                t("quiz_editor.enum.invalid", "Invalid enum value selected.")
              );
              return;
            }
            const selectedValue = enumValues[parsedIndex];
            let nextSpec = writeSpecValueAtPath(question.spec, childPath, selectedValue);
            let rerender = false;
            if (path.length === 0 && key === "mode" && typeof selectedValue === "string") {
              const nextChoices = normalizeChoicesByMode(
                readSpecValueAtPath(nextSpec, ["choices"]),
                selectedValue
              );
              nextSpec = writeSpecValueAtPath(nextSpec, ["choices"], nextChoices);
              rerender = true;
            }
            applySpecUpdate(nextSpec, { rerender });
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
              setErrorMessage(
                t("quiz_editor.numeric.empty", "Numeric field cannot be empty.")
              );
              resetFromSpec();
              return;
            }
            const parsed = Number(raw);
            if (!Number.isFinite(parsed)) {
              setErrorMessage(
                t(
                  "quiz_editor.numeric.finite",
                  "Numeric field must contain a finite number."
                )
              );
              resetFromSpec();
              return;
            }
            if (childType === "integer" && !Number.isInteger(parsed)) {
              setErrorMessage(
                t(
                  "quiz_editor.numeric.integer",
                  "Integer field must contain an integer."
                )
              );
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
          field.classList.add("qe-question__field--toggle");
          field.textContent = "";
          const labelText = document.createElement("span");
          labelText.textContent = childLabel;

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
          field.appendChild(labelText);
          field.appendChild(checkbox);
        } else if (childType === "array" && key === "choices") {
          field = document.createElement("section");
          field.className = "qe-question__field qe-schema-choices";

          const title = document.createElement("div");
          title.className = "qe-schema-choices__header";
          title.textContent = childLabel;
          field.appendChild(title);

          const currentChoices = readChoiceList(childPath);
          const minItems =
            typeof childSchema.minItems === "number" &&
            Number.isInteger(childSchema.minItems)
              ? Math.max(0, childSchema.minItems)
              : 0;
          const maxItems =
            typeof childSchema.maxItems === "number" &&
            Number.isInteger(childSchema.maxItems)
              ? Math.max(minItems, childSchema.maxItems)
              : Number.POSITIVE_INFINITY;
          const choicesWrap = document.createElement("div");
          choicesWrap.className = "qe-schema-choices__list";

          currentChoices.forEach((choice, choiceIndex) => {
            const choiceRow = document.createElement("div");
            choiceRow.className = "qe-schema-choice-row";

            const choiceLabel = document.createElement("span");
            choiceLabel.className = "qe-schema-choice-row__label";
            choiceLabel.textContent = t("quiz_editor.choice.label", "Choice {index}", {
              index: choiceIndex + 1,
            });
            choiceRow.appendChild(choiceLabel);

            const choiceInput = document.createElement("input");
            choiceInput.type = "text";
            choiceInput.className = "qe-schema-choice-row__input";
            choiceInput.value =
              typeof choice.label === "string" ? choice.label : "";
            syncChoiceInputState(choiceInput);
            choiceInput.addEventListener("input", () => {
              syncChoiceInputState(choiceInput);
              const nextChoices = readChoiceList(childPath);
              if (choiceIndex < 0 || choiceIndex >= nextChoices.length) {
                return;
              }
              nextChoices[choiceIndex] = {
                ...nextChoices[choiceIndex],
                label: String(choiceInput.value || ""),
              };
              const nextSpec = writeSpecValueAtPath(
                question.spec,
                childPath,
                nextChoices
              );
              applySpecUpdate(nextSpec);
            });
            choiceRow.appendChild(choiceInput);

            const optionsRow = document.createElement("div");
            optionsRow.className = "qe-schema-choice-row__options";

            const isMultianswerMode =
              readText(readSpecValueAtPath(question.spec, ["mode"])) === "multianswer";

            const correctToggleWrap = document.createElement("label");
            correctToggleWrap.className = "qe-schema-choice-option qe-schema-choice-option--toggle";
            const correctToggleText = document.createElement("span");
            correctToggleText.textContent = t(
              "quiz_editor.choice.correct_answer",
              "Correct answer"
            );
            const correctToggleInput = document.createElement("input");
            correctToggleInput.type = "checkbox";
            const currentWeight =
              typeof choice.weight === "number" && Number.isFinite(choice.weight)
                ? Math.trunc(choice.weight)
                : defaultQuestionPoints;
            correctToggleInput.checked = isMultianswerMode
              ? currentWeight > 0
              : choice.is_correct === true;
            correctToggleInput.addEventListener("change", () => {
              const nextChoices = readChoiceList(childPath);
              if (choiceIndex < 0 || choiceIndex >= nextChoices.length) {
                return;
              }
              if (isMultianswerMode) {
                const baseWeight = Number.isFinite(nextChoices[choiceIndex].weight)
                  ? Math.trunc(nextChoices[choiceIndex].weight)
                  : defaultQuestionPoints;
                const normalizedWeight = Math.max(
                  responseMinPoints,
                  Math.min(responseMaxPoints, baseWeight)
                );
                let nextWeight = normalizedWeight;
                if (correctToggleInput.checked) {
                  if (normalizedWeight <= 0) {
                    nextWeight = normalizedWeight === 0 ? defaultQuestionPoints : -normalizedWeight;
                    if (nextWeight <= 0) {
                      nextWeight = 1;
                    }
                  }
                } else if (normalizedWeight > 0) {
                  nextWeight = -normalizedWeight;
                }
                nextChoices[choiceIndex] = {
                  ...nextChoices[choiceIndex],
                  weight: Math.max(
                    responseMinPoints,
                    Math.min(responseMaxPoints, Math.trunc(nextWeight))
                  ),
                };
              } else {
                nextChoices[choiceIndex] = {
                  ...nextChoices[choiceIndex],
                  is_correct: Boolean(correctToggleInput.checked),
                };
              }
              const nextSpec = writeSpecValueAtPath(
                question.spec,
                childPath,
                nextChoices
              );
              applySpecUpdate(nextSpec);
            });
            correctToggleWrap.appendChild(correctToggleText);
            correctToggleWrap.appendChild(correctToggleInput);
            optionsRow.appendChild(correctToggleWrap);

            if (isMultianswerMode) {
              const pointsWrap = document.createElement("label");
              pointsWrap.className = "qe-schema-choice-option";
              const pointsLabel = document.createElement("span");
              pointsLabel.textContent = t("quiz_editor.choice.points", "Points");
              const pointsInput = document.createElement("input");
              pointsInput.type = "number";
              pointsInput.step = "1";
              pointsInput.min = String(responseMinPoints);
              pointsInput.max = String(responseMaxPoints);
              pointsInput.value = String(currentWeight);
              pointsInput.addEventListener("change", () => {
                const rawValue = String(pointsInput.value || "").trim();
                const parsedValue = Number(rawValue);
                if (
                  !Number.isInteger(parsedValue) ||
                  parsedValue < responseMinPoints ||
                  parsedValue > responseMaxPoints
                ) {
                  setErrorMessage(
                    t(
                      "quiz_editor.response_points.invalid",
                      "Response points must be an integer within [{min}, {max}].",
                      { min: responseMinPoints, max: responseMaxPoints }
                    )
                  );
                  pointsInput.value = String(currentWeight);
                  return;
                }
                const nextChoices = readChoiceList(childPath);
                if (choiceIndex < 0 || choiceIndex >= nextChoices.length) {
                  return;
                }
                nextChoices[choiceIndex] = {
                  ...nextChoices[choiceIndex],
                  weight: Math.trunc(parsedValue),
                };
                const nextSpec = writeSpecValueAtPath(
                  question.spec,
                  childPath,
                  nextChoices
                );
                applySpecUpdate(nextSpec);
              });
              pointsWrap.appendChild(pointsLabel);
              pointsWrap.appendChild(pointsInput);
              optionsRow.appendChild(pointsWrap);
            }

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "qe-btn qe-btn--danger qe-schema-choice-row__remove";
            removeButton.textContent = t("quiz_editor.choice.remove", "Delete");
            removeButton.disabled = currentChoices.length <= minItems;
            removeButton.addEventListener("click", () => {
              const nextChoices = readChoiceList(childPath);
              if (nextChoices.length <= minItems) {
                setErrorMessage(
                  t(
                    "quiz_editor.choice.min",
                    "Minimum {count} choice(s).",
                    { count: minItems }
                  )
                );
                return;
              }
              nextChoices.splice(choiceIndex, 1);
              const nextSpec = writeSpecValueAtPath(
                question.spec,
                childPath,
                nextChoices
              );
              applySpecUpdate(nextSpec, { rerender: true });
            });
            choiceRow.appendChild(removeButton);
            choiceRow.appendChild(optionsRow);

            choicesWrap.appendChild(choiceRow);
          });

          field.appendChild(choicesWrap);

          const actions = document.createElement("div");
          actions.className = "qe-schema-choices__actions";
          const addButton = document.createElement("button");
          addButton.type = "button";
          addButton.className = "qe-btn qe-schema-choices__add";
          addButton.textContent = t("quiz_editor.choice.add", "Add choice");
          addButton.disabled = currentChoices.length >= maxItems;
          addButton.addEventListener("click", () => {
            const nextChoices = readChoiceList(childPath);
            if (nextChoices.length >= maxItems) {
              setErrorMessage(
                t("quiz_editor.choice.max", "Maximum {count} choices reached.", {
                  count: maxItems,
                })
              );
              return;
            }
            const itemSchema = isPlainObject(childSchema.items)
              ? childSchema.items
              : {};
            nextChoices.push(
              buildNewChoiceItem({
                choices: nextChoices,
                itemSchema,
              })
            );
            const nextSpec = writeSpecValueAtPath(question.spec, childPath, nextChoices);
            applySpecUpdate(nextSpec, { rerender: true });
          });
          actions.appendChild(addButton);

          const limitsText = document.createElement("p");
          limitsText.className = "qe-muted-text";
          limitsText.textContent = t(
            "quiz_editor.choice.count",
            "Choices: {current} / {max} (min {min}).",
            {
              current: currentChoices.length,
              max: Number.isFinite(maxItems) ? maxItems : "∞",
              min: minItems,
            }
          );
          actions.appendChild(limitsText);
          field.appendChild(actions);
        } else {
          return;
        }

        if (childDescription) {
          const description = document.createElement("p");
          description.className = "qe-muted-text";
          description.textContent = childDescription;
          field.appendChild(description);
        }

        if (path.length === 0 && inlineRootKeys.has(key)) {
          pendingInlineFields.set(key, field);
          const row = getRootInlineRow();
          row.textContent = "";
          inlineRootKeyOrder.forEach((orderedKey) => {
            const inlineField = pendingInlineFields.get(orderedKey);
            if (inlineField) {
              row.appendChild(inlineField);
            }
          });
        } else {
          target.appendChild(field);
        }
      });
    };

    renderObjectProperties({ schemaNode: schema, path: [], target: container, depth: 0 });

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
      title: readText(
        quizPayload.title,
        t("quiz_editor.untitled_quiz", "Untitled quiz")
      ),
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
    title: readText(state.draft.title, t("quiz_editor.untitled_quiz", "Untitled quiz")),
    description: readText(state.draft.description) || null,
    questions: state.draft.questions.map((question) => ({
      question_id: question.question_id,
      type: question.type,
      title: readText(
        question.title,
        t("quiz_editor.untitled_question", "Untitled question")
      ),
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
      title: readText(
        snapshot.draft.title,
        t("quiz_editor.untitled_quiz", "Untitled quiz")
      ),
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
      ? t("quiz_editor.status.saving", "Saving...")
      : state.dirty
        ? t("quiz_editor.status.unsaved", "Unsaved")
        : t("quiz_editor.status.saved", "Saved");
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
    handle.ariaLabel = t("quiz_editor.reorder_question", "Reorder question");
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
    titleLabel.textContent = t("quiz_editor.question_title", "Question title");
    const titleField = document.createElement("input");
    titleField.type = "text";
    titleField.value = question.title;
    titleField.addEventListener("input", () => {
      question.title = readText(
        titleField.value,
        t("quiz_editor.untitled_question", "Untitled question")
      );
      titleButton.textContent = `${index + 1}. ${question.title}`;
      setDirty(true);
    });
    titleLabel.appendChild(titleField);

    const deleteButton = document.createElement("button");
    deleteButton.className = "qe-btn qe-btn--danger";
    deleteButton.type = "button";
    deleteButton.textContent = t("quiz_editor.delete_question", "Delete question");
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
    specLabel.textContent = t("quiz_editor.config_json", "Configuration (JSON)");
    const specField = document.createElement("textarea");
    specField.rows = 8;
    specField.spellcheck = false;
    specField.value = JSON.stringify(question.spec, null, 2);
    const specCopyButton = document.createElement("button");
    specCopyButton.type = "button";
    specCopyButton.className = "qe-json-copy-btn";
    specCopyButton.textContent = t("quiz_editor.copy_json", "Copy");
    specCopyButton.addEventListener("click", async () => {
      try {
        await copyTextToClipboard(specField.value);
        specCopyButton.textContent = t("quiz_editor.json_copied", "Copied");
        window.setTimeout(() => {
          specCopyButton.textContent = t("quiz_editor.copy_json", "Copy");
        }, 1200);
      } catch (error) {
        setError(t("quiz_editor.copy_json_error", "Unable to copy JSON."));
      }
    });
    const specWrap = document.createElement("div");
    specWrap.className = "qe-json-field-wrap";
    specWrap.appendChild(specCopyButton);
    specWrap.appendChild(specField);
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
      if (specField.readOnly) {
        specField.value = JSON.stringify(question.spec, null, 2);
        return;
      }
      try {
        const parsed = JSON.parse(specField.value || "{}");
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("spec must be a JSON object");
        }
        applySpecUpdate(parsed, { rerender: shouldRerenderAfterJsonChange });
      } catch (error) {
        setError(
          t(
            "quiz_editor.json_invalid",
            "Configuration must be a valid JSON object."
          )
        );
        specField.value = JSON.stringify(question.spec, null, 2);
      }
    });
    specLabel.appendChild(specWrap);

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
        specField.readOnly = true;
        specField.classList.add("qe-json-readonly");

        const advanced = document.createElement("details");
        advanced.className = "qe-schema-json-details";
        const advancedSummary = document.createElement("summary");
        advancedSummary.textContent = t("quiz_editor.advanced_json", "Advanced JSON");
        advanced.appendChild(advancedSummary);
        advanced.appendChild(specLabel);
        panel.appendChild(advanced);
      } else {
        panel.appendChild(specLabel);
        const schemaFallback = document.createElement("p");
        schemaFallback.className = "qe-muted-text";
        schemaFallback.textContent =
          t(
            "quiz_editor.schema_fallback",
            "This plugin provides a schema. Auto-form is not available for this shape yet."
          );
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
      empty.textContent = t("quiz_editor.no_questions", "No questions in this quiz.");
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

  const validateSpecAgainstSchema = (spec, schemaNode) => {
    const errors = [];

    const walk = ({ node, value, path, required }) => {
      if (!isPlainObject(node)) {
        return;
      }
      const nodeType = readSchemaType(node);
      const fieldKey = path.length ? path[path.length - 1] : "spec";
      const fieldLabel = readText(node.title, formatSchemaFieldLabel(fieldKey));
      const isMissing = () => {
        if (value === undefined || value === null) {
          return true;
        }
        if (nodeType === "string") {
          return !readText(value);
        }
        return false;
      };

      if (required && isMissing()) {
        errors.push(
          t("quiz_editor.required", "{field} is required.", { field: fieldLabel })
        );
        return;
      }
      if (isMissing()) {
        return;
      }

      if (nodeType === "enum") {
        const enumValues = Array.isArray(node.enum) ? node.enum : [];
        if (!enumValues.some((candidate) => candidate === value)) {
          errors.push(
            t("quiz_editor.invalid_value", "{field} has an invalid value.", {
              field: fieldLabel,
            })
          );
        }
        return;
      }

      if (nodeType === "string") {
        return;
      }

      if (nodeType === "integer" || nodeType === "number") {
        if (typeof value !== "number" || !Number.isFinite(value)) {
          errors.push(
            t("quiz_editor.must_be_number", "{field} must be a number.", {
              field: fieldLabel,
            })
          );
          return;
        }
        if (nodeType === "integer" && !Number.isInteger(value)) {
          errors.push(
            t("quiz_editor.must_be_integer", "{field} must be an integer.", {
              field: fieldLabel,
            })
          );
          return;
        }
        if (typeof node.minimum === "number" && value < node.minimum) {
          errors.push(
            t("quiz_editor.below_min", "{field} is below the minimum allowed.", {
              field: fieldLabel,
            })
          );
          return;
        }
        if (typeof node.maximum === "number" && value > node.maximum) {
          errors.push(
            t("quiz_editor.above_max", "{field} exceeds the maximum allowed.", {
              field: fieldLabel,
            })
          );
        }
        return;
      }

      if (nodeType === "boolean") {
        if (typeof value !== "boolean") {
          errors.push(
            t("quiz_editor.must_be_boolean", "{field} must be a boolean.", {
              field: fieldLabel,
            })
          );
        }
        return;
      }

      if (nodeType === "array") {
        if (!Array.isArray(value)) {
          errors.push(
            t("quiz_editor.must_be_list", "{field} must be a list.", {
              field: fieldLabel,
            })
          );
          return;
        }
        if (typeof node.minItems === "number" && value.length < node.minItems) {
          errors.push(
            t(
              "quiz_editor.min_items",
              "{field} must contain at least {count} item(s).",
              { field: fieldLabel, count: Math.trunc(node.minItems) }
            )
          );
        }
        if (typeof node.maxItems === "number" && value.length > node.maxItems) {
          errors.push(
            t(
              "quiz_editor.max_items",
              "{field} must contain at most {count} item(s).",
              { field: fieldLabel, count: Math.trunc(node.maxItems) }
            )
          );
        }
        if (fieldKey === "choices") {
          const currentMode = readText(readSpecValueAtPath(spec, ["mode"]));
          value.forEach((choice, index) => {
            const label =
              isPlainObject(choice) && typeof choice.label === "string"
                ? choice.label
                : "";
            if (!readText(label)) {
              errors.push(
                t("quiz_editor.choice.cannot_be_empty", "Choice {index} cannot be empty.", {
                  index: index + 1,
                })
              );
            }
          });
          const hasCorrectChoice = value.some((choice) => {
            if (!isPlainObject(choice)) {
              return false;
            }
            if (currentMode === "multianswer") {
              const weight =
                typeof choice.weight === "number" && Number.isFinite(choice.weight)
                  ? Math.trunc(choice.weight)
                  : 0;
              return weight > 0;
            }
            return choice.is_correct === true;
          });
          if (!hasCorrectChoice) {
            errors.push(
              t(
                "quiz_editor.choice.at_least_one_correct",
                "At least one choice must be marked as correct."
              )
            );
          }
        }

        const itemSchema = isPlainObject(node.items) ? node.items : null;
        if (itemSchema) {
          value.forEach((itemValue, itemIndex) => {
            walk({
              node: itemSchema,
              value: itemValue,
              path: [...path, String(itemIndex)],
              required: false,
            });
          });
        }
        return;
      }

      if (nodeType === "object") {
        if (!isPlainObject(value)) {
          errors.push(
            t("quiz_editor.must_be_object", "{field} must be an object.", {
              field: fieldLabel,
            })
          );
          return;
        }
        const properties = readSchemaProperties(node);
        if (!properties) {
          return;
        }
        const requiredFields = new Set(
          Array.isArray(node.required)
            ? node.required.filter((item) => typeof item === "string")
            : []
        );
        Object.entries(properties).forEach(([propertyKey, rawPropertySchema]) => {
          const propertySchema = isPlainObject(rawPropertySchema)
            ? rawPropertySchema
            : null;
          if (!propertySchema) {
            return;
          }
          walk({
            node: propertySchema,
            value: value[propertyKey],
            path: [...path, propertyKey],
            required: requiredFields.has(propertyKey),
          });
        });
      }
    };

    walk({ node: schemaNode, value: spec, path: [], required: true });
    return errors;
  };

  const collectBlockingQuestionIssues = () => {
    const issues = [];
    state.draft.questions.forEach((question, index) => {
      const questionIssues = [];
      if (!readText(question.title)) {
        questionIssues.push(
          t("quiz_editor.question_title_required", "Question title is required.")
        );
      }
      if (!isPlainObject(question.spec)) {
        questionIssues.push(
          t(
            "quiz_editor.question_json_invalid",
            "Question JSON configuration is invalid."
          )
        );
      }
      const option = getQuestionTypeOption(question.type);
      if (
        option &&
        isPlainObject(option.stageConfigSchema) &&
        isPlainObject(question.spec)
      ) {
        questionIssues.push(
          ...validateSpecAgainstSchema(question.spec, option.stageConfigSchema)
        );
      }

      if (questionIssues.length) {
        issues.push({
          question_id: question.question_id,
          question_index: index,
          question_title: readText(
            question.title,
            `${getDefaultTitlePrefix(question.type)} ${index + 1}`
          ),
          issues: Array.from(new Set(questionIssues)),
        });
      }
    });
    return issues;
  };

  const revealQuestion = (questionId) => {
    state.activeQuestionId = questionId;
    renderQuestions();
    window.requestAnimationFrame(() => {
      const escapedId =
        typeof CSS !== "undefined" && typeof CSS.escape === "function"
          ? CSS.escape(questionId)
          : questionId.replace(/"/g, '\\"');
      const card = listEl.querySelector(`[data-question-id="${escapedId}"]`);
      if (!card || typeof card.scrollIntoView !== "function") {
        return;
      }
      card.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const showBlockingValidationModal = (blockingIssues) => {
    validationList.replaceChildren();
    blockingIssues.forEach((entry) => {
      const item = document.createElement("li");
      const issueSummary = entry.issues.join(" ");
      item.textContent = `Q${entry.question_index + 1} - ${
        entry.question_title
      }: ${issueSummary}`;
      validationList.appendChild(item);
    });
    dialogShow(validationModal);
  };

  const saveDraft = async () => {
    if (state.saving || !state.dirty || state.quizId <= 0) {
      return;
    }

    const blockingIssues = collectBlockingQuestionIssues();
    if (blockingIssues.length > 0) {
      revealQuestion(blockingIssues[0].question_id);
      setError(
        t(
          "quiz_editor.blocking_message",
          "Cannot save because some question rules are not respected. Please fix them first."
        )
      );
      showBlockingValidationModal(blockingIssues);
      return;
    }

    dialogClose(validationModal);

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
        title: readText(saved.title, t("quiz_editor.untitled_quiz", "Untitled quiz")),
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
      setError(
        t(
          "quiz_editor.save_error",
          "Unable to save quiz. Leave this page only after saving."
        )
      );
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

  validationCloseButton.addEventListener("click", () => {
    dialogClose(validationModal);
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
    const warning = t("quiz_editor.leave_without_saving", "Leave without saving?");
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
