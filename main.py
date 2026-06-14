from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

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
    Ниша: {data.niche}
    Аудитория: {data.audience}
    Цель: {data.goal}
    Стиль: {data.style}

    Сгенерируй 5 вирусных идей контента
    """

    response = model.generate_content(prompt)

    return {"result": response.text}