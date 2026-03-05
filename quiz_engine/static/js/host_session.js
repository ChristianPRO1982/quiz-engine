const bootstrapNode = document.getElementById("qe-host-bootstrap");
const bootstrap = bootstrapNode ? JSON.parse(bootstrapNode.textContent) : {};
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

const sessionCode = bootstrap.session_code;
const playersEl = document.getElementById("qe-host-players");
const stateEl = document.getElementById("qe-host-state");
const stageEl = document.getElementById("qe-host-stage");
const statusEl = document.getElementById("qe-host-status");
const frameEl = document.getElementById("qe-host-frame");
const startButton = document.getElementById("qe-host-start");
const nextButton = document.getElementById("qe-host-next");
const endButton = document.getElementById("qe-host-end");

let client = null;

const setStatus = (text) => {
  statusEl.textContent = text;
};

const renderPlayers = (players) => {
  playersEl.innerHTML = "";
  if (!players.length) {
    const item = document.createElement("li");
    item.textContent = t("host_session.no_players", "No players yet.");
    playersEl.appendChild(item);
    return;
  }

  players.forEach((player) => {
    const item = document.createElement("li");
    item.textContent = `${player.nickname} (#${player.player_id})`;
    playersEl.appendChild(item);
  });
};

const renderFrame = (framePayload) => {
  if (window.qeSlideRenderer && typeof window.qeSlideRenderer.renderFrame === "function") {
    window.qeSlideRenderer.renderFrame(frameEl, framePayload, {
      fallbackTitle: t("host_session.stage", "Stage"),
      showPlaceholderNote: true,
    });
    return;
  }
  frameEl.textContent = t("host_session.renderer_unavailable", "Renderer unavailable.");
};

const onMessage = (message) => {
  switch (message.type) {
    case "SESSION_CREATED":
      setStatus(
        t("host_session.session_ready", "Session ready ({code}).", {
          code: message.payload.session_code,
        })
      );
      break;
    case "LOBBY_SNAPSHOT":
      renderPlayers(message.payload.players || []);
      if (message.payload.session_state) {
        stateEl.textContent = message.payload.session_state;
      }
      if (message.payload.stage_id) {
        stageEl.textContent = `${message.payload.stage_id} (${message.payload.stage_index})`;
      }
      break;
    case "PLAYER_JOINED":
      setStatus(
        t("host_session.player_joined", "{nickname} joined.", {
          nickname: message.payload.nickname,
        })
      );
      break;
    case "PLAYER_LEFT":
      setStatus(t("host_session.player_left", "A player left."));
      break;
    case "SESSION_STATE_CHANGED":
      stateEl.textContent = message.payload.session_state;
      setStatus(
        t("host_session.state_changed", "State changed: {state}.", {
          state: message.payload.session_state,
        })
      );
      break;
    case "STAGE_CHANGED":
      stageEl.textContent = `${message.payload.stage_id} (${message.payload.stage_index})`;
      setStatus(t("host_session.stage_changed", "Stage changed."));
      break;
    case "PLUGIN_FRAME":
      renderFrame(message.payload);
      break;
    case "ERROR":
      setStatus(
        t("host_session.error", "Error: {message}", {
          message: message.payload.message,
        })
      );
      break;
    default:
      break;
  }
};

const connect = () => {
  client = window.qeWsClient.createClient({
    sessionCode,
    role: "host",
    onOpen: () => {
      setStatus(t("host_session.connected", "Connected."));
      client.send("CONNECT", { role: "host" });
    },
    onClose: () => {
      setStatus(t("host_session.disconnected", "Disconnected."));
    },
    onMessage,
  });
};

startButton.addEventListener("click", () => {
  client.send("HOST_START", {});
});

nextButton.addEventListener("click", () => {
  client.send("HOST_NEXT_STAGE", {});
});

endButton.addEventListener("click", () => {
  client.send("HOST_END", {});
});

connect();
