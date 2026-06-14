import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Импортируем модули базы данных
from database import SessionLocal, engine, Base
from models import User

# Автоматически создаем таблицы в базе данных при старте приложения
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Разрешаем CORS, чтобы фронтенд мог беспрепятственно общаться с бэкендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция (Dependency) для безопасного управления сессиями БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация API-ключа Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Самая актуальная и быстрая модель
MODEL_NAME = "gemini-2.5-flash"

# Спецификация входных данных (DTO)
class RequestData(BaseModel):
    user_id: str
    prompt: str
    niche: str
    audience: str
    style: str


@app.get("/")
def root():
    return {"status": "ok", "database": "connected", "model": MODEL_NAME}


@app.post("/generate")
def generate(data: RequestData, db: Session = Depends(get_db)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="Ошибка конфигурации: на сервере Render не задан GEMINI_API_KEY."
        )

    try:
        # 1. Работа со слоем данных и историей пользователя
        user = db.query(User).filter(User.user_id == data.user_id).first()
        
        if not user:
            # Создаем нового пользователя, если он зашел впервые
            user = User(
                user_id=data.user_id,
                niche=data.niche,
                audience=data.audience,
                style=data.style,
                history=f"[История создана]\nЗапрос: {data.prompt}\n"
            )
            db.add(user)
        else:
            # Обновляем метаданные существующего пользователя и дополняем лог истории
            user.niche = data.niche
            user.audience = data.audience
            user.style = data.style
            user.history = (user.history or "") + f"\n--- Следующий запрос ---\nЗапрос: {data.prompt}\n"
        
        # 2. Инференс в нейросеть Gemini
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(data.prompt)

        if hasattr(response, "text") and response.text:
            generated_text = response.text
            
            # Дописываем успешный ответ ИИ в историю пользователя
            user.history += f"Ответ ИИ:\n{generated_text}\n"
            
            # Фиксируем транзакцию в SQLite
            db.commit()
            
            return {"result": generated_text}
        else:
            raise HTTPException(
                status_code=502, 
                detail="Модель Gemini вернула пустой ответ или контент заблокирован фильтрами."
            )

    except Exception as e:
        db.rollback()  # Откатываем изменения в БД при любом сбое
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )
