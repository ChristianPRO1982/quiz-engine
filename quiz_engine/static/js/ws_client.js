(function () {
  const buildWsUrl = (sessionCode, role) => {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const encoded = encodeURIComponent(sessionCode);
    return `${wsScheme}://${window.location.host}/ws/s/${encoded}?role=${encodeURIComponent(role)}`;
  };

  const createClient = ({ sessionCode, role, onMessage, onOpen, onClose }) => {
    const socket = new WebSocket(buildWsUrl(sessionCode, role));

    socket.addEventListener("open", () => {
      if (typeof onOpen === "function") {
        onOpen();
      }
    });

    socket.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data || typeof data.type !== "string" || typeof data.payload !== "object") {
          return;
        }
        if (typeof onMessage === "function") {
          onMessage(data);
        }
      } catch (_error) {
        // Ignore malformed frames.
      }
    });

    socket.addEventListener("close", () => {
      if (typeof onClose === "function") {
        onClose();
      }
    });

    return {
      send(type, payload = {}) {
        if (socket.readyState !== WebSocket.OPEN) {
          return;
        }
        socket.send(
          JSON.stringify({
            type,
            payload,
          })
        );
      },
      close() {
        socket.close();
      },
    };
  };

  window.qeWsClient = {
    createClient,
  };
})();
