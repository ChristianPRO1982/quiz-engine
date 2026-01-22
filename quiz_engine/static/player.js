const sessionCodeInput = document.getElementById("session-code");
const nicknameInput = document.getElementById("nickname");
const joinButton = document.getElementById("join-session");
const leaveButton = document.getElementById("leave-session");
const statusEl = document.getElementById("status");
const t = window.qeI18n.t;

let socket = null;
let pendingJoin = false;
let joined = false;
let waitingApproval = false;

const setStatus = (text) => {
  statusEl.textContent = text;
};

const formatState = (state) => t(`state.${state}`);

const sendEvent = (type, payload = {}) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    setStatus(t("player.js.ws_not_connected"));
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
    setStatus(t("player.js.connected"));
    if (pendingJoin) {
      pendingJoin = false;
      waitingApproval = true;
      setStatus(t("player.js.join_request_sent"));
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
          setStatus(t("player.js.waiting_approval"));
        } else if (!joined) {
          setStatus(
            t("player.js.session_is", {
              state: formatState(message.payload.current_state),
            })
          );
        }
        break;
      case "join_approved":
        joined = true;
        pendingJoin = false;
        waitingApproval = false;
        setStatus(t("player.js.joined_lobby"));
        break;
      case "join_rejected":
        joined = false;
        pendingJoin = false;
        waitingApproval = false;
        setStatus(
          t("player.js.join_rejected", { reason: message.payload.reason })
        );
        break;
      case "lobby_snapshot":
        if (waitingApproval) {
          waitingApproval = false;
        }
        setStatus(t("player.js.in_lobby"));
        break;
      case "player_joined":
        if (message.payload.player_id) {
          setStatus(t("player.js.joined_lobby"));
        }
        break;
      case "player_left":
        setStatus(t("player.js.left_lobby"));
        break;
      case "player_kicked":
        joined = false;
        setStatus(t("player.js.player_kicked"));
        break;
      case "session_state_changed":
        setStatus(
          t("player.js.session_is", {
            state: formatState(message.payload.current_state),
          })
        );
        break;
      case "error":
        setStatus(t("player.js.error", { message: message.payload.message }));
        break;
      default:
        break;
    }
  });

  socket.addEventListener("close", () => {
    setStatus(t("player.js.disconnected"));
  });
};

joinButton.addEventListener("click", () => {
  const nickname = nicknameInput.value.trim();
  if (!nickname) {
    setStatus(t("player.js.enter_nickname"));
    return;
  }
  joined = false;
  pendingJoin = true;
  connectSocket();
  if (socket && socket.readyState === WebSocket.OPEN) {
    pendingJoin = false;
    waitingApproval = true;
    setStatus(t("player.js.join_request_sent"));
    sendEvent("join_session", { nickname });
  }
});

leaveButton.addEventListener("click", () => {
  sendEvent("leave_session");
});

connectSocket();
