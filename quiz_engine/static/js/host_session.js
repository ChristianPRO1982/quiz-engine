const bootstrapNode = document.getElementById("qe-host-bootstrap");
const bootstrap = bootstrapNode ? JSON.parse(bootstrapNode.textContent) : {};

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
    item.textContent = "No players yet.";
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
      fallbackTitle: "Stage",
      showPlaceholderNote: true,
    });
    return;
  }
  frameEl.textContent = "Renderer unavailable.";
};

const onMessage = (message) => {
  switch (message.type) {
    case "SESSION_CREATED":
      setStatus(`Session ready (${message.payload.session_code}).`);
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
      setStatus("Stage changed.");
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
    role: "host",
    onOpen: () => {
      setStatus("Connected.");
      client.send("CONNECT", { role: "host" });
    },
    onClose: () => {
      setStatus("Disconnected.");
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
