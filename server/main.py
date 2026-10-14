from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import app as leadgen_app

# CORS — allow the frontend origin
leadgen_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    port = int(__import__("os").environ.get("SERVER_PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
