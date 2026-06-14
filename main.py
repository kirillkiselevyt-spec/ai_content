import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "models/gemini-3.5-flash"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RequestData(BaseModel):
    user_id: str
    prompt: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"user_id": user_id, "history": ""}
    return {"user_id": user_id, "history": user.history}


@app.post("/generate")
def generate(data: RequestData, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.user_id == data.user_id).first()
        
        if not user:
            user = User(
                user_id=data.user_id,
                history=f"Запрос: {data.prompt}\n"
            )
            db.add(user)
        else:
            user.history = (user.history or "") + f"\n--- Новый запрос ---\nЗапрос: {data.prompt}\n"

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(data.prompt)

        result_text = response.text if hasattr(response, "text") else str(response)
        
        user.history += f"Ответ:\n{result_text}\n"
        db.commit()

        return {"result": result_text}

    except Exception as e:
        db.rollback()
        return {"error": "Gemini error", "details": str(e)}
