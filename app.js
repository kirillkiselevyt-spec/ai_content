const API_URL = "https://ai-bot-backend-x5nr.onrender.com";

function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    userId = 'usr_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

// Переключение панели истории (открыть/закрыть)
async function toggleHistory() {
  const panel = document.getElementById("history-panel");
  panel.classList.toggle("open");

  // Если панель открылась, загружаем свежие данные из базы данных
  if (panel.classList.contains("open")) {
    await fetchHistory();
  }
}

// Запрос истории с бэкенда
async function fetchHistory() {
  const contentDiv = document.getElementById("history-content");
  const userId = getOrCreateUserId();

  try {
    const response = await fetch(`${API_URL}/history/${userId}`);
    if (!response.ok) throw new Error("Ошибка загрузки");

    const data = await response.json();
    contentDiv.innerHTML = ""; // Очищаем заглушку загрузки

    if (!data.history || data.history.trim() === "" || data.history === "[]") {
      contentDiv.innerHTML = '<p class="empty-msg">У вас пока нет сохраненных генераций.</p>';
      return;
    }

    // Парсим текстовый лог истории на блоки
    const blocks = data.history.split("--- Новый запрос ---");
    
    blocks.forEach(block => {
      if (!block.trim()) return;

      // Извлекаем текст запроса и ответа
      const promptMatch = block.match(/Запрос:([\s\S]*?)(?=Ответ:|$)/);
      const resultMatch = block.match(/Ответ:([\s\S]*?)$/);

      if (promptMatch) {
        const itemDiv = document.createElement("div");
        itemDiv.className = "history-item";

        const promptTxt = promptMatch[1].trim();
        const resultTxt = resultMatch ? resultMatch[1].trim() : "Нет ответа";

        itemDiv.innerHTML = `
          <div class="history-item-prompt">📋 ${promptTxt.split('\n')[0]}...</div>
          <div class="history-item-result">${resultTxt}</div>
        `;
        // Добавляем новые элементы наверх списка
        contentDiv.insertBefore(itemDiv, contentDiv.firstChild);
      }
    });

  } catch (err) {
    console.error(err);
    contentDiv.innerHTML = '<p class="empty-msg" style="color: #ff453a;">❌ Не удалось загрузить историю запросов.</p>';
  }
}

// Основная функция генерации
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
`.trim();

  setLoading(true);
  showOutput("⏳ Генерируем текст...", false);

  const payload = {
    user_id: getOrCreateUserId(),
    prompt: prompt,
    niche: niche,
    audience: audience,
    style: styleLabel(style)
  };

  try {
    const response = await fetch(`${API_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      showOutput("❌ Ошибка при отправке запроса на бэкенд.", true);
      return;
    }

    const data = await response.json();
    if (data.result) {
      showOutput(data.result, false);
    } else {
      showOutput("❌ Сервер вернул пустой ответ.", true);
    }
  } catch (err) {
    console.error(err);
    showOutput("❌ Не удалось подключиться к серверу.", true);
  } finally {
    setLoading(false);
  }
}

function styleLabel(value) {
  const labels = { formal: "Официальный", friendly: "Дружелюбный", sales: "Продающий", creative: "Креативный", minimal: "Минимализм" };
  return labels[value] || value;
}

function showOutput(text, isError) {
  const output = document.getElementById("output");
  output.textContent = text;
  output.style.color = isError ? "#e74c3c" : "inherit";
}

function setLoading(isLoading) {
  const btn = document.getElementById("submit-btn");
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Генерируем..." : "Сгенерировать";
}
