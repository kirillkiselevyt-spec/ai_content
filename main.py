import os
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# API KEY из Render ENV
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# МОДЕЛЬ (ВАЖНО — твоя актуальная)
MODEL_NAME = "models/gemini-3.5-flash"


class RequestData(BaseModel):
    prompt: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/generate")
def generate(data: RequestData):
    try:
        model = genai.GenerativeModel(MODEL_NAME)

        response = model.generate_content(data.prompt)

        # безопасное извлечение текста (фикс твоей ошибки 'choices')
        return {
            "result": response.text if hasattr(response, "text") else str(response)
        }

    except Exception as e:
        return {
            "error": "Gemini API error",
            "details": str(e)
        }
