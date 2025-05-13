from fastapi import FastAPI
from routes.messenger import messenger_router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# 🔁 Charge le fichier .env
load_dotenv()

app = FastAPI()

# CORS middleware to allow frontend to access these routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include messenger routes
app.include_router(messenger_router)

if __name__ == "__main__":
    import uvicorn
    print("DATABASE_URL =", os.getenv("DATABASE_URL"))  # Pour test
    uvicorn.run(app, host="0.0.0.0", port=8000)
