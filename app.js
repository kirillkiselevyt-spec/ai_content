const API_URL = "https://ai-bot-backend-x5nr.onrender.com";

function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    userId = 'usr_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

// Исправлено открытие кастомного списка стилей
function toggleSelect(event) {
  event.stopPropagation();
  document.getElementById("custom-select-wrapper").classList.toggle("open");
}

function selectOption(element) {
  const value = element.getAttribute("data-value");
  const label = element.textContent;
  
  document.getElementById("style").value = value;
  document.getElementById("selected-style-label").textContent = label;
  
  document.querySelectorAll(".custom-option").forEach(opt => opt.classList.remove("selected"));
  element.classList.add("selected");
}

document.addEventListener("click", () => {
  const wrapper = document.getElementById("custom-select-wrapper");
  if (wrapper) wrapper.classList.remove("open");
});

// Открытие панели истории запросов
async function toggleHistory() {
  const panel = document.getElementById("history-panel");
  panel.classList.toggle("open");
  if (panel.classList.contains("open")) {
    await fetchHistory();
  }
}

async function fetchHistory() {
  const contentDiv = document.getElementById("history-content");
  const userId = getOrCreateUserId();

  try {
    const response = await fetch(`${API_URL}/history/${userId}`);
    if (!response.ok) throw new Error();

    const data = await response.json();
    contentDiv.innerHTML = "";

    if (!data.history || data.history.trim() === "") {
      contentDiv.innerHTML = '<p class="empty-msg">История запросов пуста.</p>';
      return;
    }

    const blocks = data.history.split("--- Новый запрос ---");
    blocks.forEach(block => {
      if (!block.trim()) return;
      const promptMatch = block.match(/Запрос:([\s\S]*?)(?=Ответ:|$)/);
      const resultMatch = block.match(/Ответ:([\s\S]*?)$/);

      if (promptMatch) {
        const itemDiv = document.createElement("div");
        itemDiv.className = "history-item";
        const pTxt = promptMatch[1].trim().split('\n')[0];
        const rTxt = resultMatch ? resultMatch[1].trim() : "...";
        
        itemDiv.innerHTML = `
          <div class="history-item-prompt">${pTxt}</div>
          <div class="history-item-result">${rTxt}</div>
        `;
        contentDiv.insertBefore(itemDiv, contentDiv.firstChild);
      }
    });
  } catch (_) {
    contentDiv.innerHTML = '<p class="empty-msg" style="color: #e74c3c;">Не удалось получить историю.</p>';
  }
}

// Генерация контента
async function generate() {
  const niche    = document.getElementById("niche").value.trim();
  const audience = document.getElementById("audience").value.trim();
  const goal     = document.getElementById("goal").value.trim();
  const style    = document.getElementById("style").value;

  if (!niche || !audience || !goal) {
    showOutput("⚠️ Пожалуйста, заполните все поля перед генерацией.", true);
    return;
  }

  const promptText = `
Ниша: ${niche}
Целевая аудитория: ${audience}
Цель: ${goal}
Стиль: ${styleLabel(style)}
`.trim();

  setLoading(true);
  showOutput("⏳ Генерируем текст...", false);

  try {
    const response = await fetch(`${API_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: getOrCreateUserId(),
        prompt: promptText
      }),
    });

    const data = await response.json();
    if (response.ok && data.result) {
      showOutput(data.result, false);
    } else {
      showOutput(`❌ Ошибка: ${data.error || "Неизвестная ошибка"}`, true);
    }
  } catch (err) {
    showOutput("❌ Ошибка соединения с сервером.", true);
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
