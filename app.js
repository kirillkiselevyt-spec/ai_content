const API_URL = "https://ai-bot-backend-x5nr.onrender.com/chat";

function getOrCreateUserId() {
  let id = localStorage.getItem("ai_user_id");
  if (!id) {
    id = "u_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("ai_user_id", id);
  }
  return id;
}

const userId = getOrCreateUserId();
let history = [];
let isLoading = false;

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function scrollToBottom() {
  const el = document.getElementById("messages");
  el.scrollTop = el.scrollHeight;
}

function formatText(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

// ── Текстовое сообщение ───────────────────────────────────────────────────────
function addMessage(role, text) {
  const messagesEl = document.getElementById("messages");
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = formatText(text);

  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ── Сообщение с изображением ──────────────────────────────────────────────────
function addImageMessage(imageUrl, prompt) {
  const messagesEl = document.getElementById("messages");
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble bubble-image";

  // Скелетон пока грузится картинка
  bubble.innerHTML = `
    <div class="image-caption">🎨 Генерирую: <em>${prompt}</em></div>
    <div class="image-skeleton"></div>
  `;

  const img = document.createElement("img");
  img.alt = prompt;
  img.className = "generated-image";

  img.onload = () => {
    bubble.querySelector(".image-skeleton").replaceWith(img);

    // Кнопка скачать
    const dl = document.createElement("a");
    dl.href = imageUrl;
    dl.target = "_blank";
    dl.download = "image.jpg";
    dl.className = "image-download";
    dl.textContent = "⬇ Открыть в полном размере";
    bubble.appendChild(dl);

    scrollToBottom();
  };

  img.onerror = () => {
    bubble.querySelector(".image-skeleton").outerHTML =
      '<div style="color:#ff453a;font-size:13px">❌ Не удалось загрузить изображение</div>';
  };

  img.src = imageUrl;

  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function showTyping() {
  const messagesEl = document.getElementById("messages");
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.id = "typing-msg";
  wrapper.innerHTML =
    '<div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById("typing-msg");
  if (el) el.remove();
}

// ── Upgrade hint ──────────────────────────────────────────────────────────────
function showUpgradeHint(wrapper) {
  const hint = document.createElement("div");
  hint.className = "upgrade-hint";
  hint.textContent =
    "💡 Эту задачу можно полностью автоматизировать. Напишите, если хотите настроить один раз — и оно работает само.";
  wrapper.appendChild(hint);
  scrollToBottom();
}

// ── Отправка ──────────────────────────────────────────────────────────────────
async function sendMessage() {
  if (isLoading) return;

  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  autoResize(input);

  addMessage("user", text);
  history.push({ role: "user", content: text });

  isLoading = true;
  document.getElementById("sendBtn").disabled = true;
  showTyping();

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        message: text,
        history: history.slice(-20),
      }),
    });

    const data = await res.json();
    removeTyping();

    if (!res.ok) {
      addMessage("bot", `❌ ${data.detail || "Ошибка сервера."}`);
      return;
    }

    // ── Роутинг по типу ответа ─────────────────────────────────────────────
    if (data.type === "image") {
      addImageMessage(data.image_url, data.prompt);
      history.push({ role: "assistant", content: `[Изображение: ${data.prompt}]` });
    } else {
      const wrapper = addMessage("bot", data.result);
      history.push({ role: "assistant", content: data.result });
      if (data.suggest_upgrade) showUpgradeHint(wrapper);
    }

  } catch (err) {
    removeTyping();
    addMessage("bot", "❌ Не удалось подключиться к серверу.");
    console.error(err);
  } finally {
    isLoading = false;
    document.getElementById("sendBtn").disabled = false;
    input.focus();
  }
}

function clearChat() {
  history = [];
  document.getElementById("messages").innerHTML = `
    <div class="message bot">
      <div class="bubble">
        Привет. Я ваш универсальный AI-ассистент — один инструмент вместо команды специалистов.<br><br>
        Задавайте любые задачи: стратегия бизнеса, написание текстов, технические вопросы, анализ данных, автоматизация процессов.<br><br>
        Также умею <strong>генерировать изображения</strong> — просто напишите «нарисуй» или «сгенерируй картинку».
      </div>
    </div>
  `;
}

window.addEventListener("load", () => {
  document.getElementById("userInput").focus();
});
