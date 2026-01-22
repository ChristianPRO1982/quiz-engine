const sessionCodeInput = document.getElementById("session-code");
const nicknameInput = document.getElementById("nickname");
const joinButton = document.getElementById("join-session");
const leaveButton = document.getElementById("leave-session");
const statusEl = document.getElementById("status");

let socket = null;
let pendingJoin = false;
let joined = false;
let waitingApproval = false;

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
      v: "2",
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
  const sessionCode = encodeURIComponent(sessionCodeInput.value);
  const wsUrl = `${wsScheme}://${window.location.host}/ws?role=player&session_code=${sessionCode}`;
  socket = new WebSocket(wsUrl);

  socket.addEventListener("open", () => {
    setStatus("Connected.");
    if (pendingJoin) {
      pendingJoin = false;
      waitingApproval = true;
      setStatus("Join request sent.");
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
    if (!message || message.v !== "2") {
      return;
    }

    switch (message.type) {
      case "session_status":
        if (waitingApproval && message.payload.current_state === "RUNNING") {
          setStatus("Waiting for host approval.");
        } else if (!joined) {
          setStatus(`Session is ${message.payload.current_state}.`);
        }
        break;
      case "join_approved":
        joined = true;
        pendingJoin = false;
        waitingApproval = false;
        setStatus("Joined lobby.");
        break;
      case "join_rejected":
        joined = false;
        pendingJoin = false;
        waitingApproval = false;
        setStatus(`Join rejected: ${message.payload.reason}`);
        break;
      case "lobby_snapshot":
        if (waitingApproval) {
          waitingApproval = false;
        }
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
      case "player_kicked":
        joined = false;
        setStatus("You were removed by the host.");
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
  joined = false;
  pendingJoin = true;
  connectSocket();
  if (socket && socket.readyState === WebSocket.OPEN) {
    pendingJoin = false;
    waitingApproval = true;
    setStatus("Join request sent.");
    sendEvent("join_session", { nickname });
  }
});

leaveButton.addEventListener("click", () => {
  sendEvent("leave_session");
});

connectSocket();
