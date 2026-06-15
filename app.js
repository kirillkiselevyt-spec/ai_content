const API_URL = "https://ai-bot-backend-x5nr.onrender.com/chat";

// ── User identity (persisted across sessions) ─────────────────────────────────
function getOrCreateUserId() {
  let id = localStorage.getItem("ai_user_id");
  if (!id) {
    id = "u_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("ai_user_id", id);
  }
  return id;
}

const userId = getOrCreateUserId();

// ── Conversation state ────────────────────────────────────────────────────────
// Kept in memory; cleared on page reload or clearChat().
// The last 20 turns are sent to the backend on each request.
let history = [];
let isLoading = false;

// ── UI helpers ────────────────────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

function handleKey(e) {
  // Send on Enter; allow Shift+Enter for new lines
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function scrollToBottom() {
  const el = document.getElementById("messages");
  el.scrollTop = el.scrollHeight;
}

// ── Text formatting (minimal markdown → HTML) ─────────────────────────────────
function formatText(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Bold: **text**
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    // Inline code: `code`
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    // Line breaks
    .replace(/\n/g, "<br>");
}

// ── Message rendering ─────────────────────────────────────────────────────────
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

  return wrapper; // return wrapper so we can append upgrade hint
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

// ── Soft conversion hint ──────────────────────────────────────────────────────
// Appended below the bot message wrapper, not inside the bubble —
// keeps it visually separate and unobtrusive.
function showUpgradeHint(messageWrapper) {
  const hint = document.createElement("div");
  hint.className = "upgrade-hint";
  hint.textContent =
    "💡 Эту задачу можно полностью автоматизировать. Напишите, если хотите настроить один раз — и оно работает само.";
  messageWrapper.appendChild(hint);
  scrollToBottom();
}

// ── Core send ─────────────────────────────────────────────────────────────────
async function sendMessage() {
  if (isLoading) return;

  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  // Clear input immediately
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
        history: history.slice(-20), // send last 20 turns for context
      }),
    });

    const data = await res.json();
    removeTyping();

    if (!res.ok) {
      addMessage("bot", `❌ ${data.detail || "Ошибка сервера. Попробуйте ещё раз."}`);
      return;
    }

    const botWrapper = addMessage("bot", data.result);
    history.push({ role: "assistant", content: data.result });

    // Show upgrade hint only when backend signals it's appropriate
    if (data.suggest_upgrade) {
      showUpgradeHint(botWrapper);
    }
  } catch (err) {
    removeTyping();
    addMessage(
      "bot",
      "❌ Не удалось подключиться к серверу. Проверьте соединение."
    );
    console.error("Fetch error:", err);
  } finally {
    isLoading = false;
    document.getElementById("sendBtn").disabled = false;
    input.focus();
  }
}

// ── Clear conversation ────────────────────────────────────────────────────────
function clearChat() {
  history = [];
  document.getElementById("messages").innerHTML = `
    <div class="message bot">
      <div class="bubble">
        Привет. Я ваш универсальный AI-ассистент — один инструмент вместо команды специалистов.<br><br>
        Задавайте любые задачи: стратегия бизнеса, написание текстов, технические вопросы, анализ данных, автоматизация процессов.
      </div>
    </div>
  `;
}

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener("load", () => {
  document.getElementById("userInput").focus();
});
