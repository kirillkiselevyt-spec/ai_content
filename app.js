const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

// создаём или берём уникального пользователя
const USER_ID = localStorage.getItem("user_id") || crypto.randomUUID();
localStorage.setItem("user_id", USER_ID);

async function generate() {
    const niche = document.getElementById("niche").value;
    const audience = document.getElementById("audience").value;
    const goal = document.getElementById("goal").value;
    const style = document.getElementById("style").value;

    const resultBlock = document.getElementById("result");

    // базовая валидация
    if (!niche || !audience || !goal || !style) {
        resultBlock.innerText = "Заполни все поля";
        return;
    }

    resultBlock.innerText = "Генерация идей...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: USER_ID,
                niche: niche,
                audience: audience,
                goal: goal,
                style: style
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        resultBlock.innerText = data.result || "Нет ответа от сервера";

    } catch (error) {
        console.error(error);
        resultBlock.innerText = "Ошибка подключения к серверу";
    }
}
