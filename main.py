from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
import httpx
import os

# Inicializa FastAPI
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringirlo luego
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Config Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Categorías fijas (puedes hacer esto dinámico más adelante)
CATEGORIES = ["Restauración", "Transporte", "Compras", "Suscripciones", "Otros"]

@app.get("/")
def root():
    return {"status": "alive"}

# Clasificar con GPT
async def categorize_transaction(merchant: str, amount: float):
    prompt = f"""
    Clasifica esta transacción: '{merchant}' por {amount}€.
    Categorías disponibles: {', '.join(CATEGORIES)}.
    Devuelve solo una categoría exacta.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en clasificación: {str(e)}")

# Guardar en Supabase
async def save_transaction(user_id: str, merchant: str, amount: float, category: str):
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": user_id,
        "merchant": merchant,
        "amount": amount,
        "category": category
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/transactions",
            headers=headers,
            json=payload
        )
        if response.status_code not in [200, 201]:
            raise Exception(f"Error al guardar en Supabase: {response.text}")

# Endpoint principal
@app.post("/transactions")
async def create_transaction(request: Request):
    try:
        data = await request.json()
        merchant = data.get("merchant")
        amount = float(data.get("amount", 0))

        if not merchant or amount <= 0:
            raise HTTPException(status_code=400, detail="Datos inválidos")

        category = await categorize_transaction(merchant, amount)

        # Aquí pondremos el user_id real cuando esté conectado Supabase Auth
        await save_transaction("user_demo", merchant, amount, category)

        return {
            "status": "ok",
            "category": category,
            "merchant": merchant,
            "amount": amount
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
