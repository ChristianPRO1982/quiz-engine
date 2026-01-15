const sessionCode = window.__SESSION_CODE__;
const playerId = window.__PLAYER_ID__;
const statusEl = document.getElementById("player-status");
const questionEl = document.getElementById("player-question");

let currentQuestion = null;
let locked = false;

function wsUrl(path) {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}${path}`;
}

function renderQuestion() {
  if (!currentQuestion) {
    questionEl.innerHTML = "<p>Aucune question active.</p>";
    return;
  }
  const choices = currentQuestion.choices
    .map(
      (choice) => `
      <button class="choice-btn" data-choice="${choice.id}" ${
        locked ? "disabled" : ""
      }>
        ${choice.label}
      </button>
    `
    )
    .join("");

  questionEl.innerHTML = `
    <div class="question-card">
      <h3>${currentQuestion.prompt}</h3>
      <div class="choices">${choices}</div>
    </div>
  `;
}

const socket = new WebSocket(wsUrl(`/ws/player/${sessionCode}?player_id=${playerId}`));

socket.addEventListener("open", () => {
  statusEl.textContent = "Connecte";
});

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "SESSION_STATE") {
    locked = data.payload.locked;
    statusEl.textContent = `Phase: ${data.payload.phase}`;
    renderQuestion();
  }
  if (data.type === "QUESTION") {
    currentQuestion = data.payload.question;
    locked = data.payload.state.locked;
    renderQuestion();
  }
  if (data.type === "ERROR") {
    statusEl.textContent = data.payload.message;
  }
});

questionEl.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-choice]");
  if (!button || locked) {
    return;
  }
  const choiceId = Number(button.dataset.choice);
  socket.send(
    JSON.stringify({
      type: "PLAYER_ANSWER",
      payload: { question_id: currentQuestion.id, answer: { choice_id: choiceId } },
    })
  );
  locked = true;
  statusEl.textContent = "Reponse envoyee";
  renderQuestion();
});
