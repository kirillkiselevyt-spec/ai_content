const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

function getUserId() {
  let id = localStorage.getItem("user_id");
  if (!id) {
    id = "user_" + Math.random().toString(36).substring(2, 15);
    localStorage.setItem("user_id", id);
  }
  return id;
}

let currentMode = "post";

function setMode(mode) {
  currentMode = mode;
}

async function generate() {
  const niche = document.getElementById("niche").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const goal = document.getElementById("goal").value.trim();
  const style = document.getElementById("style").value;

  if (!niche || !audience || !goal) {
    showOutput("Заполни все поля", true);
    return;
  }

  showOutput("Генерация...", false);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        user_id: getUserId(),
        niche,
        audience,
        goal,
        style,
        mode: currentMode
      })
    });

    const data = await res.json();
    showOutput(data.result, false);

  } catch (e) {
    showOutput("Ошибка", true);
  }
}

function showOutput(text, isError) {
  const container = document.getElementById("resultContainer");
  const output = document.getElementById("output");

  container.style.display = "block";
  output.textContent = text;
}