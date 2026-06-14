const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

async function generate() {
  const niche = document.getElementById("niche").value;
  const audience = document.getElementById("audience").value;
  const goal = document.getElementById("goal").value;
  const style = document.getElementById("style").value;

  const prompt = `
Ниша: ${niche}
Аудитория: ${audience}
Цель: ${goal}
Стиль: ${style}

Сгенерируй текст под эти параметры.
`;

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();

    document.getElementById("output").innerText =
      data.result || data.error || "Ошибка";
  } catch (err) {
    document.getElementById("output").innerText =
      "Ошибка: " + err.message;
  }
}
