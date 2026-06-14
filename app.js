// Backend URL (без слэша на конце)
const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

// Получение или создание уникального ID пользователя в localStorage браузера
function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    // Генерируем уникальный маркер пользователя
    userId = 'usr_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

// Главная функция генерации
async function generate() {
  // Считываем значения из полей
  const niche    = document.getElementById("niche").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const goal     = document.getElementById("goal").value.trim();
  const style    = document.getElementById("style").value;

  // Валидация на заполненность
  if (!niche || !audience || !goal) {
    showOutput("⚠️ Пожалуйста, заполните все поля перед генерацией.", true);
    return;
  }

  // Создаем структурированный промпт
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

  // Формируем объект данных для отправки на бэкенд
  const payload = {
    user_id: getOrCreateUserId(), // Передаем ID пользователя для истории
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

// Преобразование системного значения стиля в красивую строку
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

// Отображение текста в блоке вывода
function showOutput(text, isError) {
  const output = document.getElementById("output");
  output.textContent = text;
  output.style.color = isError ? "#e74c3c" : "inherit";
}

// Изменение состояния кнопки во время загрузки
function setLoading(isLoading) {
  const btn = document.querySelector("button");
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Генерируем..." : "Сгенерировать";
}
