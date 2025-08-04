from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
import os

app = FastAPI()

# CORS: permite que tu API reciba peticiones desde apps o navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza con tus dominios si quieres limitar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = ["Restauración", "Transporte", "Compras", "Suscripciones", "Otros"]

@app.get("/")
def root():
    return {"status": "alive"}

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

@app.post("/transactions")
async def create_transaction(request: Request):
    try:
        data = await request.json()
        merchant = data.get("merchant")
        amount = float(data.get("amount", 0))

        if not merchant or amount <= 0:
            raise HTTPException(status_code=400, detail="Datos inválidos")

        category = await categorize_transaction(merchant, amount)

        return {
            "status": "ok",
            "category": category,
            "merchant": merchant,
            "amount": amount
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
