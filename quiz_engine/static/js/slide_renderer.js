(function () {
  const t = (key, fallback) => {
    if (window.qeI18n && typeof window.qeI18n.t === "function") {
      const translated = window.qeI18n.t(key);
      if (translated !== key) {
        return translated;
      }
    }
    return fallback;
  };

  const readText = (value, fallback = "") => {
    const text = String(value || "").trim();
    return text || fallback;
  };

  const normalizeBodyFormat = (rawFormat) => {
    const bodyFormat = readText(rawFormat, "text").toLowerCase();
    if (bodyFormat === "markdown") {
      return "markdown";
    }
    return "text";
  };

  const normalizeMedia = (rawMedia) => {
    if (!rawMedia || typeof rawMedia !== "object") {
      return null;
    }
    const mediaType = readText(rawMedia.type, "none");
    const mediaSrc = readText(rawMedia.src);
    if (mediaType === "image" && mediaSrc) {
      return { type: "image", src: mediaSrc };
    }
    return null;
  };

  const sanitizeHref = (rawHref) => {
    const href = readText(rawHref);
    if (!href) {
      return null;
    }
    if (/^\s*(javascript|data|vbscript):/i.test(href)) {
      return null;
    }
    return href;
  };

  const appendInline = (parent, source) => {
    const text = String(source || "");
    if (!text) {
      return;
    }

    const tokenPattern = /(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*)/g;
    let cursor = 0;
    let match = tokenPattern.exec(text);

    while (match) {
      const matchIndex = match.index;
      if (matchIndex > cursor) {
        parent.appendChild(document.createTextNode(text.slice(cursor, matchIndex)));
      }

      const token = match[0];
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        const label = linkMatch[1];
        const href = sanitizeHref(linkMatch[2]);
        if (href) {
          const link = document.createElement("a");
          link.href = href;
          link.rel = "noopener noreferrer nofollow";
          appendInline(link, label);
          parent.appendChild(link);
        } else {
          parent.appendChild(document.createTextNode(label));
        }
      } else if (token.startsWith("**") && token.endsWith("**")) {
        const strong = document.createElement("strong");
        appendInline(strong, token.slice(2, -2));
        parent.appendChild(strong);
      } else if (token.startsWith("*") && token.endsWith("*")) {
        const em = document.createElement("em");
        appendInline(em, token.slice(1, -1));
        parent.appendChild(em);
      } else {
        parent.appendChild(document.createTextNode(token));
      }

      cursor = matchIndex + token.length;
      match = tokenPattern.exec(text);
    }

    if (cursor < text.length) {
      parent.appendChild(document.createTextNode(text.slice(cursor)));
    }
  };

  const isUnorderedListItem = (line) => /^\s*-\s+/.test(line);
  const isOrderedListItem = (line) => /^\s*\d+\.\s+/.test(line);
  const isHeadingLine = (line) => /^\s{0,3}#{1,3}\s+/.test(line);

  const renderMarkdown = (target, rawMarkdown) => {
    const markdown = String(rawMarkdown || "").replace(/\r\n?/g, "\n");
    const lines = markdown.split("\n");
    let index = 0;

    while (index < lines.length) {
      const line = lines[index];
      if (!line || !line.trim()) {
        index += 1;
        continue;
      }

      const headingMatch = line.match(/^\s{0,3}(#{1,3})\s+(.+)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const heading = document.createElement(`h${level}`);
        heading.className = "qe-slide-body__heading";
        appendInline(heading, headingMatch[2]);
        target.appendChild(heading);
        index += 1;
        continue;
      }

      if (isUnorderedListItem(line)) {
        const list = document.createElement("ul");
        list.className = "qe-slide-body__list";
        while (index < lines.length && isUnorderedListItem(lines[index])) {
          const itemLine = lines[index].replace(/^\s*-\s+/, "");
          const item = document.createElement("li");
          appendInline(item, itemLine);
          list.appendChild(item);
          index += 1;
        }
        target.appendChild(list);
        continue;
      }

      if (isOrderedListItem(line)) {
        const list = document.createElement("ol");
        list.className = "qe-slide-body__list";
        while (index < lines.length && isOrderedListItem(lines[index])) {
          const itemLine = lines[index].replace(/^\s*\d+\.\s+/, "");
          const item = document.createElement("li");
          appendInline(item, itemLine);
          list.appendChild(item);
          index += 1;
        }
        target.appendChild(list);
        continue;
      }

      const paragraphLines = [];
      while (
        index < lines.length &&
        lines[index].trim() &&
        !isHeadingLine(lines[index]) &&
        !isUnorderedListItem(lines[index]) &&
        !isOrderedListItem(lines[index])
      ) {
        paragraphLines.push(lines[index]);
        index += 1;
      }

      if (!paragraphLines.length) {
        index += 1;
        continue;
      }

      const paragraph = document.createElement("p");
      paragraph.className = "qe-slide-body__paragraph";
      paragraphLines.forEach((paragraphLine, paragraphLineIndex) => {
        if (paragraphLineIndex > 0) {
          paragraph.appendChild(document.createElement("br"));
        }
        appendInline(paragraph, paragraphLine);
      });
      target.appendChild(paragraph);
    }
  };

  const renderFrame = (mountNode, frameLike, options = {}) => {
    if (!mountNode) {
      return;
    }

    const frame = frameLike && typeof frameLike === "object" ? frameLike : {};
    const payload = frame.payload && typeof frame.payload === "object" ? frame.payload : {};
    const bodyFormat = normalizeBodyFormat(payload.body_format);
    const body = String(payload.body || "");
    const title = readText(payload.title, readText(options.fallbackTitle, "Stage"));
    const media = normalizeMedia(payload.media);

    const card = document.createElement("article");
    card.className = "qe-card qe-card--compact qe-preview-frame";

    const metaText = readText(options.metaText);
    if (metaText) {
      const meta = document.createElement("p");
      meta.className = "qe-meta";
      meta.textContent = metaText;
      card.appendChild(meta);
    }

    const heading = document.createElement("h2");
    heading.className = "qe-title";
    heading.textContent = title;
    card.appendChild(heading);

    if (body) {
      if (bodyFormat === "markdown") {
        const markdownBody = document.createElement("section");
        markdownBody.className = "qe-slide-body qe-slide-body--markdown";
        renderMarkdown(markdownBody, body);
        card.appendChild(markdownBody);
      } else {
        const textBody = document.createElement("p");
        textBody.className = "qe-slide-body qe-slide-body--text qe-hint";
        textBody.textContent = body;
        card.appendChild(textBody);
      }
    }

    if (media) {
      const image = document.createElement("img");
      image.className = "qe-preview-image";
      image.src = media.src;
      image.alt = title;
      image.loading = "lazy";
      card.appendChild(image);
    }

    if (options.showPlaceholderNote && frame.is_placeholder) {
      const note = document.createElement("p");
      note.className = "qe-muted-text";
      note.textContent = readText(
        options.placeholderNoteText,
        t("slide_renderer.static_placeholder_only", "Static placeholder only.")
      );
      card.appendChild(note);
    }

    mountNode.replaceChildren(card);
  };

  window.qeSlideRenderer = {
    renderFrame,
  };
})();
