const createButton = document.getElementById("create-session");
const sessionPanel = document.getElementById("session-panel");
const sessionCodeEl = document.getElementById("session-code");
const joinUrlEl = document.getElementById("join-url");
const qrImage = document.getElementById("qr-image");
const playerList = document.getElementById("player-list");
const pendingList = document.getElementById("pending-list");
const startButton = document.getElementById("start-session");
const endButton = document.getElementById("end-session");
const statusEl = document.getElementById("status");
const sessionStateEl = document.getElementById("session-state");
const t = window.qeI18n.t;

let socket = null;
let currentSessionCode = null;
const pendingRequests = new Map();

const setStatus = (text) => {
  statusEl.textContent = text;
};

const formatState = (state) => t(`state.${state}`);

const updatePlayers = (players) => {
  playerList.innerHTML = "";
  if (!players.length) {
    const empty = document.createElement("li");
    empty.textContent = t("host.js.no_players");
    playerList.appendChild(empty);
    return;
  }
  players.forEach((player) => {
    const item = document.createElement("li");
    item.classList.add("player-item");
    const label = document.createElement("span");
    label.textContent = `${player.nickname} (${player.player_id})`;
    const actions = document.createElement("div");
    actions.classList.add("item-actions");
    const kickButton = document.createElement("button");
    kickButton.className = "btn small danger";
    kickButton.textContent = t("host.js.kick");
    kickButton.addEventListener("click", () => {
      sendEvent("host_kick", { player_id: player.player_id });
    });
    actions.appendChild(kickButton);
    item.appendChild(label);
    item.appendChild(actions);
    playerList.appendChild(item);
  });
};

const updatePending = () => {
  pendingList.innerHTML = "";
  if (pendingRequests.size === 0) {
    const empty = document.createElement("li");
    empty.textContent = t("host.js.no_pending");
    pendingList.appendChild(empty);
    return;
  }
  pendingRequests.forEach((request, requestId) => {
    const item = document.createElement("li");
    item.classList.add("player-item");
    const label = document.createElement("span");
    label.textContent = request.nickname;
    const actions = document.createElement("div");
    actions.classList.add("item-actions");

    const approveButton = document.createElement("button");
    approveButton.className = "btn small";
    approveButton.textContent = t("host.js.approve");
    approveButton.addEventListener("click", () => {
      sendEvent("host_approve_join", { request_id: requestId });
      pendingRequests.delete(requestId);
      updatePending();
    });

    const rejectButton = document.createElement("button");
    rejectButton.className = "btn small danger";
    rejectButton.textContent = t("host.js.reject");
    rejectButton.addEventListener("click", () => {
      sendEvent("host_reject_join", { request_id: requestId });
      pendingRequests.delete(requestId);
      updatePending();
    });

    actions.appendChild(approveButton);
    actions.appendChild(rejectButton);
    item.appendChild(label);
    item.appendChild(actions);
    pendingList.appendChild(item);
  });
};

const sendEvent = (type, payload = {}) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setStatus(t("host.js.ws_not_connected"));
    return;
  }
  socket.send(
    JSON.stringify({
      v: "2",
      type,
      session_code: currentSessionCode,
      payload,
    })
  );
};

const connectHostSocket = (sessionCode) => {
  if (socket) {
    socket.close();
  }
  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${wsScheme}://${window.location.host}/ws?role=host&session_code=${sessionCode}`;
  socket = new WebSocket(wsUrl);

  socket.addEventListener("open", () => {
    setStatus(t("host.js.connected"));
  });

  socket.addEventListener("message", (event) => {
    let message = null;
    try {
      message = JSON.parse(event.data);
    } catch (error) {
      return;
    }
    if (!message || message.v !== "2") {
      return;
    }

    switch (message.type) {
      case "session_created":
        currentSessionCode = message.payload.session_code;
        sessionCodeEl.textContent = currentSessionCode;
        break;
      case "session_status":
        sessionStateEl.textContent = formatState(message.payload.current_state);
        break;
      case "lobby_snapshot":
        updatePlayers(message.payload.players || []);
        break;
      case "join_requested":
        pendingRequests.set(message.payload.request_id, {
          nickname: message.payload.nickname,
        });
        updatePending();
        setStatus(
          t("host.js.join_request_from", {
            nickname: message.payload.nickname,
          })
        );
        break;
      case "player_joined":
        setStatus(
          t("host.js.player_joined", { nickname: message.payload.nickname })
        );
        break;
      case "player_left":
        setStatus(t("host.js.player_left"));
        break;
      case "session_state_changed":
        sessionStateEl.textContent = formatState(message.payload.current_state);
        setStatus(
          t("host.js.session_state", {
            state: formatState(message.payload.current_state),
          })
        );
        break;
      case "error":
        setStatus(t("host.js.error", { message: message.payload.message }));
        break;
      default:
        break;
    }
  });

  socket.addEventListener("close", () => {
    setStatus(t("host.js.ws_disconnected"));
  });
};

createButton.addEventListener("click", async () => {
  setStatus(t("host.js.creating_session"));
  const response = await fetch("/api/sessions", { method: "POST" });
  if (!response.ok) {
    setStatus(t("host.js.create_failed"));
    return;
  }
  const data = await response.json();
  currentSessionCode = data.session_code;
  sessionCodeEl.textContent = data.session_code;
  joinUrlEl.textContent = data.join_url;
  qrImage.src = `/qr/${data.session_code}.png`;
  sessionStateEl.textContent = t("state.LOBBY");
  sessionPanel.classList.remove("hidden");
  pendingRequests.clear();
  updatePending();
  connectHostSocket(data.session_code);
  setStatus(t("host.js.session_ready"));
});

startButton.addEventListener("click", () => {
  if (!currentSessionCode) {
    return;
  }
  sendEvent("host_start");
});

endButton.addEventListener("click", () => {
  if (!currentSessionCode) {
    return;
  }
  sendEvent("host_end");
});
