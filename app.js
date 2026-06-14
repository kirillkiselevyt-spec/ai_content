const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

// Получение или создание UUID пользователя в localStorage браузера
function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    userId = 'usr_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

async function generate() {
  const niche    = document.getElementById("niche").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const goal     = document.getElementById("goal").value.trim();
  const style    = document.getElementById("style").value;

  if (!niche || !audience || !goal) {
    showOutput("⚠️ Пожалуйста, заполните все поля перед генерацией.", true);
    return;
  }

  const prompt = `
Напиши контент для следующего запроса:

Ниша: ${niche}
Целевая аудитория: ${audience}
Цель: ${goal}
Стиль написания: ${styleLabel(style)}

Создай качественный, убедительный текст, полностью соответствующий указанным параметрам.
`.trim();

  setLoading(true);
  showOutput("⏳ Генерируем текст...", false);

  // Payload теперь включает метаданные и сгенерированный user_id для БД
  const payload = {
    user_id: getOrCreateUserId(),
    prompt: prompt,
    niche: niche,
    audience: audience,
    style: styleLabel(style)
  };

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errorDetail;
      } catch (_) {}
      showOutput(`❌ Ошибка: ${errorDetail}`, true);
      return;
    }

    const data = await response.json();

    if (data.result) {
      showOutput(data.result, false);
    } else {
      showOutput("❌ Сервер вернул пустой ответ.", true);
    }
  } catch (err) {
    console.error("Fetch error:", err);
    showOutput("❌ Не удалось подключиться к серверу. Проверьте интернет или деплой бэкенда.", true);
  } finally {
    setLoading(false);
  }
}

function styleLabel(value) {
  const labels = {
    formal:   "Официальный",
    friendly: "Дружелюбный",
    sales:    "Продающий",
    creative: "Креативный",
    minimal:  "Минимализм",
  };
  return labels[value] || value;
}

function showOutput(text, isError) {
  const output = document.getElementById("output");
  output.textContent = text;
  output.style.color = isError ? "#e74c3c" : "inherit";
}

function setLoading(isLoading) {
  const btn = document.querySelector("button");
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Генерируем..." : "Сгенерировать";
}
