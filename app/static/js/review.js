const sessionCode = window.__SESSION_CODE__;
const container = document.getElementById("review-content");

async function loadReview() {
  const response = await fetch(`/sessions/${sessionCode}/review`);
  if (!response.ok) {
    container.innerHTML = "<p>Relecture indisponible.</p>";
    return;
  }
  const data = await response.json();
  const questions = data.quiz.questions
    .sort((a, b) => a.position - b.position)
    .map((question) => {
      const answerStats = data.answers.find((item) => item.question_id === question.id);
      const byChoice = answerStats?.by_choice || [];
      const choices = question.choices
        .map((choice) => {
          const count = byChoice.find((entry) => entry.choice_id === choice.id)?.count || 0;
          return `<li>${choice.label} <span class="pill">${count}</span></li>`;
        })
        .join("");
      return `
        <div class="question-card">
          <h3>${question.prompt}</h3>
          <ul>${choices}</ul>
        </div>
      `;
    })
    .join("");
  container.innerHTML = `
    <p>${data.players_count} joueurs</p>
    ${questions}
  `;
}

loadReview();
