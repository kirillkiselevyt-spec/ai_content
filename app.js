// Константа URL бэкенда (без слэша на конце)
const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

// Генерация или извлечение UUID пользователя из памяти браузера
function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    userId = 'usr_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

async function generate() {
  // Безопасно считываем элементы интерфейса
  const niche    = document.getElementById("niche").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const goal     = document.getElementById("goal").value.trim();
  const style    = document.getElementById("style").value;

  // Первичная валидация на стороне клиента
  if (!niche || !audience || !goal) {
    showOutput("⚠️ Пожалуйста, заполните все обязательные поля перед отправкой.", true);
    return;
  }

  // Сборка структурированного промпта
  const prompt = `
Напиши контент для следующего запроса:

Ниша: ${niche}
Целевая аудитория: ${audience}
Цель: ${goal}
Стиль написания: ${styleLabel(style)}

Создай качественный, убедительный текст, полностью соответствующий указанным параметрам.
`.trim();

  setLoading(true);
  showOutput("⏳ Искусственный интеллект генерирует ваш контент...", false);

  // Формируем расширенный JSON-пакет данных, соответствующий Pydantic-модели бэкенда
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

    const data = await response.json();

    if (!response.ok) {
      showOutput(`❌ Ошибка сервера (${response.status}): ${data.detail || 'Неизвестный сбой'}`, true);
      return;
    }

    if (data.result) {
      showOutput(data.result, false);
    } else {
      showOutput("❌ Сервер обработал запрос, но вернул пустой результат.", true);
    }
  } catch (err) {
    console.error("Fetch error:", err);
    showOutput("❌ Сетевая ошибка. Не удалось связаться с сервером. Проверьте деплой на Render.", true);
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

// Вывод результатов и управление состояниями стилей контейнера
function showOutput(text, isError) {
  const container = document.getElementById("resultContainer");
  const title = document.getElementById("resultTitle");
  const output = document.getElementById("output");
  const copyBtn = document.getElementById("copyBtn");

  container.style.display = "block";
  output.textContent = text;
  
  if (isError) {
    output.style.color = "#ff453a";
    title.textContent = "Ошибка выполнения";
    title.classList.add("error-state");
    copyBtn.style.display = "none";
  } else {
    output.style.color = "inherit";
    title.textContent = "Результат генерации";
    title.classList.remove("error-state");
    copyBtn.style.display = "flex";
  }
}

// Управление состоянием кнопки отправки
function setLoading(isLoading) {
  const btn = document.getElementById("submitBtn");
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Генерируем..." : "Сгенерировать";
}

// Быстрое нативное копирование контента в буфер обмена
function copyResult() {
  const output = document.getElementById("output");
  const copyBtnText = document.getElementById("copyBtnText");
  
  if (!output || output.textContent.startsWith("⏳") || output.textContent.startsWith("❌")) return;

  navigator.clipboard.writeText(output.textContent).then(() => {
    copyBtnText.innerText = 'Скопировано!';
    setTimeout(() => {
      copyBtnText.innerText = 'Скопировать';
    }, 2000);
  }).catch(err => console.error('Не удалось скопировать текст:', err));
}
