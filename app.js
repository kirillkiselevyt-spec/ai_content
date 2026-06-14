const API_URL = "https://your-backend-url.com/generate";

async function generate() {
  const data = {
    niche: document.getElementById("niche").value,
    goal: document.getElementById("goal").value,
    tone: document.getElementById("tone").value,
    audience: document.getElementById("audience").value
  };

  document.getElementById("result").innerText = "Генерация...";

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  const json = await res.json();

  document.getElementById("result").innerText = json.result;
}