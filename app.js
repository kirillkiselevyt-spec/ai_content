const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

async function generate() {
    const niche = document.getElementById("niche").value;
    const audience = document.getElementById("audience").value;
    const goal = document.getElementById("goal").value;
    const style = document.getElementById("style").value;

    const resultBlock = document.getElementById("result");
    resultBlock.innerText = "Генерация...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ niche, audience, goal, style })
        });

        const data = await response.json();
        resultBlock.innerText = data.result;

    } catch (error) {
        resultBlock.innerText = "Ошибка: " + error;
    }
}
