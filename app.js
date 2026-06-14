const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

async function sendMessage() {
  const text = document.getElementById("userInput").value.trim();
  if (!text) return;

  const niche = document.getElementById("niche").value;
  const audience = document.getElementById("audience").value;
  const goal = document.getElementById("goal").value;
  const style = document.getElementById("style").value;

  addMessage(text, "user");
  document.getElementById("userInput").value = "";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text,
        niche,
        audience,
        goal,
        style
      })
    });

    const data = await res.json();

    const reply =
      data?.text ||
      data?.response ||
      data?.result ||
      "Ошибка API";

    addMessage(reply, "bot");

  } catch (err) {
    addMessage("Ошибка: " + err.message, "bot");
  }
}

function addMessage(text, type) {
  const chat = document.getElementById("chat");

  const div = document.createElement("div");
  div.classList.add("message", type);
  div.textContent = text;

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
