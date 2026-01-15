const sessionCode = window.__SESSION_CODE__;
const hostToken = window.__HOST_TOKEN__;
const statusEl = document.getElementById("host-status");
const questionArea = document.getElementById("question-area");
const playersCount = document.getElementById("players-count");

let currentQuestion = null;
let currentStats = null;

function wsUrl(path) {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}${path}`;
}

function renderQuestion() {
  if (!currentQuestion) {
    questionArea.innerHTML = "<p>Aucune question active.</p>";
    return;
  }
  const choices = currentQuestion.choices
    .map((choice) => {
      const count = currentStats?.by_choice?.find((item) => item.choice_id === choice.id)
        ?.count || 0;
      return `<li>${choice.label} <span class="pill">${count}</span></li>`;
    })
    .join("");
  questionArea.innerHTML = `
    <div class="question-card">
      <h3>${currentQuestion.prompt}</h3>
      <ul>${choices}</ul>
    </div>
  `;
}

const socket = new WebSocket(
  wsUrl(`/ws/host/${sessionCode}?token=${encodeURIComponent(hostToken)}`)
);

socket.addEventListener("open", () => {
  statusEl.textContent = "Connecte";
});

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "SESSION_STATE") {
    const payload = data.payload;
    statusEl.textContent = `Phase: ${payload.phase}`;
    playersCount.textContent = `${payload.players_count} joueurs`;
  }
  if (data.type === "QUESTION") {
    currentQuestion = data.payload.question;
    currentStats = null;
    renderQuestion();
  }
  if (data.type === "STATS") {
    currentStats = data.payload;
    renderQuestion();
  }
  if (data.type === "ERROR") {
    statusEl.textContent = data.payload.message;
  }
});

document.getElementById("next-btn").addEventListener("click", () => {
  socket.send(JSON.stringify({ type: "HOST_NEXT", payload: {} }));
});

document.getElementById("reveal-btn").addEventListener("click", () => {
  socket.send(JSON.stringify({ type: "HOST_REVEAL", payload: {} }));
});

document.getElementById("end-btn").addEventListener("click", () => {
  socket.send(JSON.stringify({ type: "HOST_END", payload: {} }));
});
