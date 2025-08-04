from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringirlo a ["https://tudominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi import FastAPI, Request, Header, HTTPException
import openai
import httpx
import os

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

CATEGORIES = ["Restauración", "Transporte", "Compras", "Suscripciones", "Otros"]

async def categorize_transaction(merchant: str, amount: float):
    prompt = f"""
    Clasifica esta transacción: '{merchant}' por {amount}€
    Categorías disponibles: {', '.join(CATEGORIES)}
    Devuelve solo una categoría exacta.
    """
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

@app.post("/transactions")
async def create_transaction(request: Request):
    data = await request.json()
    merchant = data["merchant"]
    amount = float(data["amount"])
    category = await categorize_transaction(merchant, amount)
    return {"status": "ok", "category": category}
