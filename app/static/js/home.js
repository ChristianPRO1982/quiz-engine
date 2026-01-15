const startBtn = document.getElementById("start-btn");
const quizIdInput = document.getElementById("quiz-id");
const links = document.getElementById("links");
const joinLink = document.getElementById("join-link");
const hostLink = document.getElementById("host-link");

const demoQuiz = {
  title: "Quiz demo",
  questions: [
    {
      position: 0,
      kind: "MULTIPLE_CHOICE",
      prompt: "Quelle est la capitale de la France ?",
      choices: [
        { position: 0, label: "Paris" },
        { position: 1, label: "Lyon" },
        { position: 2, label: "Marseille" },
      ],
    },
    {
      position: 1,
      kind: "MULTIPLE_CHOICE",
      prompt: "Combien font 3 x 4 ?",
      choices: [
        { position: 0, label: "9" },
        { position: 1, label: "12" },
        { position: 2, label: "14" },
      ],
    },
  ],
};

async function createQuiz() {
  const response = await fetch("/quizzes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(demoQuiz),
  });
  if (!response.ok) {
    throw new Error("Impossible de creer le quiz.");
  }
  return response.json();
}

async function startSession(quizId) {
  const response = await fetch("/sessions/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ quiz_id: quizId }),
  });
  if (!response.ok) {
    throw new Error("Impossible de lancer la session.");
  }
  return response.json();
}

startBtn.addEventListener("click", async () => {
  startBtn.disabled = true;
  startBtn.textContent = "Chargement...";
  try {
    let quizId = Number(quizIdInput.value);
    if (!quizId) {
      const quiz = await createQuiz();
      quizId = quiz.id;
    }
    const session = await startSession(quizId);
    joinLink.href = session.join_url;
    joinLink.textContent = session.join_url;
    hostLink.href = `/host/${session.session_code}?token=${encodeURIComponent(
      session.host_token
    )}`;
    hostLink.textContent = hostLink.href;
    links.classList.remove("hidden");
  } catch (error) {
    alert(error.message);
  } finally {
    startBtn.disabled = false;
    startBtn.textContent = "Creer un quiz demo et lancer";
  }
});
