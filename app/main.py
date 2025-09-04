from fastapi import FastAPI
from .db import ping_db
from fastapi.middleware.cors import CORSMiddleware

from .routers import sales_orders, customers, products, sales_persons, invoices

app = FastAPI(title="Sales API", version="0.1.0")

origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    # "http://127.0.0.1:8000"
    # You can add production domain later e.g. "https://yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

@app.get("/")
def read_root():
    return {"msg": "Hello World"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/__dbcheck")
async def dbcheck():
    await ping_db()
    return {"database": "ok"}


# API v1
app.include_router(sales_orders.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(sales_persons.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")

# uvicorn app.main:app --reload