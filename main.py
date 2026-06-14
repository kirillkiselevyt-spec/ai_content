import os
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS FIX (обязательно для frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEY из Render
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ актуальная модель (из твоего списка)
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

        return {
            "result": response.text if hasattr(response, "text") else str(response)
        }

    except Exception as e:
        return {
            "error": "Gemini API error",
            "details": str(e)
        }
