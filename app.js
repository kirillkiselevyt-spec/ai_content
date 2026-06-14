const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

const USER_ID = localStorage.getItem("user_id") || crypto.randomUUID();
localStorage.setItem("user_id", USER_ID);

console.log("API:", API_URL);

async function generate() {

    const niche = document.getElementById("niche").value;
    const audience = document.getElementById("audience").value;
    const goal = document.getElementById("goal").value;
    const style = document.getElementById("style").value;

    const resultBlock = document.getElementById("result");

    if (!niche || !audience || !goal || !style) {
        resultBlock.innerText = "Заполни все поля";
        return;
    }

    resultBlock.innerText = "Генерация...";

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: USER_ID,
                niche,
                audience,
                goal,
                style
            })
        });

        const text = await res.text();
        console.log("RAW RESPONSE:", text);

        const data = JSON.parse(text);

        resultBlock.innerText = data.result || "Пустой ответ";

    } catch (err) {
        console.error("FETCH ERROR:", err);
        resultBlock.innerText = "Ошибка соединения с сервером";
    }
}
