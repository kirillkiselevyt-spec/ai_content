const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

function getOrCreateUserId() {
  let userId = localStorage.getItem("ai_generator_user_id");
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem("ai_generator_user_id", userId);
  }
  return userId;
}

// Логика переключения красивого Apple селекта
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      showOutput(`❌ Ошибка: ${data.detail || 'Неизвестная ошибка сервера'}`, true);
      return;
    }

    if (data.result) {
      showOutput(data.result, false);
    } else {
      showOutput("❌ Сервер вернул пустой ответ.", true);
    }
  } catch (err) {
    console.error("Fetch error:", err);
    showOutput("❌ Не удалось подключиться к серверу. Проверьте сеть.", true);
  } finally {
    setLoading(false);
  }
}

function styleLabel(value) {
  const labels = { formal: "Официальный", friendly: "Дружелюбный", sales: "Продающий", creative: "Креативный", minimal: "Минимализм" };
  return labels[value] || value;
}

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

function setLoading(isLoading) {
  const btn = document.getElementById("submitBtn");
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Генерируем..." : "Сгенерировать";
}

function copyResult() {
  const output = document.getElementById("output");
  const copyBtnText = document.getElementById("copyBtnText");
  if (!output || output.textContent.startsWith("⏳") || output.textContent.startsWith("❌")) return;

  navigator.clipboard.writeText(output.textContent).then(() => {
    copyBtnText.innerText = 'Скопировано!';
    setTimeout(() => { copyBtnText.innerText = 'Скопировать'; }, 2000);
  }).catch(err => console.error('Ошибка буфера:', err));
}
