from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (чтобы GitHub Pages работал)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEY
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RequestData(BaseModel):
    niche: str
    audience: str
    goal: str
    style: str

@app.post("/generate")
async def generate(data: RequestData):
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Ты профессиональный маркетолог.

    Ниша: {data.niche}
    Целевая аудитория: {data.audience}
    Цель контента: {data.goal}
    Стиль: {data.style}

    Сгенерируй 5 вирусных идей контента.
    Сделай их конкретными, цепляющими и применимыми.
    """

    response = model.generate_content(prompt)

    return {"result": response.text}
