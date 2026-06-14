const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

async function sendMessage() {
  const input = document.getElementById("userInput");
  const chat = document.getElementById("chat");

  const text = input.value.trim();
  if (!text) return;

  // user message
  addMessage(text, "user");
  input.value = "";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text })
    });

    const data = await res.json();

    // защита от undefined / разных API форматов
    const reply =
      data?.text ||
      data?.answer ||
      data?.response ||
      data?.result ||
      "Ошибка: пустой ответ API";

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

  // кнопка копирования только для бота
  if (type === "bot") {
    const btn = document.createElement("button");
    btn.textContent = "Copy";
    btn.classList.add("copy-btn");

    btn.onclick = () => {
      navigator.clipboard.writeText(text);
      btn.textContent = "✓";
      setTimeout(() => (btn.textContent = "Copy"), 1000);
    };

    div.appendChild(btn);
  }

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

/* ENTER отправка */
document.getElementById("userInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
