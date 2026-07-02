from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.candidates import router as candidate_router

app = FastAPI(
    title="Molecule Atlas API",
    version="0.1.0",
    description="Candidate review API for small-molecule datasets.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidate_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
