from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai
import os

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringirlo por seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

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

    except openai.error.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
