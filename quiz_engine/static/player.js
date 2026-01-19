const sessionCodeInput = document.getElementById("session-code");
const nicknameInput = document.getElementById("nickname");
const joinButton = document.getElementById("join-session");
const leaveButton = document.getElementById("leave-session");
const statusEl = document.getElementById("status");

let socket = null;
let pendingJoin = false;

const setStatus = (text) => {
  statusEl.textContent = text;
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
      session_code: sessionCodeInput.value,
      payload,
    })
  );
};

const connectSocket = () => {
  if (socket && socket.readyState !== WebSocket.CLOSED) {
    return;
  }
  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${wsScheme}://${window.location.host}/ws?role=player`;
  socket = new WebSocket(wsUrl);

  socket.addEventListener("open", () => {
    setStatus("Connected. Ready to join.");
    if (pendingJoin) {
      pendingJoin = false;
      sendEvent("join_session", { nickname: nicknameInput.value.trim() });
    }
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
      case "lobby_snapshot":
        setStatus("In lobby.");
        break;
      case "player_joined":
        if (message.payload.player_id) {
          setStatus("Joined lobby.");
        }
        break;
      case "player_left":
        setStatus("Left lobby.");
        break;
      case "session_state_changed":
        setStatus(`Session is ${message.payload.current_state}.`);
        break;
      case "error":
        setStatus(`Error: ${message.payload.message}`);
        break;
      default:
        break;
    }
  });

  socket.addEventListener("close", () => {
    setStatus("Disconnected.");
  });
};

joinButton.addEventListener("click", () => {
  const nickname = nicknameInput.value.trim();
  if (!nickname) {
    setStatus("Please enter a nickname.");
    return;
  }
  pendingJoin = true;
  connectSocket();
  if (socket && socket.readyState === WebSocket.OPEN) {
    pendingJoin = false;
    sendEvent("join_session", { nickname });
  }
});

leaveButton.addEventListener("click", () => {
  sendEvent("leave_session");
});
