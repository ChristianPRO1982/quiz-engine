const createButton = document.getElementById("create-session");
const sessionPanel = document.getElementById("session-panel");
const sessionCodeEl = document.getElementById("session-code");
const joinUrlEl = document.getElementById("join-url");
const qrImage = document.getElementById("qr-image");
const playerList = document.getElementById("player-list");
const startButton = document.getElementById("start-session");
const endButton = document.getElementById("end-session");
const statusEl = document.getElementById("status");
const sessionStateEl = document.getElementById("session-state");

let socket = null;
let currentSessionCode = null;

const setStatus = (text) => {
  statusEl.textContent = text;
};

const updatePlayers = (players) => {
  playerList.innerHTML = "";
  if (!players.length) {
    const empty = document.createElement("li");
    empty.textContent = "No players yet.";
    playerList.appendChild(empty);
    return;
  }
  players.forEach((player) => {
    const item = document.createElement("li");
    item.textContent = `${player.nickname} (${player.player_id})`;
    playerList.appendChild(item);
  });
};

const sendEvent = (type, payload = {}) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setStatus("WebSocket not connected.");
    return;
  }
  socket.send(
    JSON.stringify({
      v: "1",
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
    setStatus("Connected as host.");
  });

  socket.addEventListener("message", (event) => {
    let message = null;
    try {
      message = JSON.parse(event.data);
    } catch (error) {
      return;
    }
    if (!message || message.v !== "1") {
      return;
    }

    switch (message.type) {
      case "session_created":
        currentSessionCode = message.payload.session_code;
        sessionCodeEl.textContent = currentSessionCode;
        break;
      case "lobby_snapshot":
        updatePlayers(message.payload.players || []);
        break;
      case "player_joined":
        setStatus(`${message.payload.nickname} joined.`);
        break;
      case "player_left":
        setStatus("Player left.");
        break;
      case "session_state_changed":
        sessionStateEl.textContent = message.payload.current_state;
        setStatus(`Session state: ${message.payload.current_state}.`);
        break;
      case "error":
        setStatus(`Error: ${message.payload.message}`);
        break;
      default:
        break;
    }
  });

  socket.addEventListener("close", () => {
    setStatus("WebSocket disconnected.");
  });
};

createButton.addEventListener("click", async () => {
  setStatus("Creating session...");
  const response = await fetch("/api/sessions", { method: "POST" });
  if (!response.ok) {
    setStatus("Failed to create session.");
    return;
  }
  const data = await response.json();
  currentSessionCode = data.session_code;
  sessionCodeEl.textContent = data.session_code;
  joinUrlEl.textContent = data.join_url;
  qrImage.src = `/qr/${data.session_code}.png`;
  sessionStateEl.textContent = "LOBBY";
  sessionPanel.classList.remove("hidden");
  connectHostSocket(data.session_code);
  setStatus("Session ready.");
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
