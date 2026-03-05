const bootstrapNode = document.getElementById("qe-player-bootstrap");
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
const nicknameInput = document.getElementById("qe-player-nickname");
const joinButton = document.getElementById("qe-player-join");
const leaveButton = document.getElementById("qe-player-leave");
const stateEl = document.getElementById("qe-player-state");
const stageEl = document.getElementById("qe-player-stage");
const statusEl = document.getElementById("qe-player-status");
const frameEl = document.getElementById("qe-player-frame");

let client = null;
let joined = false;

const setStatus = (text) => {
  statusEl.textContent = text;
};

const renderFrame = (framePayload) => {
  if (window.qeSlideRenderer && typeof window.qeSlideRenderer.renderFrame === "function") {
    window.qeSlideRenderer.renderFrame(frameEl, framePayload, {
      fallbackTitle: t("player_session.stage", "Stage"),
      showPlaceholderNote: true,
    });
    return;
  }
  frameEl.textContent = t(
    "player_session.renderer_unavailable",
    "Renderer unavailable."
  );
};

const onMessage = (message) => {
  switch (message.type) {
    case "LOBBY_SNAPSHOT":
      if (message.payload.session_state) {
        stateEl.textContent = message.payload.session_state;
      }
      setStatus(t("player_session.in_lobby", "In lobby."));
      break;
    case "PLAYER_JOINED":
      if (!joined && message.payload.nickname === nicknameInput.value.trim()) {
        joined = true;
      }
      setStatus(
        t("player_session.player_joined", "{nickname} joined.", {
          nickname: message.payload.nickname,
        })
      );
      break;
    case "PLAYER_LEFT":
      setStatus(t("player_session.player_left", "A player left."));
      break;
    case "SESSION_STATE_CHANGED":
      stateEl.textContent = message.payload.session_state;
      setStatus(
        t("player_session.state_changed", "State changed: {state}.", {
          state: message.payload.session_state,
        })
      );
      break;
    case "STAGE_CHANGED":
      stageEl.textContent = `${message.payload.stage_id} (${message.payload.stage_index})`;
      break;
    case "PLUGIN_FRAME":
      renderFrame(message.payload);
      break;
    case "ERROR":
      setStatus(
        t("player_session.error", "Error: {message}", {
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
    role: "player",
    onOpen: () => {
      setStatus(t("player_session.connected", "Connected."));
      client.send("CONNECT", { role: "player" });
      if (nicknameInput.value.trim()) {
        client.send("JOIN_SESSION", { nickname: nicknameInput.value.trim() });
      }
    },
    onClose: () => {
      setStatus(t("player_session.disconnected", "Disconnected."));
      joined = false;
    },
    onMessage,
  });
};

joinButton.addEventListener("click", () => {
  const nickname = nicknameInput.value.trim();
  if (!nickname) {
    setStatus(t("player_session.nickname_required", "Nickname is required."));
    return;
  }
  client.send("JOIN_SESSION", { nickname });
});

leaveButton.addEventListener("click", () => {
  client.send("LEAVE_SESSION", {});
  joined = false;
  setStatus(t("player_session.left_session", "You left the session."));
});

connect();
