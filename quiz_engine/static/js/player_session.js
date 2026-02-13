const bootstrapNode = document.getElementById("qe-player-bootstrap");
const bootstrap = bootstrapNode ? JSON.parse(bootstrapNode.textContent) : {};

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
  frameEl.innerHTML = "";

  const payload = framePayload.payload || {};
  const title = payload.title || "Stage";
  const body = payload.body || "";

  const card = document.createElement("article");
  card.className = "qe-card qe-card--compact qe-preview-frame";

  const heading = document.createElement("h2");
  heading.className = "qe-title";
  heading.textContent = title;
  card.appendChild(heading);

  if (body) {
    const paragraph = document.createElement("p");
    paragraph.className = "qe-hint";
    paragraph.textContent = body;
    card.appendChild(paragraph);
  }

  const media = payload.media;
  if (media && media.type === "image" && media.src) {
    const image = document.createElement("img");
    image.className = "qe-preview-image";
    image.src = media.src;
    image.alt = title;
    card.appendChild(image);
  }

  frameEl.appendChild(card);
};

const onMessage = (message) => {
  switch (message.type) {
    case "LOBBY_SNAPSHOT":
      if (message.payload.session_state) {
        stateEl.textContent = message.payload.session_state;
      }
      setStatus("In lobby.");
      break;
    case "PLAYER_JOINED":
      if (!joined && message.payload.nickname === nicknameInput.value.trim()) {
        joined = true;
      }
      setStatus(`${message.payload.nickname} joined.`);
      break;
    case "PLAYER_LEFT":
      setStatus("A player left.");
      break;
    case "SESSION_STATE_CHANGED":
      stateEl.textContent = message.payload.session_state;
      setStatus(`State changed: ${message.payload.session_state}.`);
      break;
    case "STAGE_CHANGED":
      stageEl.textContent = `${message.payload.stage_id} (${message.payload.stage_index})`;
      break;
    case "PLUGIN_FRAME":
      renderFrame(message.payload);
      break;
    case "ERROR":
      setStatus(`Error: ${message.payload.message}`);
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
      setStatus("Connected.");
      client.send("CONNECT", { role: "player" });
      if (nicknameInput.value.trim()) {
        client.send("JOIN_SESSION", { nickname: nicknameInput.value.trim() });
      }
    },
    onClose: () => {
      setStatus("Disconnected.");
      joined = false;
    },
    onMessage,
  });
};

joinButton.addEventListener("click", () => {
  const nickname = nicknameInput.value.trim();
  if (!nickname) {
    setStatus("Nickname is required.");
    return;
  }
  client.send("JOIN_SESSION", { nickname });
});

leaveButton.addEventListener("click", () => {
  client.send("LEAVE_SESSION", {});
  joined = false;
  setStatus("You left the session.");
});

connect();
