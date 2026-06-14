const API_URL = "https://ai-bot-backend-x5nr.onrender.com/generate";

async function generateContent() {

    const data = {
        user_id: "1",
        niche: document.getElementById("niche").value,
        audience: document.getElementById("audience").value,
        goal: document.getElementById("goal").value,
        style: document.getElementById("style").value
    };

    document.getElementById("output").innerText = "Генерация...";

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        console.log("SERVER RESPONSE:", result);

        document.getElementById("output").innerText =
            result.text || result.error || "Ошибка: пустой ответ";

    } catch (err) {
        document.getElementById("output").innerText =
            "Ошибка сети: " + err.message;
    }
}
