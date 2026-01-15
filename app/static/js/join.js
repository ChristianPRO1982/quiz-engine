const form = document.getElementById("join-form");
const nicknameInput = document.getElementById("nickname");
const sessionCode = document.getElementById("session-code").value;
const errorEl = document.getElementById("join-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.classList.add("hidden");
  const nickname = nicknameInput.value.trim();
  if (!nickname) {
    return;
  }
  try {
    const response = await fetch(`/sessions/${sessionCode}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nickname }),
    });
    if (!response.ok) {
      throw new Error("Impossible de rejoindre la session.");
    }
    const data = await response.json();
    window.location.href = `/play/${sessionCode}?player_id=${data.player_id}`;
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.classList.remove("hidden");
  }
});
